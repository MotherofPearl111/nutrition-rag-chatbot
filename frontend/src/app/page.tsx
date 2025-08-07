"use client";

import { useState, useRef, useEffect } from 'react';

interface Message {
  role: 'user' | 'assistant';
  content: string;
}

export default function Home() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const sendMessage = async () => {
    if (!input.trim() || loading) return;

    const userMessage: Message = { role: 'user', content: input };
    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setLoading(true);

    try {
      const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
      
      const response = await fetch(`${API_URL}/api/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ message: input }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      
      const assistantMessage: Message = { 
        role: 'assistant', 
        content: data.response || 'Sorry, I didn\'t receive a proper response.'
      };
      
      setMessages(prev => [...prev, assistantMessage]);
    } catch (error) {
      console.error('Error sending message:', error);
      const errorMessage: Message = { 
        role: 'assistant', 
        content: 'Sorry, I encountered an error connecting to the nutrition service. Please try again.'
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setLoading(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  return (
    <main className="flex min-h-screen flex-col items-center p-6 bg-gray-50">
      <div className="w-full max-w-4xl">
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold text-gray-800 mb-2">
            🥗 Nutrition RAG Chatbot
          </h1>
          <p className="text-gray-600">
            Ask me anything about nutrition, healthy eating, and dietary advice!
          </p>
        </div>
        
        <div className="bg-white rounded-lg shadow-lg p-6">
          <div className="border border-gray-200 rounded-lg p-4 h-96 overflow-y-auto mb-4 bg-gray-50">
            {messages.length === 0 && (
              <div className="text-center text-gray-500 mt-20">
                <p className="text-lg mb-2">👋 Welcome!</p>
                <p>Start by asking a nutrition question like:</p>
                <div className="mt-4 space-y-2 text-sm">
                  <p className="bg-white rounded px-3 py-2">"What are good sources of protein?"</p>
                  <p className="bg-white rounded px-3 py-2">"How much water should I drink daily?"</p>
                  <p className="bg-white rounded px-3 py-2">"What foods help with energy levels?"</p>
                </div>
              </div>
            )}
            
            {messages.map((message, index) => (
              <div key={index} className={`mb-4 p-4 rounded-lg ${
                message.role === 'user' 
                  ? 'bg-blue-500 text-white ml-auto max-w-[80%]' 
                  : 'bg-white border border-gray-200 mr-auto max-w-[85%]'
              }`}>
                <div className="flex items-start gap-2">
                  <span className="text-sm font-semibold">
                    {message.role === 'user' ? '👤 You' : '🤖 Nutritionist AI'}
                  </span>
                </div>
                <div className={`mt-2 text-sm leading-relaxed ${
                  message.role === 'user' ? 'text-white' : 'text-gray-800'
                }`}>
                  {message.content}
                </div>
              </div>
            ))}
            
            {loading && (
              <div className="bg-white border border-gray-200 mr-auto max-w-[85%] mb-4 p-4 rounded-lg">
                <div className="flex items-center gap-2">
                  <span className="text-sm font-semibold">🤖 Nutritionist AI</span>
                  <div className="flex space-x-1">
                    <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></div>
                    <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{animationDelay: '0.1s'}}></div>
                    <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{animationDelay: '0.2s'}}></div>
                  </div>
                </div>
                <p className="mt-2 text-sm text-gray-600">Thinking about your nutrition question...</p>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>

          <div className="flex gap-3">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="Ask about nutrition, diet, healthy eating..."
              className="flex-1 p-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              disabled={loading}
            />
            <button
              onClick={sendMessage}
              disabled={loading || !input.trim()}
              className="px-6 py-3 bg-blue-500 text-white rounded-lg hover:bg-blue-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors duration-200 font-medium"
            >
              {loading ? '...' : 'Send'}
            </button>
          </div>
          
          <div className="mt-4 text-center">
            <p className="text-xs text-gray-500">
              Powered by Claude AI • Always consult healthcare professionals for medical advice
            </p>
          </div>
        </div>
      </div>
    </main>
  );
}