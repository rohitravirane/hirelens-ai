# HireLens AI

**Production-Grade AI-Powered Hiring Intelligence Platform**

HireLens AI helps recruiters and hiring managers see beyond resumes. The platform uses semantic matching and explainable AI to score and rank candidates, providing transparent, actionable insights for hiring decisions.

## 🎯 Product Vision

HireLens AI is not a demo or tutorial project. It's a **real-world, enterprise-grade** platform designed for production use by recruiters at scale.

### Core Capabilities

- ✅ **Resume Parsing**: Extract structured data from PDF/DOCX resumes
- ✅ **Job Description Intelligence**: Parse and understand job requirements
- ✅ **Semantic Matching**: AI-powered candidate-job matching
- ✅ **Multi-Dimensional Scoring**: Skill match, experience, projects, domain familiarity
- ✅ **Explainable AI**: Human-readable explanations for every match
- ✅ **Candidate Ranking**: Percentile-based ranking with confidence levels
- ✅ **Recruiter Dashboard**: Interactive UI with tabs, modals, and drag-drop features
- ✅ **Job Management**: Create and manage job descriptions with AI-powered parsing
- ✅ **Resume Upload**: Drag-and-drop resume upload with automatic parsing
- ✅ **Candidate Management**: Add and manage candidates with resume linking
- ✅ **Interactive Rankings**: View AI-powered candidate rankings with detailed explanations

## 🏗️ Architecture

### High-Level Overview

```
Frontend (Next.js) → API Gateway (FastAPI) → Services → Database (PostgreSQL) + Cache (Redis)
                                                          ↓
                                                    Celery Workers (Async Tasks)
```

### Architecture Style

- **Phase 1**: Modular Monolith (current)
- **Phase 2**: Microservices-ready (documented)

See [Architecture Documentation](./docs/architecture.md) for detailed architecture.

## 🚀 Quick Start

### Prerequisites

- Docker & Docker Compose
- Python 3.11+ (for local development)
- Node.js 18+ (for frontend development)
- **OpenAI API Key (Optional)** - Only needed if using OpenAI. Hugging Face works locally without API!

