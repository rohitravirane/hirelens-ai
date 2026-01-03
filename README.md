# HireLens AI

**Production-Grade AI-Powered Hiring Intelligence Platform**

HireLens AI helps recruiters and hiring managers see beyond resumes. The platform uses semantic matching and explainable AI to score and rank candidates, providing transparent, actionable insights for hiring decisions.

## 🎯 Product Vision

HireLens AI is not a demo or tutorial project. It's a **real-world, enterprise-grade** platform designed for production use by recruiters at scale.

### Core Capabilities

- ✅ **Candidate Kundali System**: 360° technical + professional + behavioral profile extraction
- ✅ **Qwen Vision-Based Parsing**: Image-first extraction using local Qwen2.5-VL model (100% offline)
- ✅ **Personality Inference**: Work style, ownership level, learning orientation, communication strength (with confidence scores)
- ✅ **Resume-as-Source-of-Truth**: No manual forms, resume is the ONLY input
- ✅ **Ollama Integration**: Fast inference using pre-downloaded local Qwen models (Qwen2.5-VL for vision)
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
                                                          ↓
                                    Candidate Kundali Engine (Qwen Vision + Ollama)
```

### Architecture Style

- **Phase 1**: Modular Monolith (current)
- **Phase 2**: Microservices-ready (documented)

## 🚀 Quick Start

### Prerequisites

- **Docker & Docker Compose** - Works on Windows 11, macOS, and Linux
- **Python 3.11+** (for local development, optional if using Docker)
- **Node.js 18+** (for frontend development, optional if using Docker)
- **NVIDIA GPU (Highly Recommended)** - GPU with 8GB+ VRAM (RTX series or equivalent) for faster AI model inference
  - **Windows 11**: Requires Docker Desktop with WSL2 backend for GPU support
  - **Linux**: nvidia-docker or Docker with GPU support
- **Ollama (Optional but Recommended)** - For fast semantic normalization using pre-downloaded Qwen models
  - **Windows**: Install Windows version from [ollama.ai](https://ollama.ai)
  - **Linux/WSL**: Install via package manager or script
- **OpenAI API Key (Optional)** - Only needed if using OpenAI. Hugging Face + Ollama works locally without API!

**Note**: Project works on **Windows 11 directly** (no WSL required for basic setup). WSL2 is only recommended for GPU support.

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
   # - AI_PROVIDER=auto (uses Hugging Face + Ollama locally, no API costs!)
   # - OPENAI_API_KEY (optional, only if you want to use OpenAI)
   ```

3. **Install Ollama (Optional but Recommended)**
   ```bash
   # Download and install from https://ollama.ai
   # Then pull the Qwen model:
   ollama pull qwen2.5:7b-instruct-q4_K_M
   ```

4. **Start services**
   ```bash
   docker-compose up -d
   ```

5. **Initialize database**
   ```bash
   docker-compose exec backend python scripts/init_db.py
   ```

6. **Check logs**
   ```powershell
   # Check all logs (recommended)
   .\scripts\check_logs.ps1
   
   # Check specific service with more lines
   .\scripts\check_logs.ps1 -Service backend -Lines 100
   
   # Or use docker directly
   docker-compose logs -f backend
   docker-compose logs -f hirelens-celery-worker
   
   # Clear resume cache if needed (after code changes)
   docker-compose exec backend python scripts/clear_resume_cache.py
   ```

7. **Access the application**
   - Frontend: http://localhost:3000
   - API Docs: http://localhost:8000/api/docs
   - Backend API: http://localhost:8000

### Dashboard Features

The recruiter dashboard includes:

- **Jobs Tab**: View all jobs (30+ pre-loaded tech jobs), create new jobs with AI-powered parsing
- **Candidates Tab**: Upload resumes (drag & drop), add candidates, view candidate list with quality indicators
- **Rankings Tab**: View AI-powered candidate rankings for selected jobs
- **Interactive Modals**: 
  - Job creation form with full job description parsing
  - Job details modal with sticky header showing full job description
  - Resume upload with drag-and-drop support
  - Candidate creation form with resume linking
  - Candidate details modal with quality score and reprocessing
