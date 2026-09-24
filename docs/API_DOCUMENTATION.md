# Instant Mechanic — REST API Documentation

Base URL: `http://localhost:8000/api` (Local) or `https://<your-render-app>.onrender.com/api` (Production)  
Interactive OpenAPI Swagger Docs: `/api/docs/`  
OpenAPI Schema JSON: `/api/schema/`

---

## Table of Contents
1. [POST /api/chat/](#1-post-apichat)
2. [POST /api/upload/](#2-post-apiupload)
3. [POST /api/diagnosis/](#3-post-apidiagnosis)
4. [POST /api/booking/](#4-post-apibooking)
5. [GET /api/booking/{id}/](#5-get-apibookingid)
6. [GET /api/chat/history/{session_id}/](#6-get-apichathistorysession_id)
7. [GET /api/health/](#7-get-apihealth)

---

## 1. POST /api/chat/

The primary conversational mechanic endpoint. Analyzes user queries, processes automotive domain guardrails, performs slot-filling follow-ups, and formulates diagnostic cards.

### Request Body (`application/json`)
```json
{
  "session_id": "c9bf9e57-1685-4c89-bafb-ff5af830be8a", // Optional UUID. If omitted, new session is created.
  "message": "My 2018 Honda Civic makes a loud grinding noise when I apply brakes.",
  "media_ids": [1] // Optional array of uploaded media IDs
}
```

### Response (`200 OK`)
```json
{
  "session_id": "c9bf9e57-1685-4c89-bafb-ff5af830be8a",
  "reply": "Based on my garage inspection of the symptoms for your 2018 Honda Civic, I have generated your diagnostic report: Worn Brake Pads & Rotor Scoring...",
  "is_off_topic": false,
  "intent_type": "diagnosis",
  "stage": "diagnosed",
  "diagnosis_ready": true,
  "ai_invoked": false,
  "quick_replies": [
    "Book Certified Mechanic",
    "What tools do I need?",
    "Can I drive it safely?"
  ],
  "diagnosis": {
    "id": 1,
    "primary_issue": "Worn Brake Pads & Rotor Scoring",
    "severity": "moderate",
    "confidence_score": 0.9,
    "symptoms": [
      "High-pitched metallic screech or squeal when applying foot brake",
      "Harsh metallic grinding sensation through the brake pedal on hard stops"
    ],
    "possible_causes": [
      "Brake friction material worn down to the acoustic metal wear indicator tab (< 3mm)",
      "Brake pad backing plate grinding metal-on-metal directly into the brake rotor"
    ],
    "recommended_repairs": [
      "Front/Rear ceramic brake pad replacement ($150 - $250 per axle)",
      "Brake rotor resurfacing or replacement ($120 - $240 per pair)"
    ],
    "estimated_cost_min": "180.00",
    "estimated_cost_max": "420.00",
    "diy_friendly": false,
    "summary_notes": "The acoustic wear tab is designed to screech to alert you before damaging the brake rotors...",
    "ai_generated": false,
    "vehicle_summary": "2018 Honda Civic"
  }
}
```

---

## 2. POST /api/upload/

Uploads vehicle inspection media (photo of warning light/undercarriage, audio recording of engine knock, or video clip).

### Request (`multipart/form-data`)
- `file`: Binary file (JPEG, PNG, MP3, WAV, M4A, MP4, WEBM; Max: 25MB)
- `session_id`: (Optional) UUID string
- `notes`: (Optional) String description

### Response (`201 Created`)
```json
{
  "id": 1,
  "session": "c9bf9e57-1685-4c89-bafb-ff5af830be8a",
  "file": "/media/uploads/2026/09/23/brake_pad.jpg",
  "file_url": "http://localhost:8000/media/uploads/2026/09/23/brake_pad.jpg",
  "media_type": "image",
  "file_name": "brake_pad.jpg",
  "file_size": 42100,
  "analysis_summary": "[Mechanic Visual Analysis]: Inspected uploaded vehicle image. Component surfaces display typical thermal wear...",
  "created_at": "2026-09-23T18:15:00Z"
}
```

---

## 3. POST /api/diagnosis/

Forces the generation or retrieval of a formal diagnostic work order for a session.

### Request Body (`application/json`)
```json
{
  "session_id": "c9bf9e57-1685-4c89-bafb-ff5af830be8a"
}
```

### Response (`200 OK`)
Returns the complete `Diagnosis` object with severity, cost breakdown, and recommended services.

---

## 4. POST /api/booking/

Creates a confirmed service appointment linked to a diagnosis.

### Request Body (`application/json`)
```json
{
  "diagnosis_id": 1,
  "customer_name": "Alex Parker",
  "customer_email": "alex@example.com",
  "customer_phone": "+1-555-019-2834",
  "scheduled_date": "2026-10-05",
  "scheduled_time": "10:00:00",
  "service_type": "Mobile Mechanic (On-Site Repair)",
  "notes": "Parked in driveway on left side."
}
```

### Response (`201 Created`)
```json
{
  "id": 1,
  "booking_reference": "MECH-84920",
  "diagnosis": 1,
  "customer_name": "Alex Parker",
  "customer_email": "alex@example.com",
  "customer_phone": "+1-555-019-2834",
  "scheduled_date": "2026-10-05",
  "scheduled_time": "10:00:00",
  "service_type": "Mobile Mechanic (On-Site Repair)",
  "mechanic_name": "Marcus Vance (Master Automotive Technician)",
  "status": "confirmed",
  "notes": "Parked in driveway on left side.",
  "created_at": "2026-09-23T18:20:00Z"
}
```

---

## 5. GET /api/booking/{id}/

Retrieves a booking record by numeric primary key (`id`) **OR** alphanumeric booking reference (e.g., `MECH-84920`).

### Request Example
```bash
curl http://localhost:8000/api/booking/MECH-84920/
```

### Response (`200 OK`)
```json
{
  "id": 1,
  "booking_reference": "MECH-84920",
  "diagnosis": 1,
  "diagnosis_details": {
    "primary_issue": "Worn Brake Pads & Rotor Scoring",
    "severity": "moderate",
    "estimated_cost_min": "180.00",
    "estimated_cost_max": "420.00"
  },
  "customer_name": "Alex Parker",
  "customer_email": "alex@example.com",
  "customer_phone": "+1-555-019-2834",
  "scheduled_date": "2026-10-05",
  "scheduled_time": "10:00:00",
  "service_type": "Mobile Mechanic (On-Site Repair)",
  "mechanic_name": "Marcus Vance (Master Automotive Technician)",
  "status": "confirmed"
}
```

---

## 6. GET /api/chat/history/{session_id}/

Retrieves full conversation transcript, media attachments, and diagnostic status for restoring a chat session.

---

## 7. GET /api/health/

Health check endpoint for Render, Modal, or Uptime monitors.

### Response (`200 OK`)
```json
{
  "status": "healthy",
  "service": "Instant Mechanic Backend API",
  "version": "1.0.0",
  "gemini_configured": true
}
```
