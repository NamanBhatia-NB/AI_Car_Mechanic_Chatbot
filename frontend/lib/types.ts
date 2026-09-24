export type Severity = 'low' | 'moderate' | 'critical';

export interface Diagnosis {
  id: number;
  session: string;
  primary_issue: string;
  severity: Severity;
  confidence_score: number;
  symptoms: string[];
  possible_causes: string[];
  recommended_repairs: string[];
  estimated_cost_min: number | string;
  estimated_cost_max: number | string;
  diy_friendly: boolean;
  summary_notes: string;
  ai_generated: boolean;
  vehicle_summary?: string;
  created_at: string;
}

export interface MediaAttachment {
  id: number;
  session: string | null;
  file: string;
  file_url: string;
  media_type: 'image' | 'audio' | 'video' | 'other';
  file_name: string;
  file_size: number;
  analysis_summary: string;
  created_at: string;
}

export interface ChatMessage {
  id: string | number;
  sender: 'user' | 'mechanic' | 'system';
  content: string;
  ai_invoked: boolean;
  created_at?: string;
  media_attachments?: MediaAttachment[];
  diagnosis?: Diagnosis;
  quick_replies?: string[];
  is_off_topic?: boolean;
}

export interface ChatResponse {
  session_id: string;
  reply: string;
  is_off_topic: boolean;
  intent_type: string;
  stage: string;
  diagnosis_ready: boolean;
  ai_invoked: boolean;
  quick_replies: string[];
  diagnosis?: Diagnosis | null;
}

export interface Booking {
  id: number;
  booking_reference: string;
  diagnosis: number;
  diagnosis_details?: Diagnosis;
  customer_name: string;
  customer_email: string;
  customer_phone: string;
  scheduled_date: string;
  scheduled_time: string;
  service_type: string;
  mechanic_name: string;
  status: 'pending' | 'confirmed' | 'in_progress' | 'completed' | 'cancelled';
  notes: string;
  created_at: string;
}

export interface BookingRequest {
  diagnosis_id: number;
  customer_name: string;
  customer_email: string;
  customer_phone: string;
  scheduled_date: string;
  scheduled_time: string;
  service_type: string;
  notes?: string;
}