- **Quality Indicators**: 
  - Visual quality score (0-100%) in candidate list
  - Color-coded progress bars (Green/Yellow/Red)
  - Quality score display in candidate details modal
  - Reprocess button for low-quality resumes (<80%)
- **Smart Matching**: 
  - Match button disabled if resume quality < 80%
  - Error notifications for quality requirements
  - Prevents matching with incomplete data
- **Match All**: Bulk match all candidates to a job with one click
- **Real-time Notifications**: Success/error notifications for match operations
- **AI Explanations**: View detailed AI analysis with strengths, weaknesses, and recommendations
- **Improved UX**: 
  - Black text in all form inputs for better readability
  - Immediate logout redirect to login page
  - Loading states and visual feedback
  - Fully responsive design (mobile, tablet, desktop)

### Default Credentials

- **Email**: admin@hirelens.ai
- **Password**: admin123

⚠️ **Change these in production!**

## 📁 Project Structure

```
hirelens-ai/
├── backend/
│   ├── app/
│   │   ├── auth/           # Authentication & RBAC
│   │   ├── resumes/        # Resume processing
│   │   │   └── layout_parser/  # Vision-first document AI
│   │   │       ├── layout_parser.py      # Main orchestrator
│   │   │       ├── layoutlm_processor.py # LayoutLMv3-large integration
│   │   │       ├── semantic_normalizer.py # Ollama/HF LLM normalization
│   │   │       ├── section_detector.py   # Section detection
│   │   │       ├── pdf_to_image.py       # PDF rendering
│   │   │       └── ocr_engine.py          # OCR support
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
│   │   ├── verify_clean.py  # Verification scripts
│   │   ├── reprocess_all_resumes.py # Bulk reprocessing
│   │   └── clear_resume_cache.py # Cache management
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
├── docker-compose.yml      # Docker orchestration
├── rebuild_complete.sh     # Complete rebuild script
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

### 1. Candidate Kundali: Resume-as-Source-of-Truth

**Philosophy**: A resume is not just a document—it's a **structured signal + behavioral signal** that reveals the human behind it.

**What is a Candidate Kundali?**
A 360° technical + professional + behavioral snapshot that includes:
- **Identity**: Name, contact, location
- **Online Presence**: ALL links (GitHub, LinkedIn, portfolio, Twitter, Kaggle, Medium, etc.)
- **Education**: Structured timeline with fields of study
- **Experience**: Deep extraction (technologies, quantified impact, promotions)
- **Projects**: Personal vs company projects, ownership indicators
- **Skills**: Categorized (Frontend, Backend, Data, DevOps, AI/ML, Tools, Soft Skills)
- **Certifications & Achievements**
- **Languages**: Spoken languages
- **Seniority Assessment**: Junior/Mid/Senior/Staff+ with evidence-based reasoning
- **Personality Inference**: Work style, ownership level, learning orientation, communication strength, risk profile (INFERRED, not facts)
- **Leadership Signals**: Evidence-based indicators
- **Red Flags**: Honest concerns (gaps, inconsistencies)
- **Overall Confidence**: 0.0-1.0 based on data completeness

**Qwen Vision-Based Architecture (v2.0 - Masterpiece):**

The system uses a **simplified, intelligent architecture** that prioritizes understanding over complexity:

**Pipeline Flow:**
1. **PDF → Direct Processing**: PDF file read directly as binary (no conversion, no text extraction)
   - Preserves original PDF format and structure
   - No conversion overhead or data loss
2. **Qwen Model** (PRIMARY):
   - **Model**: Qwen2.5-VL (vision-capable) or Qwen2.5 (text-only, fallback)
   - **Integration**: Via Ollama (if available) or direct HuggingFace
   - **Input**: PDF file (base64 encoded) + master extraction prompt
   - **GPU Preferred**: Auto-detects CUDA (8GB+ VRAM recommended)
   - **CPU Fallback**: Fully functional, slower but acceptable
3. **Master Extraction Prompt**:
   - **Structured Extraction**: Facts (identity, experience, skills, etc.)
   - **Behavioral Inference**: Personality traits, work style, ownership signals
   - **Confidence Scores**: Every inference has confidence (0.0-1.0)
   - **Anti-Hallucination**: "unknown" for missing data, never invent
4. **Candidate Kundali Generation**:
   - **Structured Data**: Identity, experience, education, projects, skills
   - **Personality Profile**: Work style, ownership, learning, communication, risk profile
   - **Seniority Assessment**: Evidence-based (years, roles, responsibilities)
   - **Quality Scoring**: Based on data completeness and clarity
5. **Post-Processing & Validation**:
   - Normalize online presence URLs
   - Calculate experience years
   - Validate confidence scores
   - Store in CandidateKundali table

**Key Features:**
- ✅ **PDF-First Extraction**: Direct PDF processing (no conversion, no text extraction)
- ✅ **Personality Inference**: Understands work style, ownership, learning orientation (with confidence)
- ✅ **100% Offline**: No API calls, all models run locally (Qwen via Ollama)
- ✅ **Unlimited Usage**: No rate limits, no costs, complete privacy
- ✅ **Resume-Only Input**: No manual forms, resume is the source of truth
- ✅ **Confidence Scores**: Every inference has confidence (honesty over completeness)
- ✅ **GPU/CPU Fallback**: Works on both, GPU preferred for speed

**Quality Scoring System:**
- **Overall Confidence Score**: 0.0-1.0 based on data completeness
- **Identity Completeness**: Name, email, phone, location (2 points)
- **Experience Depth**: Number of entries, details, metrics (3 points)
- **Education Completeness**: Degrees, institutions, timelines (1 point)
- **Skills Coverage**: Categorized skills across all categories (2 points)
- **Projects Detail**: Personal vs company, ownership indicators (1 point)
- **Personality Confidence**: Inference quality and evidence (1 point)
- **0.8-1.0**: Excellent quality, ready for matching
- **0.5-0.79**: Moderate quality, acceptable
- **<0.5**: Low quality, reprocessing recommended

**Fallback Chain:**
1. Qwen2.5-VL (Vision) via Ollama → Qwen2.5-VL (Vision) via HuggingFace
2. Qwen2.5 (Text-only) via Ollama → Qwen2.5 (Text-only) via HuggingFace
3. Legacy AI Parser (LayoutLM + NER) → Rule-based parsing

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

### 5. Candidate Ranking

Get ranked candidates for a job:

```bash
curl "http://localhost:8000/api/v1/matching/job/1/rankings" \
  -H "Authorization: Bearer <token>"
