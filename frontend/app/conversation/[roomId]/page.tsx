"use client";
import { useState, useEffect, useRef } from 'react';
import { useParams } from 'next/navigation';
import io, { Socket } from 'socket.io-client';

interface Message {
  id: string;
  user_id: string;
  username: string;
  message: string;
  type: string;
  timestamp: string;
}

interface Conversation {
  room_id: string;
  created_at: string;
  created_by: string;
  title: string;
  description: string;
  messages: Message[];
  participants: Array<{
    user_id: string;
    username: string;
    joined_at: string;
  }>;
  is_active: boolean;
}

export default function ConversationPage() {
  const params = useParams();
  const roomId = params.roomId as string;
  
  const [socket, setSocket] = useState<Socket | null>(null);
  const [conversation, setConversation] = useState<Conversation | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [newMessage, setNewMessage] = useState('');
  const [username, setUsername] = useState('');
  const [userId] = useState(() => `user_${Math.random().toString(36).substr(2, 9)}`);
  const [isConnected, setIsConnected] = useState(false);
  const [isJoining, setIsJoining] = useState(true);
  const [error, setError] = useState('');
  const [typingUsers, setTypingUsers] = useState<string[]>([]);
  
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const typingTimeoutRef = useRef<NodeJS.Timeout | null>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  useEffect(() => {
    if (!roomId) return;

    // Initialize socket connection
    const newSocket = io('http://localhost:8081', {
      transports: ['websocket', 'polling']
    });

    newSocket.on('connect', () => {
      console.log('Connected to WebSocket server');
      setIsConnected(true);
    });

    newSocket.on('disconnect', () => {
      console.log('Disconnected from WebSocket server');
      setIsConnected(false);
    });

    newSocket.on('conversation_state', (data) => {
      console.log('Received conversation state:', data);
      setConversation(data.conversation);
      setMessages(data.conversation.messages || []);
      setIsJoining(false);
    });

    newSocket.on('new_message', (message: Message) => {
      console.log('New message received:', message);
      setMessages(prev => [...prev, message]);
    });

    newSocket.on('user_joined', (data) => {
      console.log('User joined:', data);
      // You could show a notification here
    });

    newSocket.on('user_left', (data) => {
      console.log('User left:', data);
      // You could show a notification here
    });

    newSocket.on('user_typing', (data) => {
      if (data.is_typing) {
        setTypingUsers(prev => {
          if (!prev.includes(data.username)) {
            return [...prev, data.username];
          }
          return prev;
        });
      } else {
        setTypingUsers(prev => prev.filter(user => user !== data.username));
      }
    });

    newSocket.on('conversation_ended', (data) => {
      console.log('Conversation ended:', data);
      setError('This conversation has ended');
    });

    newSocket.on('error', (data) => {
      console.error('Socket error:', data);
      setError(data.message);
      setIsJoining(false);
    });

    setSocket(newSocket);

    return () => {
      newSocket.close();
    };
  }, [roomId]);

  const joinConversation = async () => {
    if (!socket || !username.trim()) return;

    try {
      // First, try to join via API
      const response = await fetch(`http://localhost:8081/api/conversations/${roomId}/join`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          user_id: userId,
          username: username.trim()
        })
      });

      const data = await response.json();

      if (data.success) {
        // Join the WebSocket room
        socket.emit('join_room', {
          room_id: roomId,
          user_id: userId,
          username: username.trim()
        });
      } else {
        setError(data.error || 'Failed to join conversation');
        setIsJoining(false);
      }
    } catch (err) {
      console.error('Error joining conversation:', err);
      setError('Failed to connect to conversation server');
      setIsJoining(false);
    }
  };

  const sendMessage = () => {
    if (!socket || !newMessage.trim() || !username.trim()) return;

    socket.emit('send_message', {
      room_id: roomId,
      message: newMessage.trim(),
      user_id: userId,
      username: username.trim(),
      type: 'text'
    });

    setNewMessage('');
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  const handleTyping = () => {
    if (!socket || !username.trim()) return;

    // Send typing indicator
    socket.emit('typing', {
      room_id: roomId,
      user_id: userId,
      username: username.trim(),
      is_typing: true
    });

    // Clear previous timeout
    if (typingTimeoutRef.current) {
      clearTimeout(typingTimeoutRef.current);
    }

    // Set timeout to stop typing indicator
    typingTimeoutRef.current = setTimeout(() => {
      socket.emit('typing', {
        room_id: roomId,
        user_id: userId,
        username: username.trim(),
        is_typing: false
      });
    }, 1000);
  };

  if (isJoining) {
    return (
      <div className="min-h-screen bg-gradient-to-b from-black via-yellow-600 to-yellow-400 flex items-center justify-center">
        <div className="bg-white/10 backdrop-blur-sm rounded-lg p-8 max-w-md w-full mx-4">
          <h1 className="text-2xl font-bold text-white mb-6 text-center">Join Conversation</h1>
          
          {error && (
            <div className="bg-red-500/20 border border-red-500 text-red-200 px-4 py-3 rounded mb-4">
              {error}
            </div>
          )}

          <div className="space-y-4">
            <div>
              <label className="block text-white text-sm font-medium mb-2">
                Your Name
              </label>
              <input
                type="text"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                onKeyPress={(e) => e.key === 'Enter' && joinConversation()}
                className="w-full px-3 py-2 bg-white/20 border border-white/30 rounded-md text-white placeholder-white/50 focus:outline-none focus:ring-2 focus:ring-yellow-400"
                placeholder="Enter your name"
                disabled={!isConnected}
              />
            </div>
            
            <button
              onClick={joinConversation}
              disabled={!isConnected || !username.trim()}
              className="w-full bg-yellow-400 text-black font-bold py-2 px-4 rounded-md hover:bg-yellow-300 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              {!isConnected ? 'Connecting...' : 'Join Conversation'}
            </button>
          </div>
        </div>
      </div>
    );
  }

  if (error && !conversation) {
    return (
      <div className="min-h-screen bg-gradient-to-b from-black via-yellow-600 to-yellow-400 flex items-center justify-center">
        <div className="bg-white/10 backdrop-blur-sm rounded-lg p-8 max-w-md w-full mx-4 text-center">
          <h1 className="text-2xl font-bold text-white mb-4">Error</h1>
          <p className="text-red-200 mb-6">{error}</p>
          <button
            onClick={() => window.location.reload()}
            className="bg-yellow-400 text-black font-bold py-2 px-4 rounded-md hover:bg-yellow-300 transition-colors"
          >
            Try Again
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-b from-black via-yellow-600 to-yellow-400">
      {/* Header */}
      <div className="bg-black/20 backdrop-blur-sm border-b border-white/20">
        <div className="max-w-4xl mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-xl font-bold text-white">{conversation?.title}</h1>
              <p className="text-white/70 text-sm">
                {conversation?.participants.length} participant{conversation?.participants.length !== 1 ? 's' : ''}
                {!isConnected && ' • Disconnected'}
              </p>
            </div>
            <div className="flex items-center space-x-2">
              <div className={`w-3 h-3 rounded-full ${isConnected ? 'bg-green-400' : 'bg-red-400'}`}></div>
              <span className="text-white/70 text-sm">
                {isConnected ? 'Connected' : 'Disconnected'}
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* Messages */}
      <div className="max-w-4xl mx-auto px-4 py-6">
        <div className="bg-white/10 backdrop-blur-sm rounded-lg h-96 overflow-y-auto p-4 space-y-4">
          {messages.length === 0 ? (
            <div className="text-center text-white/70 py-8">
              No messages yet. Start the conversation!
            </div>
          ) : (
            messages.map((message) => (
              <div
                key={message.id}
                className={`flex ${message.user_id === userId ? 'justify-end' : 'justify-start'}`}
              >
                <div
                  className={`max-w-xs lg:max-w-md px-4 py-2 rounded-lg ${
                    message.user_id === userId
                      ? 'bg-yellow-400 text-black'
                      : 'bg-white/20 text-white'
                  }`}
                >
                  <div className="text-sm font-medium mb-1">
                    {message.username}
                  </div>
                  <div className="text-sm">{message.message}</div>
                  <div className="text-xs opacity-70 mt-1">
                    {new Date(message.timestamp).toLocaleTimeString()}
                  </div>
                </div>
              </div>
            ))
          )}
          
          {/* Typing indicators */}
          {typingUsers.length > 0 && (
            <div className="text-white/70 text-sm italic">
              {typingUsers.join(', ')} {typingUsers.length === 1 ? 'is' : 'are'} typing...
            </div>
          )}
          
          <div ref={messagesEndRef} />
        </div>

        {/* Message input */}
        <div className="mt-4 flex space-x-2">
          <input
            type="text"
            value={newMessage}
            onChange={(e) => {
              setNewMessage(e.target.value);
              handleTyping();
            }}
            onKeyPress={handleKeyPress}
            placeholder="Type your message..."
            className="flex-1 px-4 py-2 bg-white/20 border border-white/30 rounded-md text-white placeholder-white/50 focus:outline-none focus:ring-2 focus:ring-yellow-400"
            disabled={!isConnected}
          />
          <button
            onClick={sendMessage}
            disabled={!isConnected || !newMessage.trim()}
            className="bg-yellow-400 text-black font-bold px-6 py-2 rounded-md hover:bg-yellow-300 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            Send
          </button>
        </div>
      </div>
    </div>
  );
}
