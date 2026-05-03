"use client";

import { useState, useEffect, useRef } from 'react';
import { Send, Navigation, Utensils, Hotel, Car, MapPin, ArrowLeft, Sparkles, Plane, MessageCircle, CheckCircle2, Settings, History, Palette, X, Edit3, Plus } from 'lucide-react';
import Link from 'next/link';
import api from '@/lib/api';
import { useThemeStore, THEMES, ThemeName } from '@/store/themeStore';

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
  const [showSettings, setShowSettings] = useState(false);
  const [sidebarView, setSidebarView] = useState<'agents' | 'settings' | 'history'>('agents');
  const [agentStatuses, setAgentStatuses] = useState<Record<string, any>>({});
  const [overallConfidence, setOverallConfidence] = useState<number | null>(null);
  const [ragasResult, setRagasResult] = useState<any>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const { theme, setTheme } = useThemeStore();

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const sendMessage = async (message: string, action?: string, targetAgent?: string) => {
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
        action: action || undefined,
        target_agent: targetAgent || undefined,
        user_prefs: { notes: typeof window !== 'undefined' ? localStorage.getItem('yatri_user_prefs') || '' : '' }
      });
      
      const reply = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: response.data.message || 'Processing your request...',
        type: response.data.ui_type || 'text',
        data: response.data.ui_data
      };
      setMessages(prev => [...prev, reply]);

      if (response.data.collected_info) {
        setCollectedInfo(response.data.collected_info);
      }
      if (response.data.chat_mode) {
        setChatMode(response.data.chat_mode);
      }
      if (response.data.agent_statuses) {
        setAgentStatuses(response.data.agent_statuses);
      }
      if (response.data.overall_confidence != null) {
        setOverallConfidence(response.data.overall_confidence);
      }
      if (response.data.ragas_result) {
        setRagasResult(response.data.ragas_result);
      }
    } catch (error) {
      console.error("Chat API Error:", error);
      setMessages(prev => [...prev, {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: 'Our systems are experiencing a brief delay. Please try again in a moment.',
        type: 'text'
      }]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleSend = () => sendMessage(input);

  const handlePlanTrip = () => {
    setChatMode('planning');
    setSidebarView('agents');
    sendMessage('🗺️ I want to plan a trip!', 'plan_trip');
  };

  const collectedEntries = Object.entries(collectedInfo).filter(([_, v]) => v !== null && v !== undefined);

  return (
    <div className="flex h-screen overflow-hidden" style={{ backgroundColor: 'var(--bg-primary)' }}>
      {/* Sidebar */}
      <div className="hidden md:flex w-80 flex-col" style={{ borderRight: '1px solid var(--border-main)', backgroundColor: 'var(--bg-sidebar)' }}>
        {/* Sidebar Header */}
        <div className="flex items-center justify-between p-6" style={{ borderBottom: '1px solid var(--border-main)' }}>
          <div className="flex items-center gap-3">
            <span className="green-dot-lg" />
            <span className="font-semibold" style={{ letterSpacing: '-0.4px', color: 'var(--text-primary)' }}>Yatri AI</span>
          </div>
          <Link href="/" style={{ color: 'var(--text-muted)' }}>
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

        {/* Sidebar Navigation Tabs */}
        <div className="flex gap-1 px-5 mb-2">
          {[
            { id: 'agents' as const, icon: Sparkles, label: 'Agents' },
            { id: 'history' as const, icon: History, label: 'History' },
            { id: 'settings' as const, icon: Settings, label: 'Settings' },
          ].map((tab) => (
            <button
              key={tab.id}
              onClick={() => setSidebarView(tab.id)}
              className="flex-1 flex items-center justify-center gap-1.5 py-2 px-2 rounded-lg text-xs font-medium transition-all"
              style={{
                backgroundColor: sidebarView === tab.id ? 'var(--accent-light)' : 'transparent',
                color: sidebarView === tab.id ? 'var(--accent-dark)' : 'var(--text-muted)',
              }}
            >
              <tab.icon className="h-3.5 w-3.5" />
              {tab.label}
            </button>
          ))}
        </div>

        {/* Sidebar Content */}
        <div className="flex-1 p-5 overflow-y-auto">
          {/* AGENTS & DETAILS VIEW */}
          {sidebarView === 'agents' && (
            <>
              {chatMode === 'planning' && (
                <div className="mb-6">
                  <p className="clay-label mb-3">
                    {collectedEntries.length > 0 ? 'TRIP DETAILS' : 'PLANNING MODE'}
                  </p>
                  {collectedEntries.length > 0 ? (
                    <div className="space-y-2">
                      {collectedEntries.map(([key, value]) => (
                        <div 
                          key={key} 
                          className="p-3 rounded-xl flex items-start gap-3 animate-fade-in"
                          style={{ backgroundColor: 'var(--bg-surface)', border: '1px solid var(--border-main)' }}
                        >
                          <CheckCircle2 className="h-4 w-4 mt-0.5 flex-shrink-0" style={{ color: 'var(--accent-primary)' }} />
                          <div>
                            <p className="text-xs font-medium" style={{ color: 'var(--text-muted)' }}>
                              {INFO_LABELS[key] || key}
                            </p>
                            <p className="text-sm font-semibold" style={{ color: 'var(--text-primary)', letterSpacing: '-0.2px' }}>
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
                    <div className="text-center py-4 rounded-xl" style={{ border: '1px dashed var(--border-main)' }}>
                      <p className="text-xs" style={{ color: 'var(--text-muted)' }}>
                        Tell me about your trip...
                      </p>
                    </div>
                  )}
                </div>
              )}

              <p className="clay-label mb-3">AI Agents</p>
              <div className="space-y-3">
                {[
                  { id: 'transport', icon: Navigation, label: 'Transport', desc: 'Flights • Trains • Buses', color: 'var(--accent-primary)', bg: 'var(--accent-light)' },
                  { id: 'cabs', icon: Car, label: 'Cabs', desc: 'Ola vs Uber comparison', color: 'var(--accent-primary)', bg: 'var(--accent-light)' },
                  { id: 'hotels', icon: Hotel, label: 'Hotels', desc: 'Best stays for your budget', color: '#6d28d9', bg: '#ede9fe' },
                  { id: 'food', icon: Utensils, label: 'Food', desc: 'Local cuisine & restaurants', color: '#b45309', bg: '#fef3c7' },
                  { id: 'places', icon: MapPin, label: 'Places', desc: 'Tourist spots & attractions', color: '#be123c', bg: '#ffe4e6' },
                  { id: 'maps', icon: Navigation, label: 'Maps', desc: 'Optimized route planning', color: '#0e7490', bg: '#cffafe' },
                ].map((stage, i) => {
                  const status = agentStatuses[stage.id];
                  const agentState = status?.status || 'idle';
                  const confidence = status?.confidence || 0;
                  return (
                    <button 
                      key={i} 
                      onClick={() => {
                        sendMessage(`I need help with ${stage.label.toLowerCase()}...`, undefined, stage.id);
                      }}
                      className="w-full text-left p-3 rounded-xl transition-all hover:scale-[1.02]" 
                      style={{ border: `1px solid ${agentState === 'done' ? 'var(--accent-primary)' : 'var(--border-main)'}`, backgroundColor: 'var(--bg-surface)' }}
                    >
                      <div className="flex items-center gap-3 relative">
                        <div className="w-10 h-10 rounded-xl flex items-center justify-center relative" style={{ backgroundColor: stage.bg }}>
                          <stage.icon className="h-5 w-5" style={{ color: stage.color }} />
                          {agentState === 'researching' && (
                            <span className="absolute -top-1 -right-1 w-3 h-3 bg-green-500 rounded-full border-2 border-white animate-pulse" />
                          )}
                          {agentState === 're-researching' && (
                            <span className="absolute -top-1 -right-1 w-3 h-3 bg-yellow-500 rounded-full border-2 border-white animate-pulse" />
                          )}
                          {agentState === 'done' && (
                            <span className="absolute -top-1 -right-1 w-3.5 h-3.5 bg-green-500 rounded-full border-2 border-white flex items-center justify-center">
                              <CheckCircle2 className="h-2.5 w-2.5 text-white" />
                            </span>
                          )}
                          {agentState === 'error' && (
                            <span className="absolute -top-1 -right-1 w-3 h-3 bg-red-500 rounded-full border-2 border-white" />
                          )}
                        </div>
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center gap-2">
                            <p className="text-sm font-semibold" style={{ letterSpacing: '-0.2px', color: 'var(--text-primary)' }}>{stage.label}</p>
                            {agentState === 'done' && confidence > 0 && (
                              <span className="text-[10px] font-bold px-1.5 py-0.5 rounded-full" style={{ backgroundColor: confidence >= 70 ? '#d1fae5' : '#fef3c7', color: confidence >= 70 ? '#047857' : '#b45309' }}>
                                {Math.round(confidence)}%
                              </span>
                            )}
                          </div>
                          <p className="text-xs truncate" style={{ color: 'var(--text-muted)' }}>
                            {agentState === 'researching' ? 'Searching...' : agentState === 're-researching' ? 'Re-researching...' : agentState === 'done' ? (status?.message || 'Complete') : agentState === 'error' ? 'Failed' : stage.desc}
                          </p>
                        </div>
                      </div>
                    </button>
                  );
                })}
              </div>
            </>
          )}

          {/* HISTORY VIEW */}
          {sidebarView === 'history' && (
            <>
              <p className="clay-label mb-4">Chat History</p>
              <div className="text-center py-8">
                <History className="h-8 w-8 mx-auto mb-3" style={{ color: 'var(--text-faint)' }} />
                <p className="text-sm" style={{ color: 'var(--text-muted)' }}>
                  Your past trip plans will appear here
                </p>
                <p className="text-xs mt-2" style={{ color: 'var(--text-faint)' }}>
                  Start planning to build your travel history
                </p>
              </div>
            </>
          )}

          {/* SETTINGS VIEW */}
          {sidebarView === 'settings' && (
            <>
              <p className="clay-label mb-4">Appearance</p>
              <div className="space-y-3 mb-6">
                {THEMES.map((t) => (
                  <button
                    key={t.id}
                    onClick={() => setTheme(t.id)}
                    className="w-full p-3 rounded-xl flex items-center gap-3 transition-all"
                    style={{
                      backgroundColor: theme === t.id ? 'var(--accent-light)' : 'var(--bg-surface)',
                      border: `1px solid ${theme === t.id ? 'var(--accent-primary)' : 'var(--border-main)'}`,
                    }}
                  >
                    <div className={`theme-swatch ${t.swatchClass} ${theme === t.id ? 'active' : ''}`} />
                    <div className="text-left">
                      <p className="text-sm font-semibold" style={{ color: 'var(--text-primary)' }}>{t.label}</p>
                      <p className="text-xs" style={{ color: 'var(--text-muted)' }}>{t.description}</p>
                    </div>
                    {theme === t.id && <CheckCircle2 className="h-4 w-4 ml-auto" style={{ color: 'var(--accent-primary)' }} />}
                  </button>
                ))}
              </div>

              <p className="clay-label mb-4">Personal Preferences</p>
              <div className="space-y-3">
                <p className="text-xs" style={{ color: 'var(--text-muted)' }}>
                  Set your global dos, don'ts, pros, and cons here. All agents will prioritize these instructions for highly personalized results.
                </p>
                <textarea 
                  className="w-full p-3 rounded-xl text-sm transition-all focus:outline-none"
                  style={{ backgroundColor: 'var(--bg-surface)', border: '1px solid var(--border-main)', color: 'var(--text-primary)', minHeight: '120px', resize: 'vertical' }}
                  placeholder="E.g., I am strictly vegetarian. I hate long layovers. I love boutique hotels over large chains. No travel before 9 AM."
                  onChange={(e) => {
                    localStorage.setItem('yatri_user_prefs', e.target.value);
                  }}
                  defaultValue={typeof window !== 'undefined' ? localStorage.getItem('yatri_user_prefs') || '' : ''}
                />
              </div>
            </>
          )}
        </div>

        {/* Sidebar Footer */}
        <div className="p-5" style={{ borderTop: '1px solid var(--border-main)' }}>
          <div className="flex items-center gap-2 text-xs" style={{ color: 'var(--text-muted)' }}>
            <Sparkles className="h-4 w-4" />
            <span>Powered by LLaMA 3.1 + LangGraph</span>
          </div>
        </div>
      </div>

      {/* Main Chat Area */}
      <div className="flex-1 flex flex-col relative" style={{ backgroundColor: 'var(--bg-chat)' }}>
        {/* Mobile Header */}
        <div className="clay-nav flex items-center justify-between md:hidden">
          <Link href="/" style={{ color: 'var(--text-secondary)' }}><ArrowLeft className="h-5 w-5" /></Link>
          <div className="flex items-center gap-3">
            <span className="green-dot" />
            <span className="font-semibold text-sm" style={{ color: 'var(--text-primary)' }}>Yatri AI</span>
            {chatMode === 'planning' && (
              <span className="text-xs font-medium px-2 py-0.5 rounded-full" style={{ background: 'var(--accent-light)', color: 'var(--accent-dark)' }}>
                Planning
              </span>
            )}
          </div>
          <button 
            onClick={handlePlanTrip}
            className="p-2 rounded-lg"
            style={{ backgroundColor: 'var(--accent-primary)', color: 'white' }}
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
                  <p className="text-sm md:text-base" style={{ lineHeight: 1.6 }}>
                    {msg.content.split(/(\*\*[^*]+\*\*)/).map((part: string, i: number) => {
                      if (part.startsWith('**') && part.endsWith('**')) {
                        return <strong key={i}>{part.slice(2, -2)}</strong>;
                      }
                      return part;
                    })}
                  </p>
                  
                  {/* Plan Card */}
                  {msg.type === 'plan' && msg.data && (
                    <div className="mt-4 p-4 rounded-xl" style={{ background: 'var(--accent-light)', border: '1px solid var(--border-main)' }}>
                      <p className="text-xs font-semibold mb-3" style={{ color: 'var(--accent-dark)' }}>📋 YOUR TRAVEL PLAN</p>
                      {msg.data.title && (
                        <p className="text-sm font-bold mb-2" style={{ color: 'var(--text-primary)' }}>{msg.data.title}</p>
                      )}
                      {msg.data.estimated_cost && (
                        <p className="text-sm mb-2" style={{ color: 'var(--accent-dark)' }}>
                          💰 Estimated Cost: ₹{msg.data.estimated_cost.toLocaleString()}
                        </p>
                      )}
                      
                      {msg.data.confidence_score && (
                        <div className="mb-4 p-3 rounded-lg" style={{ backgroundColor: 'var(--bg-surface)', border: '1px solid var(--border-main)' }}>
                          <div className="flex items-center justify-between mb-1">
                            <span className="text-xs font-bold" style={{ color: 'var(--text-primary)' }}>Personalization Confidence</span>
                            <span className="text-xs font-bold" style={{ color: msg.data.confidence_score >= 80 ? '#10b981' : '#f59e0b' }}>
                              {msg.data.confidence_score}%
                            </span>
                          </div>
                          <div className="w-full bg-gray-200 rounded-full h-1.5 mb-2">
                            <div className="h-1.5 rounded-full" style={{ width: `${msg.data.confidence_score}%`, backgroundColor: msg.data.confidence_score >= 80 ? '#10b981' : '#f59e0b' }}></div>
                          </div>
                          {msg.data.ragas_alignment_check && (
                            <p className="text-[10px] leading-tight" style={{ color: 'var(--text-muted)' }}>
                              <span className="font-semibold text-[10px]">RAGAS Check:</span> {msg.data.ragas_alignment_check}
                            </p>
                          )}
                        </div>
                      )}
                      {msg.data.days && msg.data.days.map((day: any, di: number) => (
                        <div key={di} className="mb-3 p-3 rounded-lg plan-card plan-card-editable">
                          <div className="flex items-center justify-between mb-1">
                            <p className="text-xs font-bold" style={{ color: 'var(--accent-dark)' }}>Day {day.day}</p>
                            <Edit3 className="h-3 w-3" style={{ color: 'var(--text-muted)' }} />
                          </div>
                          {day.activities && day.activities.map((act: any, ai: number) => (
                            <p key={ai} className="text-xs mb-0.5" style={{ color: 'var(--text-secondary)' }}>
                              {act.time} — {act.name || act.description} {act.cost ? `(₹${act.cost})` : ''}
                            </p>
                          ))}
                        </div>
                      ))}
                      {msg.data.tips && (
                        <div className="mt-2">
                          <p className="text-xs font-semibold mb-1" style={{ color: 'var(--accent-dark)' }}>💡 Tips:</p>
                          {msg.data.tips.map((tip: string, ti: number) => (
                            <p key={ti} className="text-xs" style={{ color: 'var(--text-secondary)' }}>• {tip}</p>
                          ))}
                        </div>
                      )}
                    </div>
                  )}
                  {msg.type === 'hotel' && msg.data?.hotels && (
                    <div className="mt-4 space-y-2">
                      {msg.data.hotels.map((h: any, i: number) => (
                        <div key={i} className="p-3 rounded-xl" style={{ background: '#ede9fe', border: '1px solid #ddd6fe' }}>
                          <p className="text-sm font-semibold" style={{ color: 'var(--text-primary)' }}>{h.name}</p>
                          <p className="text-xs" style={{ color: 'var(--text-secondary)' }}>⭐ {h.rating} star • ₹{h.price_per_night}/night</p>
                        </div>
                      ))}
                    </div>
                  )}
                  {msg.type === 'cab' && msg.data?.options && (
                    <div className="mt-4 space-y-2">
                      {msg.data.options.map((c: any, i: number) => (
                        <div key={i} className="p-3 rounded-xl" style={{ background: '#cffafe', border: '1px solid #a5f3fc' }}>
                          <p className="text-sm font-semibold" style={{ color: 'var(--text-primary)' }}>{c.provider}</p>
                          <p className="text-xs" style={{ color: 'var(--text-secondary)' }}>🚕 {c.vehicle_type} • ETA {c.eta} • ₹{c.price}</p>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            ))}

            {isLoading && (
              <div className="flex justify-start animate-fade-in">
                <div className="bubble-assistant p-4 w-full max-w-sm">
                  <div className="flex items-center gap-2 mb-3">
                    <div className="flex gap-1">
                      <span className="w-2 h-2 rounded-full animate-bounce" style={{ backgroundColor: 'var(--accent-primary)', animationDelay: '0ms' }} />
                      <span className="w-2 h-2 rounded-full animate-bounce" style={{ backgroundColor: 'var(--accent-primary)', animationDelay: '150ms' }} />
                      <span className="w-2 h-2 rounded-full animate-bounce" style={{ backgroundColor: 'var(--accent-primary)', animationDelay: '300ms' }} />
                    </div>
                    <span className="text-xs font-bold" style={{ color: 'var(--accent-dark)' }}>
                      {chatMode === 'planning' ? 'AGENTS RESEARCHING IN PARALLEL...' : 'THINKING...'}
                    </span>
                  </div>
                  {chatMode === 'planning' && (
                    <div className="space-y-2">
                      {[
                        { id: 'transport', num: 1, label: 'Transport routes & prices', icon: '🚃' },
                        { id: 'hotels', num: 2, label: 'Hotels within budget', icon: '🏨' },
                        { id: 'cabs', num: 3, label: 'Cab fare comparison', icon: '🚕' },
                        { id: 'food', num: 4, label: 'Restaurant recommendations', icon: '🍽️' },
                        { id: 'places', num: 5, label: 'Places to visit', icon: '📍' },
                        { id: 'maps', num: 6, label: 'Optimized route map', icon: '🗺️' },
                      ].map((step, i) => {
                        const s = agentStatuses[step.id];
                        const isDone = s?.status === 'done';
                        return (
                          <div key={i} className="flex items-center gap-2 text-xs" style={{ color: isDone ? 'var(--accent-dark)' : 'var(--text-secondary)' }}>
                            <span className={`flex-shrink-0 w-4 h-4 rounded-full flex items-center justify-center font-bold text-[10px] ${isDone ? '' : 'animate-pulse'}`}
                              style={{ backgroundColor: isDone ? '#d1fae5' : 'var(--accent-light)', color: 'var(--accent-dark)' }}>
                              {isDone ? '✓' : step.num}
                            </span>
                            <span className={isDone ? '' : 'animate-pulse'}>{step.icon} {isDone ? `${step.label} ✓` : `${step.label}...`}</span>
                          </div>
                        );
                      })}
                    </div>
                  )}
                  <div className="mt-3 pt-3 flex items-center justify-between" style={{ borderTop: '1px dashed var(--border-main)' }}>
                    <span className="text-[10px]" style={{ color: 'var(--text-faint)' }}>
                      Confidence: {overallConfidence != null ? `${overallConfidence}%` : 'Evaluating...'}
                    </span>
                    <span className="text-[10px]" style={{ color: 'var(--text-faint)' }}>
                      RAGAS: {ragasResult ? 'Checked ✓' : 'Pending...'}
                    </span>
                  </div>
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>
        </div>

        {/* Input Area */}
        <div className="p-4 md:p-6" style={{ borderTop: '1px solid var(--border-main)', backgroundColor: 'var(--bg-secondary)' }}>
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
                backgroundColor: input.trim() ? 'var(--text-primary)' : 'var(--text-faint)',
                color: 'var(--bg-primary)',
              }}
            >
              <Send className="h-4 w-4" />
            </button>
          </div>
          <p className="text-center mt-3 text-xs" style={{ color: 'var(--text-muted)' }}>
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
