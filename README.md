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
- ✅ **World-Class Ollama-Based Ranking**: Deep, comprehensive candidate-job matching using Ollama LLM with multi-dimensional analysis
- ✅ **Smart Skill Matching**: Case-insensitive, alias-aware, fuzzy matching with transferable skills detection
- ✅ **Multi-Dimensional Scoring**: Skill match, experience, projects, domain familiarity
- ✅ **Explainable AI**: Human-readable explanations for every match with strengths, weaknesses, and recommendations
- ✅ **Elite Seniority Detection**: Comprehensive resume-based seniority analysis (never returns unknown) with red flag detection
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
                                    ├── Elite Seniority Analyzer (Ollama-based, red flag detection)
                                    └── Fallback: Legacy AI Parser (LayoutLM + NER + HURIDOCS)
                                                          ↓
                                    Matching & Ranking Engine
                                    ├── Ollama Ranking Engine (World-class deep matching)
                                    ├── Smart Skill Matching (Case-insensitive, aliases, fuzzy)
                                    └── Multi-Dimensional Scoring
                                                          ↓
                                    Optional Services: HURIDOCS Layout Analysis (port 5060)
```
<｜tool▁calls▁begin｜><｜tool▁call▁begin｜>
read_file

### Architecture Style

- **Phase 1**: Modular Monolith (current)
- **Phase 2**: Microservices-ready (documented)

## ⚖️ Architecture Trade-offs

### Why FastAPI?

**Chosen:** FastAPI (Python async framework)

**Pros:**
- ✅ **High Performance**: 3-10x faster than Flask, comparable to Node.js/Go
- ✅ **Type Safety**: Automatic request/response validation via Pydantic
- ✅ **Async Support**: Native async/await for I/O-bound operations
- ✅ **Auto Documentation**: OpenAPI/Swagger docs generated automatically
- ✅ **Modern Python**: Uses Python 3.11+ features (type hints, dataclasses)
- ✅ **Developer Experience**: Excellent IDE support, auto-completion
- ✅ **Production Ready**: Used by Microsoft, Uber, Netflix

**Alternatives Considered:**
- **Django**: Too heavy, ORM-centric, not async-first
- **Flask**: Slower, no built-in validation, manual async setup required
- **Node.js/Express**: Python ecosystem needed for AI/ML libraries
- **Go**: Steeper learning curve, limited AI/ML library support

**Trade-off:** FastAPI is newer than Django/Flask, but ecosystem is mature enough for production use.

---

### Why PostgreSQL?

**Chosen:** PostgreSQL 15 (relational database)

**Pros:**
- ✅ **ACID Compliance**: Strong consistency guarantees
- ✅ **Rich Data Types**: JSONB, arrays, full-text search, extensions
- ✅ **Scalability**: Read replicas, partitioning, horizontal scaling
- ✅ **Maturity**: Battle-tested, used by Apple, Instagram, Spotify
- ✅ **Open Source**: No vendor lock-in, active community
- ✅ **PostGIS**: Ready for location-based features if needed

**Alternatives Considered:**
- **MongoDB**: Document store, but we need relational queries, transactions
- **MySQL**: Less advanced features, weaker JSON support
- **SQLite**: Not suitable for production, no concurrency
- **DynamoDB**: AWS lock-in, expensive at scale, complex querying

**Trade-off:** PostgreSQL requires more schema management than NoSQL, but provides better data integrity and query capabilities for our use case.

---

### Why Redis?

**Chosen:** Redis 7 (in-memory cache & message broker)

**Pros:**
- ✅ **Speed**: Sub-millisecond latency for cached data
- ✅ **Versatility**: Cache, sessions, message queue, pub/sub all in one
- ✅ **Persistence**: AOF + RDB for data durability
- ✅ **Clustering**: Redis Sentinel/Cluster for high availability
- ✅ **Simple API**: Easy to use, well-documented
- ✅ **Memory Efficient**: Optimized data structures, LRU eviction

**Alternatives Considered:**
- **Memcached**: No persistence, no clustering, fewer data types
- **RabbitMQ**: Overkill for simple caching, separate service needed
- **Kafka**: Too complex for caching, better for event streaming at scale
- **ElastiCache**: AWS lock-in, more expensive

**Trade-off:** Redis requires memory management, but provides excellent performance and versatility. Single Redis instance suitable for <10k users, cluster needed for larger scale.

---

### Why Next.js?

**Chosen:** Next.js 14 (React framework)

**Pros:**
- ✅ **Server-Side Rendering (SSR)**: Better SEO, faster initial load
- ✅ **Static Site Generation (SSG)**: Pre-render pages for performance
- ✅ **API Routes**: Build API endpoints alongside frontend (not used, but available)
- ✅ **Image Optimization**: Automatic image optimization and lazy loading
- ✅ **Developer Experience**: Hot reload, TypeScript support, great DX
- ✅ **Production Ready**: Used by Netflix, TikTok, Hulu
- ✅ **React Ecosystem**: Access to all React libraries

**Alternatives Considered:**
- **React (CRA)**: No SSR, slower initial load, worse SEO
- **Vue.js/Nuxt**: Smaller ecosystem, less corporate adoption
- **Angular**: Too heavy, steeper learning curve, opinionated
- **Svelte/SvelteKit**: Smaller ecosystem, fewer resources

**Trade-off:** Next.js adds complexity over plain React, but provides better performance and SEO out of the box.

---

### Why Celery?

**Chosen:** Celery (distributed task queue)

**Pros:**
- ✅ **Async Processing**: Offload long-running tasks (resume parsing, matching)
- ✅ **Python Native**: Works seamlessly with FastAPI/Python stack
- ✅ **Flexible**: Supports multiple brokers (Redis, RabbitMQ, SQS)
- ✅ **Monitoring**: Flower for task monitoring
- ✅ **Retry Logic**: Built-in retry, exponential backoff
- ✅ **Scheduling**: Celery Beat for periodic tasks

**Alternatives Considered:**
- **Dramatiq**: Simpler, but smaller ecosystem, less mature
- **RQ (Redis Queue)**: Simpler, but less features, no scheduling
- **AWS SQS/Lambda**: Vendor lock-in, more expensive at scale
- **Kubernetes Jobs**: Lower-level, more complex, requires K8s

**Trade-off:** Celery adds complexity, but provides robust async task processing with retry, monitoring, and scheduling built-in.

---

### Why Ollama?

**Chosen:** Ollama (local LLM inference)

**Pros:**
- ✅ **Zero Cost**: No API costs, unlimited usage
- ✅ **Privacy**: Data never leaves your infrastructure
- ✅ **Offline**: Works without internet (after model download)
- ✅ **Fast**: Pre-downloaded models, optimized inference
- ✅ **Simple**: Single command to pull models, easy API
- ✅ **GPU Support**: Auto-uses GPU if available
- ✅ **Production Ready**: Stable, actively maintained

**Alternatives Considered:**
- **OpenAI API**: Expensive ($0.03/1K tokens), rate limits, data privacy concerns
- **Hugging Face Transformers**: Slower, more complex setup, larger memory footprint
- **Local Transformers**: Requires more code, GPU setup complexity
- **Anthropic Claude**: Expensive, API-only, no local option

**Trade-off:** Ollama requires local resources (CPU/GPU), but provides cost savings, privacy, and no rate limits compared to cloud APIs.

---

### Why Docker & Docker Compose?

**Chosen:** Docker Compose (containerization)

**Pros:**
- ✅ **Consistency**: Same environment across dev/staging/prod
- ✅ **Isolation**: Services isolated, no dependency conflicts
- ✅ **Easy Setup**: One command to start all services
- ✅ **Portability**: Works on Windows, macOS, Linux
- ✅ **Resource Management**: Easy to scale, configure resources
- ✅ **Development**: Hot reload, easy debugging

**Alternatives Considered:**
- **Kubernetes**: Overkill for <10k users, complex setup
- **Vagrant**: Slower, heavier, less modern
- **Local Installation**: Dependency hell, platform-specific issues
- **Cloud Services (ECS/EKS)**: More expensive, vendor lock-in for dev

**Trade-off:** Docker adds abstraction layer, but provides consistency and easier deployment. Docker Compose suitable for single-server deployment, Kubernetes needed for larger scale.

---

### Overall Technology Stack Rationale

**Theme:** **Production-Ready, Developer-Friendly, Cost-Effective**

1. **FastAPI + PostgreSQL + Redis**: High-performance, scalable, battle-tested stack
2. **Next.js**: Modern frontend with SSR for better UX and SEO
3. **Celery**: Robust async processing for AI-heavy workloads
4. **Ollama**: Cost-effective AI inference with privacy guarantees
5. **Docker**: Consistent deployment across environments

**Philosophy:** Choose technologies that balance performance, developer experience, and operational simplicity. Avoid over-engineering for current scale, but design for future growth.

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
  - **Fully Responsive Design**: World-class mobile-first responsive design
    - Mobile (320px+): Optimized layouts, touch-friendly buttons, stacked cards
    - Tablet (768px+): 2-column grids, improved spacing
    - Desktop (1024px+): Full table views, multi-column layouts
    - All modals, forms, and tables adapt seamlessly to screen size
    - Breakpoints: sm (640px), md (768px), lg (1024px), xl (1280px)

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
│   │   │   ├── ollama_ranking.py  # World-class Ollama-based ranking system
│   │   │   ├── scoring.py  # Smart skill matching & scoring
│   │   │   ├── service.py  # Matching orchestration
│   │   │   └── router.py  # Matching API endpoints
│   │   ├── ai_engine/      # AI reasoning engine
│   │   ├── resumes/
│   │   │   ├── seniority_analyzer.py  # Elite seniority detection with red flags
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

## 📋 API Contracts

### Base URL
```
Production: https://api.hirelens.ai
Development: http://localhost:8000
```

### Authentication

All authenticated endpoints require a Bearer token in the Authorization header:
```
Authorization: Bearer <access_token>
```

**Token Types:**
- **Access Token**: Short-lived (30 minutes default), used for API requests
- **Refresh Token**: Long-lived (7 days default), used to refresh access token

### Response Format

**Success Response:**
```json
{
  "data": { ... },
  "message": "Success message (optional)"
}
```

**Error Response:**
```json
{
  "error": {
    "message": "Human-readable error message",
    "details": "Additional error details",
    "type": "ErrorClassName"
  }
}
```

### HTTP Status Codes

| Code | Meaning | Usage |
|------|---------|-------|
| 200 | OK | Successful GET/PUT/PATCH request |
| 201 | Created | Successful POST request creating a resource |
| 204 | No Content | Successful DELETE request |
| 400 | Bad Request | Invalid request payload or parameters |
| 401 | Unauthorized | Missing or invalid authentication token |
| 403 | Forbidden | Insufficient permissions for the operation |
| 404 | Not Found | Requested resource does not exist |
| 422 | Unprocessable Entity | Validation error in request payload |
| 429 | Too Many Requests | Rate limit exceeded |
| 500 | Internal Server Error | Server-side error |

### Rate Limiting

- **Default**: 60 requests/minute, 1000 requests/hour per user
- **Headers**: Rate limit info in response headers
  - `X-RateLimit-Limit`: Request limit per window
  - `X-RateLimit-Remaining`: Remaining requests in window
  - `X-RateLimit-Reset`: Timestamp when limit resets

### API Endpoints

#### Authentication Endpoints (`/api/v1/auth`)

**POST `/api/v1/auth/register`** - Register new user
- **Request Body:**
  ```json
  {
    "email": "user@example.com",
    "password": "secure_password",
    "full_name": "John Doe",
    "role_names": ["recruiter"]
  }
  ```
- **Response:** `201 Created` - UserResponse
- **Errors:** `400` (validation error), `409` (email exists)

**POST `/api/v1/auth/login`** - Authenticate user
- **Request Body:**
  ```json
  {
    "email": "user@example.com",
    "password": "secure_password"
  }
  ```
- **Response:** `200 OK` - Token (access_token, refresh_token, expires_in)
- **Errors:** `401` (invalid credentials)

**POST `/api/v1/auth/refresh`** - Refresh access token
- **Request Body:**
  ```json
  {
    "refresh_token": "refresh_token_string"
  }
  ```
- **Response:** `200 OK` - Token (new access_token, refresh_token)
- **Errors:** `401` (invalid refresh token)

**GET `/api/v1/auth/me`** - Get current user info
- **Headers:** `Authorization: Bearer <token>` (required)
- **Response:** `200 OK` - UserResponse
- **Errors:** `401` (unauthorized)

---

#### Resume Endpoints (`/api/v1/resumes`)

**POST `/api/v1/resumes/upload`** - Upload and process resume
- **Headers:** `Authorization: Bearer <token>` (required)
- **Content-Type:** `multipart/form-data`
- **Request Body:** Form data with `file` field (PDF only, max 10MB)
- **Response:** `201 Created` - ResumeResponse
  ```json
  {
    "id": 1,
    "file_name": "resume.pdf",
    "file_path": "/uploads/abc123.pdf",
    "status": "processing",
    "quality_score": null,
    "created_at": "2024-01-01T00:00:00Z"
  }
  ```
- **Errors:** `400` (invalid file type/size), `422` (not a resume), `500` (processing error)

**GET `/api/v1/resumes`** - List all resumes
- **Headers:** `Authorization: Bearer <token>` (required)
- **Query Parameters:**
  - `skip`: int (default: 0) - Pagination offset
  - `limit`: int (default: 100, max: 1000) - Page size
  - `status`: str (optional) - Filter by status: "processing", "completed", "failed"
- **Response:** `200 OK` - List[ResumeResponse]

**GET `/api/v1/resumes/{resume_id}`** - Get resume details
- **Headers:** `Authorization: Bearer <token>` (required)
- **Path Parameters:** `resume_id` (int) - Resume ID
- **Response:** `200 OK` - ResumeDetailResponse (includes parsed data, kundali)
- **Errors:** `404` (resume not found)

**POST `/api/v1/resumes/{resume_id}/reprocess`** - Reprocess resume
- **Headers:** `Authorization: Bearer <token>` (required)
- **Path Parameters:** `resume_id` (int) - Resume ID
- **Response:** `200 OK` - ResumeResponse (status: "processing")
- **Errors:** `404` (resume not found), `400` (already processing)

---

#### Job Endpoints (`/api/v1/jobs`)

**POST `/api/v1/jobs`** - Create job description
- **Headers:** `Authorization: Bearer <token>` (required)
- **Request Body:**
  ```json
  {
    "title": "Senior Backend Engineer",
    "company": "Tech Corp",
    "department": "Engineering",
    "raw_text": "We are looking for...",
    "location": "San Francisco, CA",
    "remote_allowed": true,
    "employment_type": "full-time"
  }
  ```
- **Response:** `201 Created` - JobDescriptionResponse
- **Errors:** `400` (validation error), `401` (unauthorized)

**GET `/api/v1/jobs`** - List job descriptions
- **Headers:** `Authorization: Bearer <token>` (required)
- **Query Parameters:**
  - `skip`: int (default: 0)
  - `limit`: int (default: 100, max: 1000)
  - `is_active`: bool (optional) - Filter by active status
- **Response:** `200 OK` - List[JobDescriptionResponse]

**GET `/api/v1/jobs/{job_id}`** - Get job details
- **Headers:** `Authorization: Bearer <token>` (required)
- **Path Parameters:** `job_id` (int) - Job ID
- **Response:** `200 OK` - JobDescriptionDetailResponse (includes parsed_data, raw_text)
- **Errors:** `404` (job not found)

**PUT `/api/v1/jobs/{job_id}`** - Update job description
- **Headers:** `Authorization: Bearer <token>` (required)
- **Path Parameters:** `job_id` (int) - Job ID
- **Request Body:** JobDescriptionUpdate (all fields optional)
- **Response:** `200 OK` - JobDescriptionResponse
- **Errors:** `404` (job not found), `403` (not owner/admin)

**DELETE `/api/v1/jobs/{job_id}`** - Delete (archive) job
- **Headers:** `Authorization: Bearer <token>` (required)
- **Path Parameters:** `job_id` (int) - Job ID
- **Response:** `204 No Content`
- **Errors:** `404` (job not found), `403` (not owner/admin)

---

#### Candidate Endpoints (`/api/v1/candidates`)

**POST `/api/v1/candidates`** - Create candidate
- **Headers:** `Authorization: Bearer <token>` (required)
- **Request Body:**
  ```json
  {
    "first_name": "John",
    "last_name": "Doe",
    "email": "john@example.com",
    "phone": "+1234567890",
    "linkedin_url": "https://linkedin.com/in/johndoe",
    "portfolio_url": "https://johndoe.dev",
    "resume_id": 1,
    "notes": "Strong candidate"
  }
  ```
- **Response:** `201 Created` - CandidateResponse (updates existing if resume_id already has candidate)
- **Errors:** `400` (validation error), `404` (resume not found)

**GET `/api/v1/candidates`** - List candidates
- **Headers:** `Authorization: Bearer <token>` (required)
- **Query Parameters:**
  - `skip`: int (default: 0)
  - `limit`: int (default: 100, max: 1000)
  - `status`: str (optional) - Filter by status
- **Response:** `200 OK` - List[CandidateResponse]

**GET `/api/v1/candidates/{candidate_id}`** - Get candidate details
- **Headers:** `Authorization: Bearer <token>` (required)
- **Path Parameters:** `candidate_id` (int) - Candidate ID
- **Response:** `200 OK` - CandidateResponse (includes kundali summary)
- **Errors:** `404` (candidate not found)

**PUT `/api/v1/candidates/{candidate_id}`** - Update candidate
- **Headers:** `Authorization: Bearer <token>` (required)
- **Path Parameters:** `candidate_id` (int) - Candidate ID
- **Request Body:** CandidateUpdate (all fields optional)
- **Response:** `200 OK` - CandidateResponse
- **Errors:** `404` (candidate not found)

**DELETE `/api/v1/candidates/{candidate_id}`** - Delete candidate
- **Headers:** `Authorization: Bearer <token>` (required)
- **Path Parameters:** `candidate_id` (int) - Candidate ID
- **Response:** `204 No Content`
- **Errors:** `404` (candidate not found), `403` (not owner/admin)

---

#### Matching Endpoints (`/api/v1/matching`)

**POST `/api/v1/matching/match`** - Match candidate to job
- **Headers:** `Authorization: Bearer <token>` (required)
- **Query Parameters:**
  - `candidate_id`: int (required) - Candidate ID
  - `job_id`: int (required) - Job ID
  - `force_recalculate`: bool (default: false) - Force recalculation even if match exists
- **Response:** `201 Created` - MatchDetailResponse
  ```json
  {
    "id": 1,
    "candidate_id": 1,
    "job_description_id": 1,
    "overall_score": 85.5,
    "confidence_level": "high",
    "skill_match_score": 90.0,
    "experience_score": 80.0,
    "project_similarity_score": 85.0,
    "domain_familiarity_score": 75.0,
    "percentile_rank": 95.0,
    "calculated_at": "2024-01-01T00:00:00Z",
    "ai_explanation": {
      "summary": "Strong match...",
      "strengths": [...],
      "weaknesses": [...],
      "recommendations": [...],
      "confidence_score": 0.85,
      "reasoning_quality": "high"
    }
  }
  ```
- **Errors:** `404` (candidate/job not found), `400` (resume quality < 80%)

**GET `/api/v1/matching/job/{job_id}/rankings`** - Get candidate rankings for job
- **Headers:** `Authorization: Bearer <token>` (required)
- **Path Parameters:** `job_id` (int) - Job ID
- **Query Parameters:**
  - `limit`: int (default: 100, max: 1000) - Maximum number of rankings
- **Response:** `200 OK` - List[CandidateRankingResponse] (sorted by score, descending)
- **Note:** This recalculates matches for all candidates (may take time)

**GET `/api/v1/matching/match/{match_id}`** - Get match details
- **Headers:** `Authorization: Bearer <token>` (required)
- **Path Parameters:** `match_id` (int) - Match ID
- **Response:** `200 OK` - MatchDetailResponse
- **Errors:** `404` (match not found)

**POST `/api/v1/matching/candidate/{candidate_id}/find-best-match`** - Find best job for candidate
- **Headers:** `Authorization: Bearer <token>` (required)
- **Path Parameters:** `candidate_id` (int) - Candidate ID
- **Response:** `201 Created` - MatchDetailResponse (best matching job)
- **Note:** Matches candidate to all active jobs, returns best match
- **Errors:** `404` (candidate not found), `404` (no active jobs)

---

### Data Models

**ResumeResponse:**
```json
{
  "id": 1,
  "file_name": "resume.pdf",
  "file_path": "/uploads/abc123.pdf",
  "status": "completed",
  "quality_score": 85.5,
  "created_at": "2024-01-01T00:00:00Z"
}
```

**JobDescriptionResponse:**
```json
{
  "id": 1,
  "title": "Senior Backend Engineer",
  "company": "Tech Corp",
  "department": "Engineering",
  "required_skills": ["Python", "FastAPI", "PostgreSQL"],
  "nice_to_have_skills": ["Docker", "Kubernetes"],
  "experience_years_required": 5,
  "seniority_level": "senior",
  "location": "San Francisco, CA",
  "remote_allowed": true,
  "employment_type": "full-time",
  "is_active": true,
  "created_at": "2024-01-01T00:00:00Z"
}
```

**CandidateResponse:**
```json
{
  "id": 1,
  "first_name": "John",
  "last_name": "Doe",
  "email": "john@example.com",
  "phone": "+1234567890",
  "linkedin_url": "https://linkedin.com/in/johndoe",
  "portfolio_url": "https://johndoe.dev",
  "resume_id": 1,
  "status": "active",
  "notes": "Strong candidate",
  "created_at": "2024-01-01T00:00:00Z"
}
```

**MatchDetailResponse:**
```json
{
  "id": 1,
  "candidate_id": 1,
  "job_description_id": 1,
  "overall_score": 85.5,
  "confidence_level": "high",
  "skill_match_score": 90.0,
  "experience_score": 80.0,
  "project_similarity_score": 85.0,
  "domain_familiarity_score": 75.0,
  "percentile_rank": 95.0,
  "calculated_at": "2024-01-01T00:00:00Z",
  "ai_explanation": {
    "summary": "Strong match with excellent technical skills...",
    "strengths": [
      "5+ years Python/FastAPI experience",
      "Strong PostgreSQL knowledge",
      "Relevant project experience"
    ],
    "weaknesses": [
      "Limited Docker/Kubernetes experience",
      "No experience with microservices at scale"
    ],
    "recommendations": [
      "Consider providing Docker training",
      "Excellent candidate for senior role"
    ],
    "confidence_score": 0.85,
    "reasoning_quality": "high"
  }
}
```

### API Documentation

Interactive API documentation available at:
- **Swagger UI**: http://localhost:8000/api/docs
- **ReDoc**: http://localhost:8000/api/redoc

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
   - **Elite Seniority Assessment**: World-class comprehensive analysis based on entire resume
  - **Never Returns Unknown**: Always determines a level intelligently
  - **Multi-Dimensional Analysis**: Years, titles, responsibilities, technical depth, leadership
  - **Red Flag Detection**: Brutally honest assessment of issues:
    - Job hopping (frequent job changes)
    - Title inflation (senior title but junior responsibilities)
    - Experience mismatch (years don't match claimed seniority)
    - Gap issues (long unexplained gaps)
    - Skill inconsistency (skills don't match experience level)
    - Overstatement (claims don't match evidence)
    - Career regression (moving to lower-level roles)
    - No progression (same level for 5+ years)
    - Weak evidence (vague descriptions, no metrics)
    - Education mismatch
  - **Evidence-Based**: All assessments backed by resume evidence
  - **Positive Signals**: Identifies career progression, leadership, technical depth
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
- Required skills (with smart extraction for full-stack roles)
- Nice-to-have skills
- Experience requirements
- Seniority level
- Education requirements

**Smart Skill Extraction:**
- Automatically extracts REST API for full-stack roles
- Includes HTML/CSS for frontend roles
- Comprehensive skill keyword detection
- Context-aware extraction (required vs nice-to-have)

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

### 3. World-Class AI Matching & Scoring

**Ollama-Based Deep Ranking System:**

The platform uses a **world-class Ollama-based ranking engine** that performs comprehensive, multi-dimensional analysis of candidate-job matches:

**Pipeline Flow:**
1. **Base Rule-Based Scoring**: Initial scores using rule-based engine (skills, experience, projects, domain)
2. **Ollama Deep Analysis**: Comprehensive analysis using Qwen2.5-7B-Instruct via Ollama
   - Deep semantic analysis of entire candidate and job profiles
   - Multi-dimensional scoring with detailed breakdowns
   - Consistent, structured output format
   - World-class matching accuracy
3. **Final Scores**: Uses Ollama analysis scores (fallback to base scores if Ollama unavailable)

**Scoring Dimensions:**
- **Skill Match** (40% weight): 
  - Smart matching with case-insensitive, alias-aware detection
  - Transferable skills (e.g., React → Vue, Java → Spring)
  - Skill depth and proficiency assessment
  - Missing critical skills analysis
  - Nice-to-have skills bonus
- **Experience Alignment** (25% weight):
  - Years of experience vs required
  - Relevant industry experience
  - Role similarity and career progression
  - Experience quality over quantity
- **Project Similarity** (20% weight):
  - Project complexity and scale alignment
  - Technology stack alignment
  - Domain/industry relevance
  - Problem-solving approaches
  - Impact and achievements
- **Domain & Culture Fit** (15% weight):
  - Industry/domain knowledge
  - Team collaboration experience
  - Communication skills
  - Adaptability and learning ability
  - Cultural alignment indicators

**Output Structure:**
- Overall score (0-100) with confidence level
- Dimension scores (skill, experience, project, culture)
- Detailed analysis (matched skills, missing skills, transferable skills)
- Strengths (top 3-5 with explanations)
- Weaknesses/Gaps (top 3-5 with explanations)
- Recommendations (actionable items)
- Hiring recommendation (Strong Match / Good Match / Moderate Match / Weak Match)

**Smart Skill Matching Features:**
- ✅ **Case-Insensitive**: "JavaScript" matches "javascript", "JAVASCRIPT"
- ✅ **Alias Detection**: "JS" matches "JavaScript", "React.js" matches "React"
- ✅ **Fuzzy Matching**: Handles variations and typos
- ✅ **Transferable Skills**: Recognizes related technologies (e.g., Spring → Java)
- ✅ **Plural/Singular**: "Rest APIs" matches "rest api"
- ✅ **Compound Skills**: Handles multi-word skills intelligently
- ✅ **False Positive Prevention**: Prevents "java" matching "javascript"

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

## 🤖 AI Decision Flow

### Resume Parsing Decision Flow

```
Start: PDF Upload
  │
  ├─► File Validation
  │     │
  │     ├─► [PDF?] → NO → ❌ Reject (DOCX/DOC not allowed)
  │     │
  │     ├─► [Size < 10MB?] → NO → ❌ Reject
  │     │
  │     └─► [Valid Resume?] → Validate using text extraction
  │                              │
  │                              ├─► [Score < 20?] → ❌ Reject (Not a resume)
  │                              │
  │                              └─► [Score ≥ 20?] → ✅ Proceed
  │
  ├─► Text Extraction (Rule-based: pdfplumber/pypdf2)
  │     │
  │     └─► raw_text extracted
  │
  ├─► Async Task Queued (Celery)
  │     │
  │     └─► Worker picks up task
  │
  └─► AI Parsing Decision Tree
        │
        ├─► [Ollama Available?]
        │     │
        │     ├─► YES → [Text Model Available?]
        │     │          │
        │     │          ├─► YES → ✅ PRIMARY: Qwen2.5-7B-Instruct (Text-only)
        │     │          │          │
        │     │          │          └─► Use extracted raw_text (best reliability)
        │     │          │
        │     │          └─► NO → Try Vision Model
        │     │                    │
        │     │                    └─► [Vision Model Available?]
        │     │                           │
        │     │                           ├─► YES → Qwen2.5-VL (Vision, uses PDF base64)
        │     │                           │
        │     │                           └─► NO → Fallback Chain
        │     │
        │     └─► NO → Fallback Chain
        │
        └─► Fallback Chain (If Ollama fails)
              │
              ├─► [LayoutLMv3 Available?]
              │     │
              │     ├─► YES → Legacy Vision Parser
              │     │          │
              │     │          └─► PDF → Images → LayoutLMv3 → Section Detection → NER
              │     │
              │     └─► NO → [HURIDOCS Available?]
              │                 │
              │                 ├─► YES → HURIDOCS Layout Analysis (Port 5060)
              │                 │
              │                 └─► NO → [NER Models Available?]
              │                           │
              │                           ├─► YES → spaCy NER Parser (fast, CPU-friendly)
              │                           │
              │                           └─► NO → Rule-based Parser (pattern matching)
              │
        └─► Post-Processing
              │
              ├─► Skills Cleaning (remove company names from skills)
              ├─► Email/Phone Regex Fallback
              ├─► URL Normalization (add https://)
              ├─► Experience Calculation (with overlap handling)
              ├─► Quality Score Calculation
              │
              └─► Seniority Analysis
                    │
                    └─► [Ollama Available?]
                          │
                          ├─► YES → ✅ Ollama-based Elite Seniority Analyzer
                          │          │
                          │          ├─► Multi-dimensional analysis
                          │          ├─► Red flag detection
                          │          └─► Never returns "unknown"
                          │
                          └─► NO → Rule-based seniority detection
```

### Matching Decision Flow

```
Start: Match Request (candidate_id, job_id)
  │
  ├─► Check Existing Match
  │     │
  │     ├─► [Match Exists?] → YES → [force_recalculate?]
  │     │                          │
  │     │                          ├─► NO → ✅ Return Cached Result
  │     │                          │
  │     │                          └─► YES → Recalculate
  │     │
  │     └─► NO → Calculate New Match
  │
  ├─► Base Rule-Based Scoring (Fast)
  │     │
  │     ├─► Skill Matching (40% weight)
  │     │     ├─► Case-insensitive matching
  │     │     ├─► Alias detection (JS = JavaScript)
  │     │     ├─► Fuzzy matching
  │     │     ├─► Transferable skills (React → Vue)
  │     │     └─► Missing skills penalty
  │     │
  │     ├─► Experience Alignment (25% weight)
  │     │     ├─► Years vs required
  │     │     ├─► Industry relevance
  │     │     └─► Career progression
  │     │
  │     ├─► Project Similarity (20% weight)
  │     │     ├─► Tech stack alignment
  │     │     ├─► Complexity matching
  │     │     └─► Domain relevance
  │     │
  │     └─► Domain & Culture Fit (15% weight)
  │           ├─► Industry knowledge
  │           ├─► Communication skills
  │           └─► Adaptability
  │
  ├─► Deep Analysis Decision
  │     │
  │     ├─► [Ollama Available?]
  │     │     │
  │     │     ├─► YES → ✅ Ollama Deep Ranking Analysis
  │     │     │          │
  │     │     │          ├─► Comprehensive candidate-job analysis
  │     │     │          ├─► Multi-dimensional scoring
  │     │     │          ├─► Detailed breakdowns
  │     │     │          ├─► Strengths/weaknesses extraction
  │     │     │          └─► Recommendations generation
  │     │     │
  │     │     └─► NO → Use Base Scores Only
  │     │
  └─► AI Explanation Generation
        │
        ├─► [Ollama Analysis Available?]
        │     │
        │     ├─► YES → Use Ollama Analysis for Explanation
        │     │
        │     └─► NO → [AI_PROVIDER Setting?]
        │                 │
        │                 ├─► "openai" → OpenAI GPT-4 (if key available)
        │                 │
        │                 ├─► "huggingface" → Hugging Face Mistral-7B
        │                 │
        │                 └─► "auto" → Try OpenAI, fallback to Hugging Face
        │
        └─► Cache Result (Redis, 24h for embeddings, 1h for explanations)
```

## 📈 Scaling Strategy (100 → 1M Users)

### Phase 1: Single Server (100-1,000 Users)

**Current Architecture:**
- Single FastAPI instance
- Single PostgreSQL database
- Single Redis instance
- Single Celery worker
- All services on one server

**Capacity:**
- ~100 concurrent users
- ~1,000 resume uploads/day
- ~5,000 matches/day
- ~10GB database size

**Cost:** ~$50-100/month (single VPS)

**Limitations:**
- No horizontal scaling
- Single point of failure
- Limited to one server's resources

---

### Phase 2: Horizontal Scaling (1,000-10,000 Users)

**Changes Required:**

1. **Load Balancing**
   ```
   Nginx/HAProxy → [FastAPI Instance 1, FastAPI Instance 2, ..., FastAPI Instance N]
   ```
   - Multiple FastAPI instances behind load balancer
   - Session stickiness or stateless JWT tokens
   - Health checks and auto-recovery

2. **Database Scaling**
   ```
   Primary PostgreSQL → [Read Replica 1, Read Replica 2, ...]
   ```
   - Primary for writes
   - 2-3 read replicas for read-heavy queries
   - Connection pooling (PgBouncer)
   - Database size: ~100GB

3. **Redis Cluster**
   ```
   Redis Sentinel → [Redis Master, Redis Replica 1, Redis Replica 2]
   ```
   - Redis Cluster for high availability
   - Separate Redis instances for cache, sessions, Celery
   - Persistence enabled (AOF + RDB)

4. **Celery Scaling**
   ```
   Redis Message Queue → [Worker Pool 1 (4 workers), Worker Pool 2 (4 workers), ...]
   ```
   - Multiple Celery worker pools
   - Separate queues: `resume_processing`, `matching`, `embeddings`
   - Auto-scaling based on queue length

5. **File Storage**
   ```
   Local Storage → S3/MinIO Object Storage
   ```
   - Migrate to S3-compatible storage
   - CDN for faster file access
   - Automatic backups

**Capacity:**
- ~1,000 concurrent users
- ~10,000 resume uploads/day
- ~50,000 matches/day
- ~100GB database size

**Infrastructure:**
- 3-5 API servers (2 CPU, 4GB RAM each)
- Primary DB + 2 read replicas (4 CPU, 16GB RAM each)
- Redis Cluster (3 nodes, 4GB RAM each)
- 3-5 Celery worker servers (4 CPU, 8GB RAM each)

**Cost:** ~$500-1,000/month

---

### Phase 3: Microservices (10,000-100,000 Users)

**Service Decomposition:**

```
┌──────────────────────────────────────────────────────────────┐
│  API Gateway (Kong/Traefik)                                  │
│  - Routing, Rate Limiting, Authentication                    │
└────────────────────┬─────────────────────────────────────────┘
                     │
     ┌───────────────┼───────────────┐
     │               │               │
     ↓               ↓               ↓
┌─────────┐   ┌──────────┐   ┌──────────┐
│ Resume  │   │  Job     │   │ Matching │
│ Service │   │ Service  │   │ Service  │
└─────────┘   └──────────┘   └──────────┘
     │               │               │
     └───────────────┼───────────────┘
                     │
     ┌───────────────┼───────────────┐
     │               │               │
     ↓               ↓               ↓
┌─────────┐   ┌──────────┐   ┌──────────┐
│Resume DB│   │ Job DB   │   │Match DB  │
└─────────┘   └──────────┘   └──────────┘
```

**Service Details:**

1. **Resume Service**
   - Own database (PostgreSQL)
   - Own cache (Redis)
   - Handles resume upload, parsing, storage
   - Async via Celery workers

2. **Job Service**
   - Own database (PostgreSQL)
   - Own cache (Redis)
   - Handles job creation, parsing, management

3. **Matching Service**
   - Own database (PostgreSQL, optimized for read-heavy)
   - Own cache (Redis, for match results)
   - Handles matching, ranking, explanations
   - Communicates with Resume & Job services via gRPC/REST

4. **AI Service (Shared)**
   - Ollama cluster (multiple instances)
   - Model serving layer
   - Shared across all services

5. **Shared Services**
   - Authentication Service (JWT tokens)
   - Notification Service (WebSockets)
   - Analytics Service (Events tracking)

**Communication:**
- Service-to-service: gRPC (internal) or REST
- Async: RabbitMQ/Kafka (message queue)
- Service Discovery: Consul/etcd

**Capacity:**
- ~10,000 concurrent users
- ~100,000 resume uploads/day
- ~500,000 matches/day
- ~1TB database size (distributed)

**Infrastructure:**
- Kubernetes cluster (15-20 nodes)
- API Gateway: 3 instances
- Each microservice: 3-5 instances
- Database per service: Primary + 2 replicas
- Redis Cluster: 5-7 nodes

**Cost:** ~$5,000-10,000/month

---

### Phase 4: Multi-Region (100,000-1M Users)

**Global Architecture:**

```
Region 1 (US East)          Region 2 (EU)              Region 3 (APAC)
┌──────────────┐           ┌──────────────┐           ┌──────────────┐
│ Full Stack   │           │ Full Stack   │           │ Full Stack   │
│ - All Services│           │ - All Services│           │ - All Services│
│ - Read Replicas│          │ - Read Replicas│          │ - Read Replicas│
└──────┬───────┘           └──────┬───────┘           └──────┬───────┘
       │                          │                          │
       └──────────────┬───────────┴───────────┬──────────────┘
                      │                       │
              ┌───────▼────────┐      ┌───────▼────────┐
              │ Global Load    │      │ Global Database│
              │ Balancer       │      │ (Primary)      │
              │ (GeoDNS)       │      │ Cross-Region   │
              └────────────────┘      │ Replication    │
                                      └────────────────┘
```

**Key Features:**

1. **Multi-Region Deployment**
   - Full stack in 3+ regions
   - Users routed to nearest region
   - Active-active configuration

2. **Global Database**
   - Primary in one region
   - Cross-region read replicas
   - Write conflicts resolved via vector clocks
   - Eventual consistency for reads

3. **CDN & Edge Caching**
   - CloudFront/Cloudflare for static assets
   - Edge caching for API responses
   - Reduced latency worldwide

4. **Event-Driven Architecture**
   - Kafka/RabbitMQ for cross-region messaging
   - Event sourcing for audit trails
   - CQRS for read/write separation

5. **Monitoring & Observability**
   - Distributed tracing (Jaeger/Zipkin)
   - Centralized logging (ELK Stack)
   - Metrics (Prometheus + Grafana)
   - APM (New Relic/Datadog)

**Capacity:**
- ~100,000 concurrent users globally
- ~1M resume uploads/day
- ~5M matches/day
- ~10TB+ database size (distributed)

**Infrastructure:**
- 3 regions × 20-30 Kubernetes nodes each
- Global load balancer (GeoDNS)
- Database replication (PostgreSQL streaming replication)
- Kafka cluster for event streaming
- Multi-region Redis (Redis Sentinel)

**Cost:** ~$50,000-100,000/month

---

### Migration Path

**Step 1: Prepare for Scaling (Week 1-2)**
- [ ] Add database read replicas
- [ ] Implement connection pooling
- [ ] Add Redis cluster
- [ ] Separate Celery queues
- [ ] Load testing

**Step 2: Horizontal Scaling (Week 3-4)**
- [ ] Set up load balancer
- [ ] Deploy multiple API instances
- [ ] Scale Celery workers
- [ ] Migrate to S3 storage
- [ ] Monitoring & alerting

**Step 3: Microservices Migration (Month 2-3)**
- [ ] Extract Resume Service
- [ ] Extract Job Service
- [ ] Extract Matching Service
- [ ] Implement service discovery
- [ ] Update API Gateway

**Step 4: Multi-Region (Month 4-6)**
- [ ] Deploy to second region
- [ ] Set up database replication
- [ ] Configure GeoDNS
- [ ] Cross-region testing
- [ ] Disaster recovery plan

---

### Performance Targets

| Metric | 100 Users | 10K Users | 1M Users |
|--------|-----------|-----------|----------|
| API Response Time | <200ms | <200ms | <200ms |
| Resume Processing | <30s | <30s | <30s |
| Match Calculation | <5s | <5s | <5s |
| Database Query | <50ms | <100ms | <150ms |
| Cache Hit Rate | >80% | >85% | >90% |
| Uptime | 99% | 99.9% | 99.99% |

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
- ✅ World-class Ollama-based ranking system (deep matching)
- ✅ Smart skill matching (case-insensitive, aliases, fuzzy)
- ✅ Elite seniority detection (never unknown, red flag detection)
- ✅ Explainable AI
- ✅ Qwen text-based resume parsing (PRIMARY) - text extraction first, then Qwen text-only model
- ✅ LayoutLMv3 support (fallback)
- ✅ Ollama integration for fast inference
- ✅ GPU acceleration (optional)
- ✅ World-class AI-powered resume parsing with quality scoring
- ✅ Quality indicators and reprocessing system
- ✅ Interactive recruiter dashboard with tabs
- ✅ Job creation with AI parsing (enhanced skill extraction)
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

### Latest Features (v2.1 - World-Class Ranking & Elite Seniority)

**World-Class Ollama-Based Ranking System:**
- ✨ **Deep Candidate-Job Matching**: Comprehensive analysis using Ollama Qwen2.5-7B-Instruct
  - Multi-dimensional scoring (skills, experience, projects, domain, culture)
  - Detailed analysis with matched skills, missing skills, transferable skills
  - Strengths, weaknesses, and recommendations with explanations
  - Hiring recommendations (Strong Match / Good Match / Moderate Match / Weak Match)
  - Consistent, structured output format
  - World-class matching accuracy
- ✨ **Smart Skill Matching**: Advanced skill detection system
  - Case-insensitive matching ("JavaScript" = "javascript" = "JAVASCRIPT")
  - Alias detection ("JS" = "JavaScript", "React.js" = "React")
  - Fuzzy matching for variations and typos
  - Transferable skills recognition (Spring → Java, React → Vue)
  - Plural/singular handling ("Rest APIs" = "rest api")
  - False positive prevention (prevents "java" matching "javascript")
- ✨ **Enhanced Job Parser**: Improved skill extraction
  - Automatic REST API extraction for full-stack roles
  - HTML/CSS inclusion for frontend roles
  - Context-aware skill detection

**Elite Seniority Detection System:**
- ✨ **Comprehensive Resume Analysis**: Analyzes entire resume, not just title
  - Never returns "unknown" - always determines level intelligently
  - Multi-dimensional analysis (years, titles, responsibilities, technical depth)
  - Evidence-based reasoning with confidence scores
- ✨ **Brutal Red Flag Detection**: Honest assessment of issues
  - Job hopping detection (frequent job changes)
  - Title inflation (senior title but junior responsibilities)
  - Experience mismatch (years don't match claimed seniority)
  - Gap issues (long unexplained gaps)
  - Skill inconsistency (skills don't match experience level)
  - Overstatement (claims don't match evidence)
  - Career regression (moving to lower-level roles)
  - No progression (same level for 5+ years)
  - Weak evidence (vague descriptions, no metrics)
  - Education mismatch
- ✨ **Positive Signal Detection**: Identifies strengths
  - Career progression indicators
  - Leadership evidence
  - Technical depth indicators
  - Measurable impact and achievements

### Previous Features (v2.0 - Qwen Text-Based Architecture)

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