```

Returns candidates sorted by match score with percentile rankings.

## 🧠 AI Engine

### AI Providers Supported

**1. Ollama (Recommended - Fastest & Free)**
- ✅ **Free** - No API costs
- ✅ **Local** - Runs on your machine/server
- ✅ **Private** - Data never leaves your infrastructure
- ✅ **Fast** - Pre-downloaded models, 10-20x faster than Hugging Face
- ✅ **Works Offline** - No internet required after model download
- Model: `qwen2.5:7b-instruct-q4_K_M` (quantized, ~4GB)
- **Installation**: Download from [ollama.ai](https://ollama.ai)
- **Model Download**: `ollama pull qwen2.5:7b-instruct-q4_K_M`
- **Docker Access**: Automatically connects via `host.docker.internal:11434`

**2. Hugging Face (Fallback - Free & Local)**
- ✅ **Free** - No API costs
- ✅ **Local** - Runs on your machine/server
- ✅ **Private** - Data never leaves your infrastructure
- ✅ **Works Offline** - No internet required after model download
- Models: Sentence Transformers (embeddings), Qwen2.5-7B-Instruct (text generation)
- **Auto-downloads** on first use (~14GB for Qwen2.5-7B)

**3. OpenAI (Optional - Paid API)**
- Better quality explanations and resume parsing
- Faster API responses
- More accurate experience extraction
- Requires API key and internet

### AI Resume Parsing Architecture

The system uses a **Vision-First Document AI Architecture** (production-grade, comparable to FAANG internal tools):

**PRIMARY METHOD - Vision-First Pipeline (Mandatory for Production):**

1. **PDF → Image Rendering**: Convert PDF pages to images (200 DPI)
2. **Scanned PDF Detection**: Auto-detect if OCR needed (PyTesseract if no text layer)
3. **LayoutLMv3-Large Inference**: 
   - **GPU-accelerated** (CUDA) when available (GPU with 8GB+ VRAM)
   - **CPU fallback** with base model
   - **Vision + layout + text** triple understanding
   - **Bounding-box aware** tokenization
   - **Safetensors** for secure model loading
   - **Dtype matching** (float16 for GPU, float32 for CPU)
4. **Layout Structure Analysis**:
   - Column segmentation (2-column resume handling)
   - Visual hierarchy detection (font size + position)
   - Section boundary detection (first-class, not heuristic)
   - Table/grid awareness
   - Bullet cluster reconstruction
5. **Section-Aware NER**: spaCy NER within each detected section (not global)
6. **Semantic Normalization**: 
   - **Ollama (Primary)**: Fast inference with pre-downloaded Qwen2.5-7B
   - **Hugging Face (Fallback)**: Downloads Qwen2.5-7B on first use
7. **Quality Confidence**: Layout confidence incorporated into quality scoring

**FALLBACK METHOD - NER-Based Parsing (Only if LayoutLM unavailable):**
- **spaCy NER Models**: Uses Named Entity Recognition (NER) for fast, accurate extraction
- Extracts entities: Skills, Companies, Dates, Education, Certifications
- **10x faster** than LLM-based parsing (seconds vs minutes)
- Works efficiently on CPU - no GPU required
- Combines NER with rule-based patterns for comprehensive coverage

**Optional Refinement - LLM (Only When Needed):**
- **OpenAI GPT-4**: Used only when quality < 70% (if API key available)
- Automatic quality-based refinement
- Skip LLM on CPU for HuggingFace models (too slow) - use OpenAI API for refinement

**Features:**
- **Vision-First Architecture**: LayoutLMv3-large is PRIMARY, not optional
- **GPU Support**: Auto-detects and uses CUDA when available (GPU with 8GB+ VRAM recommended)
- **Ollama Integration**: Fast semantic normalization using pre-downloaded models
- **Quality Scoring**: Automatic quality score (0-100) indicates extraction confidence
  - **+15 bonus** when LayoutLMv3-large successfully used (vision-first success)
  - **+8 bonus** when text-based section detection used (still layout-aware)
  - **-20 penalty** when fallback to text-only parsing (layout parsing failed)
  - 80-100%: Excellent quality, ready for matching
  - 50-79%: Moderate quality, reprocessing recommended
  - <50%: Poor quality, reprocessing required
- **Experience calculation**: Automatically calculates total years from date ranges
- **Overlap handling**: Correctly handles overlapping employment periods
- **Date normalization**: Handles multiple date formats intelligently
- **Fallback mechanism**: LayoutLM → NER → Rule-based parser
- **Reprocessing**: One-click reprocessing to improve extraction quality

### Configuration

In `.env` file:
```env
# Use Hugging Face + Ollama (Free, Local, Fast)
AI_PROVIDER=auto

