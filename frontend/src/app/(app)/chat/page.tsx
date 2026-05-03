"use client";

import { useState, useEffect, useRef } from 'react';
import { Send, Navigation, Utensils, Hotel, Car, MapPin, ArrowLeft, Sparkles, Plane, MessageCircle, CheckCircle2 } from 'lucide-react';
import Link from 'next/link';
import api from '@/lib/api';

interface CollectedInfo {
  origin?: string;
  destination?: string;
  trip_type?: string;
  transport_modes?: string[];
  start_date?: string;
  end_date?: string;
  total_budget?: number;
  group_size?: number;
  hotel_stars?: number;
  is_vegetarian?: boolean;
  cuisine_preferences?: string[];
  interest_tags?: string[];
}

const INFO_LABELS: Record<string, string> = {
  origin: "From",
  destination: "To",
  trip_type: "Trip Type",
  transport_modes: "Transport",
  start_date: "Start Date",
  end_date: "End Date",
  total_budget: "Budget",
  group_size: "Group Size",
  hotel_stars: "Hotel Stars",
  is_vegetarian: "Vegetarian",
  cuisine_preferences: "Cuisine",
  interest_tags: "Interests"
};

export default function ChatPage() {
  const [messages, setMessages] = useState<any[]>([
    { 
      id: '1', 
      role: 'assistant', 
      content: "Hey! 👋 I'm Yatri AI, your personal travel companion. You can ask me anything about travel in India, or tap **Plan Trip** in the sidebar to start planning your next adventure!", 
      type: 'text' 
    }
  ]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [chatMode, setChatMode] = useState<'chat' | 'planning'>('chat');
  const [collectedInfo, setCollectedInfo] = useState<CollectedInfo>({});
  const [sessionId] = useState(() => `session_${Date.now()}`);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const sendMessage = async (message: string, action?: string) => {
    if ((!message.trim() && !action) || isLoading) return;
    
    if (message.trim()) {
      const newMsg = { id: Date.now().toString(), role: 'user', content: message, type: 'text' };
      setMessages(prev => [...prev, newMsg]);
    }
    setInput('');
    setIsLoading(true);
    
    try {
      const response = await api.post('/chat', { 
        message: message || 'plan_trip', 
        session_id: sessionId,
        action: action || undefined
      });
      
      const reply = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: response.data.message || 'Processing your request...',
        type: response.data.ui_type || 'text',
        data: response.data.ui_data
      };
      setMessages(prev => [...prev, reply]);

      // Update collected info and mode
      if (response.data.collected_info) {
        setCollectedInfo(response.data.collected_info);
      }
      if (response.data.chat_mode) {
        setChatMode(response.data.chat_mode);
      }
    } catch (error) {
      console.error("Chat API Error:", error);
      setMessages(prev => [...prev, {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: 'I\'m having trouble connecting right now. Please make sure the backend is running on port 8001.',
        type: 'text'
      }]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleSend = () => sendMessage(input);

  const handlePlanTrip = () => {
    setChatMode('planning');
    const planMsg = { 
      id: Date.now().toString(), 
      role: 'user', 
      content: '🗺️ I want to plan a trip!', 
      type: 'text' 
    };
    setMessages(prev => [...prev, planMsg]);
    sendMessage('I want to plan a trip', 'plan_trip');
  };

  const collectedEntries = Object.entries(collectedInfo).filter(([_, v]) => v !== null && v !== undefined);

  return (
    <div className="flex h-screen overflow-hidden" style={{ backgroundColor: 'var(--color-pure-white)' }}>
      {/* Sidebar */}
      <div className="hidden md:flex w-80 flex-col" style={{ borderRight: '1px solid var(--color-oat-border)', backgroundColor: 'var(--color-neutral-50)' }}>
        {/* Sidebar Header */}
        <div className="flex items-center justify-between p-6" style={{ borderBottom: '1px solid var(--color-oat-border)' }}>
          <div className="flex items-center gap-3">
            <span className="green-dot-lg" />
            <span className="font-semibold" style={{ letterSpacing: '-0.4px', color: 'var(--color-clay-black)' }}>Yatri AI</span>
          </div>
          <Link href="/" style={{ color: 'var(--color-neutral-400)' }}>
            <ArrowLeft className="h-5 w-5" />
          </Link>
        </div>

        {/* Plan Trip Button */}
        <div className="p-5">
          <button 
            onClick={handlePlanTrip}
            disabled={isLoading}
            className="clay-button-cta w-full"
            style={{ borderRadius: '12px', padding: '14px', fontSize: '15px', gap: '10px' }}
          >
            <Plane className="h-5 w-5" />
            Plan a Trip
          </button>
        </div>

        {/* Trip Info Collected */}
        {chatMode === 'planning' && (
          <div className="flex-1 p-5 overflow-y-auto">
            <p className="clay-label mb-4">
              {collectedEntries.length > 0 ? 'TRIP DETAILS' : 'PLANNING MODE'}
            </p>
            
            {collectedEntries.length > 0 ? (
              <div className="space-y-2">
                {collectedEntries.map(([key, value]) => (
                  <div 
                    key={key} 
                    className="p-3 rounded-xl flex items-start gap-3 animate-fade-in"
                    style={{ backgroundColor: 'var(--color-pure-white)', border: '1px solid var(--color-oat-border)' }}
                  >
                    <CheckCircle2 className="h-4 w-4 mt-0.5 flex-shrink-0" style={{ color: 'var(--color-emerald-500)' }} />
                    <div>
                      <p className="text-xs font-medium" style={{ color: 'var(--color-neutral-400)' }}>
                        {INFO_LABELS[key] || key}
                      </p>
                      <p className="text-sm font-semibold" style={{ color: 'var(--color-clay-black)', letterSpacing: '-0.2px' }}>
                        {Array.isArray(value) ? value.join(', ') : 
                         typeof value === 'boolean' ? (value ? 'Yes' : 'No') :
                         typeof value === 'number' ? (key === 'total_budget' ? `₹${value.toLocaleString()}` : String(value)) :
                         String(value)}
                      </p>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center py-8">
                <MessageCircle className="h-8 w-8 mx-auto mb-3" style={{ color: 'var(--color-neutral-300)' }} />
                <p className="text-sm" style={{ color: 'var(--color-neutral-400)' }}>
                  Tell me about your trip and I'll collect the details!
                </p>
              </div>
            )}
          </div>
        )}

        {/* Default sidebar when not planning */}
        {chatMode !== 'planning' && (
          <div className="flex-1 p-5 overflow-y-auto">
            <p className="clay-label mb-4">AI Agents</p>
            <div className="space-y-3">
              {[
                { icon: Navigation, label: 'Transport', desc: 'Flights • Trains • Buses', color: 'var(--color-emerald-600)', bg: '#d1fae5' },
                { icon: Car, label: 'Cabs', desc: 'Ola vs Uber comparison', color: 'var(--color-emerald-600)', bg: '#d1fae5' },
                { icon: Hotel, label: 'Hotels', desc: 'Best stays for your budget', color: '#6d28d9', bg: '#ede9fe' },
                { icon: Utensils, label: 'Food', desc: 'Local cuisine & restaurants', color: '#b45309', bg: '#fef3c7' },
                { icon: MapPin, label: 'Places', desc: 'Tourist spots & attractions', color: '#be123c', bg: '#ffe4e6' },
                { icon: Navigation, label: 'Maps', desc: 'Optimized route planning', color: '#0e7490', bg: '#cffafe' },
              ].map((stage, i) => (
                <div key={i} className="p-4 rounded-xl" style={{ border: '1px solid var(--color-oat-border)', backgroundColor: 'var(--color-pure-white)' }}>
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-xl flex items-center justify-center" style={{ backgroundColor: stage.bg }}>
                      <stage.icon className="h-5 w-5" style={{ color: stage.color }} />
                    </div>
                    <div>
                      <p className="text-sm font-semibold" style={{ letterSpacing: '-0.2px', color: 'var(--color-clay-black)' }}>{stage.label}</p>
                      <p className="text-xs" style={{ color: 'var(--color-neutral-400)' }}>{stage.desc}</p>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Sidebar Footer */}
        <div className="p-5" style={{ borderTop: '1px solid var(--color-oat-border)' }}>
          <div className="flex items-center gap-2 text-xs" style={{ color: 'var(--color-neutral-400)' }}>
            <Sparkles className="h-4 w-4" />
            <span>Powered by LLaMA 3.1 + LangGraph</span>
          </div>
        </div>
      </div>

      {/* Main Chat Area */}
      <div className="flex-1 flex flex-col relative">
        {/* Mobile Header */}
        <div className="clay-nav flex items-center justify-between md:hidden">
          <Link href="/" style={{ color: 'var(--color-neutral-600)' }}><ArrowLeft className="h-5 w-5" /></Link>
          <div className="flex items-center gap-3">
            <span className="green-dot" />
            <span className="font-semibold text-sm" style={{ color: 'var(--color-clay-black)' }}>Yatri AI</span>
            {chatMode === 'planning' && (
              <span className="text-xs font-medium px-2 py-0.5 rounded-full" style={{ background: '#d1fae5', color: 'var(--color-emerald-600)' }}>
                Planning
              </span>
            )}
          </div>
          <button 
            onClick={handlePlanTrip}
            className="p-2 rounded-lg"
            style={{ backgroundColor: 'var(--color-emerald-500)', color: 'white' }}
          >
            <Plane className="h-4 w-4" />
          </button>
        </div>

        {/* Messages */}
        <div className="flex-1 overflow-y-auto p-4 md:p-8">
          <div className="max-w-3xl mx-auto space-y-5">
            {messages.map((msg) => (
              <div
                key={msg.id}
                className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'} animate-fade-in`}
              >
                <div className={`max-w-[80%] md:max-w-[70%] ${msg.role === 'user' ? 'bubble-user' : 'bubble-assistant'}`}>
                  {/* Render markdown-like bold text */}
                  <p className="text-sm md:text-base" style={{ lineHeight: 1.6 }}>
                    {msg.content.split(/(\*\*[^*]+\*\*)/).map((part: string, i: number) => {
                      if (part.startsWith('**') && part.endsWith('**')) {
                        return <strong key={i}>{part.slice(2, -2)}</strong>;
                      }
                      return part;
                    })}
                  </p>
                  
                  {/* Rich Data Rendering */}
                  {msg.type === 'plan' && msg.data && (
                    <div className="mt-4 p-4 rounded-xl" style={{ background: '#d1fae5', border: '1px solid #a7f3d0' }}>
                      <p className="text-xs font-semibold mb-3" style={{ color: 'var(--color-emerald-600)' }}>📋 YOUR TRAVEL PLAN</p>
                      {msg.data.title && (
                        <p className="text-sm font-bold mb-2" style={{ color: 'var(--color-clay-black)' }}>{msg.data.title}</p>
                      )}
                      {msg.data.estimated_cost && (
                        <p className="text-sm mb-2" style={{ color: 'var(--color-emerald-700)' }}>
                          💰 Estimated Cost: ₹{msg.data.estimated_cost.toLocaleString()}
                        </p>
                      )}
                      {msg.data.days && msg.data.days.map((day: any, di: number) => (
                        <div key={di} className="mb-3 p-3 rounded-lg" style={{ backgroundColor: 'rgba(255,255,255,0.7)' }}>
                          <p className="text-xs font-bold mb-1" style={{ color: 'var(--color-emerald-700)' }}>Day {day.day}</p>
                          {day.activities && day.activities.map((act: any, ai: number) => (
                            <p key={ai} className="text-xs mb-0.5" style={{ color: 'var(--color-neutral-700)' }}>
                              {act.time} — {act.name || act.description} {act.cost ? `(₹${act.cost})` : ''}
                            </p>
                          ))}
                        </div>
                      ))}
                      {msg.data.tips && (
                        <div className="mt-2">
                          <p className="text-xs font-semibold mb-1" style={{ color: 'var(--color-emerald-600)' }}>💡 Tips:</p>
                          {msg.data.tips.map((tip: string, ti: number) => (
                            <p key={ti} className="text-xs" style={{ color: 'var(--color-neutral-600)' }}>• {tip}</p>
                          ))}
                        </div>
                      )}
                    </div>
                  )}
                  {msg.type === 'hotel' && msg.data?.hotels && (
                    <div className="mt-4 space-y-2">
                      {msg.data.hotels.map((h: any, i: number) => (
                        <div key={i} className="p-3 rounded-xl" style={{ background: '#ede9fe', border: '1px solid #ddd6fe' }}>
                          <p className="text-sm font-semibold" style={{ color: 'var(--color-clay-black)' }}>{h.name}</p>
                          <p className="text-xs" style={{ color: 'var(--color-neutral-600)' }}>⭐ {h.rating} star • ₹{h.price_per_night}/night</p>
                        </div>
                      ))}
                    </div>
                  )}
                  {msg.type === 'cab' && msg.data?.options && (
                    <div className="mt-4 space-y-2">
                      {msg.data.options.map((c: any, i: number) => (
                        <div key={i} className="p-3 rounded-xl" style={{ background: '#cffafe', border: '1px solid #a5f3fc' }}>
                          <p className="text-sm font-semibold" style={{ color: 'var(--color-clay-black)' }}>{c.provider}</p>
                          <p className="text-xs" style={{ color: 'var(--color-neutral-600)' }}>🚕 {c.vehicle_type} • ETA {c.eta} • ₹{c.price}</p>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            ))}

            {/* Typing Indicator */}
            {isLoading && (
              <div className="flex justify-start animate-fade-in">
                <div className="bubble-assistant flex items-center gap-2">
                  <div className="flex gap-1">
                    <span className="w-2 h-2 rounded-full animate-bounce" style={{ backgroundColor: 'var(--color-neutral-300)', animationDelay: '0ms' }} />
                    <span className="w-2 h-2 rounded-full animate-bounce" style={{ backgroundColor: 'var(--color-neutral-300)', animationDelay: '150ms' }} />
                    <span className="w-2 h-2 rounded-full animate-bounce" style={{ backgroundColor: 'var(--color-neutral-300)', animationDelay: '300ms' }} />
                  </div>
                  <span className="text-xs" style={{ color: 'var(--color-neutral-400)' }}>Yatri AI is thinking...</span>
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>
        </div>

        {/* Input Area */}
        <div className="p-4 md:p-6" style={{ borderTop: '1px solid var(--color-oat-border)', backgroundColor: 'var(--color-neutral-50)' }}>
          <div className="max-w-3xl mx-auto relative flex items-center">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleSend()}
              placeholder={chatMode === 'planning' ? "Tell me about your trip..." : "Ask me anything about travel..."}
              className="clay-input pr-14"
              style={{ borderRadius: '999px', paddingLeft: '24px', paddingRight: '56px' }}
              disabled={isLoading}
            />
            <button 
              onClick={handleSend}
              disabled={isLoading}
              className="absolute right-2 w-10 h-10 flex items-center justify-center rounded-full transition-all"
              style={{ 
                backgroundColor: input.trim() ? 'var(--color-clay-black)' : 'var(--color-neutral-300)',
                color: 'var(--color-pure-white)',
              }}
            >
              <Send className="h-4 w-4" />
            </button>
          </div>
          <p className="text-center mt-3 text-xs" style={{ color: 'var(--color-neutral-400)' }}>
            {chatMode === 'planning' 
              ? `✨ Planning mode • ${collectedEntries.length}/12 details collected`
              : 'Six AI agents ready • Transport • Cabs • Hotels • Food • Places • Maps'
            }
          </p>
        </div>
      </div>
    </div>
  );
}
