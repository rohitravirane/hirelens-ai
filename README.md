# HireLens AI

**Production-Grade AI-Powered Hiring Intelligence Platform**

HireLens AI helps recruiters and hiring managers see beyond resumes. The platform uses semantic matching and explainable AI to score and rank candidates, providing transparent, actionable insights for hiring decisions.

## 🎯 Product Vision

HireLens AI is not a demo or tutorial project. It's a **real-world, enterprise-grade** platform designed for production use by recruiters at scale.

### Core Capabilities

- ✅ **Candidate Kundali System**: 360° technical + professional + behavioral profile extraction
- ✅ **Qwen Text-Based Parsing**: Intelligent resume parsing using local Qwen2.5 text models via Ollama (100% offline)
- ✅ **Personality Inference**: Work style, ownership level, learning orientation, communication strength (with confidence scores)
- ✅ **Resume-as-Source-of-Truth**: No manual forms, resume is the ONLY input
- ✅ **Ollama Integration**: Fast inference using pre-downloaded local Qwen models (Qwen2.5-7B-Instruct)
- ✅ **Experience Calculation**: Accurate years of experience calculation from resume date ranges with overlap handling
- ✅ **Job Description Intelligence**: Parse and understand job requirements with comprehensive descriptions
- ✅ **Semantic Matching**: AI-powered candidate-job matching with embeddings
- ✅ **Multi-Dimensional Scoring**: Skill match, experience, projects, domain familiarity
- ✅ **Explainable AI**: Human-readable explanations for every match with strengths, weaknesses, and recommendations
- ✅ **Candidate Ranking**: Percentile-based ranking with confidence levels
- ✅ **Recruiter Dashboard**: Interactive UI with tabs, modals, drag-drop, and real-time notifications
- ✅ **Job Management**: Create and manage tech jobs with AI-powered parsing
- ✅ **Resume Upload**: PDF-only upload with world-class validation (automatically detects if file is actually a resume)
- ✅ **Candidate Management**: Combined Add Candidate flow - upload resume → auto-process → form auto-fill → create candidate (single smooth flow)
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
                                    Candidate Kundali Engine (Qwen Text-Only via Ollama)
                                                          ↓
                                    Fallback: Legacy AI Parser (LayoutLM + NER + HURIDOCS)
                                                          ↓
                                    Optional Services: HURIDOCS Layout Analysis (port 5060)
```
<｜tool▁calls▁begin｜><｜tool▁call▁begin｜>
read_file

### Architecture Style

- **Phase 1**: Modular Monolith (current)
- **Phase 2**: Microservices-ready (documented)

## 🚀 Quick Start

### Prerequisites

- **Docker & Docker Compose** - Works on Windows 11, macOS, and Linux
- **Python 3.11+** (for local development, optional if using Docker)
- **Node.js 18+** (for frontend development, optional if using Docker)
- **NVIDIA GPU (Optional but Recommended)** - GPU with 8GB+ VRAM (RTX series or equivalent) for faster AI model inference
  - **Windows 11**: Requires Docker Desktop with WSL2 backend for GPU support
  - **Linux**: nvidia-docker or Docker with GPU support
- **Ollama (Required)** - For fast resume parsing using pre-downloaded Qwen models
  - **Windows**: Install Windows version from [ollama.ai](https://ollama.ai)
  - **Linux/WSL**: Install via package manager or script
- **OpenAI API Key (Optional)** - Only needed if using OpenAI. Ollama works locally without API!

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
   # - AI_PROVIDER=auto (uses Ollama locally, no API costs!)
   # - OPENAI_API_KEY (optional, only if you want to use OpenAI)
   ```

3. **Install Ollama (Required)**
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
   ```bash
   # Check all logs
   docker-compose logs -f
   
   # Check specific service
   docker-compose logs -f backend
   docker-compose logs -f hirelens-celery-worker
   ```

7. **Access the application**
   - Frontend: http://localhost:3000
   - API Docs: http://localhost:8000/api/docs
   - Backend API: http://localhost:8000

### Dashboard Features

The recruiter dashboard includes:

