# negotiation_protocol.py
from __future__ import annotations
from typing import List, Optional, Literal, Tuple
from pydantic import BaseModel, Field, validator
from enum import Enum
from datetime import datetime, timedelta

# =========================
#  A. SHARED DATA MODELS
# =========================

class DaySlot(BaseModel):
    """Single availability slot in local time."""
    day: Literal["Mon","Tue","Wed","Thu","Fri","Sat","Sun"]
    start: str  # "HH:MM" 24h
    end: str    # "HH:MM" 24h

    @validator("start","end")
    def _hhmm(cls, v: str) -> str:
        hh, mm = v.split(":")
        assert 0 <= int(hh) <= 23 and 0 <= int(mm) <= 59, "HH:MM invalid"
        return v

class Location(BaseModel):
    address_line: str
    city: str
    state: str
    zip: str

class JobSpec(BaseModel):
    """What the customer wants fixed."""
    category: Literal["plumbing"]
    summary: str  # e.g., "Fix leaking kitchen sink"
    details: str  # freeform details

class MoneyRange(BaseModel):
    """Budget or acceptable rate band in USD."""
    min_usd: float
    target_usd: float
    max_usd: float

    @validator("min_usd","target_usd","max_usd")
    def _nonneg(cls, v: float) -> float:
        assert v >= 0, "Money must be non-negative"
        return v

    @validator("target_usd")
    def _order(cls, v: float, values):
        if "min_usd" in values and "max_usd" in values:
            assert values["min_usd"] <= v <= values["max_usd"], "target must lie in [min, max]"
        return v

class Window(BaseModel):
    """When the job should be completed (due-by window)."""
    latest_completion_utc: str  # ISO timestamp "2025-09-30T23:59:00Z"
    earliest_start_utc: Optional[str] = None

class Constraints(BaseModel):
    """Hard constraints the agent will not violate."""
    must_finish_by_utc: Optional[str] = None
    max_visits: int = 1  # how many site visits allowed
    on_site_required: bool = True
    parts_included: bool = False

class Party(BaseModel):
    name: str
    role: Literal["buyer","provider"]
    # reservation values (outside option) that cap the negotiation
    reservation_price_min: Optional[float] = None  # for provider: minimum acceptable total
    reservation_price_max: Optional[float] = None  # for buyer: maximum acceptable total

class NegotiationInit(BaseModel):
    """Initial request from the Buyer to open negotiation."""
    request_id: str
    buyer: Party
    provider: Party
    job: JobSpec
    location: Location
    week_availability: List[DaySlot]
    budget: MoneyRange
    window: Window
    constraints: Constraints
    currency: Literal["USD"] = "USD"
    max_rounds: int = 6

class Offer(BaseModel):
    request_id: str
    round: int
    from_party: Literal["buyer","provider"]
    price_usd: float
    # schedule: chosen slot(s) that fit both parties
    proposed_slots: List[DaySlot]
    duration_minutes: int
    includes_parts: bool
    notes: str = ""
    # optional light-weight line items
    line_items: Optional[List[Tuple[str,float]]] = None  # e.g., [("labor",200),("parts",50)]

class Decision(str, Enum):
    ACCEPT = "ACCEPT"
    COUNTER = "COUNTER"
    REJECT = "REJECT"

class Response(BaseModel):
    """Counter-offer or terminal decision."""
    request_id: str
    round: int
    decision: Decision
    offer: Optional[Offer] = None  # present only when COUNTER
    reason: Optional[str] = None

class Contract(BaseModel):
    """Final document we emit on ACCEPT."""
    contract_id: str
    request_id: str
    buyer: Party
    provider: Party
    job: JobSpec
    location: Location
    scheduled_slot: DaySlot
    duration_minutes: int
    price_usd: float
    includes_parts: bool
    currency: Literal["USD"] = "USD"
    terms: List[str]
    created_utc: str

# =========================
#  B. CORE UTILITIES
# =========================

def _hhmm_to_minutes(hhmm: str) -> int:
    h, m = [int(x) for x in hhmm.split(":")]
    return h*60 + m

def slot_overlap(a: DaySlot, b: DaySlot) -> Optional[Tuple[int,int]]:
    """Return overlapping (start_min,end_min) on same day or None."""
    if a.day != b.day:
        return None
    s1, e1 = _hhmm_to_minutes(a.start), _hhmm_to_minutes(a.end)
    s2, e2 = _hhmm_to_minutes(b.start), _hhmm_to_minutes(b.end)
    s, e = max(s1, s2), min(e1, e2)
    return (s, e) if s < e else None

