"use client";
import Image from "next/image";
import Navbar from "../components/Navbar";
import ParticlesBackground from "../components/ParticlesBackground";
import Link from "next/link";
import { useEffect, useRef, useState } from "react";

// Custom hook for scroll animations
function useScrollAnimation() {
  const [isVisible, setIsVisible] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          setIsVisible(true);
        }
      },
      { threshold: 0.1 }
    );

    if (ref.current) {
      observer.observe(ref.current);
    }

    return () => {
      if (ref.current) {
        observer.unobserve(ref.current);
      }
    };
  }, []);

  return { ref, isVisible };
}

// Typewriter component
function TypewriterText({
  text,
  delay = 50,
  className,
  shouldStart = false
}: {
  text: string,
  delay?: number,
  className?: string,
  shouldStart?: boolean
}) {
  const [displayText, setDisplayText] = useState("");

  useEffect(() => {
    if (!shouldStart) {
      setDisplayText(""); // Reset when shouldStart is false
      return;
    }

    let timeoutId: NodeJS.Timeout;
    let currentIndex = 0;
    setDisplayText(""); // Reset before starting

    const typeNextChar = () => {
      if (currentIndex < text.length) {
        setDisplayText(text.slice(0, currentIndex + 1));
        currentIndex++;
        timeoutId = setTimeout(typeNextChar, delay);
      }
    };

    // Start typing
    timeoutId = setTimeout(typeNextChar, 100);

    return () => clearTimeout(timeoutId);
  }, [text, delay, shouldStart]);

  return (
    <p className={className}>
      {displayText}
    </p>
  );
}

// Animated agent box component
function AnimatedAgentBox({
  label,
  text,
  isMyAgent = false,
  delay = 0
}: {
  label: string,
  text: string,
  isMyAgent?: boolean,
  delay?: number
}) {
  const { ref, isVisible } = useScrollAnimation();
  const [showTypewriter, setShowTypewriter] = useState(false);

  useEffect(() => {
    if (isVisible) {
      const timer = setTimeout(() => {
        setShowTypewriter(true);
      }, 800 + delay); // Wait for fade-up animation to complete
      return () => clearTimeout(timer);
    } else {
      setShowTypewriter(false); // Reset when not visible
    }
  }, [isVisible, delay]);

  const textAlign = isMyAgent ? "text-right" : "text-left";

  return (
    <div
      ref={ref}
      className={`transition-all duration-500 ${
        isVisible ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-8'
      }`}
      style={{ transitionDelay: `${delay}ms` }}
    >
      <p className={`font-mono mb-2 ${textAlign}`}>{label}</p>
      <div className="example font-mono text-md bg-[#2B2B2B] gap-10 rounded-xl">
        <TypewriterText
          text={text}
          className="text-white min-h-20 w-80 p-3 px-4 flex items-center"
          delay={30}
          shouldStart={showTypewriter}
        />
      </div>
    </div>
  );
}

export default function Home() {
  return (
    <div className="font-sans items-center justify-items-center min-h-screen pb-20">
      <Navbar/>
      <div className="hero h-[calc(100vh-120px)] relative flex items-center justify-center tracking-tighter font-sans font-medium text-6xl text-white w-screen bg-[linear-gradient(to_right,#ffffff20_1px,transparent_1px),linear-gradient(to_bottom,#ffffff20_1px,transparent_1px)] bg-[size:50px_50px]">
        {/* Left side images */}
        <div className="absolute left-50 top-1/2 transform -translate-y-1/2 space-y-16">
          <img src="camera.png" alt="cam" className="w-20 h-20 float1" />
          <img src="plumb.png" alt="plumb" className="w-20 h-20 float2" />
        </div>

        <div className="text-center space-y-3">
          <h1>Automize Negotiations.</h1>
          <h1 className="text-primary">Save your time.</h1>
          <Link className="text-xl tracking-normal text-black font-mono bg-primary p-2 px-8 rounded-xl book-button" href='/book'>Book Services</Link>
        </div>

        <div className="absolute right-50 top-1/2 transform -translate-y-1/2 space-y-16   ">
          <img src="art.png" alt="art" className="w-20   h-20  float3" />
          <img src="hand.png" alt="hand" className="w-20   h-20  float4" />
        </div>
      </div>
      <div className="hero-lower text-center mt-21 font-mono font-bold text-3xl">
        <h1>Let your personal AI Agent</h1>
        <h1>negotiate for you.</h1>
      </div>
      <div className="extended">
        <div className="box flex mt-14 items-center justify-evenly gap-13 ">
          <h1 className="font-sans font-medium text-3xl">Find a service</h1>
          <AnimatedAgentBox
            label="My Agent"
            text="I need an experienced cameraman tomorrow at 9AM-12PM with a budget of $50/hour for a beach event. Travel covered."
            isMyAgent={true}
            delay={0}
          />
        </div>
        <div className="box flex mt-14 items-center justify-evenly gap-13 ">
          <div className="huge flex flex-col items-center gap-5">
            <AnimatedAgentBox
              label="Photographer Agent"
              text="$90 would work best. I  give professional shots and had experience with various influencers."
              isMyAgent={false}
              delay={200}
            />
            <AnimatedAgentBox
              label="My Agent"
              text="What about $60? You get free travel to the beach."
              isMyAgent={true}
              delay={400}
            />
            <AnimatedAgentBox
              label="Photographer Agent"
              text="Let’s meet at $70. I can’t go anywhere below that. I have experience with tons of influencers."
              isMyAgent={false}
              delay={600}
            />
            <AnimatedAgentBox
              label="My Agent"
              text="What about $60? You get free travel to the beach."
              isMyAgent={false}
              delay={600}
            />
          </div>
          <h1 className="font-sans font-medium text-3xl">Negotiate fast</h1>
        </div>
<div className="box flex mt-14 items-center justify-evenly gap-13 ">
          <h1 className="font-sans  font-medium text-3xl">Secure the deal</h1>
          <div className="huge flex flex-col items-center gap-5">
            <AnimatedAgentBox
              label="Photographer Agent"
              text="Perfect! Let's finalize this deal."
              isMyAgent={false}
              delay={0}
            />
            <AnimatedAgentBox
              label="My Agent"
              text="Great. I'll generate the contract."
              isMyAgent={true}
              delay={200}
            />
          </div>
        </div>
      </div>
    </div>
  );
}
