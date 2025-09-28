"use client";
import React from 'react'
import MiniNavbar from '@/components/MiniNavbar'
import { useState } from 'react'


const Book = () => {
  const [name, setName] = useState("David Bowers");
  const [conversation, setConversation] = useState("Plumber");
  return (
    <div className="min-h-screen relative">
      <MiniNavbar/>
      <div className="profile font-sans font-medium absolute inset-0 flex flex-col items-center justify-center">
        
      </div>
    </div>
  )
}


export default Book
