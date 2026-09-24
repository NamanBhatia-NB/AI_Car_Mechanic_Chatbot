import { ChatResponse, MediaAttachment, Diagnosis, Booking, BookingRequest } from './types';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api';

export async function sendMessage(
  sessionId: string | null,
  message: string,
  mediaIds: number[] = []
): Promise<ChatResponse> {
  const payload = {
    session_id: sessionId || undefined,
    message,
    media_ids: mediaIds,
  };

  const response = await fetch(`${API_BASE_URL}/chat/`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.error || errorData.detail || `Server responded with ${response.status}`);
  }

  return response.json();
}

export async function uploadMedia(
  file: File,
  sessionId?: string | null,
  notes?: string
): Promise<MediaAttachment> {
  const formData = new FormData();
  formData.append('file', file);
  if (sessionId) {
    formData.append('session_id', sessionId);
  }
  if (notes) {
    formData.append('notes', notes);
  }

  const response = await fetch(`${API_BASE_URL}/upload/`, {
    method: 'POST',
    body: formData,
  });

  if (!response.ok) {
    const err = await response.json().catch(() => ({}));
    throw new Error(err.error || `Upload failed with status ${response.status}`);
  }

  return response.json();
}

export async function fetchDiagnosis(sessionId: string): Promise<Diagnosis> {
  const response = await fetch(`${API_BASE_URL}/diagnosis/`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ session_id: sessionId }),
  });

  if (!response.ok) {
    throw new Error(`Failed to load diagnosis: ${response.statusText}`);
  }

  return response.json();
}

export async function createBooking(data: BookingRequest): Promise<Booking> {
  const response = await fetch(`${API_BASE_URL}/booking/`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });

  if (!response.ok) {
    const err = await response.json().catch(() => ({}));
    throw new Error(err.error || err.detail || 'Failed to confirm booking.');
  }

  return response.json();
}

export async function fetchBooking(idOrReference: string): Promise<Booking> {
  const response = await fetch(`${API_BASE_URL}/booking/${encodeURIComponent(idOrReference)}/`);
  if (!response.ok) {
    throw new Error(`Booking '${idOrReference}' not found.`);
  }
  return response.json();
}

export async function fetchAllBookings(): Promise<{ count: number; bookings: Booking[]; admin_dashboard_url: string }> {
  const response = await fetch(`${API_BASE_URL}/booking/`, { cache: 'no-store' });
  if (!response.ok) {
    throw new Error('Failed to load bookings list.');
  }
  return response.json();
}

export async function fetchSessionHistory(sessionId: string): Promise<any> {
  const response = await fetch(`${API_BASE_URL}/chat/history/${sessionId}/`);
  if (!response.ok) {
    throw new Error(`Failed to fetch session history.`);
  }
  return response.json();
}

export async function checkBackendHealth(): Promise<{ status: string; gemini_configured: boolean }> {
  try {
    const response = await fetch(`${API_BASE_URL}/health/`, { cache: 'no-store' });
    if (!response.ok) return { status: 'down', gemini_configured: false };
    return await response.json();
  } catch (e) {
    return { status: 'offline', gemini_configured: false };
  }
}
