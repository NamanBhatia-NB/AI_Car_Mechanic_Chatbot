# 100% Free Tier Deployment Guide

This guide explains how to deploy both the **Frontend (Next.js)** and **Backend (Django REST Framework)** on **100% free hosting tiers** without requiring AWS or paid subscriptions.

---

## 1. Frontend: Deploy to Vercel (Free Tier)

Vercel provides native, free-tier hosting for Next.js applications with zero configuration.

### Steps:
1. Push this repository to **GitHub**.
2. Sign in to [Vercel.com](https://vercel.com) using your GitHub account.
3. Click **"Add New"** > **"Project"** and select this repository.
4. Set the **Root Directory** to `frontend`.
5. Under **Environment Variables**, add:
   - `NEXT_PUBLIC_API_URL`: Your live backend URL (e.g. `https://instant-mechanic-backend.onrender.com/api` or `http://localhost:8000/api` for local testing).
6. Click **Deploy**.
   - Your live frontend URL will be generated instantly (e.g., `https://instant-mechanic.vercel.app`).

---

## 2. Backend: Deploy to Render (Free Tier)

Render provides free web services for Python applications without requiring a credit card.

### Steps:
1. Sign up at [Render.com](https://render.com).
2. Click **"New +"** > **"Web Service"**.
3. Connect your GitHub repository.
4. Configure the service settings:
   - **Name**: `instant-mechanic-backend`
   - **Root Directory**: `backend`
   - **Environment**: `Python 3`
   - **Region**: Closest to your users (e.g. Oregon or Frankfurt)
   - **Branch**: `main`
   - **Build Command**:
     ```bash
     pip install -r requirements.txt && python manage.py migrate && python manage.py collectstatic --no-input
     ```
   - **Start Command**:
     ```bash
     gunicorn mechanic_backend.wsgi:application
     ```
   - **Instance Type**: **Free**
5. Under **Environment Variables**, add:
   - `DJANGO_SECRET_KEY`: `<generate-a-random-secret-key>`
   - `DJANGO_DEBUG`: `False`
   - `DJANGO_ALLOWED_HOSTS`: `*`
   - `GEMINI_API_KEY`: `<your-free-gemini-api-key-from-google-ai-studio>`
6. Click **Create Web Service**.
   - Render will build and deploy your API. Once ready, you'll receive your live backend URL (e.g. `https://instant-mechanic-backend.onrender.com`).

---

## 3. Alternative Backend: Modal (Serverless Python Free Tier)

Modal provides $30/month in free compute credits with instant cold-starts and serverless Python deployment.

### Steps:
1. Install Modal locally:
   ```bash
   pip install modal
   modal setup
   ```
2. Run or deploy using the included `deploy_modal.py` script:
   ```bash
   modal deploy backend/deploy_modal.py
   ```
3. Set secrets via Modal dashboard:
   - `GEMINI_API_KEY`
   - `DJANGO_SECRET_KEY`

---

## 4. Local Development Quickstart

To run both services locally on your machine:

### Backend:
```bash
cd backend
python -m venv venv
# Windows:
venv\Scripts\activate
# Mac/Linux:
source venv/bin/activate

pip install -r requirements.txt
python manage.py migrate
python manage.py runserver 8000
```
API will be live at `http://localhost:8000/api/` and Swagger docs at `http://localhost:8000/api/docs/`.

### Frontend:
```bash
cd frontend
npm install
npm run dev
```
Frontend will be live at `http://localhost:3000`.
