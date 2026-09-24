# Instant Mechanic — Architecture & Design Rationale

This document details the system architecture of the **AI Car Mechanic Chatbot**, with a specific focus on the engineering choices made to **minimize unnecessary AI API usage** and maximize responsiveness and cost-efficiency.

---

## 1. High-Level Architecture

The platform follows a decoupled client-server architecture:
- **Frontend**: Next.js 14 App Router, built with modern Vanilla CSS, glassmorphism, responsive mobile-first mechanics bay UI, and deployable on the **Vercel Free Tier**.
- **Backend**: Python + Django 5 + Django REST Framework (DRF), backed by SQLite, deployable on **Render Free Tier**, **Railway**, or serverless **Modal**.
- **AI Engine**: Google Gemini 1.5 Flash Multimodal API, protected behind a 4-tier filtering hierarchy.

```
+-------------------------------------------------------------------------+
|                         Next.js Frontend (Vercel)                       |
|   - Chat Interface  - Photo/Audio/Video Uploader  - Diagnostic Cards    |
|   - Booking Modal   - Real-Time AI Usage Indicator - Records Drawer     |
+------------------------------------+------------------------------------+
                                     |  REST HTTP / JSON & Multipart
                                     v
+------------------------------------+------------------------------------+
|                    Django REST Framework (Render / Modal)               |
|                                                                         |
|  +-------------------------------------------------------------------+  |
|  |                 4-Tier Diagnostic Request Router                  |  |
|  |                                                                   |  |
|  | [Tier 0: Domain Guardrails]                                       |  |
|  |   - Regex & Automotive Ontology Check                             |  |
|  |   - Instant Off-Topic Rejection (Cost: $0.00, Time: < 1ms)        |  |
|  |   - Greeting & FAQ Caching (Cost: $0.00, Time: < 1ms)             |  |
|  |                                                                   |  |
|  | [Tier 1: State Machine & Slot-Filling]                            |  |
|  |   - Tracks Vehicle Context (Year, Make, Model, Mileage)           |  |
|  |   - Generates Targeted Technician Follow-Up Questions ($0.00)     |  |
|  |                                                                   |  |
|  | [Tier 2: Classic Symptom Knowledge Base]                         |  |
|  |   - 40+ Pre-indexed Automotive Mechanical Failure Trees           |  |
|  |   - Generates Full Diagnosis, Costs, & Repairs ($0.00)            |  |
|  |                                                                   |  |
|  | [Tier 3: Gemini Multimodal Flash Engine]                          |  |
|  |   - Invoked ONLY when media is attached or complex synthesis      |  |
|  |   - Image Analysis (Warning lights, brake wear, leaks)            |  |
|  |   - Audio Spectrum Inspection (Knocks, squeals, valve ticks)      |  |
|  +---------------------------------+---------------------------------+  |
|                                    |                                    |
|                                    v                                    |
|  +---------------------------------+---------------------------------+  |
|  |                 SQLite Database & Service Layer                   |  |
|  |   - ChatSessions, ChatMessages, MediaAttachments                  |  |
|  |   - Diagnosis Reports, Mechanic Appointments & Bookings           |  |
|  +-------------------------------------------------------------------+  |
+-------------------------------------------------------------------------+
```

---

## 2. AI Minimization & Cost Reduction Strategy

The core evaluation criterion emphasizes:
> *"how effectively the candidate minimizes unnecessary AI usage and uses traditional backend logic wherever possible"*

To achieve this, our system introduces a **Strict 4-Tier Hierarchy**:

| Tier | Component | AI Cost | Latency | Responsibility |
|---|---|---|---|---|
| **Tier 0** | **Domain Guardrails** | **$0.00** | **< 1ms** | Rejects non-automotive queries (e.g. recipes, coding, politics) and handles greetings deterministically. |
| **Tier 1** | **State Machine** | **$0.00** | **< 2ms** | Slot-fills vehicle make, model, year, and operating conditions before jumping to conclusions. |
| **Tier 2** | **Rule Diagnostic Engine** | **$0.00** | **< 5ms** | Resolves classic symptoms (battery clicks, squealing brakes, coolant steam, wheel wobble) without external API calls. |
| **Tier 3** | **Gemini 1.5 Flash** | **Free Tier** | **~800ms** | Multimodal analysis (photos, audio files of engine knocks, video) or complex multi-symptom synthesis. |

### Why This Approach Excels
1. **Zero LLM spend on chit-chat & off-topic questions**: Off-topic prompts do not consume a single token.
2. **Technician Realism**: Real master technicians don't guess an issue on the first sentence; they ask targeted clarifying questions first.
3. **Deterministic Reliability**: Frequent mechanical problems receive verified diagnostic cost ranges, avoiding LLM hallucinations.
4. **Transparent Auditing**: Every mechanic message in the API returns `ai_invoked: boolean`, allowing the frontend to badge messages as `"0ms Engine • 0 AI Cost"` vs `"Gemini Multimodal AI"`.

---

## 3. Database Schema (SQLite)

- **`ChatSession`**: Stores vehicle metadata (`car_make`, `car_model`, `car_year`, `mileage`) and tracks session stage (`initial` -> `gathering_info` -> `diagnosed` -> `booked`).
- **`ChatMessage`**: Logs conversation transcripts, sender (`user`, `mechanic`, `system`), and the `ai_invoked` metric.
- **`MediaAttachment`**: Stores uploaded photos, sound clips, and video files with MIME verification and cached analysis summaries.
- **`Diagnosis`**: Stores the structured diagnostic report: `primary_issue`, `severity` (`low`, `moderate`, `critical`), `confidence_score`, `symptoms`, `possible_causes`, `recommended_repairs`, `estimated_cost_min`, `estimated_cost_max`, and `diy_friendly`.
- **`Booking`**: Stores appointment records linked to a diagnosis with unique reference codes (`MECH-XXXXX`), customer contact details, service schedule, and assigned technician.

---

## 4. Hosting on 100% Free Tiers

- **Frontend**: **Vercel**
  - Zero-config deployment from Git repository.
  - Automatic HTTPS, global CDN edge caching.
- **Backend**: **Render Free Tier** / **Railway** / **Modal**
  - Render provides free web service hosting for Python WSGI/ASGI apps.
  - WhiteNoise serves static files efficiently without external S3/CDN costs.
  - SQLite provides zero-cost persistence for local and single-instance deployments.
