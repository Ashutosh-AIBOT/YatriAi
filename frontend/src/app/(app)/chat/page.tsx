"use client";

import { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Send, Map, Navigation, Utensils, Hotel, Car, ArrowLeft } from 'lucide-react';
import Link from 'next/link';

import CabTable from '@/components/CabTable';
import FlightTable from '@/components/FlightTable';
import HotelGrid from '@/components/HotelGrid';
import MapView from '@/components/MapView';
import api from '@/lib/api';

// Dummy implementation of ChatWindow to show dynamic design
export default function ChatPage() {
  const [messages, setMessages] = useState<any[]>([
    { id: '1', role: 'assistant', content: 'Where would you like to travel from and to? (e.g. Kanpur to Noida)', type: 'text' }
  ]);
  const [input, setInput] = useState('');
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSend = async () => {
    if (!input.trim()) return;
    const newMsg = { id: Date.now().toString(), role: 'user', content: input, type: 'text' };
    setMessages(prev => [...prev, newMsg]);
    setInput('');
    
    try {
      // Connect to the real Spring Boot Gateway / Orchestrator API
      const response = await api.post('/chat', { message: input, session_id: 'default' });
      
      const reply = {
        id: Date.now().toString(),
        role: 'assistant',
        content: response.data.message || 'Processing your request...',
        type: response.data.ui_type || 'text',
        data: response.data.ui_data
      };
      setMessages(prev => [...prev, reply]);
    } catch (error) {
      console.error("Chat API Error:", error);
      setMessages(prev => [...prev, {
        id: Date.now().toString(),
        role: 'assistant',
        content: 'Error communicating with Yatra.AI orchestrator. Please check your connection.',
        type: 'text'
      }]);
    }
  };

  return (
    <div className="flex h-screen bg-slate-900 text-white overflow-hidden">
      {/* Sidebar / Plan View */}
      <motion.div 
        initial={{ x: -300, opacity: 0 }}
        animate={{ x: 0, opacity: 1 }}
        className="hidden md:flex w-80 flex-col border-r border-slate-800 glass-panel"
      >
        <div className="p-6 border-b border-slate-800 flex items-center justify-between">
          <h2 className="font-bold tracking-widest text-lg gradient-text">YATRA.AI</h2>
          <Link href="/" className="text-slate-400 hover:text-white transition">
            <ArrowLeft className="h-5 w-5" />
          </Link>
        </div>
        <div className="flex-1 p-6 overflow-y-auto">
          <h3 className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-4">Trip Stages</h3>
          <div className="space-y-4">
            {/* Dummy Stage Cards */}
            <div className="p-4 rounded-xl border border-slate-700 bg-slate-800/50 hover:bg-slate-800 transition cursor-pointer">
              <div className="flex items-center text-indigo-400 mb-2">
                <Navigation className="h-4 w-4 mr-2" />
                <span className="text-sm font-semibold">Transport</span>
              </div>
              <p className="text-xs text-slate-400">Flight • IND-DEL</p>
            </div>
            <div className="p-4 rounded-xl border border-slate-700 bg-slate-800/50 hover:bg-slate-800 transition cursor-pointer">
              <div className="flex items-center text-rose-400 mb-2">
                <Hotel className="h-4 w-4 mr-2" />
                <span className="text-sm font-semibold">Hotel</span>
              </div>
              <p className="text-xs text-slate-400">Taj Mahal Palace</p>
            </div>
            <div className="p-4 rounded-xl border border-slate-700 bg-slate-800/50 hover:bg-slate-800 transition cursor-pointer">
              <div className="flex items-center text-amber-400 mb-2">
                <Utensils className="h-4 w-4 mr-2" />
                <span className="text-sm font-semibold">Food</span>
              </div>
              <p className="text-xs text-slate-400">Lunch • Karim's</p>
            </div>
          </div>
        </div>
      </motion.div>

      {/* Main Chat Area */}
      <div className="flex-1 flex flex-col relative">
        <div className="absolute inset-0 bg-[url('https://www.transparenttextures.com/patterns/cubes.png')] opacity-5 pointer-events-none"></div>
        
        {/* Header */}
        <div className="h-16 border-b border-slate-800 flex items-center px-6 glass-panel z-10 md:hidden justify-between">
          <h2 className="font-bold gradient-text">YATRA.AI</h2>
          <Link href="/" className="text-slate-400"><ArrowLeft className="h-5 w-5" /></Link>
        </div>

        {/* Messages */}
        <div className="flex-1 overflow-y-auto p-4 md:p-8 space-y-6">
          <AnimatePresence>
            {messages.map((msg) => (
              <motion.div
                key={msg.id}
                initial={{ opacity: 0, y: 10, scale: 0.95 }}
                animate={{ opacity: 1, y: 0, scale: 1 }}
                className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
              >
                <div className={`max-w-[80%] md:max-w-[60%] p-4 rounded-2xl ${
                  msg.role === 'user' 
                    ? 'bg-indigo-600 text-white rounded-br-sm shadow-lg shadow-indigo-600/20' 
                    : 'glass-panel text-slate-200 rounded-bl-sm border border-slate-700'
                }`}>
                  <p className="text-sm md:text-base leading-relaxed">{msg.content}</p>
                  {msg.type === 'cab' && <div className="mt-4"><CabTable options={msg.data} /></div>}
                  {msg.type === 'flight' && <div className="mt-4"><FlightTable flights={msg.data} /></div>}
                  {msg.type === 'hotel' && <div className="mt-4"><HotelGrid hotels={msg.data} /></div>}
                  {msg.type === 'map' && <div className="mt-4"><MapView {...msg.data} /></div>}
                </div>
              </motion.div>
            ))}
          </AnimatePresence>
          <div ref={messagesEndRef} />
        </div>

        {/* Input Area */}
        <div className="p-4 md:p-6 z-10 glass-panel border-t border-slate-800">
          <div className="max-w-4xl mx-auto relative flex items-center">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleSend()}
              placeholder="Type your message..."
              className="w-full glass-input rounded-full py-4 pl-6 pr-16 text-sm md:text-base"
            />
            <button 
              onClick={handleSend}
              className="absolute right-2 p-2 bg-indigo-600 hover:bg-indigo-500 rounded-full text-white transition-colors"
            >
              <Send className="h-5 w-5" />
            </button>
          </div>
          <div className="text-center mt-3 text-xs text-slate-500">
            Yatra.AI sub-agents are actively standing by.
          </div>
        </div>
      </div>
    </div>
  );
}
