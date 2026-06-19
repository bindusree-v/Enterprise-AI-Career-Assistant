# CareerGPT — Enterprise AI Career Assistant

A production-grade AI SaaS platform that transforms resumes into personalized career intelligence using RAG, LangGraph agents, and OpenAI.

```
Resume PDF → Extract → Embed → RAG Pipeline → AI Agents → Career Insights
```

## Architecture

```
┌─────────────────────────────────────────────────────┐
│                   React Frontend                     │
│  Upload │ Dashboard │ ATS │ Skills │ Chat │ Jobs     │
└────────────────────┬────────────────────────────────┘
                     │ REST API
┌────────────────────▼────────────────────────────────┐
│              FastAPI Backend                         │
│                                                     │
│  ┌──────────┐  ┌──────────┐  ┌──────────────────┐  │
│  │  Routers │  │ Services │  │   AI Agents       │  │
│  │  /upload │  │  PDF     │  │  1. ATS Analyzer  │  │
│  │  /ats    │  │  Resume  │  │  2. Skill Gap     │  │
│  │  /skills │  │  Chat    │  │  3. Interview     │  │
│  │  /chat   │  └──────────┘  │  4. Career Adv.   │  │
│  └──────────┘                │  5. Job Matcher   │  │
│                              └────────┬──────────┘  │
│  ┌──────────────────────────────┐     │              │
│  │     RAG Pipeline             │◄────┘              │
│  │  Retrieve → Augment → Gen    │                    │
│  └──────────┬───────────────────┘                    │
│             │                                        │
│  ┌──────────▼────────┐  ┌────────────────────────┐  │
│  │   ChromaDB        │  │   SQLite / Postgres     │  │
│  │  (Vector Store)   │  │   (Metadata + History)  │  │
│  └───────────────────┘  └────────────────────────┘  │
└─────────────────────────────────────────────────────┘
```

## Quick Start

### Prerequisites
- Python 3.11+
- Node.js 20+
- OpenAI API key

### 1. Backend Setup

```bash
cd backend
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env
# Edit .env and set OPENAI_API_KEY=your_key_here

python main.py
# API runs at http://localhost:8000
# Docs at   http://localhost:8000/docs
```

### 2. Frontend Setup

```bash
cd frontend
npm install
npm run dev
# App runs at http://localhost:3000
```

### 3. Docker Compose (Full Stack)

```bash
cp backend/.env.example backend/.env
# Set OPENAI_API_KEY in backend/.env

docker-compose up --build
# Frontend: http://localhost:3000
# Backend:  http://localhost:8000
# API Docs: http://localhost:8000/docs
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/upload-resume` | Upload PDF resume |
| `POST` | `/api/extract-text` | Extract & parse resume |
| `POST` | `/api/generate-embeddings` | Create vector embeddings |
| `POST` | `/api/analyze-resume` | General quality analysis |
| `POST` | `/api/ats-score` | ATS compatibility score |
| `POST` | `/api/skill-gap-analysis` | Skill gap + learning roadmap |
| `POST` | `/api/interview-questions` | Personalized questions |
| `POST` | `/api/career-suggestions` | Career path recommendations |
| `POST` | `/api/job-recommendations` | AI job matching |
| `POST` | `/api/chat` | Multi-turn RAG chatbot |
| `GET`  | `/health` | Health check |
| `GET`  | `/docs` | Swagger UI |

## Typical API Flow

```bash
# 1. Upload resume
RESUME_ID=$(curl -s -X POST http://localhost:8000/api/upload-resume \
  -F "file=@resume.pdf" | jq -r .resume_id)

# 2. Extract text (builds structured profile)
curl -X POST http://localhost:8000/api/extract-text \
  -H "Content-Type: application/json" \
  -d "{\"resume_id\": \"$RESUME_ID\"}"

# 3. Generate embeddings (required for all analysis)
curl -X POST http://localhost:8000/api/generate-embeddings \
  -H "Content-Type: application/json" \
  -d "{\"resume_id\": \"$RESUME_ID\"}"

# 4. Get ATS score against a job description
curl -X POST http://localhost:8000/api/ats-score \
  -H "Content-Type: application/json" \
  -d "{\"resume_id\": \"$RESUME_ID\", \"job_description\": \"We need a Python developer...\"}"
```

## Project Structure

```
careergpt/
├── backend/
│   ├── app/
│   │   ├── agents/           # LangGraph AI agents (5 specialists)
│   │   ├── models/           # DB models + Pydantic schemas
│   │   ├── rag/              # RAG pipeline
│   │   ├── routers/          # FastAPI route handlers
│   │   ├── services/         # Business logic
│   │   ├── utils/            # File + text utilities
│   │   ├── vectorstore/      # ChromaDB integration
│   │   ├── config.py         # Settings with Pydantic
│   │   └── logging_config.py # Structured logging
│   ├── tests/
│   ├── data/                 # Runtime data (gitignored)
│   ├── Dockerfile
│   ├── main.py
│   └── requirements.txt
│
├── frontend/
│   ├── src/
│   │   ├── components/       # Reusable UI components
│   │   ├── hooks/            # usePipeline, etc.
│   │   ├── lib/              # API client (axios)
│   │   ├── pages/            # Route-level page components
│   │   └── store/            # Context + useReducer state
│   ├── Dockerfile
│   └── nginx.conf
│
├── .github/workflows/ci.yml  # GitHub Actions CI/CD
├── docker-compose.yml
└── README.md
```

## Running Tests

```bash
cd backend
pytest tests/ -v --cov=app
```

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `OPENAI_API_KEY` | ✅ | Your OpenAI API key |
| `OPENAI_MODEL` | — | Chat model (default: `gpt-4o`) |
| `OPENAI_EMBEDDING_MODEL` | — | Embedding model (default: `text-embedding-3-small`) |
| `DATABASE_URL` | — | SQLAlchemy URL (default: SQLite) |
| `CHROMA_PERSIST_DIR` | — | ChromaDB storage path |
| `MAX_FILE_SIZE_MB` | — | Upload limit (default: 10) |
| `SECRET_KEY` | ✅ prod | JWT signing key |
| `CORS_ORIGINS` | — | Allowed frontend origins |

## Deployment (AWS ECS)

The CI/CD pipeline in `.github/workflows/ci.yml` will:
1. Run tests on every PR
2. Build and push Docker images to GHCR on `main`
3. Trigger ECS rolling deployment

Set these GitHub secrets:
- `AWS_ACCESS_KEY_ID`
- `AWS_SECRET_ACCESS_KEY`  
- `AWS_REGION`