def choose_feasible_slot(buyer_slots: List[DaySlot], provider_slots: List[DaySlot], min_duration_min: int) -> Optional[DaySlot]:
    """Pick the earliest overlapping slot with at least min_duration_min."""
    for bs in buyer_slots:
        for ps in provider_slots:
            ov = slot_overlap(bs, ps)
            if ov:
                s, e = ov
                if e - s >= min_duration_min:
                    # choose bs.day with start=s and end=s+min_duration_min
                    start_h = s // 60
                    start_m = s % 60
                    end   = s + min_duration_min
                    end_h = end // 60
                    end_m = end % 60
                    return DaySlot(day=bs.day,
                                   start=f"{start_h:02d}:{start_m:02d}",
                                   end=f"{end_h:02d}:{end_m:02d}")
    return None

def score_offer(offer: Offer, buyer: NegotiationInit, provider_min_price: float) -> float:
    """
    Higher is better for mutual feasibility.
    Factors:
      - price within buyer budget / provider min
      - duration non-crazy
      - at least one proposed slot
    """
    score = 0.0
    # price fit
    if buyer.budget.min_usd <= offer.price_usd <= buyer.budget.max_usd:
        score += 0.5
        # bonus for near target
        score += max(0, 0.2 - abs(offer.price_usd - buyer.budget.target_usd)/max(1.0,buyer.budget.target_usd)) 
    # provider constraint
    if offer.price_usd >= provider_min_price:
        score += 0.2
    # duration (heuristic: 30–240 min reasonable)
    if 30 <= offer.duration_minutes <= 240:
        score += 0.1
    # proposed slot presence
    if offer.proposed_slots:
        score += 0.2
    return score

def price_concession(current: float, target: float, round_idx: int, max_rounds: int) -> float:
    """
    Geometric/linear hybrid concession toward target.
    Earlier rounds: larger moves; later: smaller.
    """
    frac = min(1.0, (round_idx+1)/max_rounds)
    # 65% linear + 35% easing
    return current + (target - current) * (0.65*frac + 0.35*(1 - (1-frac)**2))

def bounded(x: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, x))

# =========================
#  C. NEGOTIATION POLICY
# =========================

class Policy(BaseModel):
    """Deterministic policy each side follows (plus LLM guidance)."""
    min_duration_minutes: int = 60
    allow_parts: bool = False
    concession_pct_cap: float = 0.20  # don't move more than ±20% from last price per round
    polite_language: bool = True

def propose_initial_offer(init: NegotiationInit, provider_availability: List[DaySlot], provider_min_price: float, policy: Policy) -> Offer:
    slot = choose_feasible_slot(init.week_availability, provider_availability, policy.min_duration_minutes)
    # Start from buyer target, but respect provider min
    start_price = max(provider_min_price, init.budget.target_usd)
    return Offer(
        request_id=init.request_id,
        round=1,
        from_party="provider",
        price_usd=start_price,
        proposed_slots=[slot] if slot else [],
        duration_minutes=policy.min_duration_minutes,
        includes_parts=policy.allow_parts and init.constraints.parts_included,
        notes="Initial proposal",
        line_items=None
    )

def counter_offer(prev: Offer, init: NegotiationInit, actor: Party, other_party_min_or_max: float, policy: Policy, provider_availability: Optional[List[DaySlot]]=None) -> Offer:
    """
    Make a bounded concession on price and try to tighten time choice.
    - If actor is buyer: move price downward toward buyer.target_usd (but >= provider_min).
    - If actor is provider: move price upward toward provider minimum or stay near prev, but within buyer max.
    """
    is_buyer = actor.role == "buyer"
    tgt = init.budget.target_usd
    min_p = init.budget.min_usd
    max_p = init.budget.max_usd
    # other_party_min_or_max: provider_min when buyer is acting, buyer_max when provider is acting
    current = prev.price_usd

    if is_buyer:
        ideal = bounded(tgt, other_party_min_or_max, max_p)
        new_price = price_concession(current, ideal, prev.round, init.max_rounds)
        # cap movement per round
        cap = policy.concession_pct_cap * max(1.0, current)
        new_price = bounded(new_price, current - cap, current + cap)
        new_price = max(new_price, other_party_min_or_max)  # provider min
    else:
        # provider moves toward buyer's target but not below provider min
        ideal = max(other_party_min_or_max, tgt)
        new_price = price_concession(current, ideal, prev.round, init.max_rounds)
        cap = policy.concession_pct_cap * max(1.0, current)
        new_price = bounded(new_price, current - cap, current + cap)
        new_price = min(new_price, max_p)

    # Try to propose a concrete feasible slot
    if provider_availability:
        slot = choose_feasible_slot(init.week_availability, provider_availability, policy.min_duration_minutes)
    else:
        slot = prev.proposed_slots[0] if prev.proposed_slots else None

    return Offer(
        request_id=init.request_id,
        round=prev.round + 1,
        from_party=actor.role,
        price_usd=round(new_price, 2),
        proposed_slots=[slot] if slot else [],
        duration_minutes=prev.duration_minutes,
        includes_parts=prev.includes_parts,
        notes=f"Counter by {actor.role}"
    )

