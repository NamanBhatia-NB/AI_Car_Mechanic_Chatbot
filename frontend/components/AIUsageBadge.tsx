import React from 'react';
import { Zap, Sparkles } from 'lucide-react';

interface AIUsageBadgeProps {
  aiInvoked: boolean;
}

export const AIUsageBadge: React.FC<AIUsageBadgeProps> = ({ aiInvoked }) => {
  if (aiInvoked) {
    return (
      <span
        style={{
          display: 'inline-flex',
          alignItems: 'center',
          gap: '4px',
          fontSize: '0.72rem',
          padding: '2px 8px',
          borderRadius: '9999px',
          background: 'rgba(6, 182, 212, 0.12)',
          color: '#22d3ee',
          border: '1px solid rgba(6, 182, 212, 0.3)',
          fontWeight: 500,
        }}
        title="Synthesized using Google Gemini 1.5 Flash Multimodal API"
      >
        <Sparkles size={11} /> Gemini Multimodal AI
      </span>
    );
  }

  return (
    <span
      style={{
        display: 'inline-flex',
        alignItems: 'center',
        gap: '4px',
        fontSize: '0.72rem',
        padding: '2px 8px',
        borderRadius: '9999px',
        background: 'rgba(16, 185, 129, 0.12)',
        color: '#34d399',
        border: '1px solid rgba(16, 185, 129, 0.25)',
        fontWeight: 500,
      }}
      title="Resolved deterministically via zero-cost rule & slot-filling engine"
    >
      <Zap size={11} /> 0ms Engine • 0 AI Cost
    </span>
  );
};
