"use client";
import React, { useState, useEffect, useRef } from 'react'
import { createProfile } from '@/lib/createProfileServices'
import Navbar from '@/components/Navbar'
import { useParams, useRouter } from 'next/navigation'

interface Message {
  id: string;
  content: string;
  isBot: boolean;
  timestamp: Date;
}

const ProfileChatbot = () => {
  const params = useParams();
  const router = useRouter();
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [isCompleted, setIsCompleted] = useState(false);
  const [currentId, setCurrentId] = useState<string>('');
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  useEffect(() => {
    const id = params.id as string;

    // If ID changed, clear chat history
    if (currentId && currentId !== id) {
      localStorage.removeItem(`profile-chat-history-${currentId}`);
      setMessages([]);
      setIsCompleted(false);
    }

    setCurrentId(id);

    // Load message history for this specific ID
    const savedMessages = localStorage.getItem(`profile-chat-history-${id}`);
    if (savedMessages) {
      const parsed = JSON.parse(savedMessages);
      setMessages(parsed.map((msg: any) => ({
        ...msg,
        timestamp: new Date(msg.timestamp)
      })));
    } else {
      // Initial bot message
      addBotMessage("Hi! I'm here to help you create your profile. I'll need your name, job/services, pricing, email, a description of your services, and your work personality/style.");
    }
  }, [params.id, currentId]);

  useEffect(() => {
    // Save message history to localStorage with ID-specific key
    if (messages.length > 0 && currentId) {
      localStorage.setItem(`profile-chat-history-${currentId}`, JSON.stringify(messages));
    }
  }, [messages, currentId]);

  const addBotMessage = (content: string) => {
    const newMessage: Message = {
      id: Date.now().toString(),
      content,
      isBot: true,
      timestamp: new Date()
    };
    setMessages(prev => [...prev, newMessage]);
  };

  const addUserMessage = (content: string) => {
    const newMessage: Message = {
      id: Date.now().toString(),
      content,
      isBot: false,
      timestamp: new Date()
    };
    setMessages(prev => [...prev, newMessage]);
  };

  const handleSendMessage = async () => {
    if (!input.trim() || isLoading) return;

    const userMessage = input.trim();
    setInput('');
    addUserMessage(userMessage);
    setIsLoading(true);

    try {
      const response = await createProfile(userMessage);

      if (response) {
        // Check if profile is complete
        if (response.completed) {
          setIsCompleted(true);
          addBotMessage("Perfect! Your profile is now complete. Redirecting you to the home page...");

          // Redirect to home page after 2 seconds
          setTimeout(() => {
            router.push('/');
          }, 2000);
        } else {
          addBotMessage(response.message || response.content || 'Got it! What else would you like to add?');
        }
      } else {
        addBotMessage("I'm having trouble processing that. Could you try rephrasing?");
      }
    } catch (error) {
      addBotMessage("Sorry, I encountered an error. Please try again.");
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  const clearHistory = () => {
    if (currentId) {
      localStorage.removeItem(`profile-chat-history-${currentId}`);
    }
    setMessages([]);
    setIsCompleted(false);
    addBotMessage("Hi! I'm here to help you create your profile. I'll need your name, job/services, pricing, email, a description of your services, and your work personality/style.");
  };

  return (
    <div className="min-h-screen bg-black text-white">
      <Navbar />

      <div className="container mx-auto px-4 py-8 max-w-4xl">
        <div className="text-center mb-8">
          <h1 className="font-mono text-4xl font-bold mb-2">Create Your Profile</h1>
          <p className="text-gray-300 font-mono">Chat with our AI to build your service profile</p>
        </div>

        {/* Chat Container */}
        <div className="bg-[#1a1a1a] rounded-xl border border-gray-800 h-[600px] flex flex-col">
          {/* Messages */}
          <div className="flex-1 overflow-y-auto p-6 space-y-4">
            {messages.map((message) => (
              <div
                key={message.id}
                className={`flex ${message.isBot ? 'justify-start' : 'justify-end'}`}
              >
                <div
                  className={`max-w-[80%] p-4 rounded-xl font-mono text-sm ${
                    message.isBot
                      ? 'bg-[#2B2B2B] text-white'
                      : 'bg-primary text-black'
                  }`}
                >
                  {message.content}
                </div>
              </div>
            ))}

            {isLoading && (
              <div className="flex justify-start">
                <div className="bg-[#2B2B2B] text-white p-4 rounded-xl font-mono text-sm">
                  <div className="flex items-center space-x-1">
                    <div className="w-2 h-2 bg-white rounded-full animate-bounce"></div>
                    <div className="w-2 h-2 bg-white rounded-full animate-bounce" style={{ animationDelay: '0.1s' }}></div>
                    <div className="w-2 h-2 bg-white rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
                  </div>
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>

          {/* Input Area */}
          <div className="border-t border-gray-800 p-4">
            <div className="flex space-x-3">
              <input
                type="text"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyPress={handleKeyPress}
                placeholder={isCompleted ? "Profile completed! Ready to continue..." : "Type your message..."}
                disabled={isLoading || isCompleted}
                className="flex-1 bg-[#2B2B2B] text-white p-3 rounded-lg font-mono placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-primary disabled:opacity-50"
              />
              <button
                onClick={handleSendMessage}
                disabled={isLoading || !input.trim() || isCompleted}
                className="bg-primary text-black px-6 py-3 rounded-lg font-mono font-medium hover:bg-yellow-300 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                Send
              </button>
            </div>
          </div>
        </div>

        {/* Action Buttons */}
        <div className="flex justify-between items-center mt-6">
          <button
            onClick={clearHistory}
            className="text-gray-400 hover:text-white font-mono text-sm transition-colors"
          >
            Clear Chat History
          </button>

          {isCompleted && (
            <div className="text-primary font-mono">
              Redirecting to home page...
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default ProfileChatbot;
