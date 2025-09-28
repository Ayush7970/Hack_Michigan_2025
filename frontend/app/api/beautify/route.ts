import { NextResponse } from "next/server";
import { GoogleGenerativeAI } from "@google/generative-ai";

export const runtime = "nodejs"; // ensure fs/network OK on server

export async function POST(req: Request) {
  try {
    const { text } = await req.json();
    if (!text || typeof text !== "string") {
      return new NextResponse("Bad Request: missing 'text' string", { status: 400 });
    }

    const apiKey = process.env.GEMINI_API_KEY;
    if (!apiKey) {
      return new NextResponse("Server Misconfig: GEMINI_API_KEY not set", { status: 500 });
    }

    const genAI = new GoogleGenerativeAI(apiKey);
    // Use a fast, capable model. Swap if you prefer another:
    const model = genAI.getGenerativeModel({ model: "gemini-2.0-flash" });

    const prompt = `
You are a formatter. Take the raw conversation or notes below and produce a clean, concise,
professional PDF-ready text. Use clear headings, bullet points, and short lines suitable for A4 PDF
wrapping. Keep it strictly TEXT ONLY (no markdown syntax like **, #, or code fences).
Include:

- Title line
- Summary section (3–5 bullets)
- Key Details (bullet points)
- Action Items / Next Steps
- If it's a contract, add: Parties, Scope, Timeline, Payment Terms, Acceptance

Raw input:
----
${text}
----
Return only the formatted text.
    `.trim();

    const result = await model.generateContent(prompt);
    const out = result.response.text().trim();

    return new NextResponse(out, {
      status: 200,
      headers: { "Content-Type": "text/plain; charset=utf-8" },
    });
  } catch (err: any) {
    return new NextResponse(
      `Beautify error: ${err?.message ?? "unknown error"}`,
      { status: 500, headers: { "Content-Type": "text/plain; charset=utf-8" } }
    );
  }
}