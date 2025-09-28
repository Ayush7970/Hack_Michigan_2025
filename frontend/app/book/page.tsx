"use client";
import React from 'react'
import MiniNavbar from '@/components/MiniNavbar'
import { useState, useEffect, useRef } from 'react'
import { useRouter } from 'next/navigation';

import { sendInput } from '@/lib/services';

const Book = () => {
  const [input, setInput] = useState("");
  const router = useRouter();
  const [isRecording, setIsRecording] = useState(false);
  const [recognition, setRecognition] = useState(null);
  const textareaRef = useRef(null);

  // Initialize speech recognition
  useEffect(() => {
    if (typeof window !== 'undefined') {
      const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;

      if (SpeechRecognition) {
        const recognitionInstance = new SpeechRecognition();
        recognitionInstance.continuous = true;
        recognitionInstance.interimResults = true;
        recognitionInstance.lang = 'en-US';

        recognitionInstance.onstart = () => {
          console.log('Speech recognition started');
        };

        recognitionInstance.onresult = (event) => {
          let transcript = '';
          let finalTranscript = '';

          for (let i = event.resultIndex; i < event.results.length; i++) {
            const result = event.results[i];
            if (result.isFinal) {
              finalTranscript += result[0].transcript;
            } else {
              transcript += result[0].transcript;
            }
          }

          // Update input with both final and interim results
          if (finalTranscript) {
            setInput(prev => prev + finalTranscript + ' ');
          }
        };

        recognitionInstance.onerror = (event) => {
          console.error('Speech recognition error:', event.error);
          setIsRecording(false);
        };

        recognitionInstance.onend = () => {
          console.log('Speech recognition ended');
          setIsRecording(false);
        };

        setRecognition(recognitionInstance);
      } else {
        console.log('Speech recognition not supported');
      }
    }
  }, []);

  const toggleRecording = () => {
    if (!recognition) {
      alert('Speech recognition is not supported in your browser');
      return;
    }

    if (isRecording) {
      recognition.stop();
      setIsRecording(false);
    } else {
      recognition.start();
      setIsRecording(true);
    }
  };

  const handleSubmit = async () =>{
    if (input.trim()) {
      const result = await sendInput(input);
      localStorage.setItem('sendInput', JSON.stringify({result: result, originalInput: input}));
      router.push('/book/profile');
    }
  }
  return (
    <div className="min-h-screen flex flex-col">
      <MiniNavbar/>
      <div className="flex-1 flex items-center justify-center">
        <div className="-space-y-1 text-left">
          <h1 className='font-sans text-6xl font-medium tracking-tighter'><span className='text-primary'>Hello,</span> what service are you</h1>
          <h1 className='font-sans text-6xl font-medium tracking-tighter'  >looking for?</h1>
          <div className="relative mt-5">
            <textarea
              ref={textareaRef}
              value={input}
              onChange={(e)=>setInput(e.target.value)}
              placeholder='I need to hire a plumber tomorrow with a budget of $50'
              className="rounded-xl prompt-box w-5xl h-[23vh] text-lg p-2 px-4 font-inter bg-[#2B2B2B] border-[#979797] pr-32"
            />

            {/* Microphone Button */}
            <button
              onClick={toggleRecording}
              className={`absolute bottom-4 right-30 p-3 rounded-lg transition-all duration-200 ${
                isRecording
                  ? 'bg-red-500 text-white animate-pulse'
                  : 'bg-gray-600 text-gray-300 hover:bg-gray-500'
              }`}
              title={isRecording ? 'Stop recording' : 'Start recording'}
            >
              {isRecording ? (
                // Recording icon (square stop)
                <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
                  <rect x="6" y="6" width="10" height="10" rx="2"/>
                </svg>
              ) : (
                // Microphone icon
              <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" className="bi bi-mic-fill" viewBox="0 0 16 16">
               <path d="M5 3a3 3 0 0 1 6 0v5a3 3 0 0 1-6 0z"/>
              <path d="M3.5 6.5A.5.5 0 0 1 4 7v1a4 4 0 0 0 8 0V7a.5.5 0 0 1 1 0v1a5 5 0 0 1-4.5 4.975V15h3a.5.5 0 0 1 0 1h-7a.5.5 0 0 1 0-1h3v-2.025A5 5 0 0 1 3 8V7a.5.5 0 0 1 .5-.5"/>
              </svg>
              )}
            </button>

            {/* Recording Status Indicator */}
            {isRecording && (
              <div className="absolute bottom-4 left-4 flex items-center space-x-2 text-red-400 text-sm">
                <div className="w-2 h-2 bg-red-400 rounded-full animate-pulse"></div>
                <span>Recording...</span>
              </div>
            )}

            <button
              onClick={() => handleSubmit()}
              className="absolute bottom-4 right-3 bg-primary text-black font-mono px-6 py-2 rounded-lg hover:scale-105 transition-transform"
            >
              Find
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}


export default Book
