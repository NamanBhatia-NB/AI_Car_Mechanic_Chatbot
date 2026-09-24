import React, { useState } from 'react';
import {
  History,
  X,
  Search,
  Calendar,
  Wrench,
  CheckCircle,
  Clock,
  ExternalLink,
  ShieldCheck,
  Plus
} from 'lucide-react';
import { fetchBooking } from '../lib/api';
import { Booking } from '../lib/types';

interface HistorySidebarProps {
  isOpen: boolean;
  onClose: () => void;
  onNewSession: () => void;
  currentSessionId: string | null;
}

export const HistorySidebar: React.FC<HistorySidebarProps> = ({
  isOpen,
  onClose,
  onNewSession,
  currentSessionId
}) => {
  const [bookingRefInput, setBookingRefInput] = useState('');
  const [searchedBooking, setSearchedBooking] = useState<Booking | null>(null);
  const [searchLoading, setSearchLoading] = useState(false);
  const [searchError, setSearchError] = useState<string | null>(null);

  if (!isOpen) return null;

  const handleBookingSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!bookingRefInput.trim()) return;

    setSearchLoading(true);
    setSearchError(null);
    setSearchedBooking(null);

    try {
      const data = await fetchBooking(bookingRefInput.trim());
      setSearchedBooking(data);
    } catch (err: any) {
      setSearchError(err.message || 'No booking found with this reference code.');
    } finally {
      setSearchLoading(false);
    }
  };

  return (
    <div
      style={{
        position: 'fixed',
        top: 0,
        right: 0,
        bottom: 0,
        width: '100%',
        maxWidth: '400px',
        background: '#0d131f',
        borderLeft: '1px solid var(--border-subtle)',
        boxShadow: '-10px 0 30px rgba(0, 0, 0, 0.7)',
        zIndex: 9998,
        display: 'flex',
        flexDirection: 'column',
        padding: '24px',
        overflowY: 'auto'
      }}
    >
      {/* Drawer Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px', borderBottom: '1px solid rgba(255, 255, 255, 0.08)', paddingBottom: '16px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <History size={20} color="var(--amber-primary)" />
          <h3 style={{ fontSize: '1.15rem', fontWeight: 700, color: '#f8fafc' }}>
            Garage Records
          </h3>
        </div>
        <button
          onClick={onClose}
          style={{
            background: 'transparent',
            border: 'none',
            color: 'var(--text-muted)',
            cursor: 'pointer'
          }}
          aria-label="Close sidebar"
        >
          <X size={20} />
        </button>
      </div>

      {/* Action: Start New Diagnosis */}
      <div style={{ marginBottom: '24px' }}>
        <button
          onClick={() => {
            onNewSession();
            onClose();
          }}
          className="btn-secondary"
          style={{ width: '100%', justifyContent: 'center', padding: '10px' }}
        >
          <Plus size={16} /> Start Fresh Diagnostic Session
        </button>
        {currentSessionId && (
          <div style={{ fontSize: '0.72rem', color: 'var(--text-dim)', textAlign: 'center', marginTop: '6px' }}>
            Active Session: <span style={{ fontFamily: 'monospace' }}>{currentSessionId.slice(0, 8)}...</span>
          </div>
        )}
      </div>

      {/* Booking Status Lookup */}
      <div style={{ marginBottom: '28px' }}>
        <div style={{ fontSize: '0.82rem', fontWeight: 600, color: 'var(--amber-primary)', textTransform: 'uppercase', marginBottom: '8px' }}>
          Check Appointment Status
        </div>
        <form onSubmit={handleBookingSearch} style={{ display: 'flex', gap: '6px' }}>
          <div style={{ position: 'relative', flex: 1 }}>
            <Search size={15} style={{ position: 'absolute', left: '10px', top: '11px', color: 'var(--text-dim)' }} />
            <input
              type="text"
              value={bookingRefInput}
              onChange={(e) => setBookingRefInput(e.target.value)}
              placeholder="e.g. MECH-84920"
              style={{
                width: '100%',
                background: 'rgba(15, 23, 42, 0.9)',
                border: '1px solid var(--border-subtle)',
                borderRadius: '8px',
                padding: '8px 10px 8px 32px',
                color: '#f8fafc',
                fontSize: '0.85rem',
                outline: 'none'
              }}
            />
          </div>
          <button
            type="submit"
            disabled={searchLoading}
            className="btn-primary"
            style={{ padding: '8px 14px', fontSize: '0.85rem' }}
          >
            {searchLoading ? '...' : 'Track'}
          </button>
        </form>

        {searchError && (
          <div style={{ fontSize: '0.78rem', color: '#f87171', marginTop: '8px' }}>
            {searchError}
          </div>
        )}

        {searchedBooking && (
          <div
            style={{
              background: 'rgba(15, 23, 42, 0.8)',
              border: '1px solid rgba(245, 158, 11, 0.25)',
              borderRadius: '10px',
              padding: '14px',
              marginTop: '12px'
            }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
              <span style={{ fontWeight: 700, fontFamily: 'monospace', color: 'var(--amber-primary)' }}>
                {searchedBooking.booking_reference}
              </span>
              <span
                style={{
                  fontSize: '0.72rem',
                  padding: '2px 8px',
                  borderRadius: '9999px',
                  background: 'rgba(16, 185, 129, 0.15)',
                  color: '#34d399',
                  border: '1px solid rgba(16, 185, 129, 0.3)',
                  textTransform: 'uppercase'
                }}
              >
                {searchedBooking.status}
              </span>
            </div>
            <div style={{ fontSize: '0.82rem', color: '#e2e8f0', marginBottom: '4px' }}>
              <strong>Date:</strong> {searchedBooking.scheduled_date} ({searchedBooking.scheduled_time})
            </div>
            <div style={{ fontSize: '0.82rem', color: '#94a3b8', marginBottom: '4px' }}>
              <strong>Service:</strong> {searchedBooking.service_type}
            </div>
            <div style={{ fontSize: '0.82rem', color: '#94a3b8' }}>
              <strong>Mechanic:</strong> {searchedBooking.mechanic_name}
            </div>
          </div>
        )}
      </div>

      {/* Senior Mechanic Profile Info */}
      <div
        style={{
          marginTop: 'auto',
          background: 'rgba(15, 23, 42, 0.6)',
          border: '1px solid var(--border-subtle)',
          borderRadius: '12px',
          padding: '14px'
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '6px' }}>
          <ShieldCheck size={18} color="#10b981" />
          <span style={{ fontSize: '0.85rem', fontWeight: 600, color: '#f8fafc' }}>
            Marcus Vance, ASE Master
          </span>
        </div>
        <p style={{ fontSize: '0.76rem', color: 'var(--text-dim)', lineHeight: 1.4, marginBottom: '10px' }}>
          Lead Automotive Diagnostic Specialist with 25+ years hands-on master technician certification.
        </p>
        <div style={{ display: 'flex', gap: '10px' }}>
          <a
            href="http://localhost:8000/api/docs/"
            target="_blank"
            rel="noopener noreferrer"
            style={{
              fontSize: '0.75rem',
              color: 'var(--amber-primary)',
              textDecoration: 'none',
              display: 'inline-flex',
              alignItems: 'center',
              gap: '4px'
            }}
          >
            Swagger API Docs <ExternalLink size={12} />
          </a>
        </div>
      </div>
    </div>
  );
};
