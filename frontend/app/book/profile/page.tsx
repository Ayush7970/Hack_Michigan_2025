"use client";
import React from 'react'
import MiniNavbar from '@/components/MiniNavbar'
import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'


const Book = () => {
  const [name, setName] = useState("David Bowers");
  const [job, setJob] = useState("Plumber");
  const [location, setLocation] = useState("Ann Arbor, MI");
  const [avgPrice, setAvgPrice] = useState("$45/hr");
  const [sendInputResult, setSendInputResult] = useState(null);
  const router = useRouter();

  useEffect(() => {
    const result = localStorage.getItem('sendInput');
    
    if (result) {
      const parsedResult = JSON.parse(result);
      setSendInputResult(parsedResult);
      console.log(parsedResult);
      localStorage.removeItem('sendInput');

      // Extract data from the result structure
      const matchData = parsedResult.result;
      setJob(matchData?.matched_uagent?.job || "Plumber");
      setName(matchData?.matched_uagent?.name || "David Bowers");
      setLocation((matchData?.matched_uagent?.location || ["Ann Arbor", "MI"]).join(", "));
      setAvgPrice(`$${matchData?.matched_uagent?.averagePrice || 45}/hr`);
    }
  }, []);

  const nextPage = () => {
    // Generate unique negotiation ID
    const negotiationId = `conv_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;

    const profileData = {
      name,
      job,
      location,
      avgPrice,
      address: sendInputResult?.result?.matched_address,
      originalInput: sendInputResult?.originalInput,
      originalMatchData: sendInputResult?.result
    };

    // Store profile data with unique key for this negotiation
    localStorage.setItem(`profileData_${negotiationId}`, JSON.stringify(profileData));

    // Navigate to the dynamic route with the unique ID
    router.push(`/book/negotiation/${negotiationId}`);
  }
  return (
    <div className="min-h-screen relative">
      <MiniNavbar/>
      <div className="profile font-sans font-medium absolute inset-0 flex flex-col items-center justify-center">
        <h2 className='text-2xl'>{name}</h2>
        <h2 className='text-lg'>{job} | {location}</h2>
        <h2 className='text-lg'>{avgPrice}</h2>

        <div className="box w-[45vh] mt-10 h-[45vh] bg-gray-300"></div>

        <button onClick={()=> nextPage()} className='font-mono mt-6 bg-primary py-2 px-5 text-black rounded-3xl'>Continue</button>
      </div>
    </div>
  )
}


export default Book
