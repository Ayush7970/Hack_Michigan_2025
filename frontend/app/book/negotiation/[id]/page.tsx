"use client";
import React from 'react'
import MiniNavbar from '@/components/MiniNavbar'
import { useState, useEffect } from 'react'
import { useParams } from 'next/navigation'
import { sendNegotiationMessage, getConversation } from '@/lib/negotiationServices'


const NegotiationPage = () => {
  const params = useParams()
  const negotiationId = params.id as string

  const [name, setName] = useState("David Bowers");
  const [conversation, setConversation] = useState("Plumber");
  const [sendInputResult, setSendInputResult] = useState(null);
  const [address, setAddress] = useState(null);
  const [originalInput, setOriginalInput] = useState(null);
  const [messages, setMessages] = useState([]);
  const [currentInput, setCurrentInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [negotiationComplete, setNegotiationComplete] = useState(false);
  const [agentProfile, setAgentProfile] = useState(null);

  useEffect(() => {
    const profileData = localStorage.getItem(`profileData_${negotiationId}`);
    if (profileData) {
      const parsedData = JSON.parse(profileData);
      setSendInputResult(parsedData.originalMatchData);
      setAddress(parsedData.address);
      setName(parsedData.name);
      setConversation(parsedData.job);
      setOriginalInput(parsedData.originalInput);

      // Set up agent profile for negotiation
      const matchData = parsedData.originalMatchData;
      if (matchData && matchData.matched_uagent) {
        setAgentProfile(matchData.matched_uagent);
      }

      console.log("Profile data:", parsedData);

      // Start conversation with original input if available
      if (parsedData.originalInput && matchData?.matched_uagent) {
        startNegotiation(parsedData.originalInput, matchData.matched_uagent);
      }
    } else {
      // If no profile data, try to load existing conversation
      loadConversation();
    }
  }, [negotiationId]);

  const startNegotiationWithId = async (initialMessage: string, profile: any, convId: string) => {
    setIsLoading(true);
    try {
      const response = await sendNegotiationMessage(initialMessage, profile, convId);
      if (response && response.success) {
        // Load the conversation to get all messages
        loadConversationWithId(convId);
      }
    } catch (error) {
      console.error("Error starting negotiation:", error);
    } finally {
      setIsLoading(false);
    }
  };

  const startNegotiation = async (initialMessage: string, profile: any) => {
    setIsLoading(true);
    try {
      const response = await sendNegotiationMessage(initialMessage, profile, negotiationId);
      if (response && response.success) {
        // Load the conversation to get all messages
        loadConversation();
      }
    } catch (error) {
      console.error("Error starting negotiation:", error);
    } finally {
      setIsLoading(false);
    }
  };

  const loadConversationWithId = async (convId: string) => {
    try {
      const data = await getConversation(convId);
      if (data && data.messages) {
        const formattedMessages = data.messages.map((msg) => ({
          role: msg.role === 'agent' ? 'agent' : 'user',
          content: msg.content,
          timestamp: new Date(msg.timestamp)
        }));
        setMessages(formattedMessages);
        setNegotiationComplete(data.is_complete || false);
      }
    } catch (error) {
      console.error("Error loading conversation:", error);
    }
  };

  const loadConversation = async () => {
    try {
      const data = await getConversation(negotiationId);
      if (data && data.messages) {
        const formattedMessages = data.messages.map((msg) => ({
          role: msg.role === 'agent' ? 'agent' : 'user',
          content: msg.content,
          timestamp: new Date(msg.timestamp)
        }));
        setMessages(formattedMessages);
        setNegotiationComplete(data.is_complete || false);

        // If we have agent profile from conversation, set it
        if (data.agent_profile && !agentProfile) {
          setAgentProfile(data.agent_profile);
          setName(data.agent_profile.name || "Agent");
          setConversation(data.agent_profile.job || "Service Provider");
        }
      }
    } catch (error) {
      console.error("Error loading conversation:", error);
    }
  };

  const sendMessage = async () => {
    if (!currentInput.trim() || !agentProfile || isLoading || negotiationComplete) return;

    const messageToSend = currentInput.trim();
    setCurrentInput("");
    setIsLoading(true);

    try {
      const response = await sendNegotiationMessage(messageToSend, agentProfile, negotiationId);

      if (response && response.success) {
        // Reload conversation to get updated messages
        await loadConversation();
        console.log("✅ Message sent and conversation updated");
      } else {
        throw new Error("Failed to send message");
      }
    } catch (error) {
      console.error("💥 Error sending message:", error);
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
    <div className="min-h-screen  text-white flex flex-col">
      <MiniNavbar/>

      {/* Header */}
      <div className="p-4 px-16 font-mono border-gray-800">
        <h2 className="text-xl font-semibold">Negotiating with {name}</h2>
        <p className="text-gray-400">{conversation}</p>
        <p className="text-xs text-gray-500">ID: {negotiationId}</p>
        {negotiationComplete && (
          <div className="mt-2 px-3 py-1 bg-green-900 text-green-200 rounded-full text-sm inline-block">
            Negotiation Complete
          </div>
        )}
      </div>

      {/* Messages */}
      <div className="flex-1 font-inter overflow-y-auto p-4 px-16 space-y-4">
        {messages.map((message, index) => (
          <div
            key={index}
            className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
          >
            <div
              className={`max-w-[70%] p-3 rounded-lg ${
                message.role === 'user'
                  ? 'border-1-primary text-white'
                  : message.role === 'system'
                  ? 'bg-red-900 text-red-200'
                  : 'bg-gray-800 text-white'
              }`}
            >
              <p className="whitespace-pre-wrap">{message.content}</p>
              
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

      
    </div>
  )
}


export default NegotiationPage
