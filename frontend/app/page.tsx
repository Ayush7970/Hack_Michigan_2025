"use client";
import Image from "next/image";
import Navbar from "../components/Navbar";
import Link from "next/link";


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
      <div className="hero-lower text-center mt-21 font-mono font-bold text-2xl">
        <h1>Let your personal AI Agent</h1>
        <h1>negotiate for you.</h1>
      </div>
    </div>
  );
}
