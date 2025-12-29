# HireLens AI - Architecture Documentation

## Overview

HireLens AI is a production-grade AI-powered hiring intelligence platform designed to help recruiters and hiring managers make data-driven hiring decisions through semantic matching and explainable AI.

## Architecture Style

**Phase 1: Modular Monolith**
- Single codebase with clear module boundaries
- FastAPI backend with modular structure
- Next.js frontend
- PostgreSQL for primary data storage
- Redis for caching and session management
- Celery for async task processing

**Phase 2: Microservices-Ready**
- Architecture designed for easy migration to microservices
- Clear service boundaries documented
- Independent scaling capabilities

## System Architecture

```
┌─────────────────┐
│   Frontend      │  Next.js + React + TailwindCSS
│   (Next.js)     │
└────────┬────────┘
         │ HTTP/REST
         │
┌────────▼─────────────────────────────────────┐
│           API Gateway (FastAPI)                │
│  ┌─────────────────────────────────────────┐  │
│  │  Authentication & RBAC                   │  │
│  │  Request Middleware                     │  │
│  │  Error Handling                         │  │
│  └─────────────────────────────────────────┘  │
└────────┬──────────────────────────────────────┘
         │
    ┌────┴────┬──────────┬──────────┬──────────┐
    │         │          │          │          │
┌───▼───┐ ┌──▼───┐ ┌────▼────┐ ┌───▼───┐ ┌───▼───┐
│ Auth  │ │Resume│ │  Jobs   │ │Match  │ │  AI   │
│Module │ │Module│ │ Module  │ │Module │ │Engine │
└───┬───┘ └──┬───┘ └────┬────┘ └───┬───┘ └───┬───┘
    │        │          │          │          │
    └────────┴──────────┴──────────┴──────────┘
                    │
         ┌──────────┴──────────┐
         │                      │
    ┌────▼────┐          ┌─────▼─────┐
    │PostgreSQL│          │   Redis   │
    │ Database│          │  Cache   │
    └────┬────┘          └─────┬─────┘
         │                      │
         └──────────┬───────────┘
                    │
            ┌───────▼───────┐
            │ Celery Workers│
            │ (Async Tasks) │
            └───────────────┘
```

## Core Layers

### 1. API Layer (FastAPI)
- RESTful API endpoints
- Request/response validation with Pydantic
- Authentication middleware
- Error handling
- Rate limiting (configurable)

### 2. Authentication & RBAC
- JWT-based authentication
- Role-Based Access Control (RBAC)
- Token refresh mechanism
- Password hashing with bcrypt

**Roles:**
- **Admin**: Full system access
- **Recruiter**: Manage jobs, candidates, resumes, view matches
- **Hiring Manager**: Read-only access to insights

### 3. Resume Processing
- PDF and DOCX parsing
- Text extraction
- Structured data extraction:
  - Skills
  - Experience
  - Education
  - Projects
  - Certifications
- Version control for auditability

### 4. Job Description Intelligence
- Text parsing and extraction
- Skill identification (required vs nice-to-have)
- Experience requirements extraction
- Seniority level detection
- Semantic embedding generation

### 5. AI Matching & Reasoning Engine
**Core Responsibilities:**
- Semantic resume ↔ JD matching using embeddings
- Multi-dimensional scoring
- Explainable AI reasoning

**Scoring Dimensions:**
- Skill Match (40% weight)
- Experience Relevance (25% weight)
- Project Similarity (20% weight)
- Domain Familiarity (15% weight)

**Explainability:**
Every match includes:
- Summary explanation
- Strengths (3-5 points)
- Weaknesses/Gaps (3-5 points)
- Recommendations (2-3 actionable items)
- Confidence level (High/Medium/Low)

### 6. Scoring & Ranking Engine
- Weighted multi-dimensional scoring
- Percentile-based ranking
- Confidence band classification
- Deterministic + AI-assisted hybrid approach

### 7. Async Task Processing
**Use Cases:**
- Resume parsing (CPU-intensive)
- AI inference (API calls)
- Bulk candidate scoring
- Embedding generation

**Implementation:**
- Celery workers
- Redis as message broker
- Task status tracking
- Retry logic with exponential backoff
- Failure handling

### 8. Caching & Cost Optimization
**Strategy:**
- Redis caching for:
  - Parsed resumes (hash-based keys)
  - JD embeddings
  - AI explanations
  - Match results
- TTL-based invalidation
- Cost-aware AI API calls (cache-first)

