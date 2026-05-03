"use client";

import { useState } from 'react';
import Link from 'next/link';
import { ArrowLeft, KeyRound, Mail, ArrowRight } from 'lucide-react';

export default function Login() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');

  const handleLogin = (e: React.FormEvent) => {
    e.preventDefault();
    window.location.href = '/chat';
  };

  return (
    <div className="min-h-screen flex flex-col" style={{ backgroundColor: 'var(--color-pure-white)' }}>
      {/* Nav */}
      <nav className="clay-nav flex items-center justify-between container-wide">
        <Link href="/" className="flex items-center gap-2" style={{ color: 'var(--color-neutral-600)' }}>
          <ArrowLeft className="h-5 w-5" />
          <span className="text-sm font-medium">Back</span>
        </Link>
        <div className="flex items-center gap-3">
          <span className="green-dot" />
          <span className="font-semibold text-sm" style={{ letterSpacing: '-0.3px', color: 'var(--color-clay-black)' }}>Yatri AI</span>
        </div>
      </nav>

      {/* Login Card */}
      <div className="flex-1 flex items-center justify-center px-4 pb-12">
        <div className="w-full max-w-md">
          <div className="clay-card p-10">
            <div className="text-center mb-8">
              <span className="clay-badge mb-4 inline-block">WELCOME BACK</span>
              <h1 className="text-3xl font-semibold mb-2" style={{ letterSpacing: '-0.8px', color: 'var(--color-clay-black)' }}>
                Sign In
              </h1>
              <p className="text-sm" style={{ color: 'var(--color-neutral-400)' }}>Continue planning your next adventure</p>
            </div>

            <form onSubmit={handleLogin} className="space-y-5">
              <div>
                <label className="clay-label mb-2 block">Email</label>
                <div className="relative">
                  <Mail className="absolute left-4 top-3.5 h-5 w-5" style={{ color: 'var(--color-neutral-300)' }} />
                  <input 
                    type="email" 
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    placeholder="you@example.com"
                    required
                    className="clay-input pl-12"
                  />
                </div>
              </div>
              <div>
                <label className="clay-label mb-2 block">Password</label>
                <div className="relative">
                  <KeyRound className="absolute left-4 top-3.5 h-5 w-5" style={{ color: 'var(--color-neutral-300)' }} />
                  <input 
                    type="password" 
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    placeholder="••••••••"
                    required
                    className="clay-input pl-12"
                  />
                </div>
              </div>
              
              <button type="submit" className="clay-button w-full" style={{ borderRadius: '10px', padding: '14px' }}>
                Sign In <ArrowRight className="h-4 w-4" />
              </button>
            </form>

            <div className="text-center mt-6" style={{ borderTop: '1px solid var(--color-oat-border)', paddingTop: '20px' }}>
              <p className="text-sm" style={{ color: 'var(--color-neutral-400)' }}>
                Don&apos;t have an account?{' '}
                <Link href="/register" className="font-medium" style={{ color: 'var(--color-emerald-600)' }}>
                  Create one
                </Link>
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
