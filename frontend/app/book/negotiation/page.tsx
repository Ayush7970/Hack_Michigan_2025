"use client";
import React from 'react'
import MiniNavbar from '@/components/MiniNavbar'
import { useState, useEffect } from 'react'
import { sendInput, getConversation } from '@/lib/negotiationServices'


const Book = () => {
  const [name, setName] = useState("David Bowers");
  const [conversation, setConversation] = useState("Plumber");
  const [sendInputResult, setSendInputResult] = useState(null);
  const [address, setAddress] = useState(null);
  const [originalInput, setOriginalInput] = useState(null);
  const [messages, setMessages] = useState([]);
  const [currentInput, setCurrentInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [negotiationComplete, setNegotiationComplete] = useState(false);
  const [lastMessageCount, setLastMessageCount] = useState(0);

  useEffect(() => {
    const profileData = localStorage.getItem('profileData');
    if (profileData) {
      const parsedData = JSON.parse(profileData);
      setSendInputResult(parsedData.originalMatchData);
      setAddress(parsedData.address);
      setName(parsedData.name);
      setConversation(parsedData.job);
      setOriginalInput(parsedData.originalInput);
      console.log("Profile data:", parsedData);
      localStorage.removeItem('profileData');

      // Initialize conversation with original input if available
      if (parsedData.originalInput) {
        setMessages([
          { role: 'user', content: parsedData.originalInput, timestamp: new Date() }
        ]);
      }
    }
  }, []);

  // Poll for conversation updates
  useEffect(() => {
    if (!address) return;

    const pollConversation = async () => {
      try {
        const data = await getConversation();
        if (data && data.messages) {
          // Only update if we have new messages
          if (data.messages.length > lastMessageCount) {
            const formattedMessages = data.messages.map((msg, index) => ({
              role: msg.role === 'buyer' ? 'user' : msg.role === 'seller' ? 'agent' : msg.role,
              content: msg.content,
              timestamp: new Date()
            }));
            setMessages(formattedMessages);
            setLastMessageCount(data.messages.length);
          }

          // Update negotiation status
          setNegotiationComplete(data.is_complete || false);
        }
      } catch (error) {
        console.error("Error polling conversation:", error);
      }
    };

    // Poll every 2 seconds
    const interval = setInterval(pollConversation, 2000);

    // Initial poll
    pollConversation();

    return () => clearInterval(interval);
  }, [address, lastMessageCount]);

  const sendMessage = async () => {
    if (!currentInput.trim() || !address || isLoading || negotiationComplete) return;

    console.log("🚀 FRONTEND: About to send message");
    console.log("📨 Message:", currentInput.trim());
    console.log("🎯 Address:", address);
    console.log("🔗 API URL: http://localhost:8001/rest/post");

    const messageToSend = currentInput.trim();
    setCurrentInput("");
    setIsLoading(true);

    try {
      const response = await sendInput(messageToSend, address);
      console.log("📡 FRONTEND: API Response:", response);

      if (response && response.success) {
        // The conversation will be updated via polling
        console.log("✅ FRONTEND: Message sent successfully");
      } else {
        console.error("❌ FRONTEND: API returned unsuccessful response:", response);
        throw new Error("Failed to send message");
      }
    } catch (error) {
      console.error("💥 FRONTEND: Error sending message:", error);
      const errorMessage = {
        role: 'system',
        content: 'Failed to send message. Please try again.',
        timestamp: new Date()
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };
  return (
    <div className="min-h-screen bg-black text-white flex flex-col">
      <MiniNavbar/>

      {/* Header */}
      <div className="p-4 border-b border-gray-800">
        <h2 className="text-xl font-semibold">Negotiating with {name}</h2>
        <p className="text-gray-400">{conversation}</p>
        {negotiationComplete && (
          <div className="mt-2 px-3 py-1 bg-green-900 text-green-200 rounded-full text-sm inline-block">
            Negotiation Complete
          </div>
        )}
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.map((message, index) => (
          <div
            key={index}
            className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
          >
            <div
              className={`max-w-[70%] p-3 rounded-lg ${
                message.role === 'user'
                  ? 'bg-primary text-black'
                  : message.role === 'system'
                  ? 'bg-red-900 text-red-200'
                  : 'bg-gray-800 text-white'
              }`}
            >
              <p className="whitespace-pre-wrap">{message.content}</p>
              <p className="text-xs opacity-60 mt-1">
                {message.timestamp.toLocaleTimeString()}
              </p>
            </div>
          </div>
        ))}

        {isLoading && (
          <div className="flex justify-start">
            <div className="bg-gray-800 text-white p-3 rounded-lg">
              <div className="flex space-x-1">
                <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></div>
                <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{animationDelay: '0.1s'}}></div>
                <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{animationDelay: '0.2s'}}></div>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Input */}
      {!negotiationComplete && (
        <div className="border-t border-gray-800 p-4">
          <div className="flex space-x-2">
            <textarea
              value={currentInput}
              onChange={(e) => setCurrentInput(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="Type your message..."
              className="flex-1 bg-gray-800 text-white p-3 rounded-lg resize-none focus:outline-none focus:ring-2 focus:ring-primary"
              rows={1}
              disabled={isLoading}
            />
            <button
              onClick={sendMessage}
              disabled={isLoading || !currentInput.trim()}
              className="px-6 py-3 bg-primary text-black rounded-lg font-medium disabled:opacity-50 disabled:cursor-not-allowed hover:scale-105 transition-transform"
            >
              Send
            </button>
          </div>
        </div>
      )}
    </div>
  )
}


export default Book