### 9. Data Layer (PostgreSQL)
**Core Tables:**
- `users` - User accounts
- `roles` - RBAC roles
- `resumes` - Resume files and metadata
- `resume_versions` - Versioned parsed data
- `job_descriptions` - Job postings
- `candidates` - Candidate profiles
- `match_results` - Match scores
- `ai_explanations` - AI-generated explanations
- `audit_logs` - System audit trail

**Design Principles:**
- Normalized core schema
- JSON fields for flexible AI outputs
- Full auditability
- Indexed for performance

### 10. Observability
- Structured logging (structlog)
- Request correlation IDs
- Error tracking
- Performance metrics
- Clean exception handling

## Data Flow

### Resume Upload Flow
```
1. User uploads resume → API
2. File saved to disk
3. Resume record created (status: pending)
4. Celery task triggered
5. Worker extracts text
6. Worker parses structured data
7. Resume version created
8. Status updated to "completed"
```

### Matching Flow
```
1. User requests match (candidate + job)
2. Check cache for existing match
3. If not cached:
   a. Load candidate resume data
   b. Load job description data
   c. Calculate scores (4 dimensions)
   d. Generate AI explanation
   e. Store match result
   f. Cache result
4. Return match with explanation
```

### Ranking Flow
```
1. User requests rankings for job
2. For each candidate:
   a. Calculate/retrieve match
   b. Store scores
3. Sort by overall score
4. Calculate percentile ranks
5. Return ranked list
```

## Technology Stack

### Backend
- **Framework**: FastAPI 0.104+
- **Database**: PostgreSQL 15
- **Cache**: Redis 7
- **Task Queue**: Celery 5.3
- **AI/LLM**: OpenAI GPT-4, Sentence Transformers
- **Document Processing**: pdfplumber, python-docx

### Frontend
- **Framework**: Next.js 14
- **UI Library**: React 18
- **Styling**: TailwindCSS
- **State Management**: React Query
- **HTTP Client**: Axios

### Infrastructure
- **Containerization**: Docker + Docker Compose
- **Orchestration**: Docker Compose (Phase 1), Kubernetes-ready (Phase 2)

## Security Considerations

1. **Authentication**: JWT tokens with expiration
2. **Password Security**: bcrypt hashing
3. **RBAC**: Enforced at service layer
4. **Input Validation**: Pydantic schemas
5. **File Upload**: Size limits, type validation
6. **CORS**: Configurable origins
7. **Rate Limiting**: Per-user limits
8. **Audit Logging**: All actions logged

## Scalability Strategy

### 100 Users
- Single server deployment
- Current architecture sufficient
- No special optimizations needed

### 10k Users
- Horizontal scaling of API servers
- Database read replicas
- Redis cluster
- Celery worker scaling
- CDN for static assets

### 1M Users
- Microservices migration:
  - Auth service
  - Resume service
  - Matching service
  - AI service
- Database sharding
- Message queue (RabbitMQ/Kafka)
- Caching layer (Redis Cluster)
- Load balancers
- Auto-scaling groups

## Trade-offs

### Why FastAPI?
- **Pros**: High performance, async support, automatic API docs, type hints
- **Cons**: Smaller ecosystem than Django/Flask

### Why Redis?
- **Pros**: Fast, supports caching + message broker, simple setup
- **Cons**: Memory-based (cost at scale)

### Why Async?
- **Pros**: Better I/O handling, scalability, non-blocking operations
- **Cons**: More complex debugging, requires async-aware libraries

### Why Modular Monolith First?
- **Pros**: Simpler deployment, easier development, single codebase
- **Cons**: Limited independent scaling, single point of failure

## Limitations & Future Roadmap

### Current Limitations
1. Single-tenant (no multi-tenancy)
2. No ATS integrations
3. Basic bias detection (future enhancement)
4. Limited real-time features

### Future Enhancements
1. **Multi-tenant SaaS**: Tenant isolation, billing
2. **ATS Integrations**: Greenhouse, Lever, Workday
3. **Bias & Fairness Analysis**: Demographic parity, fairness metrics
4. **Real-time Collaboration**: WebSocket updates
5. **Candidate Feedback Engine**: Candidate-side insights
6. **Advanced Analytics**: Hiring funnel metrics, time-to-hire
7. **Mobile App**: React Native application

## Deployment

### Development
```bash
docker-compose up
```

### Production
- Use orchestration (Kubernetes, ECS)
- Environment-specific configs
- Database backups
- Monitoring (Prometheus, Grafana)
- Log aggregation (ELK, Datadog)

## Monitoring & Observability

- **Logging**: Structured JSON logs
- **Metrics**: Prometheus-compatible endpoints
- **Tracing**: Correlation IDs
- **Error Tracking**: Sentry integration
- **Health Checks**: `/health` endpoint

