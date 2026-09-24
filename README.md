# Instant Mechanic — AI Car Mechanic Chatbot & Mobile Dispatch

An enterprise-grade, full-stack automotive diagnostic chatbot where vehicle owners can consult a virtual Senior Master Technician (**Marcus Vance**) for troubleshooting, multimodal symptom analysis (photos, engine sound recordings, video clips), and instant mechanic appointment booking.

Built with **Next.js (React)**, **Python + Django REST Framework**, **SQLite**, and **Google Gemini 1.5 Flash Multimodal AI**, engineered with a **zero-cost rule-based guardrail and diagnostic layer** to minimize unnecessary AI/API usage.

---

## 🏆 Evaluation Focus: How We Minimize Unnecessary AI Usage

The assignment explicitly evaluates:
> *"How effectively the candidate minimizes unnecessary AI usage and uses traditional backend logic wherever possible."*

Our architecture implements a **Multi-Tiered Request Pipeline**:

```
[User Request]
       │
       ▼
[Tier 0: Domain Guardrails (Cost: $0.00 | Time: < 1ms)]
       │ ──► Off-Topic Filter: Instantly rejects non-automotive queries (politics, cooking, coding)
       │ ──► Greeting & FAQ Cache: Returns immediate mechanic welcome at zero cost
       ▼
[Tier 1: State Machine & Slot-Filling (Cost: $0.00 | Time: < 2ms)]
       │ ──► Extracts Vehicle Info: Make, Model, Year, Mileage via regex/dictionary
       │ ──► Technician Follow-Ups: Prompts user for operating conditions (braking vs cold start)
       ▼
[Tier 2: Classic Symptom Knowledge Base (Cost: $0.00 | Time: < 5ms)]
       │ ──► Resolves 40+ classic failure patterns (battery clicks, squealing pads, coolant steam)
       │ ──► Generates complete diagnosis, parts price ranges, and severity without LLMs
       ▼
[Tier 3: Gemini 1.5 Flash Multimodal AI (Free Tier API)]
       │ ──► Invoked ONLY for uploaded media analysis (photos, engine sound audio, video)
       │     or ambiguous multi-symptom synthesis.
```

### Transparent Cost Savings Indicator
Every response from the mechanic includes an `ai_invoked` boolean metric. The frontend renders a live badge on each message:
- `⚡ 0ms Engine • 0 AI Cost` for Tier 0–2 deterministic answers.
- `✨ Gemini Multimodal AI` for Tier 3 media/deep synthesis.

---

## 🛠 Tech Stack

- **Frontend**: Next.js 14 (App Router), TypeScript, Vanilla CSS design tokens (modern dark garage aesthetic, glassmorphism, micro-animations), Lucide Icons, Canvas Confetti.
- **Backend**: Python 3.11+, Django 5, Django REST Framework, WhiteNoise, Gunicorn, drf-spectacular (OpenAPI Swagger).
- **Database**: SQLite (zero-configuration, embedded relational store).
- **AI Engine**: Google Gemini 1.5 Flash (via free API key).
- **Hosting (100% Free)**:
  - Frontend: **Vercel Free Tier**
  - Backend: **Render Free Tier** / **Railway** / **Modal**

---

## 🚀 REST API Specification

| Method | Endpoint | Description | AI Cost |
|---|---|---|---|
| `POST` | `/api/chat/` | Conversational diagnostic mechanic (processes text & media) | Tier 0-2: **$0.00** / Tier 3: Gemini |
| `POST` | `/api/upload/` | Upload photo (leak/warning light), audio (engine knock), or video | Free Tier Gemini Vision/Audio |
| `POST` | `/api/diagnosis/` | Generate or fetch structured diagnostic work order | Tier 2: **$0.00** / Tier 3: Gemini |
| `POST` | `/api/booking/` | Book certified mechanic appointment after diagnosis | **$0.00** (Traditional Backend) |
| `GET` | `/api/booking/{id}/` | Retrieve appointment status by ID or reference (`MECH-XXXXX`) | **$0.00** (Traditional Backend) |
| `GET` | `/api/chat/history/{session_id}/` | Retrieve complete chat transcript and media attachments | **$0.00** (Traditional Backend) |
| `GET` | `/api/health/` | Health check for hosting monitors | **$0.00** (Traditional Backend) |

