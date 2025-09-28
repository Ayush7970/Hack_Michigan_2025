"use client";
import React from 'react'
import MiniNavbar from '@/components/MiniNavbar'
import { useState, useEffect, useRef } from 'react'
import { sendNegotiationMessage, getConversation } from '@/lib/negotiationServices'
import { io, Socket } from 'socket.io-client'
import Link from 'next/link';

const Book = () => {
  const [name, setName] = useState("David Bowers");
  const [conversation, setConversation] = useState("Plumber");
  const [sendInputResult, setSendInputResult] = useState(null);
  const [address, setAddress] = useState(null);
  const [originalInput, setOriginalInput] = useState(null);
  const [messages, setMessages] = useState<Array<{
    role: string;
    content: string;
    timestamp: Date;
    isTyping?: boolean;
    displayContent?: string;
  }>>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [negotiationComplete, setNegotiationComplete] = useState(false);
  const [conversationId, setConversationId] = useState('default');
  const [agentProfile, setAgentProfile] = useState(null);
  const [socket, setSocket] = useState<Socket | null>(null);
  const socketRef = useRef<Socket | null>(null);

  // Typing animation function
  const typeMessage = (messageId: number, fullContent: string, delay: number = 30) => {
    let currentIndex = 0;
    const typingInterval = setInterval(() => {
      if (currentIndex <= fullContent.length) {
        setMessages(prev => prev.map((msg, index) => 
          index === messageId 
            ? { ...msg, displayContent: fullContent.slice(0, currentIndex), isTyping: currentIndex < fullContent.length }
            : msg
        ));
        currentIndex++;
      } else {
        clearInterval(typingInterval);
        // Mark as not typing when done
        setMessages(prev => prev.map((msg, index) => 
          index === messageId 
            ? { ...msg, isTyping: false }
            : msg
        ));
      }
    }, delay);
  };

  useEffect(() => {
    const profileData = localStorage.getItem('profileData');
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

      // Create unique conversation ID
      const newConversationId = `conv_${Date.now()}`;
      setConversationId(newConversationId);

      console.log("Profile data:", parsedData);
      localStorage.removeItem('profileData');

      // Store the data for later use when WebSocket is ready
      setOriginalInput(parsedData.originalInput);
      setAgentProfile(matchData?.matched_uagent);
    }
  }, []);

  // WebSocket connection and event handling
  useEffect(() => {
    if (conversationId && conversationId !== 'default') {
      console.log('🔌 Connecting to WebSocket for conversation:', conversationId);
      
      // Create socket connection
      const newSocket = io('http://localhost:8001', {
        transports: ['websocket', 'polling']
      });
      
      socketRef.current = newSocket;
      setSocket(newSocket);

      // Join conversation room
      newSocket.emit('join_conversation', { conversation_id: conversationId });

          // Handle new messages
          newSocket.on('new_message', (data) => {
            console.log('📨 Received new message:', data);
            console.log('📨 Message role:', data.role);
            console.log('📨 Message content:', data.content);
            const newMessage = {
              role: data.role,
              content: data.content,
              timestamp: new Date(),
              isTyping: true,
              displayContent: ''
            };
            setMessages(prev => {
              console.log('📨 Adding message to state. Current messages:', prev.length);
              const updatedMessages = [...prev, newMessage];
              // Start typing animation for the new message
              setTimeout(() => {
                typeMessage(updatedMessages.length - 1, data.content, 20);
              }, 100);
              return updatedMessages;
            });
          });

      // Handle negotiation completion
      newSocket.on('negotiation_complete', (data) => {
        console.log('✅ Negotiation completed:', data);
        setNegotiationComplete(true);
        setIsLoading(false);
      });

      // Handle connection events
      newSocket.on('connect', () => {
        console.log('🔌 WebSocket connected');
      });

      newSocket.on('disconnect', () => {
        console.log('🔌 WebSocket disconnected');
      });

      newSocket.on('joined_conversation', (data) => {
        console.log('🏠 Joined conversation room:', data.conversation_id);
        // Start negotiation after WebSocket is ready
        if (originalInput && agentProfile) {
          console.log('🚀 Starting negotiation after WebSocket setup');
          setTimeout(() => {
            startNegotiationWithId(originalInput, agentProfile, conversationId);
          }, 1000); // Small delay to ensure WebSocket is ready
        }
      });

      // Cleanup on unmount
      return () => {
        if (newSocket) {
          newSocket.emit('leave_conversation', { conversation_id: conversationId });
          newSocket.disconnect();
        }
      };
    }
  }, [conversationId, originalInput, agentProfile]);

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
      const response = await sendNegotiationMessage(initialMessage, profile, conversationId);
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
        const formattedMessages = data.messages.map((msg: any) => ({
          role: msg.role === 'agent' ? 'agent' : 'user',
          content: msg.content,
          timestamp: new Date(msg.timestamp),
          isTyping: false,
          displayContent: msg.content
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
      const data = await getConversation(conversationId);
      if (data && data.messages) {
        const formattedMessages = data.messages.map((msg: any) => ({
          role: msg.role === 'agent' ? 'agent' : 'user',
          content: msg.content,
          timestamp: new Date(msg.timestamp),
          isTyping: false,
          displayContent: msg.content
        }));
        setMessages(formattedMessages);
        setNegotiationComplete(data.is_complete || false);
      }
    } catch (error) {
      console.error("Error loading conversation:", error);
    }
  };

  return (
    <div className="min-h-screen  text-white flex flex-col">
      <MiniNavbar/>

      {/* Header */}
      <div className="p-4 px-16 font-mono  border-gray-800">
        <h2 className="text-xl font-semibold">AI Agent Negotiation</h2>
        <p className="text-gray-400">Watching {name} negotiate with the service provider</p>
        <p className="text-gray-500 text-sm">Messages: {messages.length}</p>
        {negotiationComplete && (
          <div className="mt-2 px-3 py-1 bg-green-900 text-green-200 rounded-full text-sm inline-block">
            Negotiation Complete
          </div>
        )}
        {isLoading && !negotiationComplete && (
          <div className="mt-2 px-3 py-1 bg-blue-900 text-blue-200 rounded-full text-sm inline-block">
            AI Agents are negotiating...
          </div>
        )}
      </div>

          {/* Messages */}
          <div className="flex-1 font-inter overflow-y-auto p-4 px-16 space-y-4">
            {messages.map((message, index) => {
              console.log('Rendering message:', message);
              return (
              <div
                key={index}
                className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
              >
                <div
                  className={`max-w-[70%] p-3 rounded-lg ${
                    message.role === 'user'
                      ? 'bg-blue-800 text-white border-l-4 border-blue-400'
                      : message.role === 'system'
                      ? 'bg-red-900 text-red-200'
                      : 'bg-gray-800 text-white border-l-4 border-gray-400'
                  }`}
                >
                  <div className="text-xs text-gray-300 mb-1 font-mono">
                    {message.role === 'user' ? 'Customer AI' : 'Service Provider AI'}
                  </div>
                  <p className="whitespace-pre-wrap">
                    {message.displayContent || message.content}
                    {message.isTyping && (
                      <span className="inline-block w-0.5 h-4 bg-current ml-1 animate-pulse"></span>
                    )}
                  </p>
                </div>
              </div>
              );
            })}

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
      <Link
        href="/generate-pdf"
        className="inline-block px-4 py-2 rounded-xl bg-emerald-600 hover:bg-emerald-500"
      >
        Create Contract PDF
      </Link>

      
    </div>
  )
}


export default Book
