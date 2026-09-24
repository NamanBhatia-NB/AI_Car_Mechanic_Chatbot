import React from 'react';
import { Diagnosis } from '../lib/types';
import {
  AlertTriangle,
  CheckCircle2,
  Wrench,
  IndianRupee,
  Calendar,
  ShieldAlert,
  ChevronRight,
  Info
} from 'lucide-react';

interface DiagnosisCardProps {
  diagnosis: Diagnosis;
  onBookClick: (diagnosis: Diagnosis) => void;
}

export const DiagnosisCard: React.FC<DiagnosisCardProps> = ({ diagnosis, onBookClick }) => {
  const getSeverityBadge = () => {
    switch (diagnosis.severity) {
      case 'critical':
        return (
          <span className="badge-severity-critical" style={{ padding: '4px 10px', borderRadius: '9999px', fontSize: '0.78rem', fontWeight: 600, display: 'inline-flex', alignItems: 'center', gap: '4px' }}>
            <ShieldAlert size={14} /> Critical — Do Not Drive
          </span>
        );
      case 'moderate':
        return (
          <span className="badge-severity-moderate" style={{ padding: '4px 10px', borderRadius: '9999px', fontSize: '0.78rem', fontWeight: 600, display: 'inline-flex', alignItems: 'center', gap: '4px' }}>
            <AlertTriangle size={14} /> Moderate — Repair Soon
          </span>
        );
      case 'low':
      default:
        return (
          <span className="badge-severity-low" style={{ padding: '4px 10px', borderRadius: '9999px', fontSize: '0.78rem', fontWeight: 600, display: 'inline-flex', alignItems: 'center', gap: '4px' }}>
            <CheckCircle2 size={14} /> Low — Minor Issue
          </span>
        );
    }
  };

  const minCost = Number(diagnosis.estimated_cost_min) || 0;
  const maxCost = Number(diagnosis.estimated_cost_max) || 0;

  return (
    <div
      style={{
        background: 'rgba(30, 41, 59, 0.75)',
        backdropFilter: 'blur(12px)',
        border: '1px solid rgba(245, 158, 11, 0.3)',
        borderRadius: '16px',
        padding: '20px',
        marginTop: '12px',
        marginBottom: '12px',
        boxShadow: '0 8px 30px rgba(0, 0, 0, 0.4), 0 0 15px rgba(245, 158, 11, 0.08)',
        position: 'relative',
        overflow: 'hidden'
      }}
    >
      {/* Top accent line */}
      <div
        style={{
          position: 'absolute',
          top: 0,
          left: 0,
          right: 0,
          height: '3px',
          background: diagnosis.severity === 'critical' 
            ? 'linear-gradient(90deg, #ef4444, #b91c1c)' 
            : 'linear-gradient(90deg, #f59e0b, #06b6d4)'
        }}
      />

      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '10px', marginBottom: '14px' }}>
        <div>
          <div style={{ fontSize: '0.75rem', textTransform: 'uppercase', letterSpacing: '0.06em', color: 'var(--amber-primary)', fontWeight: 700, marginBottom: '4px' }}>
            Official Garage Diagnostic Report
          </div>
          <h3 style={{ fontSize: '1.25rem', fontWeight: 700, color: '#f8fafc', lineHeight: 1.3 }}>
            {diagnosis.primary_issue}
          </h3>
          {diagnosis.vehicle_summary && (
            <div style={{ fontSize: '0.82rem', color: 'var(--text-muted)', marginTop: '2px' }}>
              Vehicle: <span style={{ color: '#e2e8f0', fontWeight: 500 }}>{diagnosis.vehicle_summary}</span>
            </div>
          )}
        </div>
        <div>{getSeverityBadge()}</div>
      </div>

      {/* Cost & DIY highlight cards */}
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))',
          gap: '12px',
          marginBottom: '16px'
        }}
      >
        <div
          style={{
            background: 'rgba(15, 23, 42, 0.65)',
            border: '1px solid rgba(255, 255, 255, 0.06)',
            borderRadius: '12px',
            padding: '12px 14px',
            display: 'flex',
            alignItems: 'center',
            gap: '10px'
          }}
        >
          <div
            style={{
              width: '36px',
              height: '36px',
              borderRadius: '8px',
              background: 'rgba(245, 158, 11, 0.15)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: 'var(--amber-primary)'
            }}
          >
            <IndianRupee size={20} />
          </div>
          <div>
            <div style={{ fontSize: '0.72rem', color: 'var(--text-dim)', textTransform: 'uppercase' }}>
              Standard Service Rate
            </div>
            <div style={{ fontSize: '1.05rem', fontWeight: 700, color: '#f8fafc' }}>
              {minCost === maxCost
                ? `₹${minCost.toLocaleString('en-IN')}`
                : `₹${minCost.toLocaleString('en-IN')} – ₹${maxCost.toLocaleString('en-IN')}`}
            </div>
          </div>
        </div>

        <div
          style={{
            background: 'rgba(15, 23, 42, 0.65)',
            border: '1px solid rgba(255, 255, 255, 0.06)',
            borderRadius: '12px',
            padding: '12px 14px',
            display: 'flex',
            alignItems: 'center',
            gap: '10px'
          }}
        >
          <div
            style={{
              width: '36px',
              height: '36px',
              borderRadius: '8px',
              background: diagnosis.diy_friendly ? 'rgba(16, 185, 129, 0.15)' : 'rgba(6, 182, 212, 0.15)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: diagnosis.diy_friendly ? '#34d399' : '#22d3ee'
            }}
          >
            <Wrench size={18} />
          </div>
          <div>
            <div style={{ fontSize: '0.72rem', color: 'var(--text-dim)', textTransform: 'uppercase' }}>
              Repair Difficulty
            </div>
            <div style={{ fontSize: '0.9rem', fontWeight: 600, color: '#f8fafc' }}>
              {diagnosis.diy_friendly ? 'DIY Possible with Tools' : 'Certified Tech Required'}
            </div>
          </div>
        </div>
      </div>

      {/* Summary Notes */}
      {diagnosis.summary_notes && (
        <div
          style={{
            fontSize: '0.86rem',
            lineHeight: 1.5,
            color: '#cbd5e1',
            background: 'rgba(15, 23, 42, 0.4)',
            padding: '12px 14px',
            borderRadius: '10px',
            marginBottom: '16px',
            borderLeft: '3px solid var(--amber-primary)'
          }}
        >
          {diagnosis.summary_notes}
        </div>
      )}

      {/* Symptoms & Possible causes */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '14px', marginBottom: '18px' }}>
        {diagnosis.possible_causes && diagnosis.possible_causes.length > 0 && (
          <div>
            <div style={{ fontSize: '0.78rem', fontWeight: 700, color: 'var(--amber-primary)', marginBottom: '6px', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
              Probable Root Causes
            </div>
            <ul style={{ listStyleType: 'none', paddingLeft: 0 }}>
              {diagnosis.possible_causes.map((cause, idx) => (
                <li
                  key={idx}
                  style={{
                    fontSize: '0.82rem',
                    color: '#94a3b8',
                    marginBottom: '4px',
                    display: 'flex',
                    alignItems: 'flex-start',
                    gap: '6px'
                  }}
                >
                  <span style={{ color: 'var(--amber-primary)', marginTop: '2px' }}>•</span>
                  <span>{cause}</span>
                </li>
              ))}
            </ul>
          </div>
        )}

        {diagnosis.recommended_repairs && diagnosis.recommended_repairs.length > 0 && (
          <div>
            <div style={{ fontSize: '0.78rem', fontWeight: 700, color: '#38bdf8', marginBottom: '6px', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
              Recommended Services
            </div>
            <ul style={{ listStyleType: 'none', paddingLeft: 0 }}>
              {diagnosis.recommended_repairs.map((repair, idx) => (
                <li
                  key={idx}
                  style={{
                    fontSize: '0.82rem',
                    color: '#94a3b8',
                    marginBottom: '4px',
                    display: 'flex',
                    alignItems: 'flex-start',
                    gap: '6px'
                  }}
                >
                  <CheckCircle2 size={13} style={{ color: '#38bdf8', flexShrink: 0, marginTop: '2px' }} />
                  <span>{repair}</span>
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>

      {/* CTA Button */}
      <div style={{ display: 'flex', justifyContent: 'flex-end', paddingTop: '10px', borderTop: '1px solid rgba(255, 255, 255, 0.08)' }}>
        <button
          onClick={() => onBookClick(diagnosis)}
          className="btn-primary"
          style={{
            fontSize: '0.92rem',
            padding: '12px 24px',
            width: '100%',
            maxWidth: '320px',
            display: 'flex',
            justifyContent: 'center',
            alignItems: 'center',
            gap: '8px'
          }}
          id="btn-book-mechanic-cta"
        >
          <Calendar size={18} />
          Book Certified Mechanic
          <ChevronRight size={16} />
        </button>
      </div>
    </div>
  );
};
