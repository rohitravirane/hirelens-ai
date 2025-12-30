# HireLens AI

**Production-Grade AI-Powered Hiring Intelligence Platform**

HireLens AI helps recruiters and hiring managers see beyond resumes. The platform uses semantic matching and explainable AI to score and rank candidates, providing transparent, actionable insights for hiring decisions.

## 🎯 Product Vision

HireLens AI is not a demo or tutorial project. It's a **real-world, enterprise-grade** platform designed for production use by recruiters at scale.

### Core Capabilities

- ✅ **AI-Powered Resume Parsing**: Intelligent extraction of structured data from PDF/DOCX resumes using LLMs
- ✅ **Experience Calculation**: Accurate years of experience calculation from resume date ranges with overlap handling
- ✅ **Job Description Intelligence**: Parse and understand job requirements with comprehensive descriptions
- ✅ **Semantic Matching**: AI-powered candidate-job matching with embeddings
- ✅ **Multi-Dimensional Scoring**: Skill match, experience, projects, domain familiarity
- ✅ **Explainable AI**: Human-readable explanations for every match with strengths, weaknesses, and recommendations
- ✅ **Candidate Ranking**: Percentile-based ranking with confidence levels
- ✅ **Recruiter Dashboard**: Interactive UI with tabs, modals, drag-drop, and real-time notifications
- ✅ **Job Management**: Create and manage tech jobs with AI-powered parsing
- ✅ **Resume Upload**: Drag-and-drop resume upload with automatic AI parsing
- ✅ **Candidate Management**: Add and manage candidates with resume linking
- ✅ **Interactive Rankings**: View AI-powered candidate rankings with detailed explanations
- ✅ **Bulk Matching**: Match all candidates to a job with one click
- ✅ **Quality Control**: Quality indicators prevent matching with low-quality resume data
- ✅ **Reprocessing**: One-click reprocessing to improve resume extraction quality
- ✅ **Database Management**: Utility scripts for data cleanup and verification

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

- **Jobs Tab**: View all jobs (30+ pre-loaded tech jobs), create new jobs with AI-powered parsing
- **Candidates Tab**: Upload resumes (drag & drop), add candidates, view candidate list
- **Rankings Tab**: View AI-powered candidate rankings for selected jobs
- **Interactive Modals**: 
  - Job creation form with full job description parsing
  - Resume upload with drag-and-drop support
  - Candidate creation form with resume linking
- **Match All**: Bulk match all candidates to a job with one click
- **Real-time Notifications**: Success/error notifications for match operations
- **AI Explanations**: View detailed AI analysis with strengths, weaknesses, and recommendations
- **Improved UX**: 
  - Black text in all form inputs for better readability
  - Immediate logout redirect to login page
  - Loading states and visual feedback

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
│   │   ├── init_db.py      # Database initialization
│   │   ├── create_test_data.py # Test data generation
│   │   ├── clean_database.py # Database cleanup
│   │   ├── clean_test_users.py # User cleanup
│   │   └── verify_clean.py  # Verification scripts
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

### 1. World-Class AI-Powered Resume Processing

Upload resumes (PDF/DOCX) and extract using advanced AI:
- **Skills**: Comprehensive technical and soft skills extraction
- **Experience**: Years of experience calculated from date ranges (handles overlapping periods intelligently)
- **Education**: Degrees, institutions, graduation dates, fields of study
- **Projects**: Project descriptions, technologies, and URLs
- **Certifications**: Professional certifications and licenses
- **Languages**: Programming and spoken languages

**Advanced Features:**
- **World-Class AI Parsing**: Enhanced LLM prompts for intelligent extraction from any resume format
- **Quality Scoring System**: Automatic quality score (0-100) for each parsed resume
  - Scores based on: Skills extraction, Experience calculation, Education, Projects, Data completeness
  - Quality indicators in UI show data extraction confidence
  - Reprocessing available for low-quality extractions
