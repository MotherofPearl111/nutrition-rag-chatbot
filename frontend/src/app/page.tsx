'use client';

import React, { useState, useRef, useEffect } from 'react';

export default function Home() {
  const [messages, setMessages] = useState([
    {
      role: 'assistant',
      content: "🎉 Hello! I'm your nutrition assistant powered by Claude AI. Ask me anything about nutrition!"
    }
  ]);
  const [inputMessage, setInputMessage] = useState('');
  const [isThinking, setIsThinking] = useState(false);
  const [error, setError] = useState(null);
  const messagesEndRef = useRef(null);
  const API_URL = 'https://nutrition-rag-chatbot-production.up.railway.app';

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const showError = (message) => {
    setError(message);
    setTimeout(() => setError(null), 5000);
  };

  const handleSendMessage = async () => {
    if (!inputMessage.trim()) return;

    const userMessage = { role: 'user', content: inputMessage };
    setMessages(prev => [...prev, userMessage]);
    const currentMessage = inputMessage;
    setInputMessage('');
    setIsThinking(true);
    setError(null);

    try {
      const response = await fetch(`${API_URL}/api/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: currentMessage }),
      });

      if (!response.ok) {
        throw new Error(`API Error: ${response.status}`);
      }

      const data = await response.json();
      
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: data.response
      }]);

    } catch (error) {
      showError(`Failed: ${error.message}`);
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: "❌ Connection failed. Please try again."
      }]);
    }

    setIsThinking(false);
  };

  const testConnection = async () => {
    try {
      const response = await fetch(`${API_URL}/api/health`);
      const data = await response.json();
      
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: `🔍 Connection Test - API: ${data.status}, Claude: ${data.claude ? 'Connected' : 'Not connected'}`
      }]);
    } catch (error) {
      showError("❌ Cannot connect to backend!");
    }
  };

  return (
    <div className="max-w-4xl mx-auto p-4 bg-gray-50 min-h-screen">
      <div className="bg-white rounded-lg shadow-xl overflow-hidden">
        
        <div className="bg-gradient-to-r from-green-600 to-blue-600 p-6 text-white">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold">🥗 Nutrition Assistant</h1>
              <p className="text-green-100">AI-Powered Nutrition Advice with Claude</p>
            </div>
            
            <button
              onClick={testConnection}
              className="bg-white/20 hover:bg-white/30 px-4 py-2 rounded-lg text-sm"
            >
              Test Connection
            </button>
          </div>
        </div>

        {error && (
          <div className="bg-red-50 border-l-4 border-red-400 p-4 m-4">
            <p className="text-red-700">{error}</p>
          </div>
        )}

        <div className="h-96 overflow-y-auto p-6 space-y-4">
          {messages.map((message, index) => (
            <div key={index} className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}>
              <div className={`max-w-3/4 p-4 rounded-lg ${
                message.role === 'user' ? 'bg-blue-500 text-white' : 'bg-gray-100'
              }`}>
                <p className="whitespace-pre-wrap">{message.content}</p>
              </div>
            </div>
          ))}
          
          {isThinking && (
            <div className="flex justify-start">
              <div className="bg-gray-100 p-4 rounded-lg">
                <span>🤔 Thinking...</span>
              </div>
            </div>
          )}
          
          <div ref={messagesEndRef} />
        </div>

        <div className="px-6 py-3 border-t bg-gray-50">
          <div className="grid grid-cols-2 gap-2">
            {[
              "What are good protein sources?",
              "How much water should I drink daily?",
              "What vitamins are important for bone health?", 
              "Tell me about healthy fats"
            ].map((question, index) => (
              <button
                key={index}
                onClick={() => setInputMessage(question)}
                className="text-xs bg-blue-100 hover:bg-blue-200 text-blue-800 px-3 py-2 rounded-lg text-left"
              >
                {question}
              </button>
            ))}
          </div>
        </div>

        <div className="p-6 border-t">
          <div className="flex gap-3">
            <input
              type="text"
              value={inputMessage}
              onChange={(e) => setInputMessage(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && handleSendMessage()}
              placeholder="Ask about nutrition..."
              className="flex-1 p-3 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
            <button
              onClick={handleSendMessage}
              disabled={!inputMessage.trim() || isThinking}
              className="bg-blue-500 hover:bg-blue-600 disabled:bg-gray-300 text-white px-4 py-2 rounded-lg"
            >
              Send
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}