# Or explicitly use Hugging Face
AI_PROVIDER=huggingface

# Or use OpenAI (requires API key)
AI_PROVIDER=openai
OPENAI_API_KEY=your-key-here
```

### Cost Optimization

- **Ollama**: Completely free, runs locally, fastest option
- **Hugging Face**: Completely free, runs locally, slower but fully functional
- **OpenAI**: Aggressive caching (24-hour TTL for embeddings)
- Hash-based cache keys
- Batch processing
- Fallback models when appropriate

## 🖥️ GPU/CUDA Support (Highly Recommended)

### Prerequisites

- **NVIDIA GPU**: GPU with 8GB+ VRAM recommended (RTX series or equivalent)
- **CUDA Support**: CUDA 12.1+ compatible drivers
- **Docker GPU Support**: 
  - Windows: Docker Desktop with WSL2 backend
  - Linux: nvidia-docker or Docker with GPU support

### GPU Benefits

- 🚀 **5-10x faster** resume parsing with LayoutLMv3-large
- ⚡ **Faster model inference** for semantic normalization
- 💾 **Memory efficient** with float16 precision
- 🎯 **Better quality** with larger models (LayoutLMv3-large vs base)

### Automatic GPU Detection

The system automatically detects and uses GPU when available:
- **LayoutLMv3**: Auto-uses CUDA if available, falls back to CPU
- **Semantic Normalizer**: Uses GPU for Hugging Face models if available
- **Ollama**: Runs on host system (uses host GPU if configured)

### Verification

Check GPU availability:
```bash
# Inside container
docker-compose exec backend python -c "import torch; print('CUDA:', torch.cuda.is_available()); print('Device:', torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'CPU')"