- **Jobs Tab**: View all jobs, create new jobs with AI-powered parsing
- **Candidates Tab**: Add candidates (single combined flow: upload PDF resume → auto-process → form auto-fill → create), view candidate list with quality indicators
- **Rankings Tab**: View AI-powered candidate rankings for selected jobs
- **Interactive Modals**: 
  - Job creation form with full job description parsing
  - Job details modal with sticky header showing full job description
  - **Combined Add Candidate modal** with 3-step flow (Upload Resume → Processing → Add Details)
  - Candidate creation form with auto-fill from extracted resume data
  - Candidate details modal with quality score, experience, skills, and reprocessing
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
  - Auto-fill candidate form from extracted resume data
  - Loading indicators while data is being fetched
  - Exponential backoff retry for async processing
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
│   │   │   ├── kundali_parser.py  # PRIMARY: Qwen text-based parser (via Ollama)
│   │   │   ├── parser.py   # Rule-based parser (fallback)
│   │   │   ├── ai_parser.py # Legacy AI parser (fallback)
│   │   │   └── layout_parser/  # LayoutLMv3 (legacy/fallback)
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
│   │   │   ├── candidate.py
│   │   │   ├── candidate_kundali.py  # Kundali data storage
│   │   │   ├── resume.py
│   │   │   └── ...
│   │   ├── tasks/          # Async Celery tasks
│   │   │   └── resume_tasks.py  # Resume processing pipeline
│   │   └── main.py         # FastAPI application
│   ├── scripts/            # Utility scripts
│   │   ├── init_db.py      # Database initialization
│   │   ├── create_test_data.py # Test data generation
│   │   ├── clean_database.py # Database cleanup
│   │   ├── add_quality_score_migration.py # Quality score migration
│   │   └── update_quality_scores.py # Quality score updater
│   ├── requirements.txt    # Python dependencies
│   └── Dockerfile
├── frontend/
│   ├── app/                # Next.js app directory
│   │   ├── dashboard/      # Main dashboard with tabs
│   │   └── login/          # Login page
│   ├── components/         # React components
│   │   ├── JobModal.tsx    # Job creation modal
│   │   ├── JobDetailsModal.tsx # Job details view
│   │   ├── AddCandidateModal.tsx # Combined candidate creation (upload + form + create in single flow)
│   │   ├── CandidateDetailsModal.tsx # Candidate details view
│   │   └── BulkReprocessModal.tsx # Bulk reprocessing
│   ├── lib/                # Utilities
│   ├── hooks/              # React hooks
│   └── package.json
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

**Qwen Text-Based Architecture (v2.0 - Current):**

The system uses a **simplified, intelligent architecture** that prioritizes understanding over complexity:

**Pipeline Flow:**
1. **PDF Upload**: Resume uploaded via drag-and-drop or API (**PDF-only**, DOCX/DOC files are rejected immediately)
2. **Early Validation**: World-class resume validation at upload endpoint (before async processing)
   - Extracts text from PDF immediately
   - Validates if document is actually a resume (score-based validation)
   - Rejects non-resume files with user-friendly error messages
   - Only valid resumes proceed to processing
3. **Text Extraction**: Extract raw text from PDF using rule-based parser (pdfplumber/pypdf2)
4. **Qwen Model** (PRIMARY):
   - **Model**: Qwen2.5-7B-Instruct (text-only, quantized q4_K_M, via Ollama)
   - **Integration**: Via Ollama API at `host.docker.internal:11434`
   - **Input**: Extracted `raw_text` from step 2 (text-only models work better with extracted text than PDF base64)
   - **Model Name**: `qwen2.5:7b-instruct-q4_K_M` (confirmed working model)
   - **Optional Vision Models**: Qwen2.5-VL (if available via Ollama, uses PDF base64, but text-only is PRIMARY)
   - **GPU Preferred**: Auto-detects CUDA (8GB+ VRAM recommended) - Ollama uses host GPU if available
   - **CPU Fallback**: Fully functional, slower but acceptable
5. **Master Extraction Prompt**:
   - **Structured Extraction**: Facts (identity, experience, skills, etc.)
   - **Behavioral Inference**: Personality traits, work style, ownership signals
   - **Confidence Scores**: Every inference has confidence (0.0-1.0)
   - **Anti-Hallucination**: "unknown" for missing data, never invent
   - **Complete Extraction**: Extracts ALL experience entries, ALL skills (no missing data)
6. **Candidate Kundali Generation**:
   - **Structured Data**: Identity, experience, education, projects, skills
   - **Personality Profile**: Work style, ownership, learning, communication, risk profile
   - **Seniority Assessment**: Evidence-based (years, roles, responsibilities)
   - **Quality Scoring**: Based on data completeness and clarity