def should_accept(offer: Offer, init: NegotiationInit, actor: Party, provider_min_price: float, min_score: float=0.75) -> bool:
    score = score_offer(offer, init, provider_min_price)
    # Accept if price in acceptable range for actor and score is high
    if actor.role == "buyer":
        ok_price = init.budget.min_usd <= offer.price_usd <= init.budget.max_usd
        return ok_price and score >= min_score
    else:
        ok_price = offer.price_usd >= (actor.reservation_price_min or provider_min_price)
        return ok_price and score >= min_score

def terminal_decision_for(offer: Offer, init: NegotiationInit, actor: Party, provider_min_price: float, round_idx: int) -> Response:
    """
    Actor decides on the received offer.
    Priority:
      1) Accept if fits constraints & high score
      2) Counter if rounds remain and feasible path exists
      3) Reject otherwise
    """
    if should_accept(offer, init, actor, provider_min_price):
        return Response(request_id=init.request_id, round=offer.round, decision=Decision.ACCEPT, reason="Meets constraints and target.")

    # If reached max rounds, reject
    if round_idx >= init.max_rounds:
        return Response(request_id=init.request_id, round=offer.round, decision=Decision.REJECT, reason="Reached max rounds without agreement.")

    return Response(request_id=init.request_id, round=offer.round, decision=Decision.COUNTER)

def build_contract(request_id: str, buyer: Party, provider: Party, job: JobSpec, location: Location, offer: Offer) -> Contract:
    now = datetime.utcnow().isoformat() + "Z"
    slot = offer.proposed_slots[0] if offer.proposed_slots else DaySlot(day="Mon", start="09:00", end="10:00")
    terms = [
        "Provider will perform the specified plumbing work professionally and safely.",
        "Payment due at completion unless otherwise agreed in writing.",
        "Cancellations require 12-hour notice.",
        "Any extra parts beyond initial estimate require written approval."
    ]
    return Contract(
        contract_id=f"ctr_{request_id}",
        request_id=request_id,
        buyer=buyer,
        provider=provider,
        job=job,
        location=location,
        scheduled_slot=slot,
        duration_minutes=offer.duration_minutes,
        price_usd=offer.price_usd,
        includes_parts=offer.includes_parts,
        terms=terms,
        created_utc=now
    )

# =========================
#  D. LLM PROMPT HELPERS
# =========================

def buyer_llm_prompt(init: NegotiationInit, last_offer: Optional[Offer]) -> str:
    """
    Instruct buyer LLM to return STRICT JSON Response schema only.
    """
    baseline = f"""
You are BUYER. Negotiate strictly within these constraints:
- Budget: min={init.budget.min_usd}, target={init.budget.target_usd}, max={init.budget.max_usd} USD.
- Must finish by: {init.window.latest_completion_utc}.
- Availability: {[s.dict() for s in init.week_availability]}.
- Max rounds: {init.max_rounds}.

You MUST return JSON ONLY in this exact pydantic schema for Response:
{Response.schema_json(indent=2)}

If you COUNTER, you MUST include an Offer matching this schema:
{Offer.schema_json(indent=2)}

Guidelines:
- Prefer feasible overlapping times from Availability.
- Keep tone concise. No prose outside JSON.
- Never exceed max budget.
- Accept when the offer meets constraints and is near target.
"""
    if last_offer:
        baseline += f"\nLast offer:\n{last_offer.json()}\n"
    return baseline.strip()

def provider_llm_prompt(init: NegotiationInit, provider_availability: List[DaySlot], provider_min_price: float, last_offer: Optional[Offer]) -> str:
    baseline = f"""
You are PROVIDER (Plumber). Your minimum acceptable price is {provider_min_price} USD.
Your availability: {[s.dict() for s in provider_availability]}.
Job must finish by {init.window.latest_completion_utc}.
Max rounds: {init.max_rounds}.

Return JSON ONLY as Response (exact schema shown below). If COUNTER, include Offer schema exactly.

Response schema:
{Response.schema_json(indent=2)}

Offer schema:
{Offer.schema_json(indent=2)}

Guidelines:
- Never go below your minimum price.
- Propose concrete slots that overlap with buyer availability.
- Keep concessions per round reasonable; keep within buyer's max.
- Accept when price >= min and constraints are satisfied.
"""
    if last_offer:
        baseline += f"\nLast offer:\n{last_offer.json()}\n"
    return baseline.strip()