# Check logs
docker-compose logs celery-worker | grep -i "gpu\|cuda\|layoutlmv3"
```

### Celery Worker Configuration

Celery workers use `--pool=solo` to avoid CUDA re-initialization issues in forked processes. This is configured in `docker-compose.yml`:

```yaml
celery-worker:
  command: celery -A app.core.celery_app worker --loglevel=info --pool=solo
```

## 📈 Scaling Strategy

HireLens AI is designed to scale from 100 to 1 million users:

- **100 users**: Single server, current architecture
- **10k users**: Horizontal scaling, read replicas, Redis cluster
- **1M users**: Microservices, multi-region, distributed database

## 🛠️ Development

### Backend Development

```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# Configure .env file in project root
# Set AI_PROVIDER=auto for Hugging Face + Ollama (free, local)

# Run migrations
alembic upgrade head

# Initialize database
python scripts/init_db.py

# Run server
uvicorn app.main:app --reload
```

**Note**: First time running with Hugging Face will download models (~100MB-14GB). Ollama models should be pre-downloaded on host system.

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

### Using Ollama (Fastest - Recommended)

**Installation:**
1. Download from [ollama.ai](https://ollama.ai)
2. Pull the Qwen model:
   ```bash
   ollama pull qwen2.5:7b-instruct-q4_K_M
   ```

**Configuration:**
```env
AI_PROVIDER=auto
# System automatically detects Ollama at host.docker.internal:11434
```

**Benefits:**
- ✅ No API costs
- ✅ 100% local and private
- ✅ Works offline
- ✅ 10-20x faster than Hugging Face
- ✅ Production ready

### Using Hugging Face (Free, Local - Fallback)

```env
AI_PROVIDER=auto
# or
AI_PROVIDER=huggingface

# Models (auto-downloads on first use)
HUGGINGFACE_EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
HUGGINGFACE_LLM_MODEL=Qwen/Qwen2.5-7B-Instruct
HUGGINGFACE_PARSER_MODEL=Qwen/Qwen2.5-7B-Instruct
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
- Safetensors for secure model loading

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

**Reprocess All Resumes:**
```bash
docker-compose exec backend python scripts/reprocess_all_resumes.py
# Reprocesses all resumes with latest parsing improvements
```

**Clear Resume Cache:**
```bash
docker-compose exec backend python scripts/clear_resume_cache.py
# Clears Redis cache for resume parsing
```

## 🚧 Roadmap

### Phase 1 (Current)
- ✅ Core matching engine
- ✅ Explainable AI
- ✅ Vision-first document AI system (LayoutLMv3-large)
- ✅ Ollama integration for fast semantic normalization
- ✅ GPU acceleration (GPU with 8GB+ VRAM)
- ✅ PyTorch 2.5.1+cu121 with safetensors support
- ✅ PyTesseract OCR for scanned PDFs
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
- LayoutLMv3-large (Microsoft)
- Ollama
- Qwen2.5-7B (Alibaba Cloud)
- OpenAI / Hugging Face
- Docker & Docker Compose
- PyTorch 2.5.1+cu121
- And many other open-source tools

