import React, { useState, useRef, useEffect } from 'react';
import {
  Send,
  Wrench,
  Bot,
  User as UserIcon,
  Play,
  Volume2,
  FileText,
  Sparkles,
  Zap,
  Image as ImageIcon,
  AlertTriangle,
  RotateCcw
} from 'lucide-react';
import { ChatMessage, MediaAttachment, Diagnosis } from '../lib/types';
import { sendMessage, fetchSessionHistory } from '../lib/api';
import { AIUsageBadge } from './AIUsageBadge';
import { DiagnosisCard } from './DiagnosisCard';
import { MediaUploader } from './MediaUploader';

// Clean text formatter that parses **bold** markdown tags, bullet points, and numbered lists
const FormattedContent: React.FC<{ text: string }> = ({ text }) => {
  if (!text) return null;

  const lines = text.split('\n');

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '6px', fontSize: '0.92rem', lineHeight: '1.6' }}>
      {lines.map((line, lineIdx) => {
        const trimmed = line.trim();
        if (!trimmed) {
          return <div key={lineIdx} style={{ height: '4px' }} />;
        }

        // Parse inline **bold**
        const parts: (string | React.ReactNode)[] = [];
        let lastIndex = 0;
        const boldRegex = /\*\*(.*?)\*\*/g;
        let match;

        while ((match = boldRegex.exec(line)) !== null) {
          if (match.index > lastIndex) {
            parts.push(line.substring(lastIndex, match.index));
          }
          parts.push(
            <strong
              key={`b-${lineIdx}-${match.index}`}
              style={{
                fontWeight: 700,
                color: '#f8fafc',
              }}
            >
              {match[1]}
            </strong>
          );
          lastIndex = match.index + match[0].length;
        }

        if (lastIndex < line.length) {
          parts.push(line.substring(lastIndex));
        }

        const isBullet = trimmed.startsWith('•') || trimmed.startsWith('- ') || trimmed.startsWith('* ');
        const isNumbered = /^\d+\.\s/.test(trimmed);

        return (
          <div
            key={lineIdx}
            style={{
              paddingLeft: isBullet || isNumbered ? '12px' : '0',
            }}
          >
            {parts}
          </div>
        );
      })}
    </div>
  );
};

interface ChatInterfaceProps {
  sessionId: string | null;
  setSessionId: (id: string | null) => void;
  onBookClick: (diagnosis: Diagnosis) => void;
}

const DEFAULT_WELCOME_MSG: ChatMessage = {
  id: 'welcome',
  sender: 'mechanic',
  content:
    "Hey friend, I'm Marcus Vance, Senior Automotive Diagnostic Technician with 25+ years in the bay. " +
    "I'm here to help you troubleshoot strange noises, warning lights, fluid leaks, or starting issues. " +
    "What vehicle are you driving, and what's going on under the hood?",
  ai_invoked: false,
  quick_replies: [
    'Rapid clicking when starting (car dead)',
    'Squeaking / grinding brakes',
    'Check Engine light is blinking',
    'Engine temperature gauge in red',
  ],
};

