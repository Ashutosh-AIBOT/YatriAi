"use client";

import { useState } from 'react';
import Link from 'next/link';
import { ArrowLeft, User, Mail, KeyRound } from 'lucide-react';

export default function Register() {
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');

  const handleRegister = (e: React.FormEvent) => {
    e.preventDefault();
    // Dummy register logic
    window.location.href = '/chat';
  };

  return (
    <div className="min-h-screen bg-slate-900 flex flex-col items-center justify-center p-4">
      <Link href="/" className="absolute top-8 left-8 text-slate-400 hover:text-white transition flex items-center">
        <ArrowLeft className="h-5 w-5 mr-2" /> Back to Home
      </Link>
      
      <div className="w-full max-w-md glass-panel p-8 rounded-2xl">
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold gradient-text mb-2">Create Account</h1>
          <p className="text-slate-400 text-sm">Start your AI travel journey</p>
        </div>

        <form onSubmit={handleRegister} className="space-y-6">
          <div className="space-y-4">
            <div className="relative">
              <User className="absolute left-4 top-3.5 h-5 w-5 text-slate-400" />
              <input 
                type="text" 
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="Full Name"
                required
                className="w-full glass-input rounded-xl py-3 pl-12 pr-4"
              />
            </div>
            <div className="relative">
              <Mail className="absolute left-4 top-3.5 h-5 w-5 text-slate-400" />
              <input 
                type="email" 
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="Email address"
                required
                className="w-full glass-input rounded-xl py-3 pl-12 pr-4"
              />
            </div>
            <div className="relative">
              <KeyRound className="absolute left-4 top-3.5 h-5 w-5 text-slate-400" />
              <input 
                type="password" 
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="Password"
                required
                className="w-full glass-input rounded-xl py-3 pl-12 pr-4"
              />
            </div>
          </div>
          
          <button type="submit" className="w-full py-3 bg-indigo-600 hover:bg-indigo-500 text-white rounded-xl font-medium transition-colors shadow-lg shadow-indigo-600/20">
            Sign Up
          </button>
        </form>

        <p className="text-center mt-6 text-sm text-slate-400">
          Already have an account?{' '}
          <Link href="/login" className="text-indigo-400 hover:text-indigo-300 font-medium">
            Sign In
          </Link>
        </p>
      </div>
    </div>
  );
}
