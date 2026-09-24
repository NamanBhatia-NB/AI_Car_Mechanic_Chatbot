'use client';

import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import {
  Wrench,
  Search,
  CheckCircle,
  Calendar,
  Clock,
  ArrowLeft,
  Truck,
  ShieldCheck,
  User,
  Phone,
  Mail,
  ExternalLink,
  ClipboardList
} from 'lucide-react';
import { fetchBooking, fetchAllBookings } from '../../lib/api';
import { Booking } from '../../lib/types';

const formatIST = (dateStr?: string) => {
  if (!dateStr) return '';
  try {
    const d = new Date(dateStr);
    return d.toLocaleString('en-IN', {
      timeZone: 'Asia/Kolkata',
      day: 'numeric',
      month: 'short',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
      hour12: true
    }) + ' IST';
  } catch {
    return dateStr;
  }
};

export default function BookingsPage() {
  const [refInput, setRefInput] = useState('');
  const [booking, setBooking] = useState<Booking | null>(null);
  const [recentBookings, setRecentBookings] = useState<Booking[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    // Load recent bookings list
    loadAllBookings();

    // If query param exists (e.g. ?ref=MECH-12345)
    if (typeof window !== 'undefined') {
      const params = new URLSearchParams(window.location.search);
      const queryRef = params.get('ref');
      if (queryRef) {
        setRefInput(queryRef);
        searchBooking(queryRef);
      }
    }
  }, []);

  const loadAllBookings = async () => {
    try {
      const data = await fetchAllBookings();
      setRecentBookings(data.bookings || []);
    } catch {
      // Graceful fallback if no bookings yet
    }
  };

  const searchBooking = async (reference: string) => {
    if (!reference.trim()) return;
    setLoading(true);
    setError(null);
    setBooking(null);

    try {
      const data = await fetchBooking(reference.trim());
      setBooking(data);
    } catch (err: any) {
      setError(err.message || 'Booking not found.');
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    searchBooking(refInput);
  };

  return (
    <div
      style={{
        minHeight: '100vh',
        padding: '24px 20px',
        maxWidth: '900px',
        margin: '0 auto',
      }}
    >
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '14px', marginBottom: '24px' }}>
        <div>
          <Link
            href="/"
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: '6px',
              color: 'var(--amber-primary)',
              textDecoration: 'none',
              fontSize: '0.85rem',
              marginBottom: '14px',
            }}
          >
            <ArrowLeft size={16} /> Back to Diagnostic Chat
          </Link>
          <h1 style={{ fontSize: '1.65rem', fontWeight: 800, color: '#f8fafc' }}>
            Mechanic Service & Bookings Bay
          </h1>
          <p style={{ color: 'var(--text-muted)', fontSize: '0.88rem' }}>
            Customer service dispatch records & administrative management.
          </p>
        </div>
      </div>

      {/* Search Bar */}
      <form onSubmit={handleSearch} style={{ display: 'flex', gap: '10px', marginBottom: '24px' }}>
        <div style={{ position: 'relative', flex: 1 }}>
          <Search size={18} style={{ position: 'absolute', left: '12px', top: '13px', color: 'var(--text-dim)' }} />
          <input
            type="text"
            required
            value={refInput}
            onChange={(e) => setRefInput(e.target.value)}
            placeholder="Search by Booking Reference (e.g. MECH-12345)..."
            style={{
              width: '100%',
              background: 'rgba(15, 23, 42, 0.9)',
              border: '1px solid var(--border-subtle)',
              borderRadius: '10px',
              padding: '12px 14px 12px 40px',
              color: '#f8fafc',
              fontSize: '0.95rem',
              outline: 'none',
            }}
          />
        </div>
        <button type="submit" disabled={loading} className="btn-primary" style={{ padding: '0 24px' }}>
          {loading ? 'Searching...' : 'Track Service'}
        </button>
      </form>

      {error && (
        <div
          style={{
            background: 'rgba(239, 68, 68, 0.15)',
            border: '1px solid rgba(239, 68, 68, 0.3)',
            borderRadius: '12px',
            padding: '16px',
            color: '#fca5a5',
            marginBottom: '24px',
          }}
        >
          {error}
        </div>
      )}

      {/* Detailed Booking Card */}
      {booking && (
        <div
          className="glass-panel"
          style={{
            padding: '28px',
            border: '1px solid rgba(245, 158, 11, 0.3)',
            marginBottom: '32px'
          }}
        >
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px', flexWrap: 'wrap', gap: '10px' }}>
            <div>
              <span style={{ fontSize: '0.75rem', textTransform: 'uppercase', color: 'var(--amber-primary)', fontWeight: 700 }}>
                Work Order Reference
              </span>
              <h2 style={{ fontSize: '1.4rem', fontFamily: 'monospace', color: '#f8fafc' }}>
                {booking.booking_reference}
              </h2>
            </div>
            <span
              style={{
                padding: '6px 14px',
                borderRadius: '9999px',
                background: 'rgba(16, 185, 129, 0.2)',
                border: '1px solid #10b981',
                color: '#34d399',
                fontSize: '0.85rem',
                fontWeight: 600,
                textTransform: 'uppercase',
              }}
            >
              {booking.status}
            </span>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '16px', marginBottom: '24px' }}>
            <div style={{ background: 'rgba(15, 23, 42, 0.6)', padding: '14px', borderRadius: '10px' }}>
              <div style={{ fontSize: '0.76rem', color: 'var(--text-dim)', marginBottom: '4px' }}>Customer</div>
              <div style={{ fontWeight: 600, color: '#f8fafc', display: 'flex', alignItems: 'center', gap: '6px' }}>
                <User size={16} color="var(--amber-primary)" />
                {booking.customer_name}
              </div>
              <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginTop: '4px' }}>
                {booking.customer_phone}
              </div>
            </div>

            <div style={{ background: 'rgba(15, 23, 42, 0.6)', padding: '14px', borderRadius: '10px' }}>
              <div style={{ fontSize: '0.76rem', color: 'var(--text-dim)', marginBottom: '4px' }}>Appointment Window</div>
              <div style={{ fontWeight: 600, color: '#f8fafc', display: 'flex', alignItems: 'center', gap: '6px' }}>
                <Calendar size={16} color="var(--amber-primary)" />
                {booking.scheduled_date} at {booking.scheduled_time} (IST)
              </div>
              <div style={{ fontSize: '0.74rem', color: 'var(--text-dim)', marginTop: '4px' }}>
                Booked: {formatIST(booking.created_at)}
              </div>
            </div>

            <div style={{ background: 'rgba(15, 23, 42, 0.6)', padding: '14px', borderRadius: '10px' }}>
              <div style={{ fontSize: '0.76rem', color: 'var(--text-dim)', marginBottom: '4px' }}>Assigned Technician</div>
              <div style={{ fontWeight: 600, color: '#10b981', display: 'flex', alignItems: 'center', gap: '6px' }}>
                <ShieldCheck size={16} />
                {booking.mechanic_name}
              </div>
            </div>
          </div>

          {booking.diagnosis_details && (
            <div
              style={{
                background: 'rgba(15, 23, 42, 0.8)',
                borderRadius: '12px',
                padding: '16px',
                border: '1px solid var(--border-subtle)',
              }}
            >
              <div style={{ fontSize: '0.78rem', color: 'var(--amber-primary)', fontWeight: 700, textTransform: 'uppercase', marginBottom: '6px' }}>
                Diagnosed Malfunction
              </div>
              <div style={{ fontSize: '1.05rem', fontWeight: 700, color: '#f8fafc', marginBottom: '8px' }}>
                {booking.diagnosis_details.primary_issue}
              </div>
              <div style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>
                Service rate: {Number(booking.diagnosis_details.estimated_cost_min) === Number(booking.diagnosis_details.estimated_cost_max)
                  ? `₹${Number(booking.diagnosis_details.estimated_cost_min).toLocaleString('en-IN')} (Flat Service Rate)`
                  : `₹${Number(booking.diagnosis_details.estimated_cost_min).toLocaleString('en-IN')} - ₹${Number(booking.diagnosis_details.estimated_cost_max).toLocaleString('en-IN')}`}
              </div>
            </div>
          )}
        </div>
      )}

      {/* List of All Confirmed Bookings (Admin & User View) */}
      <div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '14px' }}>
          <ClipboardList size={18} color="var(--amber-primary)" />
          <h2 style={{ fontSize: '1.15rem', fontWeight: 700, color: '#f8fafc' }}>
            Garage Service Roster ({recentBookings.length} Total Bookings)
          </h2>
        </div>

        {recentBookings.length === 0 ? (
          <div style={{ color: 'var(--text-dim)', fontSize: '0.9rem', fontStyle: 'italic', padding: '16px 0' }}>
            No bookings recorded yet. Once a user books a mechanic via the chat diagnostic report, it appears here immediately.
          </div>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
            {recentBookings.map((b) => (
              <div
                key={b.id}
                onClick={() => {
                  setRefInput(b.booking_reference);
                  searchBooking(b.booking_reference);
                }}
                className="glass-panel"
                style={{
                  padding: '16px 20px',
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  flexWrap: 'wrap',
                  gap: '12px',
                  cursor: 'pointer',
                  border: booking?.id === b.id ? '1px solid var(--amber-primary)' : '1px solid var(--border-subtle)',
                  transition: 'border-color 0.15s ease'
                }}
              >
                <div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '4px' }}>
                    <span style={{ fontFamily: 'monospace', fontWeight: 700, color: 'var(--amber-primary)', fontSize: '0.95rem' }}>
                      {b.booking_reference}
                    </span>
                    <span style={{ fontWeight: 600, color: '#f8fafc', fontSize: '0.95rem' }}>
                      {b.customer_name}
                    </span>
                  </div>
                  <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                    {b.diagnosis_details?.primary_issue || 'Automotive Inspection'} • {b.scheduled_date} at {b.scheduled_time} (IST)
                  </div>
                  <div style={{ fontSize: '0.72rem', color: 'var(--text-dim)', marginTop: '2px' }}>
                    Booked on: {formatIST(b.created_at)}
                  </div>
                </div>

                <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                  <span
                    style={{
                      padding: '4px 10px',
                      borderRadius: '9999px',
                      background: 'rgba(16, 185, 129, 0.15)',
                      border: '1px solid rgba(16, 185, 129, 0.4)',
                      color: '#34d399',
                      fontSize: '0.78rem',
                      fontWeight: 600,
                      textTransform: 'uppercase'
                    }}
                  >
                    {b.status}
                  </span>
                  <span style={{ fontSize: '0.85rem', color: 'var(--amber-primary)', fontWeight: 600 }}>
                    View Details →
                  </span>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
