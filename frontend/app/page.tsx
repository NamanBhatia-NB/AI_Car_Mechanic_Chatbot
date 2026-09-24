'use client';

import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import {
  Wrench,
  ShieldCheck,
  History,
  Calendar,
  Sparkles,
  Zap,
  CheckCircle,
  AlertTriangle
} from 'lucide-react';
import { ChatInterface } from '../components/ChatInterface';
import { BookingModal } from '../components/BookingModal';
import { HistorySidebar } from '../components/HistorySidebar';
import { Diagnosis, Booking } from '../lib/types';
import { checkBackendHealth } from '../lib/api';

export default function HomePage() {
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [activeDiagnosis, setActiveDiagnosis] = useState<Diagnosis | null>(null);
  const [isBookingOpen, setIsBookingOpen] = useState(false);
  const [isHistoryOpen, setIsHistoryOpen] = useState(false);
  const [backendHealth, setBackendHealth] = useState<{ status: string; gemini_configured: boolean }>({
    status: 'checking',
    gemini_configured: false,
  });

  useEffect(() => {
    if (typeof window !== 'undefined') {
      const storedId = localStorage.getItem('instant_mechanic_session_id');
      if (storedId) {
        setSessionId(storedId);
      }
    }
    // Check backend health on mount
    checkBackendHealth().then((health) => {
      setBackendHealth(health);
    });
  }, []);

  const handleBookClick = (diagnosis: Diagnosis) => {
    setActiveDiagnosis(diagnosis);
    setIsBookingOpen(true);
  };

  const handleNewSession = () => {
    if (typeof window !== 'undefined') {
      localStorage.removeItem('instant_mechanic_session_id');
    }
    setSessionId(null);
    setActiveDiagnosis(null);
    window.location.reload();
  };

  const handleSelectSession = (id: string) => {
    if (typeof window !== 'undefined') {
      localStorage.setItem('instant_mechanic_session_id', id);
    }
    setSessionId(id);
    window.location.reload();
  };

  return (
    <main
      style={{
        minHeight: '100vh',
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        padding: '16px 20px',
        maxWidth: '1200px',
        margin: '0 auto',
      }}
    >
      {/* Top Navbar */}
      <header
        style={{
          width: '100%',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          padding: '12px 0 20px 0',
          borderBottom: '1px solid var(--border-subtle)',
          marginBottom: '20px',
        }}
      >
        {/* Brand */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <div
            style={{
              width: '38px',
              height: '38px',
              borderRadius: '10px',
              background: 'linear-gradient(135deg, #f59e0b 0%, #b45309 100%)',
              color: '#0b0f17',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              boxShadow: '0 0 15px rgba(245, 158, 11, 0.4)',
            }}
          >
            <Wrench size={22} />
          </div>
          <div>
            <h1 style={{ fontSize: '1.2rem', fontWeight: 800, letterSpacing: '-0.02em', color: '#f8fafc' }}>
              Instant<span style={{ color: 'var(--amber-primary)' }}>Mechanic</span>
            </h1>
            <p style={{ fontSize: '0.7rem', color: 'var(--text-dim)', letterSpacing: '0.04em', textTransform: 'uppercase' }}>
              AI Diagnostic & Mobile Repair Bay
            </p>
          </div>
        </div>

        {/* Status and Action Buttons */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          {/* Health indicator */}
          <div
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: '6px',
              fontSize: '0.75rem',
              padding: '4px 10px',
              borderRadius: '9999px',
              background: 'rgba(15, 23, 42, 0.8)',
              border: '1px solid var(--border-subtle)',
              color: backendHealth.status === 'healthy' ? '#34d399' : '#f59e0b',
            }}
          >
            <span
              style={{
                width: '7px',
                height: '7px',
                borderRadius: '50%',
                backgroundColor: backendHealth.status === 'healthy' ? '#10b981' : '#f59e0b',
              }}
              className="pulse-indicator"
            />
            <span>
              {backendHealth.status === 'healthy' ? 'API Online' : 'Connecting to Bay'}
            </span>
          </div>

          {/* Appointments Navigation Link */}
          <Link
            href="/bookings"
            className="btn-secondary"
            style={{
              fontSize: '0.82rem',
              padding: '6px 12px',
              display: 'inline-flex',
              alignItems: 'center',
              gap: '6px',
              textDecoration: 'none',
              color: '#f8fafc',
              background: 'rgba(30, 41, 59, 0.85)',
              border: '1px solid rgba(245, 158, 11, 0.4)',
              borderRadius: '8px',
              cursor: 'pointer',
              transition: 'all 0.2s ease',
            }}
            id="btn-nav-appointments"
            title="View and track your scheduled mechanic appointments"
          >
            <Calendar size={15} style={{ color: 'var(--amber-primary)' }} />
            <span>My Appointments</span>
          </Link>

          {/* Garage Records Drawer Toggle */}
          <button
            onClick={() => setIsHistoryOpen(true)}
            className="btn-secondary"
            style={{ fontSize: '0.82rem', padding: '6px 12px' }}
            id="btn-open-garage-records"
          >
            <History size={15} /> Garage Records
          </button>
        </div>
      </header>

      {/* Main Chat Area */}
      <section style={{ width: '100%', maxWidth: '880px', flex: 1 }}>
        <ChatInterface
          sessionId={sessionId}
          setSessionId={setSessionId}
          onBookClick={handleBookClick}
        />
      </section>

      {/* Modals */}
      <BookingModal
        isOpen={isBookingOpen}
        onClose={() => setIsBookingOpen(false)}
        diagnosis={activeDiagnosis}
      />

      <HistorySidebar
        isOpen={isHistoryOpen}
        onClose={() => setIsHistoryOpen(false)}
        onNewSession={handleNewSession}
        onSelectSession={handleSelectSession}
        currentSessionId={sessionId}
      />

      {/* Footer */}
      <footer
        style={{
          width: '100%',
          textAlign: 'center',
          padding: '24px 0 10px 0',
          fontSize: '0.76rem',
          color: 'var(--text-dim)',
        }}
      >
        <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', gap: '16px', flexWrap: 'wrap', marginBottom: '6px' }}>
          <span>⚡ Multi-Tier AI Optimization (0ms Guardrails + Gemini Flash)</span>
          <span>•</span>
          <a
            href="http://localhost:8000/api/docs/"
            target="_blank"
            rel="noopener noreferrer"
            style={{ color: 'var(--amber-primary)', textDecoration: 'none' }}
          >
            Swagger API Docs
          </a>
          <span>•</span>
          <span>100% Free Tier Architecture</span>
        </div>
        <div>Instant Mechanic — Virtual Automotive Master Technician</div>
      </footer>
    </main>
  );
}
