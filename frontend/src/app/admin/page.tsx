"use client";

import { useState, useEffect, useCallback } from 'react';
import { Shield, Activity, AlertTriangle, RefreshCw, Terminal, BarChart3, ArrowLeft, Lock, Eye, EyeOff } from 'lucide-react';
import Link from 'next/link';

const ADMIN_PASSWORD = "yatri2026admin";
const SPACE_ID = "Ashutosh1975271/YatriAi";

interface LogEntry {
  timestamp: string;
  level: 'info' | 'warning' | 'error';
  message: string;
}

export default function AdminDashboard() {
  const [authenticated, setAuthenticated] = useState(false);
  const [password, setPassword] = useState('');
  const [hfToken, setHfToken] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [buildLogs, setBuildLogs] = useState<LogEntry[]>([]);
  const [runLogs, setRunLogs] = useState<LogEntry[]>([]);
  const [activeTab, setActiveTab] = useState<'overview' | 'build' | 'run'>('overview');
  const [loading, setLoading] = useState(false);
  const [stats] = useState({
    totalSessions: 142,
    activePlans: 38,
    avgResponseTime: '1.8s',
    uptime: '99.2%',
    agentsActive: 6,
    errorRate: '0.3%',
  });

  const handleLogin = (e: React.FormEvent) => {
    e.preventDefault();
    if (password === ADMIN_PASSWORD && hfToken.startsWith('hf_')) {
      setAuthenticated(true);
    } else {
      alert('Incorrect password or invalid HF token');
    }
  };

  const fetchLogs = useCallback(async (type: 'build' | 'run') => {
    setLoading(true);
    try {
      const res = await fetch(`https://huggingface.co/api/spaces/${SPACE_ID}/logs/${type}`, {
        headers: { 'Authorization': `Bearer ${hfToken}` },
      });
      const text = await res.text();
      const lines = text.split('\n').filter(l => l.trim()).slice(-100);
      const parsed: LogEntry[] = lines.map(line => {
        let clean = line;
        if (line.startsWith('data:')) clean = line.slice(5).trim();
        try {
          const obj = JSON.parse(clean);
          return {
            timestamp: obj.timestamp || new Date().toISOString(),
            level: obj.data?.includes('ERROR') || obj.data?.includes('error') ? 'error' :
                   obj.data?.includes('WARNING') || obj.data?.includes('warn') ? 'warning' : 'info',
            message: obj.data || clean,
          };
        } catch {
          return {
            timestamp: new Date().toISOString(),
            level: clean.toLowerCase().includes('error') ? 'error' as const :
                   clean.toLowerCase().includes('warn') ? 'warning' as const : 'info' as const,
            message: clean,
          };
        }
      });
      if (type === 'build') setBuildLogs(parsed);
      else setRunLogs(parsed);
    } catch (err) {
      const errorLog: LogEntry = { timestamp: new Date().toISOString(), level: 'error', message: `Failed to fetch ${type} logs: ${err}` };
      if (type === 'build') setBuildLogs([errorLog]);
      else setRunLogs([errorLog]);
    }
    setLoading(false);
  }, [hfToken]);

  useEffect(() => {
    if (authenticated) {
      fetchLogs('build');
      fetchLogs('run');
    }
  }, [authenticated, fetchLogs]);

  if (!authenticated) {
    return (
      <div className="min-h-screen flex items-center justify-center" style={{ backgroundColor: 'var(--bg-primary)' }}>
        <div className="w-full max-w-sm">
          <div className="settings-panel text-center">
            <Shield className="h-10 w-10 mx-auto mb-4" style={{ color: 'var(--accent-primary)' }} />
            <h1 className="text-xl font-semibold mb-1" style={{ color: 'var(--text-primary)' }}>Admin Access</h1>
            <p className="text-sm mb-6" style={{ color: 'var(--text-muted)' }}>Enter password to view dashboard</p>
            <form onSubmit={handleLogin} className="space-y-4">
              <div className="relative">
                <Lock className="absolute left-4 top-3.5 h-4 w-4" style={{ color: 'var(--text-faint)' }} />
                <input
                  type={showPassword ? 'text' : 'password'}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="Password"
                  className="clay-input pl-11 pr-11"
                  autoFocus
                />
                <button type="button" onClick={() => setShowPassword(!showPassword)} className="absolute right-4 top-3.5" style={{ color: 'var(--text-faint)' }}>
                  {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                </button>
              </div>
              <div className="relative">
                <Terminal className="absolute left-4 top-3.5 h-4 w-4" style={{ color: 'var(--text-faint)' }} />
                <input
                  type="password"
                  value={hfToken}
                  onChange={(e) => setHfToken(e.target.value)}
                  placeholder="HF Access Token (hf_...)"
                  className="clay-input pl-11"
                />
              </div>
              <button type="submit" className="clay-button w-full" style={{ borderRadius: '10px' }}>
                Sign In
              </button>
            </form>
          </div>
        </div>
      </div>
    );
  }

  const statCards = [
    { label: 'Total Sessions', value: stats.totalSessions, icon: BarChart3, color: 'var(--accent-primary)' },
    { label: 'Active Plans', value: stats.activePlans, icon: Activity, color: '#6d28d9' },
    { label: 'Avg Response', value: stats.avgResponseTime, icon: RefreshCw, color: '#0e7490' },
    { label: 'Uptime', value: stats.uptime, icon: Shield, color: 'var(--accent-primary)' },
    { label: 'Active Agents', value: stats.agentsActive, icon: Terminal, color: '#b45309' },
    { label: 'Error Rate', value: stats.errorRate, icon: AlertTriangle, color: '#be123c' },
  ];

  const LogViewer = ({ logs }: { logs: LogEntry[] }) => (
    <div className="rounded-xl overflow-hidden" style={{ backgroundColor: 'var(--bg-sidebar)', border: '1px solid var(--border-main)' }}>
      <div className="max-h-96 overflow-y-auto p-4 font-mono text-xs space-y-1">
        {logs.length === 0 ? (
          <p style={{ color: 'var(--text-muted)' }}>No logs available. Click refresh to fetch.</p>
        ) : (
          logs.map((log, i) => (
            <div key={i} className={`log-line ${log.level === 'error' ? 'log-line-error' : log.level === 'warning' ? 'log-line-warning' : 'log-line-info'}`}>
              <span style={{ color: 'var(--text-faint)' }}>{new Date(log.timestamp).toLocaleTimeString()} </span>
              {log.message}
            </div>
          ))
        )}
      </div>
    </div>
  );

  return (
    <div className="min-h-screen" style={{ backgroundColor: 'var(--bg-primary)' }}>
      {/* Nav */}
      <nav className="clay-nav flex items-center justify-between container-wide">
        <div className="flex items-center gap-3">
          <Link href="/" style={{ color: 'var(--text-muted)' }}><ArrowLeft className="h-5 w-5" /></Link>
          <span className="green-dot-lg" />
          <span className="font-semibold" style={{ color: 'var(--text-primary)' }}>Admin Dashboard</span>
        </div>
        <div className="flex items-center gap-3">
          {['overview', 'build', 'run'].map(tab => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab as any)}
              className="px-4 py-2 rounded-lg text-sm font-medium transition-all"
              style={{
                backgroundColor: activeTab === tab ? 'var(--accent-light)' : 'transparent',
                color: activeTab === tab ? 'var(--accent-dark)' : 'var(--text-muted)',
              }}
            >
              {tab.charAt(0).toUpperCase() + tab.slice(1)} {tab !== 'overview' ? 'Logs' : ''}
            </button>
          ))}
        </div>
      </nav>

      <div className="container-wide py-8">
        {activeTab === 'overview' && (
          <>
            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4 mb-8">
              {statCards.map((s, i) => (
                <div key={i} className="admin-card text-center">
                  <s.icon className="h-5 w-5 mx-auto mb-2" style={{ color: s.color }} />
                  <p className="text-2xl font-bold mb-1" style={{ color: 'var(--text-primary)' }}>{s.value}</p>
                  <p className="text-xs" style={{ color: 'var(--text-muted)' }}>{s.label}</p>
                </div>
              ))}
            </div>

            <div className="grid md:grid-cols-2 gap-6">
              <div>
                <div className="flex items-center justify-between mb-3">
                  <h3 className="font-semibold text-sm" style={{ color: 'var(--text-primary)' }}>Recent Build Logs</h3>
                  <button onClick={() => fetchLogs('build')} disabled={loading} className="text-xs flex items-center gap-1" style={{ color: 'var(--accent-primary)' }}>
                    <RefreshCw className={`h-3 w-3 ${loading ? 'animate-spin' : ''}`} /> Refresh
                  </button>
                </div>
                <LogViewer logs={buildLogs.slice(-20)} />
              </div>
              <div>
                <div className="flex items-center justify-between mb-3">
                  <h3 className="font-semibold text-sm" style={{ color: 'var(--text-primary)' }}>Recent Run Logs</h3>
                  <button onClick={() => fetchLogs('run')} disabled={loading} className="text-xs flex items-center gap-1" style={{ color: 'var(--accent-primary)' }}>
                    <RefreshCw className={`h-3 w-3 ${loading ? 'animate-spin' : ''}`} /> Refresh
                  </button>
                </div>
                <LogViewer logs={runLogs.slice(-20)} />
              </div>
            </div>
          </>
        )}

        {activeTab === 'build' && (
          <div>
            <div className="flex items-center justify-between mb-4">
              <h2 className="font-semibold" style={{ color: 'var(--text-primary)' }}>Build Logs — HF Spaces</h2>
              <button onClick={() => fetchLogs('build')} disabled={loading} className="clay-button-ghost text-sm" style={{ padding: '8px 16px' }}>
                <RefreshCw className={`h-4 w-4 ${loading ? 'animate-spin' : ''}`} /> Refresh
              </button>
            </div>
            <LogViewer logs={buildLogs} />
          </div>
        )}

        {activeTab === 'run' && (
          <div>
            <div className="flex items-center justify-between mb-4">
              <h2 className="font-semibold" style={{ color: 'var(--text-primary)' }}>Runtime Logs — HF Spaces</h2>
              <button onClick={() => fetchLogs('run')} disabled={loading} className="clay-button-ghost text-sm" style={{ padding: '8px 16px' }}>
                <RefreshCw className={`h-4 w-4 ${loading ? 'animate-spin' : ''}`} /> Refresh
              </button>
            </div>
            <LogViewer logs={runLogs} />
          </div>
        )}
      </div>
    </div>
  );
}