7. **Post-Processing & Validation**:
   - **Skills Cleaning**: Automatically removes company names from skills arrays (e.g., "Team 4 Progress Technologies" removed from tools/skills)
   - Normalize online presence URLs (add `https://` if missing)
   - Calculate experience years
   - Email/Phone regex fallback (if AI misses them)
   - Validate confidence scores
   - Store in CandidateKundali table
8. **Candidate Creation**: Automatically create Candidate record from Kundali data
9. **Resume Version**: Create ResumeVersion with parsed data for backward compatibility

**Key Features:**
- ✅ **PDF-Only Upload**: Only PDF resume files accepted (DOCX/DOC rejected immediately)
- ✅ **World-Class Validation**: Validates if file is actually a resume before processing (detects invoices, contracts, academic papers, etc.)
- ✅ **Text-First Extraction**: Extract text from PDF first, then process with Qwen text-only model (more reliable than PDF base64 for text models)
- ✅ **Skills Cleaning**: Automatically removes company names from skills arrays (post-processing)
- ✅ **Personality Inference**: Understands work style, ownership, learning orientation (with confidence)
- ✅ **100% Offline**: No API calls, all models run locally (Qwen via Ollama)
- ✅ **Unlimited Usage**: No rate limits, no costs, complete privacy
- ✅ **Resume-Only Input**: No manual forms, resume is the source of truth
- ✅ **Confidence Scores**: Every inference has confidence (honesty over completeness)
- ✅ **GPU/CPU Fallback**: Works on both, GPU preferred for speed
- ✅ **Anti-Hallucination**: Strict rules prevent inventing companies/roles
- ✅ **Complete Extraction**: Extracts ALL experience entries and ALL skills
- ✅ **Email/Phone Fallback**: Regex-based extraction if AI fails
- ✅ **Combined Add Candidate Flow**: Single smooth flow - upload resume → auto-process → form auto-fill → create candidate

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
1. **Primary**: Qwen2.5-7B-Instruct (text-only) via Ollama → Uses extracted `raw_text` (best reliability)
2. **Fallback 1**: Qwen2.5-VL (vision) via Ollama → Uses PDF base64 (if vision model available, optional)
3. **Fallback 2**: Legacy AI Parser (LayoutLMv3 + NER + HURIDOCS) → Vision-first document AI with layout analysis
4. **Fallback 3**: Rule-based parser → Pattern matching and heuristics

**File Upload Requirements:**
- **Only PDF files accepted** (DOCX/DOC files are rejected immediately)
- **World-class validation**: System validates if uploaded file is actually a resume before processing
- **Max file size**: 10MB
- **Validation errors**: Clear, user-friendly error messages if file is not a resume

**API Example:**
```bash
curl -X POST http://localhost:8000/api/v1/resumes/upload \
  -H "Authorization: Bearer <token>" \
  -F "file=@resume.pdf"
```

**Note**: Only PDF files are accepted. Non-PDF files or files that don't appear to be resumes will be rejected with clear error messages.

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

