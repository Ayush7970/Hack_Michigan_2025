"use client";
import Image from "next/image";
import Navbar from "../components/Navbar";
import Link from "next/link";
import Graph3D from "../components/Graph3D";

export default function Home() {
      return (
        <div className="font-sans items-center justify-items-center min-h-screen pb-20 relative overflow-hidden">
          {/* Gradient Background */}
          <div className="absolute inset-0 w-full h-full bg-gradient-to-b from-black via-yellow-600 to-yellow-400"></div>
          
          {/* 3D Graph Background */}
          <div className="absolute inset-0 w-full h-full">
            <Graph3D onServiceFound={() => {}} />
          </div>
      
      {/* Content overlay */}
      <div className="relative z-10">
        <Navbar/>
        <div className="hero h-[calc(100vh-120px)] relative flex items-center justify-center tracking-tighter font-sans font-medium text-6xl text-white w-screen">
              <div className="text-center space-y-3 z-20">
                <h1 className="drop-shadow-2xl">Automize Negotiations.</h1>
                <h1 className="text-primary drop-shadow-2xl">Save your time.</h1>
                <div className="flex gap-4 justify-center">
                  <Link className="text-xl tracking-normal text-black font-mono bg-primary p-2 px-8 rounded-xl book-button hover:bg-yellow-300 transition-colors" href='/book'>Book Services</Link>
                  <Link className="text-xl tracking-normal text-black font-mono bg-white/20 backdrop-blur-sm p-2 px-8 rounded-xl hover:bg-white/30 transition-colors" href='/conversations'>Live Conversations</Link>
                </div>
              </div>
        </div>
        
      </div>
      
          {/* Footer */}
          <footer className="relative z-20 text-center py-16">
            <div className="font-mono text-xl text-white font-bold">
              <h1>Let your personal AI Agent</h1>
              <h1>negotiate for you.</h1>
            </div>
          </footer>
    </div>
  );
}
