import Link from 'next/link';
import { ArrowRight, Globe2, Map, Zap } from 'lucide-react';

export default function Home() {
  return (
    <main className="flex min-h-screen flex-col items-center justify-center p-6 lg:p-24">
      <div className="z-10 max-w-5xl w-full items-center justify-between font-mono text-sm lg:flex">
        <p className="fixed left-0 top-0 flex w-full justify-center border-b border-gray-800 bg-gradient-to-b from-zinc-900 pb-6 pt-8 backdrop-blur-2xl lg:static lg:w-auto lg:rounded-xl lg:border lg:bg-gray-900/40 lg:p-4">
          <Globe2 className="mr-2 h-5 w-5 text-indigo-400" />
          <span className="font-bold tracking-wider">YATRA.AI</span>
        </p>
      </div>

      <div className="relative flex flex-col items-center place-items-center mt-20 md:mt-32">
        <h1 className="text-5xl md:text-7xl font-extrabold tracking-tight text-center mb-6">
          Travel Planning, <br />
          <span className="gradient-text">Reimagined with AI</span>
        </h1>
        <p className="text-lg md:text-xl text-slate-300 text-center max-w-2xl mb-12">
          Your personal autonomous agent that plans, books, and tracks your entire journey. From flights and hotels to local food and cabs.
        </p>
        
        <div className="flex flex-col sm:flex-row gap-4">
          <Link href="/login" className="flex items-center justify-center px-8 py-4 text-base font-medium text-white bg-indigo-600 rounded-full hover:bg-indigo-700 transition-all shadow-lg shadow-indigo-500/30">
            Get Started
            <ArrowRight className="ml-2 h-5 w-5" />
          </Link>
          <Link href="/chat" className="flex items-center justify-center px-8 py-4 text-base font-medium text-indigo-300 bg-slate-800/50 border border-slate-700 rounded-full hover:bg-slate-800 transition-all">
            Open App
          </Link>
        </div>
      </div>

      <div className="mt-32 grid text-center lg:max-w-5xl lg:w-full lg:mb-0 lg:grid-cols-3 gap-8">
        <div className="glass-panel p-8 rounded-2xl flex flex-col items-center">
          <Zap className="h-10 w-10 text-yellow-400 mb-4" />
          <h2 className="text-xl font-bold mb-2">Lightning Fast</h2>
          <p className="text-sm text-slate-400">Six specialized AI sub-agents run in parallel to curate the perfect itinerary in seconds.</p>
        </div>
        <div className="glass-panel p-8 rounded-2xl flex flex-col items-center">
          <Map className="h-10 w-10 text-green-400 mb-4" />
          <h2 className="text-xl font-bold mb-2">Smart Routing</h2>
          <p className="text-sm text-slate-400">Integrated directly with maps to provide logical, optimized travel routes for your trip.</p>
        </div>
        <div className="glass-panel p-8 rounded-2xl flex flex-col items-center">
          <Globe2 className="h-10 w-10 text-blue-400 mb-4" />
          <h2 className="text-xl font-bold mb-2">Scale to a Billion</h2>
          <p className="text-sm text-slate-400">Built on a robust microservices architecture ensuring high availability and real-time updates.</p>
        </div>
      </div>
    </main>
  );
}
