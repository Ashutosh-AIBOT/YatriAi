"use client";

import Link from 'next/link';
import { ArrowRight, Globe2, Map, Zap, Sparkles, Navigation, Car, Hotel, Utensils, MapPin, ChevronRight, Star, Shield, Clock, Users } from 'lucide-react';
import { motion } from 'framer-motion';

const fadeUp = {
  hidden: { opacity: 0, y: 24 },
  visible: (i: number = 0) => ({
    opacity: 1,
    y: 0,
    transition: { delay: i * 0.1, duration: 0.5, ease: [0.25, 0.46, 0.45, 0.94] as const },
  }),
};

const staggerContainer = {
  hidden: {},
  visible: { transition: { staggerChildren: 0.08 } },
};

export default function Home() {
  return (
    <main className="min-h-screen" style={{ backgroundColor: 'var(--bg-primary)' }}>
      {/* ═══════════════ NAV ═══════════════ */}
      <nav className="clay-nav flex items-center justify-between container-wide">
        <div className="flex items-center gap-3">
          <span className="green-dot-lg" />
          <span className="font-semibold text-lg" style={{ letterSpacing: '-0.5px', color: 'var(--text-primary)' }}>Yatri AI</span>
        </div>
        <div className="hidden md:flex items-center gap-8">
          <a href="#features" className="text-sm font-medium" style={{ color: 'var(--text-secondary)' }}>Features</a>
          <a href="#agents" className="text-sm font-medium" style={{ color: 'var(--text-secondary)' }}>Agents</a>
          <a href="#testimonials" className="text-sm font-medium" style={{ color: 'var(--text-secondary)' }}>Testimonials</a>
          <a href="#faq" className="text-sm font-medium" style={{ color: 'var(--text-secondary)' }}>FAQ</a>
        </div>
        <div className="flex items-center gap-3">
          <Link href="/login" className="text-sm font-medium" style={{ color: 'var(--text-secondary)', padding: '8px 16px' }}>
            Sign in
          </Link>
          <Link href="/register" className="clay-button" style={{ padding: '8px 20px', fontSize: '14px', borderRadius: '8px' }}>
            Get started <ArrowRight className="h-4 w-4" />
          </Link>
        </div>
      </nav>

      {/* ═══════════════ HERO ═══════════════ */}
      <section className="section-padding-lg">
        <motion.div
          className="container-narrow text-center"
          initial="hidden"
          animate="visible"
          variants={staggerContainer}
        >
          <motion.div variants={fadeUp} custom={0}>
            <span className="clay-badge mb-6 inline-flex items-center gap-2">
              <span className="green-dot" />
              AI-POWERED TRAVEL PLANNING
            </span>
          </motion.div>

          <motion.h1 variants={fadeUp} custom={1} className="heading-xl mb-6">
            Travel planning,<br />
            reimagined with AI.
          </motion.h1>

          <motion.p variants={fadeUp} custom={2} className="body-text mb-10 max-w-2xl mx-auto" style={{ fontSize: '18px' }}>
            Your personal autonomous agent that plans, books, and tracks your entire journey.
            From flights and hotels to local food and cabs — all in one chat.
          </motion.p>

          <motion.div variants={fadeUp} custom={3} className="flex flex-col sm:flex-row gap-4 justify-center">
            <Link href="/chat" className="clay-button" style={{ padding: '14px 32px', fontSize: '16px', borderRadius: '10px' }}>
              Start Planning <ArrowRight className="h-5 w-5" />
            </Link>
            <Link href="/register" className="clay-button-ghost" style={{ padding: '14px 32px', fontSize: '16px', borderRadius: '10px' }}>
              Create Account
            </Link>
          </motion.div>
        </motion.div>
      </section>

      {/* ═══════════════ STATS BAR ═══════════════ */}
      <section style={{ borderTop: '1px solid var(--border-main)', borderBottom: '1px solid var(--border-main)' }}>
        <div className="container-wide py-10">
          <motion.div
            className="grid grid-cols-2 md:grid-cols-4 gap-8"
            initial="hidden"
            whileInView="visible"
            viewport={{ once: true, amount: 0.3 }}
            variants={staggerContainer}
          >
            {[
              { value: '6', label: 'AI Sub-Agents' },
              { value: '<2s', label: 'Response Time' },
              { value: '100+', label: 'Cities Covered' },
              { value: '24/7', label: 'Always Available' },
            ].map((stat, i) => (
              <motion.div key={i} variants={fadeUp} custom={i} className="text-center">
                <p className="text-3xl md:text-4xl font-semibold mb-1" style={{ letterSpacing: '-1.5px', color: 'var(--text-primary)' }}>{stat.value}</p>
                <p className="text-sm" style={{ color: 'var(--text-muted)' }}>{stat.label}</p>
              </motion.div>
            ))}
          </motion.div>
        </div>
      </section>

      {/* ═══════════════ FEATURES ═══════════════ */}
      <section id="features" className="section-padding-lg" style={{ backgroundColor: 'var(--bg-secondary)' }}>
        <div className="container-wide">
          <motion.div
            className="mb-16"
            initial="hidden"
            whileInView="visible"
            viewport={{ once: true, amount: 0.3 }}
            variants={staggerContainer}
          >
            <motion.span variants={fadeUp} custom={0} className="clay-badge mb-4 block">
              FEATURES
            </motion.span>
            <motion.h2 variants={fadeUp} custom={1} className="heading-lg mb-4">
              Built for travelers who<br />care about craft.
            </motion.h2>
            <motion.p variants={fadeUp} custom={2} className="body-text max-w-xl" style={{ fontSize: '17px' }}>
              Every feature designed to make your journey seamless — from planning to arrival.
            </motion.p>
          </motion.div>

          <motion.div
            className="grid md:grid-cols-3 gap-6"
            initial="hidden"
            whileInView="visible"
            viewport={{ once: true, amount: 0.2 }}
            variants={staggerContainer}
          >
            {[
              {
                icon: <Zap className="h-6 w-6" />,
                iconClass: 'feature-icon feature-icon-amber',
                title: 'Lightning Fast',
                desc: 'Six specialized AI sub-agents run in parallel to curate the perfect itinerary in seconds.',
              },
              {
                icon: <Map className="h-6 w-6" />,
                iconClass: 'feature-icon feature-icon-emerald',
                title: 'Smart Routing',
                desc: 'Integrated with Google Maps to provide logical, optimized travel routes for your trip.',
              },
              {
                icon: <Sparkles className="h-6 w-6" />,
                iconClass: 'feature-icon feature-icon-purple',
                title: 'Scale to a Billion',
                desc: 'Built on robust microservices with Kafka streaming, ensuring real-time updates at any scale.',
              },
              {
                icon: <Shield className="h-6 w-6" />,
                iconClass: 'feature-icon feature-icon-blue',
                title: 'Production-grade',
                desc: 'Enterprise-ready architecture with Java Gateway, Python Orchestrator, and Node.js notifications.',
              },
              {
                icon: <Clock className="h-6 w-6" />,
                iconClass: 'feature-icon feature-icon-rose',
                title: 'Real-time Updates',
                desc: 'Live price tracking, booking confirmations, and travel alerts pushed via WebSocket.',
              },
              {
                icon: <Users className="h-6 w-6" />,
                iconClass: 'feature-icon feature-icon-cyan',
                title: 'Built to Evolve',
                desc: 'Modular agent architecture makes it easy to add new capabilities and integrations.',
              },
            ].map((feature, i) => (
              <motion.div key={i} variants={fadeUp} custom={i} className="clay-card p-8">
                <div className={feature.iconClass + ' mb-5'}>
                  {feature.icon}
                </div>
                <h3 className="text-lg font-semibold mb-2" style={{ letterSpacing: '-0.3px', color: 'var(--text-primary)' }}>{feature.title}</h3>
                <p className="body-text-sm">{feature.desc}</p>
              </motion.div>
            ))}
          </motion.div>
        </div>
      </section>

      {/* ═══════════════ AGENTS SHOWCASE ═══════════════ */}
      <section id="agents" className="section-padding-lg">
        <div className="container-wide">
          <motion.div
            className="mb-16 text-center"
            initial="hidden"
            whileInView="visible"
            viewport={{ once: true, amount: 0.3 }}
            variants={staggerContainer}
          >
            <motion.span variants={fadeUp} custom={0} className="clay-badge mb-4 inline-block">
              IN PRODUCTION
            </motion.span>
            <motion.h2 variants={fadeUp} custom={1} className="heading-lg mb-4">
              One chat. Six agents.<br />Complete itinerary.
            </motion.h2>
            <motion.p variants={fadeUp} custom={2} className="body-text max-w-xl mx-auto" style={{ fontSize: '17px' }}>
              Just tell Yatri AI where you want to go. Our specialized agents work together to build your perfect trip.
            </motion.p>
          </motion.div>

          {/* Dashboard Preview */}
          <motion.div
            className="dashboard-preview max-w-4xl mx-auto"
            initial={{ opacity: 0, y: 30 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.6, ease: [0.25, 0.46, 0.45, 0.94] }}
          >
            <div className="dashboard-preview-header">
              <span className="preview-dot" />
              <span className="preview-dot" />
              <span className="preview-dot" />
            </div>
            <div className="p-6 md:p-8" style={{ background: 'var(--bg-primary)' }}>
              <div className="flex items-center gap-3 mb-6">
                <span className="green-dot-lg" />
                <span className="font-semibold" style={{ letterSpacing: '-0.4px', color: 'var(--text-primary)' }}>Yatri AI</span>
                <span className="text-xs font-medium px-2 py-0.5 rounded-full ml-auto" style={{ background: '#d1fae5', color: 'var(--accent-hover)' }}>
                  ↑ Active
                </span>
              </div>

              {/* Agent Grid inside dashboard */}
              <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
                {[
                  { emoji: '🚃', label: 'Transport', desc: 'Flights • Trains • Buses', bg: '#f0fdf4', border: '#bbf7d0' },
                  { emoji: '🚕', label: 'Cabs', desc: 'Ola vs Uber comparison', bg: '#f0fdf4', border: '#bbf7d0' },
                  { emoji: '🏨', label: 'Hotels', desc: 'Best stays for budget', bg: '#faf5ff', border: '#e9d5ff' },
                  { emoji: '🍽️', label: 'Food', desc: 'Local cuisine & spots', bg: '#fffbeb', border: '#fde68a' },
                  { emoji: '📍', label: 'Places', desc: 'Tourist attractions', bg: '#fff1f2', border: '#fecdd3' },
                  { emoji: '🗺️', label: 'Maps', desc: 'Optimized routing', bg: '#ecfeff', border: '#a5f3fc' },
                ].map((agent, i) => (
                  <div
                    key={i}
                    className="p-4 rounded-xl transition-all"
                    style={{ backgroundColor: agent.bg, border: `1px solid ${agent.border}` }}
                  >
                    <p className="text-lg mb-1">{agent.emoji}</p>
                    <p className="text-sm font-semibold" style={{ letterSpacing: '-0.2px', color: 'var(--text-primary)' }}>{agent.label}</p>
                    <p className="text-xs" style={{ color: 'var(--text-secondary)' }}>{agent.desc}</p>
                  </div>
                ))}
              </div>
            </div>
          </motion.div>
        </div>
      </section>

      {/* ═══════════════ TESTIMONIALS ═══════════════ */}
      <section id="testimonials" className="section-padding-lg" style={{ backgroundColor: 'var(--bg-secondary)' }}>
        <div className="container-wide">
          <motion.div
            className="mb-16"
            initial="hidden"
            whileInView="visible"
            viewport={{ once: true, amount: 0.3 }}
            variants={staggerContainer}
          >
            <motion.span variants={fadeUp} custom={0} className="clay-badge mb-4 block">
              TRAVELERS
            </motion.span>
            <motion.h2 variants={fadeUp} custom={1} className="heading-lg">
              Loved by teams who<br />care about craft.
            </motion.h2>
          </motion.div>

          <motion.div
            className="grid md:grid-cols-2 gap-6"
            initial="hidden"
            whileInView="visible"
            viewport={{ once: true, amount: 0.2 }}
            variants={staggerContainer}
          >
            {[
              {
                quote: '"Yatri AI planned my entire Rajasthan trip in under 30 seconds. The itinerary was better than what I spent 3 hours doing manually."',
                name: 'Priya Sharma',
                role: 'Product Designer · Mumbai',
              },
              {
                quote: '"We integrated this into our corporate travel workflow. The six-agent architecture is genuinely impressive — it handles every edge case."',
                name: 'Rahul Verma',
                role: 'Engineering Lead · Bangalore',
              },
              {
                quote: '"The food and places recommendations were spot on. It felt like having a local guide who knows every hidden gem in the city."',
                name: 'Ananya Patel',
                role: 'Travel Blogger · Delhi',
              },
              {
                quote: '"From Kanpur to Noida — transport options, cab comparisons, hotel picks — everything was curated in one clean chat interface."',
                name: 'Vikram Singh',
                role: 'Software Engineer · Noida',
              },
            ].map((testimonial, i) => (
              <motion.div key={i} variants={fadeUp} custom={i} className="testimonial-card">
                <p className="text-base mb-6" style={{ color: 'var(--text-primary)', lineHeight: 1.7, letterSpacing: '-0.2px' }}>
                  {testimonial.quote}
                </p>
                <div className="flex items-center gap-3">
                  <span className="green-dot-lg" />
                  <div>
                    <p className="text-sm font-semibold" style={{ color: 'var(--text-primary)' }}>{testimonial.name}</p>
                    <p className="text-xs" style={{ color: 'var(--text-muted)' }}>{testimonial.role}</p>
                  </div>
                </div>
              </motion.div>
            ))}
          </motion.div>
        </div>
      </section>

      {/* ═══════════════ FAQ ═══════════════ */}
      <section id="faq" className="section-padding-lg">
        <div className="container-narrow">
          <motion.div
            className="mb-12"
            initial="hidden"
            whileInView="visible"
            viewport={{ once: true, amount: 0.3 }}
            variants={staggerContainer}
          >
            <motion.span variants={fadeUp} custom={0} className="clay-badge mb-4 block">
              FAQ
            </motion.span>
            <motion.h2 variants={fadeUp} custom={1} className="heading-lg">
              Questions, answered.
            </motion.h2>
          </motion.div>

          <motion.div
            initial="hidden"
            whileInView="visible"
            viewport={{ once: true, amount: 0.2 }}
            variants={staggerContainer}
          >
            {[
              {
                q: 'What AI model powers Yatri AI?',
                a: 'Yatri AI is powered by LLaMA 3.1 through LangGraph orchestration. Six specialized sub-agents handle Transport, Cabs, Hotels, Food, Places, and Maps independently.',
              },
              {
                q: 'Is this production-ready?',
                a: 'Yes. The system runs on a Java Spring Boot Gateway, Python FastAPI Orchestrator, Node.js Notification Service, and Next.js Frontend — all containerized with Docker and deployed on Hugging Face Spaces.',
              },
              {
                q: 'How does it handle scale?',
                a: 'Built with Kafka for async event streaming, Redis for caching, PostgreSQL for persistence, and stateless microservices that can be horizontally scaled to handle millions of concurrent users.',
              },
              {
                q: 'What cities does it cover?',
                a: 'Yatri AI covers 100+ cities across India with real-time data for transport, hotels, restaurants, and tourist attractions. Coverage is expanding continuously.',
              },
            ].map((faq, i) => (
              <motion.div key={i} variants={fadeUp} custom={i} className="faq-item">
                <h3 className="faq-question">{faq.q}</h3>
                <p className="faq-answer">{faq.a}</p>
              </motion.div>
            ))}
          </motion.div>
        </div>
      </section>

      {/* ═══════════════ CTA SECTION ═══════════════ */}
      <section className="section-padding" style={{ backgroundColor: 'var(--text-primary)' }}>
        <motion.div
          className="container-narrow text-center"
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.5 }}
        >
          <h2 className="heading-lg mb-4" style={{ color: 'var(--bg-primary)' }}>
            Ready to plan your<br />next adventure?
          </h2>
          <p className="body-text mb-8 max-w-lg mx-auto" style={{ color: 'var(--text-muted)', fontSize: '17px' }}>
            Start chatting with Yatri AI and get a complete travel plan in seconds. No sign-up required.
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Link href="/chat" className="clay-button-cta" style={{ padding: '14px 32px', fontSize: '16px', borderRadius: '10px' }}>
              Start Planning <ArrowRight className="h-5 w-5" />
            </Link>
            <Link href="/register" className="clay-button-ghost" style={{ padding: '14px 32px', fontSize: '16px', borderRadius: '10px', borderColor: 'var(--text-secondary)', color: 'var(--text-faint)' }}>
              Create Account
            </Link>
          </div>
        </motion.div>
      </section>

      {/* ═══════════════ FOOTER ═══════════════ */}
      <footer style={{ borderTop: '1px solid var(--border-main)' }}>
        <div className="container-wide py-12">
          <div className="flex flex-col md:flex-row items-center justify-between gap-6">
            <div className="flex items-center gap-3">
              <span className="green-dot" />
              <span className="text-sm font-semibold" style={{ letterSpacing: '-0.3px', color: 'var(--text-primary)' }}>Yatri AI</span>
            </div>
            <div className="flex items-center gap-8">
              <a href="#features" className="text-sm" style={{ color: 'var(--text-secondary)' }}>Features</a>
              <a href="#agents" className="text-sm" style={{ color: 'var(--text-secondary)' }}>Agents</a>
              <a href="#testimonials" className="text-sm" style={{ color: 'var(--text-secondary)' }}>Testimonials</a>
              <a href="#faq" className="text-sm" style={{ color: 'var(--text-secondary)' }}>FAQ</a>
            </div>
            <p className="text-xs" style={{ color: 'var(--text-muted)' }}>
              © 2026 Yatri AI · Built with Java + Python + Node.js + Next.js
            </p>
          </div>
        </div>
      </footer>
    </main>
  );
}