**1. Ollama (Required - Fastest & Free)**
- ✅ **Free** - No API costs
- ✅ **Local** - Runs on your machine/server
- ✅ **Private** - Data never leaves your infrastructure
- ✅ **Fast** - Pre-downloaded models, 10-20x faster than Hugging Face
- ✅ **Works Offline** - No internet required after model download
- Model: `qwen2.5:7b-instruct-q4_K_M` (quantized, ~4GB)
- **Installation**: Download from [ollama.ai](https://ollama.ai)
- **Model Download**: `ollama pull qwen2.5:7b-instruct-q4_K_M`
- **Docker Access**: Automatically connects via `host.docker.internal:11434`

**2. Hugging Face (Fallback for Matching/Explanations - Free & Local)**
- ✅ **Free** - No API costs
- ✅ **Local** - Runs on your machine/server
- ✅ **Private** - Data never leaves your infrastructure
- ✅ **Works Offline** - No internet required after model download
- **Used For**: Semantic embeddings (matching) and AI explanations (if OpenAI not available)
- Models: Sentence Transformers (embeddings), Mistral-7B-Instruct (text generation)
- **Auto-downloads** on first use (~14GB for full models)
- **Note**: Not used for resume parsing (Ollama handles that). Only used for matching/explanation features.

**3. OpenAI (Optional - Paid API for Matching/Explanations)**
- Better quality AI explanations for candidate-job matches
- Faster API responses for embeddings and explanations
- **Note**: Not used for resume parsing (Ollama handles that). Only used for matching/explanation features if AI_PROVIDER=openai.
- Requires API key and internet

### AI Resume Parsing Architecture

The system uses a **Qwen Text-Based Architecture** (production-grade, 100% offline):

**PRIMARY METHOD - Qwen Text-Based Pipeline (Current Production):**

1. **PDF Upload**: Resume uploaded via API or frontend (**PDF-only**, DOCX/DOC files rejected immediately)
2. **Early Validation**: World-class resume validation at upload endpoint (before async processing)
   - Extracts text from PDF immediately for validation
   - Validates if document is actually a resume using score-based validation
   - Rejects non-resume files (invoices, contracts, academic papers, etc.) with clear error messages
   - Only valid resumes proceed to async processing
3. **Text Extraction**: Extract raw text from PDF using rule-based parser (pdfplumber/pypdf2)
4. **Resume Validation** (Async): Additional validation during async processing (redundant check)
4. **Qwen Model** (PRIMARY):
   - **Text-Only Model**: Qwen2.5-7B-Instruct (q4_K_M quantized) via Ollama (uses extracted `raw_text`)
   - **Model Name**: `qwen2.5:7b-instruct-q4_K_M`
   - **Integration**: Via Ollama API at `host.docker.internal:11434`
   - **Input Method**: Extracted text (text-only models work better with extracted text than PDF base64)
   - **Optional Vision Model**: Qwen2.5-VL via Ollama (uses PDF base64, if available, but text-only is PRIMARY)
   - **GPU Preferred**: Ollama auto-uses host GPU if available (8GB+ VRAM recommended)
   - **CPU Fallback**: Fully functional, slower but acceptable
5. **Master Extraction Prompt**:
   - **Anti-Hallucination Rules**: Strict instructions to prevent inventing companies/roles
   - **Complete Extraction**: Extracts ALL experience entries, ALL skills
   - **Structured Output**: JSON format with identity, experience, skills, personality
   - **Confidence Scores**: Every inference has confidence (0.0-1.0)
6. **Post-Processing**:
   - **Skills Cleaning**: Automatically removes company names from skills arrays (compares extracted companies with skills, filters matches)
   - Email/Phone regex fallback (if AI misses them)
   - URL normalization (add `https://` if missing)
   - Experience years calculation
   - Quality score calculation
7. **Data Storage**:
   - Store in CandidateKundali table (full Kundali data)
   - Create Candidate record (identity, contact, links)
   - Create ResumeVersion (parsed data for backward compatibility)

**FALLBACK METHOD - Legacy Vision-First Pipeline (Available but not primary):**

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

**Features:**
- **Qwen Text-Based Architecture**: Qwen2.5-7B-Instruct (text-only) is PRIMARY via Ollama, uses extracted text (more reliable)
- **LayoutLMv3 Support**: Available as fallback for vision-first parsing
- **GPU Support**: Auto-detects and uses CUDA when available (GPU with 8GB+ VRAM recommended)
- **Ollama Integration**: Fast inference using pre-downloaded models
- **Quality Scoring**: Automatic quality score (0-100) indicates extraction confidence
  - 80-100%: Excellent quality, ready for matching
  - 50-79%: Moderate quality, reprocessing recommended
  - <50%: Poor quality, reprocessing required
- **Experience calculation**: Automatically calculates total years from date ranges
- **Overlap handling**: Correctly handles overlapping employment periods
- **Date normalization**: Handles multiple date formats intelligently
- **Fallback mechanism**: Qwen → LayoutLM → NER → Rule-based parser
- **Reprocessing**: One-click reprocessing to improve extraction quality
- **Anti-Hallucination**: Strict rules prevent inventing companies/roles
- **Complete Extraction**: Extracts ALL experience entries and ALL skills

### Configuration

**File Upload Configuration:**
- **ALLOWED_FILE_EXTENSIONS**: `"pdf"` (only PDF resumes allowed)
- **MAX_UPLOAD_SIZE_MB**: `10` (maximum file size)
- **Early Validation**: Enabled by default (validates resume before async processing)

**Resume Parsing Configuration:**
- Resume parsing uses Ollama directly (not controlled by AI_PROVIDER)
- Make sure Ollama is installed and `qwen2.5:7b-instruct-q4_K_M` model is downloaded
- Ollama endpoint: `http://host.docker.internal:11434` (auto-detected)

**Matching/Explanation Configuration (`.env` file):**
```env
# Matching/Explanations: Control which provider to use
AI_PROVIDER=auto  # Uses Hugging Face (local) for embeddings/explanations, or OpenAI if key provided

# Or explicitly use Hugging Face for matching/explanations
AI_PROVIDER=huggingface

# Or use OpenAI for matching/explanations (requires API key)
AI_PROVIDER=openai
OPENAI_API_KEY=your-key-here
```

**Important:** AI_PROVIDER only controls matching/explanation features, not resume parsing (which always uses Ollama).

### Cost Optimization

- **Ollama (Resume Parsing)**: Completely free, runs locally, fastest option, no API calls
- **Hugging Face (Matching/Explanations)**: Completely free, runs locally, slower but fully functional
- **OpenAI (Matching/Explanations)**: Aggressive caching (24-hour TTL for embeddings)
- Hash-based cache keys
- Batch processing
- Fallback models when appropriate

## 🖥️ GPU/CUDA Support (Optional but Recommended)

### Prerequisites

- **NVIDIA GPU**: GPU with 8GB+ VRAM recommended (RTX series or equivalent)
- **CUDA Support**: CUDA 12.1+ compatible drivers
- **Docker GPU Support**: 
  - Windows: Docker Desktop with WSL2 backend
  - Linux: nvidia-docker or Docker with GPU support

### GPU Benefits

- 🚀 **5-10x faster** resume parsing with Qwen models
- ⚡ **Faster model inference** for semantic normalization
- 💾 **Memory efficient** with float16 precision
- 🎯 **Better quality** with larger models

### Automatic GPU Detection

The system automatically detects and uses GPU when available:
- **Qwen Models**: Auto-uses CUDA if available, falls back to CPU
- **LayoutLMv3**: Auto-uses CUDA if available, falls back to CPU
- **Ollama**: Runs on host system (uses host GPU if configured)

### Verification

Check GPU availability:
```bash
# Inside container
docker-compose exec backend python -c "import torch; print('CUDA:', torch.cuda.is_available()); print('Device:', torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'CPU')"

# Check logs
docker-compose logs celery-worker | grep -i "gpu\|cuda\|qwen"
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
# Set AI_PROVIDER=auto for Ollama (free, local)

# Run migrations
alembic upgrade head

# Initialize database
python scripts/init_db.py

# Run server
uvicorn app.main:app --reload
```

**Note**: Ollama models should be pre-downloaded on host system. First time running with Hugging Face will download models (~100MB-14GB).

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

### Using Ollama (Required for Resume Parsing - Fastest & Recommended)

**Installation:**
1. Download from [ollama.ai](https://ollama.ai)
2. Pull the Qwen text-only model:
   ```bash
   ollama pull qwen2.5:7b-instruct-q4_K_M
   ```

**Configuration:**
- Ollama is used directly by the resume parser (not controlled by AI_PROVIDER)
- System automatically detects Ollama at `host.docker.internal:11434`
- No configuration needed in `.env` for resume parsing

**Benefits:**
- ✅ No API costs
- ✅ 100% local and private
- ✅ Works offline
- ✅ 10-20x faster than Hugging Face
- ✅ Production ready
- ✅ Text-only model works better with extracted text than PDF base64

**Note:** Ollama is used for resume parsing. The AI_PROVIDER setting only affects matching/explanation features.

### Using Hugging Face (Free, Local - For Matching/Explanations)

```env
AI_PROVIDER=auto
# or
AI_PROVIDER=huggingface

# Models (auto-downloads on first use)
HUGGINGFACE_EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
HUGGINGFACE_LLM_MODEL=mistralai/Mistral-7B-Instruct-v0.1
```

**Benefits:**
- ✅ No API costs
- ✅ 100% local and private
- ✅ Works offline
- ✅ Production ready

**Note:** Used for matching/explanation features only. Resume parsing uses Ollama.

### Using OpenAI (Optional - Paid - For Matching/Explanations)

```env
AI_PROVIDER=openai
OPENAI_API_KEY=your-api-key-here
```

**Benefits:**
- ✅ Better quality explanations for candidate-job matches
- ✅ Faster API responses
- ✅ No local model downloads

**Note:** Used for matching/explanation features only. Resume parsing uses Ollama.

## 🔒 Security

- JWT-based authentication
- Password hashing with bcrypt
- RBAC at service layer
- Input validation (Pydantic)
- File upload restrictions (PDF-only, max 10MB)
- World-class resume validation (detects non-resume files before processing)
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

**Initialize Database:**
```bash
docker-compose exec backend python scripts/init_db.py
# Creates default roles and admin user
```

**Clean Database:**
```bash
docker-compose exec backend python scripts/clean_database.py
# Removes all candidates, jobs, resumes, matches (preserves users)
```

**Create Test Data:**
```bash
docker-compose exec backend python scripts/create_test_data.py
# Generates comprehensive test data for all entities
```

**Update Quality Scores:**
```bash
docker-compose exec backend python scripts/update_quality_scores.py
# Recalculates quality scores for all resumes
```

## 🚧 Roadmap

### Phase 1 (Current)
- ✅ Core matching engine
- ✅ Explainable AI
- ✅ Qwen text-based resume parsing (PRIMARY) - text extraction first, then Qwen text-only model
- ✅ LayoutLMv3 support (fallback)
- ✅ Ollama integration for fast inference
- ✅ GPU acceleration (optional)
- ✅ World-class AI-powered resume parsing with quality scoring
- ✅ Quality indicators and reprocessing system
- ✅ Interactive recruiter dashboard with tabs
- ✅ Job creation with AI parsing
- ✅ Resume upload with drag-and-drop
- ✅ Candidate management with quality indicators and auto-fill
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
- Ollama
- Qwen2.5-7B (Alibaba Cloud)
- LayoutLMv3-large (Microsoft) - Fallback
- OpenAI / Hugging Face
- Docker & Docker Compose
- PyTorch 2.5.1+cu121
- And many other open-source tools

---

## 📝 Recent Updates

### Latest Features (v2.0 - Qwen Text-Based Architecture)

**Resume Extraction Improvements:**
- ✨ **Qwen Text-Based Parsing**: Intelligent resume parsing using Qwen2.5-7B-Instruct text-only model via Ollama
  - **Anti-Hallucination Rules**: Strict instructions to prevent model from inventing companies/roles
  - **Complete Experience Extraction**: Extracts ALL experience entries (no missing entries)
  - **Accurate Company Names**: Extracts exact company names (e.g., Deloitte, Randstad) without hallucination
  - **Complete Skills Extraction**: Extracts ALL skills visible in resume (frontend, backend, tools)
  - **Text-Only Model Support**: Properly uses extracted `raw_text` for text-only models (not PDF base64)
  - **Email/Phone Fallback**: Regex-based fallback extraction if AI fails to extract contact info
  - **URL Normalization**: Automatically adds `https://` prefix to LinkedIn, GitHub, portfolio URLs

**Frontend Enhancements:**
- ✨ **Auto-Fill Candidate Form**: Automatically populates form fields from extracted resume data
  - First Name, Last Name, Email, Phone auto-filled
  - LinkedIn URL, Portfolio URL auto-filled
  - Loading indicator while data is being fetched
  - Exponential backoff retry mechanism for async processing
- ✨ **Enhanced Candidate Details Modal**: 
  - Experience entries display with job titles, companies, dates
  - Responsibilities displayed as formatted description
  - Technologies used shown as badges for each experience entry
  - Skills displayed in categorized badges
  - Education, Projects, Certifications properly formatted
- ✨ **Improved Data Display**: Experience data normalized for frontend compatibility
  - Role → Title/Position mapping
  - Responsibilities array → Description string conversion
  - Technologies displayed as visual badges

**Backend Improvements:**
- 🔧 **Duplicate Candidate Handling**: Backend gracefully handles duplicate candidate creation (updates instead of error)
- 🔧 **Experience Data Normalization**: Transforms Kundali format to frontend-expected format
- 🔧 **Better Error Handling**: Comprehensive error handling with fallback mechanisms

**Code Cleanup:**
- 🧹 **Removed Temporary Scripts**: Cleaned up temporary testing/debugging scripts
- 🧹 **Code Organization**: Better structure and maintainability

### Architecture Notes

**Qwen Text-Based System:**
- ✨ **Qwen2.5-7B-Instruct**: Primary model via Ollama (text-only, quantized q4_K_M, uses extracted raw_text)
- ✨ **Text-First Approach**: Extract text from PDF first, then send to Qwen text-only model (more reliable than PDF base64)
- ✨ **Ollama Integration**: Fast inference using pre-downloaded models via Ollama API
- ✨ **100% Offline**: No API calls, all models run locally
- ✨ **GPU Acceleration**: Ollama auto-uses host GPU if available for faster inference
- ✨ **Anti-Hallucination**: Strict rules prevent inventing data
- ✨ **Complete Extraction**: Extracts ALL experience entries and ALL skills
- ✨ **Optional Vision Models**: Qwen2.5-VL support if available, but text-only is PRIMARY

### Previous Features (v1.3 - LayoutLM Vision-First)
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
