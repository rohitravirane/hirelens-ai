# HireLens AI - Setup & Run Guide

## ✅ Project Status: READY

सभी modules complete हैं और project run करने के लिए ready है।

## 📋 Prerequisites

1. **Docker & Docker Compose** (Recommended)
   - Download: https://www.docker.com/products/docker-desktop
   - Verify: `docker --version` और `docker-compose --version`

2. **Python 3.11+** (Optional - for local development)
3. **Node.js 18+** (Optional - for frontend development)
4. **OpenAI API Key** (AI features के लिए)

## 🚀 Step-by-Step Setup

### Step 1: Environment Variables Setup

```bash
# Project root में .env file बनाएं
cp .env.example .env
```

`.env` file में ये values set करें:

```env
# Required: OpenAI API Key
OPENAI_API_KEY=your-openai-api-key-here

# Optional: Secret Key (32+ characters)
SECRET_KEY=your-secret-key-min-32-characters-long

# Database (Docker Compose के लिए auto-set है)
DATABASE_URL=postgresql://hirelens_user:hirelens_pass@postgres:5432/hirelens_db

# Redis (Docker Compose के लिए auto-set है)
REDIS_URL=redis://redis:6379/0
```

### Step 2: Start Services with Docker Compose

```bash
# Project root directory में
cd D:\hirelens-ai

# सभी services start करें
docker-compose up -d

# Services status check करें
docker-compose ps
```

यह start करेगा:
- ✅ PostgreSQL database
- ✅ Redis cache
- ✅ Backend API (FastAPI)
- ✅ Celery workers (async tasks)
- ✅ Frontend (Next.js)

### Step 3: Database Initialization

```bash
# Database tables create करें और admin user बनाएं
docker-compose exec backend python backend/scripts/init_db.py
```

यह create करेगा:
- ✅ Database tables
- ✅ Default roles (admin, recruiter, hiring_manager)
- ✅ Admin user: `rohitravikantrane@gmail.com` / `admin123`

### Step 4: Verify Services

```bash
# सभी services check करें
docker-compose logs backend
docker-compose logs frontend
docker-compose logs celery-worker
```

### Step 5: Access Application

1. **Frontend Dashboard**: http://localhost:3000
2. **Backend API**: http://localhost:8000
3. **API Documentation**: http://localhost:8000/api/docs
4. **ReDoc**: http://localhost:8000/api/redoc

### Step 6: Login

- **Email**: rohitravikantrane@gmail.com
- **Password**: admin123

## 🧪 Test the Application

### 1. Create a Job Description

```bash
# API के through
curl -X POST http://localhost:8000/api/v1/jobs/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Senior Backend Engineer",
    "company": "Tech Corp",
    "raw_text": "We need a senior backend engineer with Python, FastAPI, PostgreSQL experience..."
  }'
```

या Frontend dashboard से job create करें।

### 2. Upload a Resume

Frontend dashboard से resume upload करें (PDF/DOCX)।

### 3. Match Candidates

Dashboard में job select करें और candidate rankings देखें।

## 🛠️ Development Mode

### Backend (Local)

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# .env file setup करें
export DATABASE_URL=postgresql://hirelens_user:hirelens_pass@localhost:5432/hirelens_db
export REDIS_URL=redis://localhost:6379/0
export OPENAI_API_KEY=your-key

# Run server
uvicorn app.main:app --reload
```

### Frontend (Local)

```bash
cd frontend
npm install
npm run dev
```

## 📊 Services Overview

| Service | Port | Purpose |
|---------|------|---------|
| Frontend | 3000 | Next.js Dashboard |
| Backend API | 8000 | FastAPI REST API |
| PostgreSQL | 5432 | Database |
| Redis | 6379 | Cache & Message Queue |

## 🔍 Troubleshooting

### Issue: Services not starting

```bash
# Logs check करें
docker-compose logs

# Services restart करें
docker-compose restart
```

### Issue: Database connection error

```bash
# Database health check
docker-compose exec postgres pg_isready -U hirelens_user

# Database reset (⚠️ data loss)
docker-compose down -v
docker-compose up -d
docker-compose exec backend python backend/scripts/init_db.py
```

### Issue: Frontend not loading

```bash
# Frontend rebuild
docker-compose up -d --build frontend
```

### Issue: Celery workers not working

```bash
# Celery logs
docker-compose logs celery-worker

# Restart workers
docker-compose restart celery-worker
```

## 🎯 Next Steps

Project successfully run होने के बाद, हम next level features add करेंगे:

1. ✅ **Current**: Basic matching & scoring
2. 🔜 **Next**: Advanced features (see below)

## 📝 Notes

- First time setup में Docker images download होने में time लग सकता है
- OpenAI API key required है AI explanations के लिए
- Production में password change करना जरूरी है

---

**Ready to run!** 🚀

