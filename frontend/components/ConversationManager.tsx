"use client";
import { useState } from 'react';
import Link from 'next/link';

interface Conversation {
  room_id: string;
  title: string;
  description: string;
  created_at: string;
  participant_count: number;
  message_count: number;
  join_link: string;
}

export default function ConversationManager() {
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [newConversation, setNewConversation] = useState({
    title: '',
    description: '',
    user_id: `user_${Math.random().toString(36).substr(2, 9)}`
  });
  const [createdConversation, setCreatedConversation] = useState<Conversation | null>(null);

  const loadConversations = async () => {
    setIsLoading(true);
    setError('');
    
    try {
      const response = await fetch('http://localhost:8081/api/conversations');
      const data = await response.json();
      
      if (data.success) {
        setConversations(data.conversations);
      } else {
        setError(data.error || 'Failed to load conversations');
      }
    } catch (err) {
      setError('Failed to connect to server');
      console.error('Error loading conversations:', err);
    } finally {
      setIsLoading(false);
    }
  };

  const createConversation = async () => {
    if (!newConversation.title.trim()) {
      setError('Title is required');
      return;
    }

    setIsLoading(true);
    setError('');
    
    try {
      const response = await fetch('http://localhost:8081/api/conversations/create', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(newConversation)
      });
      
      const data = await response.json();
      
      if (data.success) {
        setCreatedConversation({
          room_id: data.room_id,
          title: data.conversation.title,
          description: data.conversation.description,
          created_at: data.conversation.created_at,
          participant_count: 0,
          message_count: 0,
          join_link: data.join_link
        });
        setNewConversation({ title: '', description: '', user_id: newConversation.user_id });
        setShowCreateForm(false);
        loadConversations(); // Refresh the list
      } else {
        setError(data.error || 'Failed to create conversation');
      }
    } catch (err) {
      setError('Failed to connect to server');
      console.error('Error creating conversation:', err);
    } finally {
      setIsLoading(false);
    }
  };

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text).then(() => {
      // You could show a toast notification here
      console.log('Copied to clipboard');
    });
  };

  return (
    <div className="min-h-screen bg-gradient-to-b from-black via-yellow-600 to-yellow-400 p-6">
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold text-white mb-4">Conversation Manager</h1>
          <p className="text-white/80 text-lg">Create and join real-time conversations</p>
        </div>

        {/* Create Conversation Button */}
        <div className="text-center mb-8">
          <button
            onClick={() => setShowCreateForm(true)}
            className="bg-yellow-400 text-black font-bold py-3 px-8 rounded-lg hover:bg-yellow-300 transition-colors text-lg"
          >
            Create New Conversation
          </button>
        </div>

        {/* Create Conversation Form */}
        {showCreateForm && (
          <div className="bg-white/10 backdrop-blur-sm rounded-lg p-6 mb-8 max-w-2xl mx-auto">
            <h2 className="text-2xl font-bold text-white mb-4">Create Conversation</h2>
            
            {error && (
              <div className="bg-red-500/20 border border-red-500 text-red-200 px-4 py-3 rounded mb-4">
                {error}
              </div>
            )}

            <div className="space-y-4">
              <div>
                <label className="block text-white text-sm font-medium mb-2">
                  Title *
                </label>
                <input
                  type="text"
                  value={newConversation.title}
                  onChange={(e) => setNewConversation(prev => ({ ...prev, title: e.target.value }))}
                  className="w-full px-3 py-2 bg-white/20 border border-white/30 rounded-md text-white placeholder-white/50 focus:outline-none focus:ring-2 focus:ring-yellow-400"
                  placeholder="Enter conversation title"
                />
              </div>
              
              <div>
                <label className="block text-white text-sm font-medium mb-2">
                  Description
                </label>
                <textarea
                  value={newConversation.description}
                  onChange={(e) => setNewConversation(prev => ({ ...prev, description: e.target.value }))}
                  className="w-full px-3 py-2 bg-white/20 border border-white/30 rounded-md text-white placeholder-white/50 focus:outline-none focus:ring-2 focus:ring-yellow-400 h-20 resize-none"
                  placeholder="Enter conversation description (optional)"
                />
              </div>
              
              <div className="flex space-x-4">
                <button
                  onClick={createConversation}
                  disabled={isLoading || !newConversation.title.trim()}
                  className="flex-1 bg-yellow-400 text-black font-bold py-2 px-4 rounded-md hover:bg-yellow-300 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                >
                  {isLoading ? 'Creating...' : 'Create Conversation'}
                </button>
                <button
                  onClick={() => setShowCreateForm(false)}
                  className="flex-1 bg-white/20 text-white font-bold py-2 px-4 rounded-md hover:bg-white/30 transition-colors"
                >
                  Cancel
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Created Conversation Success */}
        {createdConversation && (
          <div className="bg-green-500/20 border border-green-500 rounded-lg p-6 mb-8 max-w-2xl mx-auto">
            <h3 className="text-xl font-bold text-green-200 mb-4">Conversation Created!</h3>
            <div className="space-y-3">
              <div>
                <label className="block text-green-200 text-sm font-medium mb-1">
                  Join Link:
                </label>
                <div className="flex space-x-2">
                  <input
                    type="text"
                    value={createdConversation.join_link}
                    readOnly
                    className="flex-1 px-3 py-2 bg-white/20 border border-white/30 rounded-md text-white text-sm"
                  />
                  <button
                    onClick={() => copyToClipboard(createdConversation.join_link)}
                    className="bg-green-400 text-black font-bold px-4 py-2 rounded-md hover:bg-green-300 transition-colors"
                  >
                    Copy
                  </button>
                </div>
              </div>
              <div className="flex space-x-4">
                <Link
                  href={`/conversation/${createdConversation.room_id}`}
                  className="bg-yellow-400 text-black font-bold py-2 px-4 rounded-md hover:bg-yellow-300 transition-colors"
                >
                  Join Now
                </Link>
                <button
                  onClick={() => setCreatedConversation(null)}
                  className="bg-white/20 text-white font-bold py-2 px-4 rounded-md hover:bg-white/30 transition-colors"
                >
                  Close
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Load Conversations Button */}
        <div className="text-center mb-6">
          <button
            onClick={loadConversations}
            disabled={isLoading}
            className="bg-white/20 text-white font-bold py-2 px-6 rounded-md hover:bg-white/30 disabled:opacity-50 transition-colors"
          >
            {isLoading ? 'Loading...' : 'Load Active Conversations'}
          </button>
        </div>

        {/* Error Display */}
        {error && !showCreateForm && (
          <div className="bg-red-500/20 border border-red-500 text-red-200 px-4 py-3 rounded mb-6 max-w-2xl mx-auto text-center">
            {error}
          </div>
        )}

        {/* Conversations List */}
        {conversations.length > 0 && (
          <div className="space-y-4">
            <h2 className="text-2xl font-bold text-white text-center mb-6">
              Active Conversations ({conversations.length})
            </h2>
            
            {conversations.map((conv) => (
              <div key={conv.room_id} className="bg-white/10 backdrop-blur-sm rounded-lg p-6">
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <h3 className="text-xl font-bold text-white mb-2">{conv.title}</h3>
                    {conv.description && (
                      <p className="text-white/70 mb-3">{conv.description}</p>
                    )}
                    <div className="flex items-center space-x-4 text-sm text-white/60">
                      <span>{conv.participant_count} participant{conv.participant_count !== 1 ? 's' : ''}</span>
                      <span>{conv.message_count} message{conv.message_count !== 1 ? 's' : ''}</span>
                      <span>Created {new Date(conv.created_at).toLocaleString()}</span>
                    </div>
                  </div>
                  
                  <div className="flex space-x-2 ml-4">
                    <Link
                      href={`/conversation/${conv.room_id}`}
                      className="bg-yellow-400 text-black font-bold py-2 px-4 rounded-md hover:bg-yellow-300 transition-colors"
                    >
                      Join
                    </Link>
                    <button
                      onClick={() => copyToClipboard(conv.join_link)}
                      className="bg-white/20 text-white font-bold py-2 px-4 rounded-md hover:bg-white/30 transition-colors"
                    >
                      Copy Link
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Empty State */}
        {conversations.length === 0 && !isLoading && !showCreateForm && (
          <div className="text-center text-white/70 py-12">
            <p className="text-lg mb-4">No active conversations found.</p>
            <p>Create a new conversation to get started!</p>
          </div>
        )}
      </div>
    </div>
  );
}