---

## 📝 Recent Updates

### Latest Features (v2.0 - Vision-First Architecture)

**Major Architecture Upgrade:**
- ✨ **Vision-First Document AI System**: Complete upgrade to production-grade vision-first architecture
  - **LayoutLMv3-Large**: Enterprise-grade vision + layout + text understanding
  - **GPU Acceleration**: GPU with 8GB+ VRAM support with automatic CUDA detection
  - **Ollama Integration**: Fast semantic normalization using pre-downloaded Qwen2.5-7B models
  - **PyTorch 2.5.1+cu121**: Latest PyTorch with CUDA 12.1 support
  - **Safetensors**: Secure model loading to prevent PyTorch vulnerabilities
  - **Dtype Matching**: Automatic float16/float32 matching for GPU/CPU compatibility
  - **PyTesseract OCR**: Offline OCR support for scanned PDFs
  - **Celery Solo Pool**: Fixed CUDA re-initialization issues in forked processes
  - **Quality Scoring**: Enhanced with layout confidence bonuses (+15 for LayoutLM, +8 for text-based)
  - **Intelligent Fallbacks**: Graceful degradation from LayoutLM-large → base → CPU → NER

**Technical Improvements:**
- 🔧 **Fixed dtype mismatch**: Input tensors now match model dtype (float16 for GPU, float32 for CPU)
- 🔧 **Fixed CUDA forking**: Celery workers use `--pool=solo` to avoid CUDA re-initialization errors
- 🔧 **Fixed model loading**: Safetensors support with fallback to standard PyTorch loading
- 🔧 **Fixed Ollama connectivity**: Automatic detection of `host.docker.internal:11434` for Docker Desktop
- 🔧 **Improved error handling**: Comprehensive fallback chain for maximum reliability

**Performance:**
- 🚀 **10-20x faster** semantic normalization with Ollama vs Hugging Face
- 🚀 **5-10x faster** resume parsing with LayoutLMv3-large on GPU
- 💾 **Memory efficient** with float16 precision and safetensors
- ⚡ **Zero API costs** with 100% offline operation

### Previous Features (v1.3)
- ✨ **Layout-Aware Resume Parser**: Vision + Layout + Semantic hybrid system using LayoutLMv3
  - Handles multi-column layouts, complex designs (Canva/Figma), scanned PDFs
  - Section detection using font size, position, layout structure
  - OCR support (PaddleOCR) for scanned PDFs - 100% offline
  - Local LLM normalization (Qwen2.5-7B/Mistral-7B) for structured extraction
  - Quality scoring: +10 bonus for LayoutLM usage, -15 penalty for fallback
- ✨ **Docker Support**: Updated Dockerfile with poppler-utils for PDF to image conversion

### Previous Features (v1.2)
- ✨ **World-Class Resume Parsing**: Enhanced AI prompts for comprehensive data extraction
- ✨ **Quality Scoring System**: Automatic quality score (0-100) for each parsed resume
- ✨ **Quality Indicators in UI**: Visual quality score with progress bars in candidate list
- ✨ **Reprocessing in UI**: One-click reprocessing button in candidate details modal
- ✨ **Smart Blocking**: Prevents matching if resume quality is too low (<80%) with error notifications
- ✨ **Job & Candidate Details Modals**: Full details view with sticky headers
- ✨ 30+ pre-loaded tech jobs with comprehensive descriptions
- ✨ Improved UI/UX with better form styling and logout redirect
- ✨ Real-time notifications for match operations
- ✨ Frontend hot-reloading in Docker for better development experience
- ✨ Database cleanup and management utility scripts
- 🐛 Fixed experience calculation errors in AI explanations
- 🐛 Fixed Docker PostgreSQL healthcheck configuration

---

**Built by engineers who understand systems, scale, and business.**