### Using Docker Compose (Recommended)

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd hirelens-ai
   ```

2. **Set up environment variables**
   ```bash
   # .env file already exists with default settings
   # Edit .env and configure:
   # - AI_PROVIDER=auto (uses Hugging Face locally, no API costs!)
   # - OPENAI_API_KEY (optional, only if you want to use OpenAI)
   ```

3. **Start services**
   ```bash
   docker-compose up -d
   ```

4. **Initialize database**
   ```bash
   docker-compose exec backend python backend/scripts/init_db.py
   ```

5. **Access the application**
   - Frontend: http://localhost:3000
   - API Docs: http://localhost:8000/api/docs
   - Backend API: http://localhost:8000

### Dashboard Features

The recruiter dashboard includes:

- **Jobs Tab**: View all jobs, create new jobs with AI-powered parsing
- **Candidates Tab**: Upload resumes (drag & drop), add candidates, view candidate list
- **Rankings Tab**: View AI-powered candidate rankings for selected jobs
- **Interactive Modals**: 
  - Job creation form with full job description parsing
  - Resume upload with drag-and-drop support
  - Candidate creation form with resume linking
- **Match All**: Bulk match all candidates to a job with one click
- **AI Explanations**: View detailed AI analysis with strengths, weaknesses, and recommendations

### Default Credentials

- **Email**: rohitravikantrane@gmail.com
- **Password**: admin123

⚠️ **Change these in production!**

## 📁 Project Structure

```
hirelens-ai/
├── backend/
│   ├── app/
│   │   ├── auth/           # Authentication & RBAC
│   │   ├── resumes/        # Resume processing
│   │   ├── jobs/           # Job description intelligence
│   │   ├── candidates/     # Candidate management
│   │   ├── matching/       # Matching & scoring engine
│   │   ├── ai_engine/      # AI reasoning engine
│   │   ├── core/           # Core utilities
│   │   ├── models/         # Database models
│   │   ├── tasks/          # Async Celery tasks
│   │   └── main.py         # FastAPI application
│   ├── scripts/            # Utility scripts
│   ├── requirements.txt    # Python dependencies
│   └── Dockerfile
├── frontend/
│   ├── app/                # Next.js app directory
│   │   ├── dashboard/      # Main dashboard with tabs
│   │   └── login/          # Login page
│   ├── components/         # React components
│   │   ├── JobModal.tsx    # Job creation modal
│   │   ├── ResumeUpload.tsx # Resume upload with drag-drop
│   │   └── CandidateModal.tsx # Candidate creation form
│   ├── lib/                # Utilities
│   ├── hooks/              # React hooks
│   └── package.json
├── docs/
│   ├── architecture.md     # System architecture
│   ├── ai_reasoning.md     # AI explainability
│   └── scaling.md         # Scaling strategy
├── docker-compose.yml      # Docker orchestration
└── README.md
```

## 🔐 Authentication & RBAC

### Roles

- **Admin**: Full system access
- **Recruiter**: Manage jobs, candidates, resumes, view matches
- **Hiring Manager**: Read-only access to insights

### API Authentication

All API endpoints (except `/api/v1/auth/*`) require authentication:

```bash
curl -H "Authorization: Bearer <token>" http://localhost:8000/api/v1/jobs/
```

## 📊 Core Features

### 1. Resume Processing

Upload resumes (PDF/DOCX) and extract:
- Skills
- Experience (years, roles, companies)
- Education
- Projects
- Certifications

**API Example:**
```bash
curl -X POST http://localhost:8000/api/v1/resumes/upload \
  -H "Authorization: Bearer <token>" \
  -F "file=@resume.pdf"
```

### 2. Job Description Intelligence

Create job descriptions and extract:
- Required skills
- Nice-to-have skills
- Experience requirements
- Seniority level
- Education requirements

**API Example:**
```bash
curl -X POST http://localhost:8000/api/v1/jobs/ \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Senior Backend Engineer",
    "company": "Tech Corp",
    "raw_text": "We are looking for a senior backend engineer..."
  }'
```

### 3. AI Matching & Scoring

Match candidates to jobs with:
- **Overall Score** (0-100)
- **Skill Match Score** (40% weight)
- **Experience Score** (25% weight)
- **Project Similarity** (20% weight)
- **Domain Familiarity** (15% weight)

**API Example:**
```bash
curl -X POST "http://localhost:8000/api/v1/matching/match?candidate_id=1&job_id=1" \
  -H "Authorization: Bearer <token>"
```

### 4. Explainable AI

Every match includes:
- **Summary**: Overall assessment
- **Strengths**: 3-5 specific positive points
- **Weaknesses**: 3-5 gaps or concerns
- **Recommendations**: 2-3 actionable items
- **Confidence Level**: High/Medium/Low

See [AI Reasoning Documentation](./docs/ai_reasoning.md) for details.

### 5. Candidate Ranking

Get ranked candidates for a job:

```bash
curl "http://localhost:8000/api/v1/matching/job/1/rankings" \
  -H "Authorization: Bearer <token>"
```

Returns candidates sorted by match score with percentile rankings.

## 🧠 AI Engine

### AI Providers Supported

**1. Hugging Face (Recommended - Free & Local)**
- ✅ **Free** - No API costs
- ✅ **Local** - Runs on your machine/server
- ✅ **Private** - Data never leaves your infrastructure
- ✅ **Works Offline** - No internet required after model download
- Models: Sentence Transformers (embeddings), TinyLlama/Mistral (text generation)

**2. OpenAI (Optional - Paid API)**
- Better quality explanations
- Faster API responses
- Requires API key and internet

### Configuration

In `.env` file:
```env
# Use Hugging Face (Free, Local)
AI_PROVIDER=auto

# Or explicitly use Hugging Face
AI_PROVIDER=huggingface

# Or use OpenAI (requires API key)
AI_PROVIDER=openai
OPENAI_API_KEY=your-key-here
```

### Cost Optimization

- **Hugging Face**: Completely free, runs locally
- **OpenAI**: Aggressive caching (24-hour TTL for embeddings)
- Hash-based cache keys
- Batch processing
- Fallback models when appropriate

## 📈 Scaling Strategy

HireLens AI is designed to scale from 100 to 1 million users:

- **100 users**: Single server, current architecture
- **10k users**: Horizontal scaling, read replicas, Redis cluster
- **1M users**: Microservices, multi-region, distributed database

See [Scaling Documentation](./docs/scaling.md) for detailed strategy.

## 🛠️ Development

### Backend Development

```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# Configure .env file in project root
# Set AI_PROVIDER=auto for Hugging Face (free, local)

# Run migrations
alembic upgrade head

# Initialize database
python scripts/init_db.py

# Run server
uvicorn app.main:app --reload
```

**Note**: First time running with Hugging Face will download models (~100MB-1GB). This happens automatically.

### Frontend Development

```bash
cd frontend
npm install
npm run dev
```

### Running Tests

```bash
# Backend tests
cd backend
pytest

# Frontend tests
cd frontend
npm test
```

## 📚 Documentation

- [Architecture](./docs/architecture.md): System design and architecture
- [AI Reasoning](./docs/ai_reasoning.md): AI explainability and reasoning
- [Scaling Strategy](./docs/scaling.md): Scaling from 100 to 1M users

## 🤖 AI Configuration

### Using Hugging Face (Free, Local - Recommended)

```env
AI_PROVIDER=auto
# or
AI_PROVIDER=huggingface

# Models (auto-downloads on first use)
HUGGINGFACE_EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
HUGGINGFACE_LLM_MODEL=TinyLlama/TinyLlama-1.1B-Chat-v1.0
USE_GPU=false
MODEL_DEVICE=cpu
```

**Benefits:**
- ✅ No API costs
- ✅ 100% local and private
- ✅ Works offline
- ✅ Production ready

### Using OpenAI (Optional - Paid)

```env
AI_PROVIDER=openai
OPENAI_API_KEY=your-api-key-here
```

**Benefits:**
- ✅ Better quality explanations
- ✅ Faster API responses
- ✅ No local model downloads

## 🔒 Security

- JWT-based authentication
- Password hashing with bcrypt
- RBAC at service layer
- Input validation (Pydantic)
- File upload restrictions
- CORS configuration
- Rate limiting
- Audit logging

## 🧪 Testing

### Backend

```bash
cd backend
pytest tests/
```

### Frontend

```bash
cd frontend
npm test
```

## 📊 Monitoring & Observability

- **Structured Logging**: JSON logs with correlation IDs
- **Health Checks**: `/health` endpoint
- **Metrics**: Prometheus-compatible (future)
- **Error Tracking**: Sentry integration (configurable)

## 🚧 Roadmap

### Phase 1 (Current)
- ✅ Core matching engine
- ✅ Explainable AI
- ✅ Recruiter dashboard
- ✅ Basic RBAC

### Phase 2 (Future)
- [ ] Multi-tenant SaaS
- [ ] ATS integrations (Greenhouse, Lever)
- [ ] Bias & fairness analysis
- [ ] Real-time collaboration
- [ ] Candidate feedback engine
- [ ] Advanced analytics
- [ ] Mobile app

## 🤝 Contributing

This is a production-grade system. Contributions should:
- Follow existing code patterns
- Include tests
- Update documentation
- Maintain code quality standards

## 📄 License

See [LICENSE](./LICENSE) file.

## 🆘 Support

For issues, questions, or contributions, please open an issue on the repository.

## 🙏 Acknowledgments

Built with:
- FastAPI
- Next.js
- PostgreSQL
- Redis
- Celery
- OpenAI
- And many other open-source tools

---

**Built by engineers who understand systems, scale, and business.**
