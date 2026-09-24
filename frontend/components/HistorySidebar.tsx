import React, { useState, useEffect } from 'react';
import {
  History,
  X,
  Search,
  Calendar,
  Wrench,
  CheckCircle,
  Clock,
  Plus,
  MessageSquare,
  ChevronRight
} from 'lucide-react';
import { fetchBooking, fetchChatSessions } from '../lib/api';
import { Booking } from '../lib/types';

interface HistorySidebarProps {
  isOpen: boolean;
  onClose: () => void;
  onNewSession: () => void;
  onSelectSession?: (id: string) => void;
  currentSessionId: string | null;
}

const formatIST = (dateStr?: string) => {
  if (!dateStr) return '';
  try {
    const d = new Date(dateStr);
    return d.toLocaleString('en-IN', {
      timeZone: 'Asia/Kolkata',
      day: 'numeric',
      month: 'short',
      hour: '2-digit',
      minute: '2-digit',
      hour12: true,
    }) + ' IST';
  } catch {
    return dateStr;
  }
};

export const HistorySidebar: React.FC<HistorySidebarProps> = ({
  isOpen,
  onClose,
  onNewSession,
  onSelectSession,
  currentSessionId
}) => {
  const [bookingRefInput, setBookingRefInput] = useState('');
  const [searchedBooking, setSearchedBooking] = useState<Booking | null>(null);
  const [searchLoading, setSearchLoading] = useState(false);
  const [searchError, setSearchError] = useState<string | null>(null);

  const [pastSessions, setPastSessions] = useState<any[]>([]);
  const [sessionsLoading, setSessionsLoading] = useState(false);

  useEffect(() => {
    if (isOpen) {
      setSessionsLoading(true);
      fetchChatSessions()
        .then((res) => setPastSessions(res.sessions || []))
        .catch(() => setPastSessions([]))
        .finally(() => setSessionsLoading(false));
    }
  }, [isOpen]);

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
        maxWidth: '430px',
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
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px', borderBottom: '1px solid rgba(255, 255, 255, 0.08)', paddingBottom: '16px' }}>
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
      <div style={{ marginBottom: '22px' }}>
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

      {/* Past Diagnostic Chats List */}
      <div style={{ marginBottom: '24px' }}>
        <div style={{ fontSize: '0.82rem', fontWeight: 600, color: 'var(--amber-primary)', textTransform: 'uppercase', marginBottom: '10px', display: 'flex', alignItems: 'center', gap: '6px' }}>
          <MessageSquare size={14} /> Past Diagnostic Chats
        </div>

        {sessionsLoading ? (
          <div style={{ fontSize: '0.8rem', color: 'var(--text-dim)', padding: '10px 0' }}>
            Loading previous diagnostic sessions...
          </div>
        ) : pastSessions.length === 0 ? (
          <div style={{ fontSize: '0.8rem', color: 'var(--text-dim)', fontStyle: 'italic', padding: '10px 0' }}>
            No past chats recorded yet.
          </div>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', maxHeight: '240px', overflowY: 'auto' }}>
            {pastSessions.map((s) => {
              const isActive = s.id === currentSessionId;
              return (
                <div
                  key={s.id}
                  onClick={() => {
                    if (onSelectSession) {
                      onSelectSession(s.id);
                      onClose();
                    }
                  }}
                  style={{
                    background: isActive ? 'rgba(245, 158, 11, 0.12)' : 'rgba(15, 23, 42, 0.7)',
                    border: isActive ? '1px solid var(--amber-primary)' : '1px solid rgba(255, 255, 255, 0.08)',
                    borderRadius: '8px',
                    padding: '10px 12px',
                    cursor: 'pointer',
                    transition: 'all 0.15s ease',
                  }}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '4px' }}>
                    <span style={{ fontWeight: 600, fontSize: '0.84rem', color: isActive ? 'var(--amber-primary)' : '#f8fafc' }}>
                      {s.vehicle}
                    </span>
                    <span style={{ fontSize: '0.7rem', color: 'var(--text-dim)' }}>
                      {formatIST(s.created_at)}
                    </span>
                  </div>
                  <div style={{ fontSize: '0.76rem', color: '#94a3b8', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                    {s.primary_issue ? `Report: ${s.primary_issue}` : s.preview}
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* Booking Status Lookup */}
      <div style={{ marginBottom: '24px' }}>
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
              <strong>Date:</strong> {searchedBooking.scheduled_date} ({searchedBooking.scheduled_time}) (IST)
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
    </div>
  );
};
