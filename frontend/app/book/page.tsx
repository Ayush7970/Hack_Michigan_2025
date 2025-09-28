"use client";
import React from 'react'
import MiniNavbar from '@/components/MiniNavbar'
import { useState } from 'react'


const Book = () => {
  const [input, setInput] = useState("");
  return (
    <div className="min-h-screen flex flex-col">
      <MiniNavbar/>
      <div className="flex-1 flex items-center justify-center">
        <div className="-space-y-1 text-left">
          <h1 className='font-sans text-6xl font-medium tracking-tighter'><span className='text-primary'>Hello,</span> what service are you</h1>
          <h1 className='font-sans text-6xl font-medium tracking-tighter'  >looking for?</h1>
          <div className="relative mt-5">
            <textarea onChange={(e)=>setInput(e.target.value)} placeholder='I need to hire a plumber tomorrow with a budget of $50' className="rounded-xl prompt-box w-5xl h-[23vh] text-lg p-2 px-4 font-inter bg-[#2B2B2B] border-[#979797] pr-20"></textarea>
            <button className="absolute bottom-4 right-3 bg-primary text-black font-mono px-6 py-2 rounded-lg hover:scale-105 transition-transform">Find</button>
          </div>
        </div>
      </div>
    </div>
  )
}


export default Book
