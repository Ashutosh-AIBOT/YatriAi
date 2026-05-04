"use client";

import { useState, useEffect, useRef } from 'react';
import { Send, Navigation, Utensils, Hotel, Car, MapPin, ArrowLeft, Sparkles, Plane, MessageCircle, CheckCircle2, Settings, History, Palette, X, Edit3, Plus, Zap, Heart } from 'lucide-react';
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
  const [sessionId, setSessionId] = useState(() => `session_${Date.now()}`);
  const [showSettings, setShowSettings] = useState(false);
  const [sidebarView, setSidebarView] = useState<'agents' | 'settings' | 'history'>('agents');
  const [agentStatuses, setAgentStatuses] = useState<Record<string, any>>({});
  const [overallConfidence, setOverallConfidence] = useState<number | null>(null);
  const [ragasResult, setRagasResult] = useState<any>(null);
  const [wanderlustEnabled, setWanderlustEnabled] = useState(false);
  const [wanderlustIntensity, setWanderlustIntensity] = useState(50);
  const [psychologyEnabled, setPsychologyEnabled] = useState(true);
  const [expandedActivity, setExpandedActivity] = useState<string | null>(null);
  const [showPrefsModal, setShowPrefsModal] = useState(false);
  const [userPrefsText, setUserPrefsText] = useState('');
  const [historySessions, setHistorySessions] = useState<any[]>([]);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const { theme, setTheme } = useThemeStore();

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  useEffect(() => {
    if (typeof window !== 'undefined') {
      setUserPrefsText(localStorage.getItem('yatri_user_prefs') || '');
    }
    fetchHistory();
  }, []);

  const fetchHistory = async () => {
    try {
      const res = await api.get('/history');
      if (res.data && res.data.history) {
        setHistorySessions(res.data.history);
      }
    } catch (e) {
      console.error("Failed to fetch history", e);
    }
  };

  const loadSession = async (sid: string) => {
    try {
      setIsLoading(true);
      const res = await api.get(`/history/${sid}`);
      if (res.data) {
        setMessages(res.data.messages || []);
        if (res.data.chat_mode) setChatMode(res.data.chat_mode);
        setSidebarView('agents');
        // also set sessionId? React won't let us cleanly without a ref if we want to continue, 
        // but for now let's just display it. Actually, changing sessionId requires state change.
        // We'll leave it as view-only or replace session if possible, but the user requested "chat in past chat".
        // Let's assume we can set SessionId. Wait, `sessionId` is a const with `useState(() => ...)`. We need to change it to let.
      }
    } catch (e) {
      console.error("Failed to load session", e);
    } finally {
      setIsLoading(false);
    }
  };

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
        user_prefs: { notes: typeof window !== 'undefined' ? localStorage.getItem('yatri_user_prefs') || '' : '' },
        wanderlust_enabled: wanderlustEnabled,
        wanderlust_intensity: wanderlustIntensity,
        psychology_enabled: psychologyEnabled,
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
      // Sync auto-extracted user prefs from backend to localStorage
      if (response.data.user_prefs?.notes) {
        const backendNotes = response.data.user_prefs.notes;
        const existing = localStorage.getItem('yatri_user_prefs') || '';
        if (backendNotes.length > existing.length) {
          localStorage.setItem('yatri_user_prefs', backendNotes);
          setUserPrefsText(backendNotes);
        }
      }
    } catch (error: any) {
      console.error("Chat API Error:", error);
      const errorMsg = error?.response?.data?.message || '';
      const isTimeout = error?.code === 'ECONNABORTED' || errorMsg.includes('timeout');
      const isServerError = error?.response?.status >= 500;
      
      let userMessage = '😔 I couldn\'t process that right now. ';
      if (isTimeout) {
        userMessage += 'The request took too long — our servers might be busy. Please try again in a moment.';
      } else if (isServerError) {
        userMessage += 'Our AI services are temporarily experiencing high load. Your data is safe — just tap send again!';
      } else {
        userMessage += 'Please check your connection and try again. If this keeps happening, try refreshing the page.';
      }
      
      setMessages(prev => [...prev, {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: userMessage,
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
                  { id: 'psychology', icon: Sparkles, label: 'Psychology', desc: 'Mood & Motivations', color: '#db2777', bg: '#fce7f3' },
                ].map((stage, i) => {
                  const status = agentStatuses[stage.id];
                  const agentState = status?.status || 'idle';
                  const confidence = status?.confidence || 0;
                  return (
                    <button 
                      key={i} 
                      onClick={() => {
                        sendMessage(`Can you activate the ${stage.label} agent for me?`, undefined, stage.id);
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
              {historySessions.length > 0 ? (
                <div className="space-y-3">
                  {historySessions.map((session, i) => (
                    <button
                      key={i}
                      onClick={() => {
                        setSessionId(session.session_id);
                        loadSession(session.session_id);
                      }}
                      className="w-full text-left p-3 rounded-xl transition-all hover:scale-[1.02]"
                      style={{ backgroundColor: 'var(--bg-surface)', border: '1px solid var(--border-main)' }}
                    >
                      <p className="text-sm font-semibold" style={{ color: 'var(--text-primary)' }}>
                        {session.origin && session.destination ? `${session.origin} → ${session.destination}` : 'Trip Plan'}
                      </p>
                      <p className="text-xs mt-1" style={{ color: 'var(--text-muted)' }}>{session.preview}</p>
                    </button>
                  ))}
                </div>
              ) : (
                <div className="text-center py-8">
                  <History className="h-8 w-8 mx-auto mb-3" style={{ color: 'var(--text-faint)' }} />
                  <p className="text-sm" style={{ color: 'var(--text-muted)' }}>
                    Your past trip plans will appear here
                  </p>
                  <p className="text-xs mt-2" style={{ color: 'var(--text-faint)' }}>
                    Start planning to build your travel history
                  </p>
                </div>
              )}
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

              {/* Wanderlust Motivator */}
              <p className="clay-label mb-4">Wanderlust Motivator</p>
              <div className="space-y-3 mb-6">
                <div className="flex items-center justify-between p-3 rounded-xl" style={{ backgroundColor: 'var(--bg-surface)', border: '1px solid var(--border-main)' }}>
                  <div className="flex items-center gap-2">
                    <Heart className="h-4 w-4" style={{ color: wanderlustEnabled ? '#ef4444' : 'var(--text-muted)' }} />
                    <span className="text-sm font-semibold" style={{ color: 'var(--text-primary)' }}>Travel Motivator</span>
                  </div>
                  <button
                    onClick={() => setWanderlustEnabled(!wanderlustEnabled)}
                    className="w-11 h-6 rounded-full transition-all relative"
                    style={{ backgroundColor: wanderlustEnabled ? 'var(--accent-primary)' : 'var(--border-main)' }}
                  >
                    <span className="absolute top-0.5 w-5 h-5 rounded-full bg-white shadow transition-all" style={{ left: wanderlustEnabled ? '22px' : '2px' }} />
                  </button>
                </div>
                {wanderlustEnabled && (
                  <div className="p-3 rounded-xl" style={{ backgroundColor: 'var(--bg-surface)', border: '1px solid var(--border-main)' }}>
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-xs" style={{ color: 'var(--text-muted)' }}>Intensity</span>
                      <span className="text-xs font-bold" style={{ color: 'var(--accent-dark)' }}>{wanderlustIntensity}%</span>
                    </div>
                    <input
                      type="range" min="0" max="100" value={wanderlustIntensity}
                      onChange={(e) => setWanderlustIntensity(parseInt(e.target.value))}
                      className="w-full accent-emerald-500 h-1.5"
                    />
                    <div className="flex justify-between mt-1">
                      <span className="text-[10px]" style={{ color: 'var(--text-faint)' }}>Gentle 💚</span>
                      <span className="text-[10px]" style={{ color: 'var(--text-faint)' }}>Strong 🔥</span>
                    </div>
                  </div>
                )}
              </div>

              {/* Psychology Subagent Toggle */}
              <p className="clay-label mb-4">Psychology Profiling</p>
              <div className="space-y-3 mb-6">
                <div className="flex items-center justify-between p-3 rounded-xl" style={{ backgroundColor: 'var(--bg-surface)', border: '1px solid var(--border-main)' }}>
                  <div className="flex items-center gap-2">
                    <Sparkles className="h-4 w-4" style={{ color: psychologyEnabled ? '#db2777' : 'var(--text-muted)' }} />
                    <span className="text-sm font-semibold" style={{ color: 'var(--text-primary)' }}>Continuous Psychology</span>
                  </div>
                  <button
                    onClick={() => setPsychologyEnabled(!psychologyEnabled)}
                    className="w-11 h-6 rounded-full transition-all relative"
                    style={{ backgroundColor: psychologyEnabled ? '#db2777' : 'var(--border-main)' }}
                  >
                    <span className="absolute top-0.5 w-5 h-5 rounded-full bg-white shadow transition-all" style={{ left: psychologyEnabled ? '22px' : '2px' }} />
                  </button>
                </div>
              </div>

              {/* Personal Preferences — clickable to open modal */}
              <p className="clay-label mb-4">Personal Preferences</p>
              <div className="space-y-3">
                <p className="text-xs" style={{ color: 'var(--text-muted)' }}>
                  Auto-collected from your chats + your custom notes. Click to edit.
                </p>
                <button
                  onClick={() => setShowPrefsModal(true)}
                  className="w-full p-3 rounded-xl text-left text-sm transition-all hover:scale-[1.01]"
                  style={{ backgroundColor: 'var(--bg-surface)', border: '1px solid var(--border-main)', color: 'var(--text-primary)', minHeight: '80px' }}
                >
                  {userPrefsText ? (
                    <span className="line-clamp-4">{userPrefsText}</span>
                  ) : (
                    <span style={{ color: 'var(--text-faint)' }}>Tap to add your preferences...</span>
                  )}
                  <div className="flex items-center gap-1 mt-2">
                    <Edit3 className="h-3 w-3" style={{ color: 'var(--accent-primary)' }} />
                    <span className="text-[10px] font-semibold" style={{ color: 'var(--accent-primary)' }}>Click to edit</span>
                  </div>
                </button>
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
                    {msg.content.split(/(\*\*[^*]+\*\*|\*[^*]+\*|\n)/).map((part: string, i: number) => {
                      if (part.startsWith('**') && part.endsWith('**')) {
                        return <strong key={i}>{part.slice(2, -2)}</strong>;
                      }
                      if (part.startsWith('*') && part.endsWith('*') && !part.startsWith('**')) {
                        return <em key={i} style={{ color: 'var(--text-muted)' }}>{part.slice(1, -1)}</em>;
                      }
                      if (part === '\n') return <br key={i} />;
                      return part;
                    })}
                  </p>
                  
                  {/* Plan Card — Comprehensive */}
                  {msg.type === 'plan' && msg.data && (
                    <div className="mt-4 p-4 rounded-xl" style={{ background: 'var(--accent-light)', border: '1px solid var(--border-main)' }}>
                      <div className="flex items-center justify-between mb-3">
                        <p className="text-xs font-semibold" style={{ color: 'var(--accent-dark)' }}>📋 YOUR TRAVEL PLAN</p>
                        <span className="text-[10px] px-2 py-0.5 rounded-full" style={{ background: 'var(--accent-primary)', color: 'white' }}>Editable</span>
                      </div>
                      {msg.data.title && (
                        <p className="text-sm font-bold mb-2" style={{ color: 'var(--text-primary)' }}>{msg.data.title}</p>
                      )}

                      {/* Budget & Cost Bar */}
                      <div className="flex items-center gap-3 mb-3 flex-wrap">
                        {msg.data.estimated_cost && (
                          <span className="text-xs px-2 py-1 rounded-full" style={{ background: '#d1fae5', color: '#065f46' }}>
                            💰 ₹{msg.data.estimated_cost.toLocaleString()}
                          </span>
                        )}
                        {msg.data.total_days && (
                          <span className="text-xs px-2 py-1 rounded-full" style={{ background: '#dbeafe', color: '#1e40af' }}>
                            📅 {msg.data.total_days} days
                          </span>
                        )}
                        {msg.data.budget && msg.data.estimated_cost && (
                          <span className="text-xs px-2 py-1 rounded-full" style={{
                            background: msg.data.estimated_cost <= msg.data.budget ? '#d1fae5' : '#fee2e2',
                            color: msg.data.estimated_cost <= msg.data.budget ? '#065f46' : '#991b1b'
                          }}>
                            {msg.data.estimated_cost <= msg.data.budget 
                              ? `✅ Under budget by ₹${(msg.data.budget - msg.data.estimated_cost).toLocaleString()}`
                              : `⚠️ Over budget by ₹${(msg.data.estimated_cost - msg.data.budget).toLocaleString()}`
                            }
                          </span>
                        )}
                      </div>

                      {/* Route Chain */}
                      {msg.data.route_chain && msg.data.route_chain.length > 1 && (
                        <div className="mb-4 p-3 rounded-lg" style={{ background: 'var(--bg-surface)', border: '1px solid var(--border-main)' }}>
                          <p className="text-[10px] font-bold mb-2" style={{ color: 'var(--accent-dark)' }}>🗺️ ROUTE</p>
                          <div className="flex items-center gap-1 flex-wrap">
                            {msg.data.route_chain.map((city: string, ci: number) => (
                              <span key={ci} className="flex items-center gap-1">
                                <span className="text-xs font-semibold px-2 py-0.5 rounded-full" style={{ background: 'var(--accent-primary)', color: 'white' }}>{city}</span>
                                {ci < msg.data.route_chain.length - 1 && <span className="text-xs" style={{ color: 'var(--text-muted)' }}>→</span>}
                              </span>
                            ))}
                          </div>
                        </div>
                      )}

                      {/* Confidence Score */}
                      {msg.data.confidence_score && (
                        <div className="mb-4 p-3 rounded-lg" style={{ backgroundColor: 'var(--bg-surface)', border: '1px solid var(--border-main)' }}>
                          <div className="flex items-center justify-between mb-1">
                            <span className="text-xs font-bold" style={{ color: 'var(--text-primary)' }}>Personalization Confidence</span>
                            <span className="text-xs font-bold" style={{ color: msg.data.confidence_score >= 80 ? '#10b981' : '#f59e0b' }}>
                              {msg.data.confidence_score}%
                            </span>
                          </div>
                          <div className="w-full bg-gray-200 rounded-full h-1.5">
                            <div className="h-1.5 rounded-full transition-all" style={{ width: `${msg.data.confidence_score}%`, backgroundColor: msg.data.confidence_score >= 80 ? '#10b981' : '#f59e0b' }}></div>
                          </div>
                        </div>
                      )}

                      {/* Agent Contributions */}
                      {msg.data.agent_contributions && (
                        <div className="mb-4 grid grid-cols-2 gap-2">
                          {Object.entries(msg.data.agent_contributions).map(([agent, contribution]: [string, any], i: number) => (
                            <div key={i} className="p-2 rounded-lg text-[10px]" style={{ background: 'var(--bg-surface)', border: '1px solid var(--border-main)' }}>
                              <span className="font-bold" style={{ color: 'var(--accent-dark)' }}>{agent.charAt(0).toUpperCase() + agent.slice(1)}:</span>{' '}
                              <span style={{ color: 'var(--text-secondary)' }}>{String(contribution)}</span>
                            </div>
                          ))}
                        </div>
                      )}

                      {/* Day-by-Day Itinerary */}
                      {msg.data.days && msg.data.days.map((day: any, di: number) => {
                        const typeIcons: Record<string, string> = { food: '🍽️', place: '📍', hotel: '🏨', transport: '🚃', activity: '🎯' };
                        const typeColors: Record<string, string> = { food: '#fef3c7', place: '#dbeafe', hotel: '#ede9fe', transport: '#cffafe', activity: '#d1fae5' };
                        return (
                        <div key={di} className="mb-3 p-3 rounded-lg" style={{ background: 'var(--bg-surface)', border: '1px solid var(--border-main)' }}>
                          <div className="flex items-center justify-between mb-2">
                            <div>
                              <p className="text-xs font-bold" style={{ color: 'var(--accent-dark)' }}>Day {day.day}{day.city ? ` — ${day.city}` : ''}</p>
                              {day.theme && <p className="text-[10px]" style={{ color: 'var(--text-muted)' }}>{day.theme}</p>}
                            </div>
                            <div className="flex items-center gap-2">
                              {day.remaining_budget != null && (
                                <span className="text-[10px] px-1.5 py-0.5 rounded" style={{ background: '#d1fae5', color: '#065f46' }}>
                                  ₹{day.remaining_budget.toLocaleString()} left
                                </span>
                              )}
                              <Edit3 className="h-3 w-3" style={{ color: 'var(--text-muted)' }} />
                            </div>
                          </div>
                          {day.activities && day.activities.map((act: any, ai: number) => {
                            const actKey = `${di}-${ai}`;
                            const isExpanded = expandedActivity === actKey;
                            return (
                            <div key={ai} className="mb-2">
                              <div className="flex items-start gap-2">
                                <span className="text-[10px] flex-shrink-0 font-mono" style={{ color: 'var(--accent-primary)', minWidth: '55px' }}>{act.time}</span>
                                <div className="flex-1">
                                  <div className="flex items-center gap-1">
                                    <span className="text-[10px] px-1 rounded" style={{ background: typeColors[act.type] || '#f3f4f6' }}>
                                      {typeIcons[act.type] || '•'} {act.type}
                                    </span>
                                    <span className="text-xs font-medium" style={{ color: 'var(--text-primary)' }}>{act.name || act.description}</span>
                                    {act.cost > 0 && <span className="text-[10px] font-mono" style={{ color: 'var(--accent-dark)' }}>₹{act.cost}</span>}
                                  </div>
                                  {act.details && <p className="text-[10px] mt-0.5" style={{ color: 'var(--text-muted)' }}>{act.details}</p>}
                                  {act.why_chosen && <p className="text-[10px] italic mt-0.5" style={{ color: '#10b981' }}>✨ {act.why_chosen}</p>}
                                  
                                  {/* More Button for Alternatives */}
                                  {act.alternatives && act.alternatives.length > 0 && (
                                    <button 
                                      onClick={() => setExpandedActivity(isExpanded ? null : actKey)}
                                      className="mt-1 text-[10px] font-semibold px-2 py-0.5 rounded-full transition-all hover:scale-105"
                                      style={{ background: 'var(--accent-primary)', color: 'white' }}
                                    >
                                      {isExpanded ? '▲ Less' : `▼ More (${act.alternatives.length} options)`}
                                    </button>
                                  )}
                                  
                                  {/* Expanded Alternatives Panel */}
                                  {isExpanded && act.alternatives && (
                                    <div className="mt-2 space-y-1.5 p-2 rounded-lg animate-fade-in" style={{ background: '#fefce8', border: '1px solid #fde68a' }}>
                                      <p className="text-[10px] font-bold" style={{ color: '#92400e' }}>🔄 Alternative Options:</p>
                                      {act.alternatives.map((alt: any, altI: number) => (
                                        <div key={altI} className="p-2 rounded-lg" style={{ background: 'white', border: '1px solid #e5e7eb' }}>
                                          <div className="flex items-center justify-between">
                                            <span className="text-xs font-semibold" style={{ color: 'var(--text-primary)' }}>{alt.name}</span>
                                            <span className="text-xs font-mono" style={{ color: alt.cost > act.cost ? '#dc2626' : '#16a34a' }}>₹{alt.cost}</span>
                                          </div>
                                          <div className="flex items-center gap-1 mt-0.5">
                                            {Array.from({length: 5}).map((_, si) => (
                                              <span key={si} className="text-[8px]">{si < (alt.rating || 0) ? '⭐' : '☆'}</span>
                                            ))}
                                          </div>
                                          {alt.pros && <p className="text-[10px] mt-0.5" style={{ color: '#16a34a' }}>✅ {alt.pros}</p>}
                                          {alt.cons && <p className="text-[10px]" style={{ color: '#dc2626' }}>❌ {alt.cons}</p>}
                                        </div>
                                      ))}
                                    </div>
                                  )}
                                </div>
                              </div>
                            </div>
                            );
                          })}
                        </div>
                        );
                      })}

                      {/* Budget Summary */}
                      {msg.data.summary && (
                        <div className="mt-4 p-3 rounded-lg" style={{ background: '#f0fdf4', border: '1px solid #86efac' }}>
                          <p className="text-xs font-bold mb-2" style={{ color: '#065f46' }}>📊 TRIP SUMMARY</p>
                          <div className="grid grid-cols-2 gap-2 text-[11px]">
                            {msg.data.summary.total_transport_cost != null && (
                              <div><span style={{ color: 'var(--text-muted)' }}>🚃 Transport:</span> <strong>₹{msg.data.summary.total_transport_cost.toLocaleString()}</strong></div>
                            )}
                            {msg.data.summary.total_food_cost != null && (
                              <div><span style={{ color: 'var(--text-muted)' }}>🍽️ Food:</span> <strong>₹{msg.data.summary.total_food_cost.toLocaleString()}</strong></div>
                            )}
                            {msg.data.summary.total_hotel_cost != null && (
                              <div><span style={{ color: 'var(--text-muted)' }}>🏨 Hotels:</span> <strong>₹{msg.data.summary.total_hotel_cost.toLocaleString()}</strong></div>
                            )}
                            {msg.data.summary.total_activities_cost != null && (
                              <div><span style={{ color: 'var(--text-muted)' }}>🎯 Activities:</span> <strong>₹{msg.data.summary.total_activities_cost.toLocaleString()}</strong></div>
                            )}
                            {msg.data.summary.total_cost != null && (
                              <div className="col-span-2 pt-2 mt-1" style={{ borderTop: '1px dashed var(--border-main)' }}>
                                <span className="font-bold" style={{ color: 'var(--accent-dark)' }}>💰 Total: ₹{msg.data.summary.total_cost.toLocaleString()}</span>
                              </div>
                            )}
                            {msg.data.summary.total_travel_time_hrs != null && (
                              <div><span style={{ color: 'var(--text-muted)' }}>⏱️ Travel Time:</span> <strong>{msg.data.summary.total_travel_time_hrs}h</strong></div>
                            )}
                            {msg.data.summary.total_stops != null && (
                              <div><span style={{ color: 'var(--text-muted)' }}>📍 Stops:</span> <strong>{msg.data.summary.total_stops}</strong></div>
                            )}
                          </div>
                          {msg.data.summary.budget_status && (
                            <p className="mt-2 text-xs font-semibold" style={{ color: msg.data.summary.budget_status.includes('Under') ? '#16a34a' : '#dc2626' }}>
                              {msg.data.summary.budget_status}
                            </p>
                          )}
                          {msg.data.summary.key_highlights && (
                            <div className="mt-2">
                              {msg.data.summary.key_highlights.map((h: string, hi: number) => (
                                <p key={hi} className="text-[10px]" style={{ color: 'var(--text-secondary)' }}>🌟 {h}</p>
                              ))}
                            </div>
                          )}
                        </div>
                      )}

                      {/* Tips */}
                      {msg.data.tips && (
                        <div className="mt-3">
                          <p className="text-xs font-semibold mb-1" style={{ color: 'var(--accent-dark)' }}>💡 Tips:</p>
                          {msg.data.tips.map((tip: string, ti: number) => (
                            <p key={ti} className="text-xs" style={{ color: 'var(--text-secondary)' }}>• {tip}</p>
                          ))}
                        </div>
                      )}
                      {msg.data.personalization_notes && (
                        <p className="mt-2 text-[10px] italic" style={{ color: 'var(--text-muted)' }}>
                          ✨ {msg.data.personalization_notes}
                        </p>
                      )}
                    </div>
                  )}

                  {/* Transport Route Cards */}
                  {msg.type === 'text' && msg.role === 'assistant' && agentStatuses?.transport?.status === 'done' && (
                    <>
                      {/* This will render when transport data is available through plan rendering */}
                    </>
                  )}

                  {/* Hotel Cards */}
                  {msg.type === 'hotel' && msg.data?.hotels && (
                    <div className="mt-4 space-y-2">
                      {msg.data.hotels.map((h: any, i: number) => (
                        <div key={i} className="p-3 rounded-xl" style={{ background: '#ede9fe', border: '1px solid #ddd6fe' }}>
                          <p className="text-sm font-semibold" style={{ color: 'var(--text-primary)' }}>{h.name}</p>
                          <p className="text-xs" style={{ color: 'var(--text-secondary)' }}>⭐ {h.rating} star • ₹{h.price_per_night}/night</p>
                          {h.note && h.note.includes('not configured') && (
                            <p className="text-[10px] mt-1 italic" style={{ color: '#f59e0b' }}>ℹ️ Live pricing temporarily unavailable</p>
                          )}
                        </div>
                      ))}
                    </div>
                  )}

                  {/* Cab Comparison Cards */}
                  {msg.type === 'cab' && msg.data?.options && (
                    <div className="mt-4 space-y-2">
                      {msg.data.options.map((c: any, i: number) => (
                        <div key={i} className="p-3 rounded-xl" style={{ background: '#cffafe', border: '1px solid #a5f3fc' }}>
                          <p className="text-sm font-semibold" style={{ color: 'var(--text-primary)' }}>{c.provider}</p>
                          <p className="text-xs" style={{ color: 'var(--text-secondary)' }}>
                            🚕 {c.vehicle_type} • ETA {c.eta} • {c.price === 'N/A' ? 'Pricing unavailable' : `₹${c.price}`}
                          </p>
                          {c.note && c.note.includes('not configured') && (
                            <p className="text-[10px] mt-1 italic" style={{ color: '#f59e0b' }}>ℹ️ Live pricing temporarily unavailable</p>
                          )}
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
                        { id: 'psychology', num: 7, label: 'Psychology profiling', icon: '🧠' },
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
              : 'Seven AI agents ready • Transport • Cabs • Hotels • Food • Places • Maps • Psychology'
            }
          </p>
        </div>
      </div>

      {/* Preferences Modal */}
      {showPrefsModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center" style={{ backgroundColor: 'rgba(0,0,0,0.5)' }}>
          <div className="w-full max-w-lg mx-4 rounded-2xl shadow-2xl overflow-hidden animate-fade-in" style={{ backgroundColor: 'var(--bg-primary)', border: '1px solid var(--border-main)' }}>
            <div className="flex items-center justify-between p-5" style={{ borderBottom: '1px solid var(--border-main)' }}>
              <div>
                <h3 className="font-semibold" style={{ color: 'var(--text-primary)', letterSpacing: '-0.3px' }}>Personal Preferences</h3>
                <p className="text-xs mt-1" style={{ color: 'var(--text-muted)' }}>Auto-collected + your custom notes. All agents use this.</p>
              </div>
              <button onClick={() => setShowPrefsModal(false)} className="p-1.5 rounded-lg hover:bg-gray-100 transition-all">
                <X className="h-5 w-5" style={{ color: 'var(--text-muted)' }} />
              </button>
            </div>
            <div className="p-5 space-y-4">
              <div>
                <label className="text-xs font-semibold mb-2 block" style={{ color: 'var(--text-secondary)', letterSpacing: '0.5px' }}>YOUR PREFERENCES</label>
                <textarea
                  className="w-full p-4 rounded-xl text-sm focus:outline-none transition-all"
                  style={{ backgroundColor: 'var(--bg-surface)', border: '1px solid var(--border-main)', color: 'var(--text-primary)', minHeight: '200px', resize: 'vertical', lineHeight: '1.6' }}
                  placeholder={"Write your preferences here. Examples:\n• I am strictly vegetarian\n• I prefer 3-star hotels\n• No travel before 9 AM\n• I love heritage forts and local street food\n• Budget-conscious traveler\n• I live in Kanpur"}
                  value={userPrefsText}
                  onChange={(e) => setUserPrefsText(e.target.value)}
                />
              </div>
              <div className="flex items-center gap-2 text-xs p-3 rounded-lg" style={{ backgroundColor: 'var(--accent-light)', color: 'var(--accent-dark)' }}>
                <Sparkles className="h-3.5 w-3.5 flex-shrink-0" />
                <span>Yatri AI auto-discovers preferences from your chats (name, city, diet, interests) and adds them here.</span>
              </div>
            </div>
            <div className="flex gap-3 p-5" style={{ borderTop: '1px solid var(--border-main)' }}>
              <button
                onClick={() => setShowPrefsModal(false)}
                className="flex-1 py-2.5 rounded-xl text-sm font-semibold transition-all"
                style={{ border: '1px solid var(--border-main)', color: 'var(--text-secondary)' }}
              >Cancel</button>
              <button
                onClick={() => {
                  localStorage.setItem('yatri_user_prefs', userPrefsText);
                  setShowPrefsModal(false);
                }}
                className="flex-1 py-2.5 rounded-xl text-sm font-semibold text-white transition-all hover:opacity-90"
                style={{ backgroundColor: 'var(--accent-primary)' }}
              >Save Preferences</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