- **Intelligent Date Parsing**: Handles multiple date formats (YYYY-MM, YYYY, "Present", etc.)
- **Automatic Experience Calculation**: Handles overlapping job periods correctly
- **Fallback System**: Rule-based parser if AI parsing fails
- **Reprocessing**: One-click reprocessing to improve extraction quality

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
- Better quality explanations and resume parsing
- Faster API responses
- More accurate experience extraction
- Requires API key and internet

### AI Resume Parsing

The system uses world-class AI to intelligently extract information from resumes:
- **Enhanced LLM-based parsing**: Advanced GPT prompts for comprehensive data extraction from any format
- **Quality Scoring**: Automatic quality score (0-100) indicates extraction confidence
  - 80-100%: Excellent quality, ready for matching
  - 50-79%: Moderate quality, reprocessing recommended
  - <50%: Poor quality, reprocessing required
- **Experience calculation**: Automatically calculates total years from date ranges
- **Overlap handling**: Correctly handles overlapping employment periods
- **Date normalization**: Handles multiple date formats intelligently
- **Fallback mechanism**: Falls back to rule-based parser if AI parsing fails
- **Reprocessing**: One-click reprocessing to improve extraction quality
- **Configurable**: Enable/disable AI parsing via `USE_AI_RESUME_PARSER` environment variable

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

**Docker Development:**
- Frontend hot-reloading enabled in Docker
- Webpack polling configured for file change detection
- Changes reflect immediately without container restart

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

## 🗄️ Database Management

### Utility Scripts

The project includes several utility scripts for database management:

**Clean Database:**
```bash
docker-compose exec backend python scripts/clean_database.py
# Removes all candidates, jobs, resumes, matches (preserves users)
```

**Clean Test Users:**
```bash
docker-compose exec backend python scripts/clean_test_users.py
# Removes all users except admin
```

**Verify Clean:**
```bash
docker-compose exec backend python scripts/verify_clean.py
# Shows database status and entity counts
```

**Create Test Data:**
```bash
docker-compose exec backend python scripts/create_test_data.py
# Generates comprehensive test data for all entities
```

## 🚧 Roadmap

### Phase 1 (Current)
- ✅ Core matching engine
- ✅ Explainable AI
- ✅ World-class AI-powered resume parsing with quality scoring
- ✅ Quality indicators and reprocessing system
- ✅ Interactive recruiter dashboard with tabs
- ✅ Job creation with AI parsing
- ✅ 30+ pre-loaded tech jobs with comprehensive descriptions
- ✅ Resume upload with drag-and-drop
- ✅ Candidate management with quality indicators
- ✅ AI-powered rankings with explanations
- ✅ Match all candidates functionality with notifications
- ✅ Improved UI/UX (form styling, logout redirect, responsive design)
- ✅ Frontend hot-reloading in Docker
- ✅ Database cleanup and management scripts
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
- OpenAI / Hugging Face
- Docker & Docker Compose
- And many other open-source tools

---

## 📝 Recent Updates

### Latest Features (v1.2)
- ✨ **World-Class Resume Parsing**: Enhanced AI prompts for comprehensive data extraction
- ✨ **Quality Scoring System**: Automatic quality score (0-100) for each parsed resume
- ✨ **Quality Indicators**: Visual indicators in UI showing data extraction confidence
- ✨ **Reprocessing**: One-click reprocessing to improve extraction quality
- ✨ **Smart Blocking**: Prevents matching if resume quality is too low (<80%)
- ✨ 30+ pre-loaded tech jobs with comprehensive descriptions
- ✨ Improved UI/UX with better form styling and logout redirect
- ✨ Real-time notifications for match operations
- ✨ Frontend hot-reloading in Docker for better development experience
- ✨ Database cleanup and management utility scripts
- 🐛 Fixed experience calculation errors in AI explanations
- 🐛 Fixed Docker PostgreSQL healthcheck configuration

---

**Built by engineers who understand systems, scale, and business.**