Interactive OpenAPI documentation is available live at `http://localhost:8000/api/docs/`.

---

## 💻 Local Quickstart

### Prerequisites
- Python 3.10+
- Node.js 18+ and npm

### 1. Backend Setup
```bash
# Clone the repository
git clone <repo-url>
cd "Instant Mechanic"

# Setup virtual environment
cd backend
python -m venv venv

# Activate venv:
# Windows:
venv\Scripts\activate
# Mac/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run migrations
python manage.py migrate

# (Optional) Add your Gemini free API key in backend/.env:
# GEMINI_API_KEY=your_key_here

# Start backend server
python manage.py runserver 8000
```
Backend API will be running at `http://localhost:8000/api/`  
Swagger docs available at `http://localhost:8000/api/docs/`

### 2. Frontend Setup
In a new terminal window:
```bash
cd "Instant Mechanic/frontend"
npm install
npm run dev
```
Open `http://localhost:3000` in your browser.

---

## 🧪 Running Automated Tests

A comprehensive test suite verifies guardrails, state machine, rule diagnostics, media validation, and booking flows:

```bash
cd backend
python manage.py test api
```

Sample output:
```
Found 7 test(s).
.......
Ran 7 tests in 5.244s
OK
```

---

## 🌐 100% Free Tier Deployment

See [`docs/DEPLOYMENT_GUIDE.md`](./docs/DEPLOYMENT_GUIDE.md) for step-by-step instructions on deploying the frontend to **Vercel** and the backend to **Render Free Tier** or **Modal**.

---

## 📁 Repository Structure

```
Instant Mechanic/
├── backend/
│   ├── manage.py
│   ├── requirements.txt
│   ├── .env.example
│   ├── mechanic_backend/      # Django settings, URLs, WSGI
│   └── api/
│       ├── models.py          # ChatSession, ChatMessage, MediaAttachment, Diagnosis, Booking
│       ├── serializers.py     # DRF serializers & request validation
│       ├── views.py           # REST endpoints
│       ├── services/
│       │   ├── guardrails.py       # Tier 0 automotive domain guardrail
│       │   ├── state_machine.py    # Tier 1 slot-filling & follow-ups
│       │   ├── rule_diagnostics.py # Tier 2 40+ symptom knowledge base
│       │   └── gemini_service.py   # Tier 3 Gemini multimodal client
│       └── tests.py           # Automated test suite
├── frontend/
│   ├── app/
│   │   ├── layout.tsx         # SEO metadata & root layout
│   │   ├── page.tsx           # Main mechanic diagnostic bay
│   │   ├── globals.css        # Modern garage design tokens & animations
│   │   └── bookings/          # Dedicated appointment tracking
│   ├── components/
│   │   ├── ChatInterface.tsx  # Message stream & quick chips
│   │   ├── MediaUploader.tsx  # Photo/audio/video uploader & recorder
│   │   ├── DiagnosisCard.tsx  # Severity badge, cost estimation, & CTA
│   │   ├── BookingModal.tsx   # Appointment scheduler & confirmation
│   │   ├── HistorySidebar.tsx # Session history & status lookup
│   │   └── AIUsageBadge.tsx   # Transparent 0ms engine vs AI badge
│   └── lib/
│       ├── api.ts             # API client with error handling
│       └── types.ts           # TypeScript interfaces
├── docs/
│   ├── ARCHITECTURE.md        # AI minimization architecture deep dive
│   ├── API_DOCUMENTATION.md   # Complete REST endpoint specifications
│   └── DEPLOYMENT_GUIDE.md    # Free-tier Vercel, Render & Modal setup
└── README.md
```
