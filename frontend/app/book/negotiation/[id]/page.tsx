"use client";
import React, { useState, useEffect, useRef } from 'react';
import { useParams } from 'next/navigation';
import MiniNavbar from '@/components/MiniNavbar';
import { sendNegotiationMessage, getConversation } from '@/lib/negotiationServices';
import { io, Socket } from 'socket.io-client';
import axios from 'axios';

const NegotiationPage = () => {
  const params = useParams();
  const negotiationId = params.id as string;

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
  const [agentProfile, setAgentProfile] = useState(null);
  const [socket, setSocket] = useState<Socket | null>(null);
  const socketRef = useRef<Socket | null>(null);
  
  // Live conversation states
  const [liveConversationId, setLiveConversationId] = useState<string | null>(null);
  const [liveConversationLink, setLiveConversationLink] = useState<string | null>(null);
  const [showLiveConversation, setShowLiveConversation] = useState(false);
  const [liveMessages, setLiveMessages] = useState<Array<{
    id: string;
    sender: string;
    content: string;
    timestamp: number;
  }>>([]);
  const [liveInput, setLiveInput] = useState('');
  const [liveSocket, setLiveSocket] = useState<Socket | null>(null);
  const [isCreatingLiveConversation, setIsCreatingLiveConversation] = useState(false);

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
        setMessages(prev => prev.map((msg, index) => 
          index === messageId 
            ? { ...msg, isTyping: false }
            : msg
        ));
      }
    }, delay);
  };

  useEffect(() => {
    const profileData = localStorage.getItem(`profileData_${negotiationId}`);
    if (profileData) {
      const parsedData = JSON.parse(profileData);
      setSendInputResult(parsedData.originalMatchData);
      setAddress(parsedData.address);
      setName(parsedData.name);
      setConversation(parsedData.job);
      setOriginalInput(parsedData.originalInput);

      const matchData = parsedData.originalMatchData;
      if (matchData && matchData.matched_uagent) {
        setAgentProfile(matchData.matched_uagent);
      }

      console.log("Profile data:", parsedData);
    } else {
      loadConversation();
    }
  }, [negotiationId]);

  // WebSocket connection and event handling
  useEffect(() => {
    if (negotiationId && negotiationId !== 'default') {
      console.log('🔌 Connecting to WebSocket for conversation:', negotiationId);
      
      const newSocket = io('http://localhost:8001', {
        transports: ['websocket', 'polling']
      });
      
      socketRef.current = newSocket;
      setSocket(newSocket);

      newSocket.emit('join_conversation', { conversation_id: negotiationId });

      newSocket.on('new_message', (data) => {
        console.log('📨 Received new message:', data);
        const newMessage = {
          role: data.role,
          content: data.content,
          timestamp: new Date(),
          isTyping: true,
          displayContent: ''
        };
        setMessages(prev => {
          const updatedMessages = [...prev, newMessage];
          setTimeout(() => {
            typeMessage(updatedMessages.length - 1, data.content, 20);
          }, 100);
          return updatedMessages;
        });
      });

      newSocket.on('negotiation_complete', (data) => {
        console.log('✅ Negotiation completed:', data);
        setNegotiationComplete(true);
        setIsLoading(false);
      });

      newSocket.on('connect', () => {
        console.log('🔌 WebSocket connected');
      });

      newSocket.on('disconnect', () => {
        console.log('🔌 WebSocket disconnected');
      });

      newSocket.on('joined_conversation', (data) => {
        console.log('🏠 Joined conversation room:', data.conversation_id);
        if (originalInput && agentProfile) {
          console.log('🚀 Starting negotiation after WebSocket setup');
          setTimeout(() => {
            startNegotiationWithId(originalInput, agentProfile, negotiationId);
          }, 1000);
        }
      });

      return () => {
        if (newSocket) {
          newSocket.emit('leave_conversation', { conversation_id: negotiationId });
          newSocket.disconnect();
        }
        if (liveSocket) {
          liveSocket.emit('leave_room', { room_id: liveConversationId });
          liveSocket.disconnect();
        }
      };
    }
  }, [negotiationId, originalInput, agentProfile]);

  const startNegotiationWithId = async (initialMessage: string, profile: any, convId: string) => {
    setIsLoading(true);
    try {
      const response = await sendNegotiationMessage(initialMessage, profile, convId);
      if (response && response.success) {
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
      const data = await getConversation(negotiationId);
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

  // Live conversation functions
  const createLiveConversation = async () => {
    setIsCreatingLiveConversation(true);
    try {
      const response = await axios.post('http://localhost:8081/api/conversations/create', {
        title: `Live Negotiation - ${name}`,
        description: `Live conversation for ${conversation} service negotiation`,
        user_id: 'book_user'
      });
      
      if (response.data.success) {
        setLiveConversationId(response.data.room_id);
        setLiveConversationLink(response.data.join_link);
        setShowLiveConversation(true);
        connectToLiveConversation(response.data.room_id);
      }
    } catch (error) {
      console.error('Error creating live conversation:', error);
      alert('Failed to create live conversation. Please try again.');
    } finally {
      setIsCreatingLiveConversation(false);
    }
  };

  const connectToLiveConversation = (roomId: string) => {
    const newSocket = io('http://localhost:8081', {
      transports: ['websocket', 'polling']
    });
    
    setLiveSocket(newSocket);

    newSocket.on('connect', () => {
      console.log('🔌 Connected to live conversation WebSocket');
      newSocket.emit('join_room', {
        room_id: roomId,
        user_id: 'book_user',
        username: 'Negotiation Viewer'
      });
    });

    newSocket.on('conversation_state', (data) => {
      console.log('📋 Live conversation state:', data);
      if (data.conversation && data.conversation.messages) {
        setLiveMessages(data.conversation.messages);
      }
    });

    newSocket.on('new_message', (message) => {
      console.log('📨 New live message:', message);
      setLiveMessages(prev => [...prev, message]);
    });

    newSocket.on('user_joined', (data) => {
      console.log('👤 User joined live conversation:', data);
      setLiveMessages(prev => [...prev, {
        id: `system_${Date.now()}`,
        sender: 'System',
        content: `${data.username} joined the conversation`,
        timestamp: Date.now() / 1000
      }]);
    });

    newSocket.on('user_left', (data) => {
      console.log('👋 User left live conversation:', data);
      setLiveMessages(prev => [...prev, {
        id: `system_${Date.now()}`,
        sender: 'System',
        content: `${data.username} left the conversation`,
        timestamp: Date.now() / 1000
      }]);
    });

    newSocket.on('error', (error) => {
      console.error('❌ Live conversation error:', error);
    });
  };

  const sendLiveMessage = () => {
    if (liveSocket && liveConversationId && liveInput.trim()) {
      liveSocket.emit('send_message', {
        room_id: liveConversationId,
        message: liveInput,
        user_id: 'book_user',
        username: 'Negotiation Viewer',
        type: 'text'
      });
      setLiveInput('');
    }
  };

  const copyLiveConversationLink = () => {
    if (liveConversationLink) {
      navigator.clipboard.writeText(liveConversationLink);
      alert('Live conversation link copied to clipboard!');
    }
  };

  const formatTimestamp = (timestamp: number) => {
    const date = new Date(timestamp * 1000);
    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  };

  return (
    <div className="min-h-screen text-white flex flex-col">
      <MiniNavbar/>

      {/* Header */}
      <div className="p-4 px-16 font-mono border-gray-800">
        <div className="flex justify-between items-start">
          <div>
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
          
          {/* Live Conversation Controls */}
          <div className="flex flex-col gap-2">
            {!showLiveConversation ? (
              <button
                onClick={createLiveConversation}
                disabled={isCreatingLiveConversation}
                className="bg-primary text-black px-4 py-2 rounded-lg font-mono text-sm hover:bg-yellow-300 transition-colors disabled:opacity-50"
              >
                {isCreatingLiveConversation ? 'Creating...' : 'Create Live Conversation'}
              </button>
            ) : (
              <div className="flex flex-col gap-2">
                <div className="bg-green-900 text-green-200 px-3 py-1 rounded-full text-sm">
                  Live Conversation Active
                </div>
                <div className="flex gap-2">
                  <button
                    onClick={copyLiveConversationLink}
                    className="bg-gray-600 text-white px-3 py-1 rounded text-sm hover:bg-gray-500 transition-colors"
                  >
                    Copy Link
                  </button>
                  <button
                    onClick={() => setShowLiveConversation(false)}
                    className="bg-red-600 text-white px-3 py-1 rounded text-sm hover:bg-red-500 transition-colors"
                  >
                    Close
                  </button>
                </div>
                {liveConversationLink && (
                  <p className="text-xs text-gray-400 break-all max-w-xs">
                    {liveConversationLink}
                  </p>
                )}
              </div>
            )}
          </div>
        </div>
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

      {/* Live Conversation Section */}
      {showLiveConversation && (
        <div className="border-t border-gray-800 bg-gray-900/50">
          <div className="p-4 px-16">
            <h3 className="text-lg font-semibold text-primary mb-4">Live Conversation</h3>
            <div className="bg-black/70 backdrop-blur-sm rounded-lg p-4 h-64 overflow-y-auto space-y-2">
              {liveMessages.length === 0 ? (
                <p className="text-gray-400 text-center">No messages yet. Share the link to invite others!</p>
              ) : (
                liveMessages.map((msg) => (
                  <div key={msg.id} className={`flex ${msg.sender === 'Negotiation Viewer' ? 'justify-end' : 'justify-start'}`}>
                    <div className={`max-w-[70%] p-2 rounded-lg ${
                      msg.sender === 'Negotiation Viewer' 
                        ? 'bg-primary text-black' 
                        : msg.sender === 'System'
                        ? 'bg-gray-600 text-white text-sm italic'
                        : 'bg-gray-700 text-white'
                    }`}>
                      <div className="text-xs opacity-70 mb-1">
                        {msg.sender !== 'System' && <strong>{msg.sender}:</strong>} {formatTimestamp(msg.timestamp)}
                      </div>
                      <p className="text-sm">{msg.content}</p>
                    </div>
                  </div>
                ))
              )}
            </div>
            
            {/* Live Message Input */}
            <div className="flex gap-2 mt-4">
              <input
                type="text"
                value={liveInput}
                onChange={(e) => setLiveInput(e.target.value)}
                onKeyPress={(e) => {
                  if (e.key === 'Enter') {
                    sendLiveMessage();
                  }
                }}
                placeholder="Type a message for the live conversation..."
                className="flex-grow p-2 rounded bg-gray-800 text-white border border-gray-700 focus:outline-none focus:border-primary"
              />
              <button
                onClick={sendLiveMessage}
                disabled={!liveInput.trim()}
                className="bg-primary text-black px-4 py-2 rounded font-mono hover:bg-yellow-300 transition-colors disabled:opacity-50"
              >
                Send
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default NegotiationPage;