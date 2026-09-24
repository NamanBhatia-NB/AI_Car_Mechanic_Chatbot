import React, { useRef, useState } from 'react';
import { Camera, Mic, Film, X, UploadCloud, CheckCircle } from 'lucide-react';
import { uploadMedia } from '../lib/api';
import { MediaAttachment } from '../lib/types';

interface MediaUploaderProps {
  sessionId: string | null;
  onMediaUploaded: (attachment: MediaAttachment) => void;
  disabled?: boolean;
}

export const MediaUploader: React.FC<MediaUploaderProps> = ({
  sessionId,
  onMediaUploaded,
  disabled
}) => {
  const [isUploading, setIsUploading] = useState(false);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [isRecording, setIsRecording] = useState(false);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);

  const fileInputRef = useRef<HTMLInputElement>(null);
  const [acceptType, setAcceptType] = useState<string>('image/*,audio/*,video/*');

  const handleFileSelect = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    await processUpload(file);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  const processUpload = async (file: File) => {
    setIsUploading(true);
    setUploadError(null);

    try {
      const attachment = await uploadMedia(file, sessionId);
      onMediaUploaded(attachment);
    } catch (err: any) {
      setUploadError(err.message || 'Media upload failed.');
      setTimeout(() => setUploadError(null), 4000);
    } finally {
      setIsUploading(false);
    }
  };

  const triggerUpload = (accept: string) => {
    setAcceptType(accept);
    setTimeout(() => {
      fileInputRef.current?.click();
    }, 50);
  };

  // Browser Audio Sound Recorder for engine rattles
  const toggleAudioRecording = async () => {
    if (isRecording) {
      // Stop recording
      if (mediaRecorderRef.current) {
        mediaRecorderRef.current.stop();
        setIsRecording(false);
      }
    } else {
      // Start recording
      try {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        audioChunksRef.current = [];
        const recorder = new MediaRecorder(stream);
        mediaRecorderRef.current = recorder;

        recorder.ondataavailable = (event) => {
          if (event.data.size > 0) {
            audioChunksRef.current.push(event.data);
          }
        };

        recorder.onstop = async () => {
          const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/webm' });
          const audioFile = new File([audioBlob], `engine_sound_${Date.now()}.webm`, {
            type: 'audio/webm',
          });
          stream.getTracks().forEach((track) => track.stop());
          await processUpload(audioFile);
        };

        recorder.start();
        setIsRecording(true);
      } catch (err) {
        setUploadError('Microphone permission required to record engine audio.');
        setTimeout(() => setUploadError(null), 4000);
      }
    }
  };

  return (
    <div style={{ position: 'relative' }}>
      <input
        type="file"
        ref={fileInputRef}
        onChange={handleFileSelect}
        accept={acceptType}
        style={{ display: 'none' }}
      />

      <div className="chat-media-group">
        {/* Photo Button */}
        <button
          type="button"
          onClick={() => triggerUpload('image/*')}
          disabled={disabled || isUploading}
          className="media-upload-btn"
          title="Upload photo of dashboard light, leaking fluid, or worn brake pads"
          aria-label="Upload photo"
        >
          <Camera size={16} color="var(--amber-primary)" />
          <span className="media-btn-label">Photo</span>
        </button>

        {/* Audio / Engine Sound Recorder */}
        <button
          type="button"
          onClick={toggleAudioRecording}
          disabled={disabled || isUploading}
          className="media-upload-btn"
          style={{
            background: isRecording ? 'rgba(239, 68, 68, 0.25)' : undefined,
            borderColor: isRecording ? '#ef4444' : undefined,
            color: isRecording ? '#fca5a5' : undefined,
          }}
          title="Record or upload engine knocking, squealing, or ticking audio"
          aria-label="Record or upload engine audio"
        >
          <Mic size={16} color={isRecording ? '#ef4444' : '#22d3ee'} className={isRecording ? 'pulse-indicator' : ''} />
          <span className="media-btn-label">{isRecording ? 'Stop' : 'Audio'}</span>
        </button>

        {/* Video Button */}
        <button
          type="button"
          onClick={() => triggerUpload('video/*')}
          disabled={disabled || isUploading}
          className="media-upload-btn"
          title="Upload video clip of exhaust smoke, rattling component, or engine shudder"
          aria-label="Upload video"
        >
          <Film size={16} color="#a78bfa" />
          <span className="media-btn-label">Video</span>
        </button>
      </div>

      {/* Uploading progress or error pill */}
      {isUploading && (
        <div
          style={{
            position: 'absolute',
            bottom: '45px',
            left: '0',
            background: 'rgba(15, 23, 42, 0.95)',
            border: '1px solid var(--amber-primary)',
            borderRadius: '8px',
            padding: '6px 12px',
            fontSize: '0.78rem',
            color: 'var(--amber-primary)',
            display: 'flex',
            alignItems: 'center',
            gap: '6px',
            boxShadow: '0 4px 15px rgba(0,0,0,0.5)',
            zIndex: 10
          }}
        >
          <UploadCloud size={14} className="pulse-indicator" />
          Uploading & analyzing media...
        </div>
      )}

      {uploadError && (
        <div
          style={{
            position: 'absolute',
            bottom: '45px',
            left: '0',
            background: 'rgba(239, 68, 68, 0.95)',
            borderRadius: '8px',
            padding: '6px 12px',
            fontSize: '0.78rem',
            color: '#fff',
            zIndex: 10
          }}
        >
          {uploadError}
        </div>
      )}
    </div>
  );
};
