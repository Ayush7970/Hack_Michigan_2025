"use client";
import React from 'react'
import MiniNavbar from '@/components/MiniNavbar'
import { useState } from 'react'


const Book = () => {
  const [name, setName] = useState("David Bowers");
  const [job, setJob] = useState("Plumber");
  const [location, setLocation] = useState("Ann Arbor, MI");
  const [avgPrice, setAvgPrice] = useState("$45/hr");
  return (
    <div className="min-h-screen relative">
      <MiniNavbar/>
      <div className="profile font-sans font-medium absolute inset-0 flex flex-col items-center justify-center">
        <h2 className='text-2xl'>{name}</h2>
        <h2 className='text-lg'>{job} | {location}</h2>
        <h2 className='text-lg'>{avgPrice}</h2>

        <div className="box w-[45vh] mt-10 h-[45vh] bg-gray-300"></div>

        Loading..
      </div>
    </div>
  )
}


export default Book