export const ChatInterface: React.FC<ChatInterfaceProps> = ({
  sessionId,
  setSessionId,
  onBookClick,
}) => {
  const [messages, setMessages] = useState<ChatMessage[]>([DEFAULT_WELCOME_MSG]);
  const [inputText, setInputText] = useState('');
  const [pendingMedia, setPendingMedia] = useState<MediaAttachment[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // Restore chat session from localStorage on initial page load
  useEffect(() => {
    if (typeof window === 'undefined') return;
    const storedId = localStorage.getItem('instant_mechanic_session_id');
    if (storedId) {
      setSessionId(storedId);
      setIsLoading(true);
      fetchSessionHistory(storedId)
        .then((data) => {
          if (data && data.messages && data.messages.length > 0) {
            const restoredMessages: ChatMessage[] = data.messages.map((m: any, idx: number) => ({
              id: m.id ? String(m.id) : `hist-${idx}`,
              sender: m.sender,
              content: m.content,
              ai_invoked: m.ai_invoked,
              diagnosis: (idx === data.messages.length - 1 && data.diagnosis) ? data.diagnosis : undefined,
            }));

            // Always ensure Marcus Vance's opening greeting is the first message in the bay
            const hasWelcome = restoredMessages.some(
              (m) => m.sender === 'mechanic' && m.content.includes("Marcus Vance")
            );

            if (!hasWelcome) {
              setMessages([DEFAULT_WELCOME_MSG, ...restoredMessages]);
            } else {
              setMessages(restoredMessages);
            }
          }
        })
        .catch((err) => {
          console.warn('Could not restore past session:', err);
        })
        .finally(() => {
          setIsLoading(false);
        });
    }
  }, []);

  const handleResetChat = () => {
    if (typeof window !== 'undefined') {
      localStorage.removeItem('instant_mechanic_session_id');
    }
    setSessionId(null);
    setMessages([DEFAULT_WELCOME_MSG]);
    setPendingMedia([]);
    setErrorMsg(null);
  };

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isLoading]);

  const handleMediaUploaded = (attachment: MediaAttachment) => {
    setPendingMedia((prev) => [...prev, attachment]);
  };

  const removePendingMedia = (id: number) => {
    setPendingMedia((prev) => prev.filter((m) => m.id !== id));
  };

  const handleSend = async (overrideText?: string) => {
    const textToSend = overrideText !== undefined ? overrideText : inputText;
    if (!textToSend.trim() && pendingMedia.length === 0) return;

    setErrorMsg(null);
    const mediaIds = pendingMedia.map((m) => m.id);
    const currentMedia = [...pendingMedia];

    // Optimistically add user message
    const userMsg: ChatMessage = {
      id: `user-${Date.now()}`,
      sender: 'user',
      content: textToSend.trim(),
      ai_invoked: false,
      media_attachments: currentMedia,
    };

    setMessages((prev) => [...prev, userMsg]);
    setInputText('');
    setPendingMedia([]);
    setIsLoading(true);

    try {
      const response = await sendMessage(sessionId, textToSend.trim(), mediaIds);

      // Save/Update session ID in state & localStorage
      if (response.session_id) {
        setSessionId(response.session_id);
        if (typeof window !== 'undefined') {
          localStorage.setItem('instant_mechanic_session_id', response.session_id);
        }
      }

      // Add mechanic reply
      const mechanicMsg: ChatMessage = {
        id: `mech-${Date.now()}`,
        sender: 'mechanic',
        content: response.reply,
        ai_invoked: response.ai_invoked,
        quick_replies: response.quick_replies,
        diagnosis: response.diagnosis || undefined,
        is_off_topic: response.is_off_topic,
      };

      setMessages((prev) => [...prev, mechanicMsg]);
    } catch (err: any) {
      setErrorMsg(err.message || 'Connection to mechanic diagnostic engine failed.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="chat-main-card">
      {/* Mechanic Header */}
      <div className="chat-card-header">
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <div
            style={{
              width: '42px',
              height: '42px',
              borderRadius: '12px',
              background: 'linear-gradient(135deg, #f59e0b 0%, #b45309 100%)',
              color: '#0b0f17',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              boxShadow: '0 0 15px rgba(245, 158, 11, 0.35)',
              position: 'relative',
            }}
          >
            <Wrench size={22} />
            <span
              style={{
                position: 'absolute',
                bottom: '-2px',
                right: '-2px',
                width: '12px',
                height: '12px',
                borderRadius: '50%',
                backgroundColor: '#10b981',
                border: '2px solid #0f172a',
              }}
            />
          </div>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <span style={{ fontWeight: 700, fontSize: '1.02rem', color: '#f8fafc' }}>
                Marcus Vance
              </span>
              <span
                style={{
                  fontSize: '0.68rem',
                  textTransform: 'uppercase',
                  padding: '1px 6px',
                  borderRadius: '4px',
                  background: 'rgba(245, 158, 11, 0.2)',
                  color: 'var(--amber-primary)',
                  fontWeight: 600,
                }}
              >
                ASE Master Tech
              </span>
            </div>
            <div style={{ fontSize: '0.78rem', color: 'var(--text-dim)' }}>
              Online • Automotive Diagnostic & Repair Station
            </div>
          </div>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <button
            onClick={handleResetChat}
            title="Start a fresh diagnostic session"
            className="btn-secondary"
            style={{
              fontSize: '0.78rem',
              padding: '6px 12px',
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              background: 'rgba(255, 255, 255, 0.05)',
            }}
            id="btn-reset-chat"
          >
            <RotateCcw size={13} />
            <span>New Chat</span>
          </button>
        </div>
      </div>

      {/* Message Stream */}
      <div
        style={{
          flex: 1,
          overflowY: 'auto',
          padding: '20px',
          display: 'flex',
          flexDirection: 'column',
          gap: '16px',
        }}
      >
        {messages.map((msg) => (
          <div
            key={msg.id}
            className="animate-slide-up"
            style={{
              display: 'flex',
              flexDirection: 'column',
              alignItems: msg.sender === 'user' ? 'flex-end' : 'flex-start',
              width: '100%',
            }}
          >
            <div
              style={{
                display: 'flex',
                alignItems: 'flex-start',
                gap: '8px',
                maxWidth: '85%',
                flexDirection: msg.sender === 'user' ? 'row-reverse' : 'row',
              }}
            >
              {/* Avatar Icon */}
              <div
                style={{
                  width: '32px',
                  height: '32px',
                  borderRadius: '8px',
                  background:
                    msg.sender === 'user'
                      ? 'rgba(6, 182, 212, 0.2)'
                      : 'rgba(245, 158, 11, 0.2)',
                  color: msg.sender === 'user' ? '#22d3ee' : 'var(--amber-primary)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  flexShrink: 0,
                  marginTop: '2px',
                }}
              >
                {msg.sender === 'user' ? <UserIcon size={16} /> : <Bot size={16} />}
              </div>

              {/* Message Bubble */}
              <div
                style={{
                  background:
                    msg.sender === 'user'
                      ? 'linear-gradient(135deg, rgba(6, 182, 212, 0.15) 0%, rgba(30, 41, 59, 0.9) 100%)'
                      : 'rgba(30, 41, 59, 0.75)',
                  border:
                    msg.sender === 'user'
                      ? '1px solid rgba(6, 182, 212, 0.3)'
                      : msg.is_off_topic
                      ? '1px solid rgba(239, 68, 68, 0.4)'
                      : '1px solid rgba(255, 255, 255, 0.08)',
                  borderRadius:
                    msg.sender === 'user'
                      ? '16px 4px 16px 16px'
                      : '4px 16px 16px 16px',
                  padding: '14px 18px',
                  color: '#f8fafc',
                  fontSize: '0.92rem',
                  lineHeight: 1.5,
                  boxShadow: '0 4px 15px rgba(0,0,0,0.2)',
                }}
              >
                {/* Media attachments inside user message */}
                {msg.media_attachments && msg.media_attachments.length > 0 && (
                  <div style={{ marginBottom: '10px', display: 'flex', flexWrap: 'wrap', gap: '8px' }}>
                    {msg.media_attachments.map((media) => (
                      <div
                        key={media.id}
                        style={{
                          background: 'rgba(15, 23, 42, 0.8)',
                          borderRadius: '8px',
                          overflow: 'hidden',
                          border: '1px solid rgba(255,255,255,0.1)',
                          maxWidth: '240px',
                        }}
                      >
                        {media.media_type === 'image' && (
                          <img
                            src={media.file_url}
                            alt="Vehicle Inspection Media"
                            style={{ width: '100%', maxHeight: '160px', objectFit: 'cover' }}
                          />
                        )}
                        {media.media_type === 'audio' && (
                          <div style={{ padding: '8px' }}>
                            <div style={{ fontSize: '0.72rem', color: '#38bdf8', marginBottom: '4px', display: 'flex', alignItems: 'center', gap: '4px' }}>
                              <Volume2 size={12} /> Engine Sound Clip
                            </div>
                            <audio controls src={media.file_url} style={{ width: '100%', height: '32px' }} />
                          </div>
                        )}
                        {media.media_type === 'video' && (
                          <video
                            controls
                            src={media.file_url}
                            style={{ width: '100%', maxHeight: '180px' }}
                          />
                        )}
                      </div>
                    ))}
                  </div>
                )}

                {/* Text Content with Markdown Formatting */}
                <FormattedContent text={msg.content} />

                {/* Embedded Diagnosis Card if available */}
                {msg.diagnosis && (
                  <DiagnosisCard
                    diagnosis={msg.diagnosis}
                    onBookClick={onBookClick}
                  />
                )}
              </div>
            </div>

            {/* Quick action chips if offered by mechanic */}
            {msg.sender === 'mechanic' && msg.quick_replies && msg.quick_replies.length > 0 && (
              <div
                style={{
                  display: 'flex',
                  flexWrap: 'wrap',
                  gap: '8px',
                  marginTop: '10px',
                  marginLeft: '40px',
                }}
              >
                {msg.quick_replies.map((chip, idx) => (
                  <button
                    key={idx}
                    onClick={() => handleSend(chip)}
                    className="btn-secondary"
                    style={{
                      fontSize: '0.78rem',
                      padding: '6px 12px',
                      borderRadius: '9999px',
                      background: 'rgba(245, 158, 11, 0.08)',
                      borderColor: 'rgba(245, 158, 11, 0.25)',
                      color: '#fde68a',
                    }}
                  >
                    {chip}
                  </button>
                ))}
              </div>
            )}
          </div>
        ))}

        {/* Typing indicator */}
        {isLoading && (
          <div
            className="animate-slide-up"
            style={{ display: 'flex', alignItems: 'center', gap: '10px', marginLeft: '40px' }}
          >
            <div
              style={{
                background: 'rgba(30, 41, 59, 0.75)',
                padding: '10px 16px',
                borderRadius: '12px',
                border: '1px solid rgba(255, 255, 255, 0.08)',
                color: 'var(--amber-primary)',
                fontSize: '0.82rem',
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
              }}
            >
              <Wrench size={14} className="pulse-indicator" />
              Marcus is analyzing telemetry & mechanical symptoms...
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Pending Media Previews before Sending */}
      {pendingMedia.length > 0 && (
        <div
          style={{
            padding: '8px 20px',
            background: 'rgba(15, 23, 42, 0.95)',
            borderTop: '1px solid var(--border-subtle)',
            display: 'flex',
            gap: '10px',
            overflowX: 'auto',
          }}
        >
          {pendingMedia.map((m) => (
            <div
              key={m.id}
              style={{
                position: 'relative',
                background: 'rgba(30, 41, 59, 0.9)',
                border: '1px solid var(--border-active)',
                borderRadius: '8px',
                padding: '6px 10px',
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
                fontSize: '0.78rem',
              }}
            >
              <span>{m.media_type.toUpperCase()}: {m.file_name || 'Attached'}</span>
              <button
                type="button"
                onClick={() => removePendingMedia(m.id)}
                style={{
                  background: 'transparent',
                  border: 'none',
                  color: '#f87171',
                  cursor: 'pointer',
                }}
              >
                ✕
              </button>
            </div>
          ))}
        </div>
      )}

      {/* Error Banner */}
      {errorMsg && (
        <div
          style={{
            background: 'rgba(239, 68, 68, 0.2)',
            borderTop: '1px solid rgba(239, 68, 68, 0.4)',
            padding: '8px 20px',
            color: '#fca5a5',
            fontSize: '0.82rem',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
          }}
        >
          <span>{errorMsg}</span>
          <button
            onClick={() => setErrorMsg(null)}
            style={{ background: 'transparent', border: 'none', color: '#fca5a5', cursor: 'pointer' }}
          >
            ✕
          </button>
        </div>
      )}

      {/* Responsive Input Bar */}
      <div className="chat-input-container">
        {/* Media Uploader button group */}
        <MediaUploader
          sessionId={sessionId}
          onMediaUploaded={handleMediaUploaded}
          disabled={isLoading}
        />

        {/* Text Area with min-width: 0 protection */}
        <div className="chat-textarea-wrapper">
          <textarea
            ref={textareaRef}
            rows={1}
            value={inputText}
            onChange={(e) => setInputText(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Describe car symptom, light, or noise..."
            className="chat-textarea-field"
            aria-label="Vehicle symptom description input"
          />
        </div>

        {/* Send Button */}
        <button
          type="button"
          onClick={() => handleSend()}
          disabled={isLoading || (!inputText.trim() && pendingMedia.length === 0)}
          className="btn-primary chat-send-btn"
          id="btn-send-chat"
          aria-label="Send message to mechanic"
        >
          <Send size={18} />
        </button>
      </div>
    </div>
  );
};
