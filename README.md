# ScoutOps - NBA Scouting Platform

ScoutOps is a full-stack web application for managing NBA player scouting notes and reports. Built with FastAPI, PostgreSQL, React, and TypeScript.

## Project Structure

```
Scout_OPS_/
├── backend/              # FastAPI backend
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py      # FastAPI app and routes
│   │   ├── models.py    # SQLAlchemy models
│   │   ├── schemas.py   # Pydantic schemas
│   │   ├── crud.py      # Database operations
│   │   ├── database.py  # Database configuration
│   │   └── config.py    # Settings management
│   ├── tests/           # Backend tests
│   ├── requirements.txt
│   └── .env            # Environment variables (create from .env.example)
│
├── frontend/            # React + TypeScript frontend
│   ├── src/
│   │   ├── api/        # API client
│   │   ├── components/ # React components
│   │   ├── pages/      # Page components
│   │   ├── types/      # TypeScript types
│   │   ├── App.tsx
│   │   └── main.tsx
│   ├── package.json
│   └── vite.config.ts
│
└── README.md
```

## Features

### Week 1 - Scout Notes
- ✅ **Player Management**: Full CRUD operations for players
- ✅ **Note Management**: Create, read, update, and delete scouting notes
- ✅ **Search & Filter**: Filter players by name, team, position
- ✅ **Clean UI**: Modern, responsive design with smooth animations
- ✅ **Data Persistence**: PostgreSQL database with SQLAlchemy ORM
- ✅ **Tests**: Comprehensive test suite for backend API

### Week 2 - RAG System
- ✅ **Hybrid Search**: Combines keyword (PostgreSQL tsvector) and semantic search (embeddings)
- ✅ **AI-Powered Answers**: Google Gemini generates grounded answers with citations
- ✅ **Citation System**: Every claim cited with [1], [2], etc.
- ✅ **Semantic Embeddings**: all-MiniLM-L6-v2 for meaning-based search
- ✅ **Confidence Scoring**: High/Medium/Low based on available information
- ✅ **Interactive Citations**: Click citations to view source notes

## Tech Stack

### Backend
- **FastAPI**: Modern, fast web framework with async support
- **PostgreSQL**: Robust relational database
- **SQLAlchemy**: SQL toolkit and ORM
- **Pydantic**: Data validation using Python type annotations
- **Pytest**: Testing framework

### Frontend
- **React 18**: UI library with hooks
- **TypeScript**: Type-safe JavaScript
- **Vite**: Next-generation frontend tooling
- **Axios**: HTTP client
- **React Router**: Client-side routing

## Prerequisites

### Option 1: Docker (Recommended)
- Docker Desktop installed
- Docker Compose installed

### Option 2: Manual Setup
- Python 3.9+
- Node.js 18+
- PostgreSQL 14+

## Quick Start with Docker

### Start Everything with One Command

```bash
# Navigate to project root
cd Scout_OPS_

# Start all services (database, backend, frontend)
docker-compose up

# Or run in background
docker-compose up -d
```

This will start:
- **PostgreSQL Database**: `localhost:5433`
- **Backend API**: `http://localhost:8000` (API docs: `http://localhost:8000/docs`)
- **Frontend**: `http://localhost:5173`

### Stop All Services

```bash
docker-compose down

# To also remove database data
docker-compose down -v
```

### View Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f backend
docker-compose logs -f frontend
docker-compose logs -f db
```

### Seed Sample Data

```bash
# With Docker running
curl -X POST http://localhost:8000/api/seed
```

Or visit http://localhost:8000/docs and use the `/api/seed` endpoint.

## Manual Setup Instructions

### 1. Clone the Repository

```bash
git clone <repository-url>
cd Scout_OPS_
```

### 2. Database Setup

Create a PostgreSQL database:

```bash
# Access PostgreSQL
psql -U postgres

# Create database and user
CREATE DATABASE scoutops_db;
CREATE USER scoutops_user WITH PASSWORD 'scoutops_password';
GRANT ALL PRIVILEGES ON DATABASE scoutops_db TO scoutops_user;
\q
```

### 3. Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Create .env file
cp .env.example .env

# Edit .env file with your database credentials
# DATABASE_URL=postgresql://scoutops_user:scoutops_password@localhost:5432/scoutops_db
```

### 4. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# The frontend will proxy API requests to http://localhost:8000
```

### 5. Running the Application

You need two terminal windows:

**Terminal 1 - Backend:**
```bash
cd backend
# Activate virtual environment first
uvicorn app.main:app --reload --port 8000
```

The API will be available at: http://localhost:8000
API documentation: http://localhost:8000/docs

**Terminal 2 - Frontend:**
```bash
cd frontend
npm run dev
```

The frontend will be available at: http://localhost:3000

### 6. Seed Sample Data (Optional)

To populate the database with sample players and notes:

```bash
# Make a POST request to the seed endpoint
curl -X POST http://localhost:8000/api/seed
```

Or visit http://localhost:8000/docs and use the `/api/seed` endpoint.

## Running Tests

### Backend Tests

```bash
cd backend
# Activate virtual environment
pytest
```

## API Endpoints

### Players
- `GET /api/players` - List all players (with optional filters)
- `GET /api/players/{id}` - Get player details with notes
- `POST /api/players` - Create a new player
- `PUT /api/players/{id}` - Update a player
- `DELETE /api/players/{id}` - Delete a player

### Notes
- `GET /api/notes` - List all notes (with optional filters)
- `GET /api/notes/{id}` - Get a specific note
- `POST /api/notes` - Create a new note
- `PUT /api/notes/{id}` - Update a note
- `DELETE /api/notes/{id}` - Delete a note

### RAG Endpoints (Week 2)
- `POST /api/rag/retrieve` - Retrieve relevant notes using hybrid search
- `POST /api/rag/generate` - Generate AI answer with citations

### Utility
- `POST /api/seed` - Seed database with sample data
- `GET /health` - Health check

### Query Parameters
- **Players**: `?search=curry&team=warriors&position=guard`
- **Notes**: `?player_id=1&search=shooting&tag=offense&is_important=true`

## Database Schema

### Players Table
- `id` (Integer, Primary Key)
- `name` (String, Required)
- `position` (String, Optional)
- `team` (String, Optional)
- `jersey_number` (Integer, Optional)
- `height` (String, Optional)
- `weight` (String, Optional)
- `age` (Integer, Optional)
- `created_at` (DateTime)
- `updated_at` (DateTime)

### Notes Table
- `id` (Integer, Primary Key)
- `player_id` (Integer, Foreign Key)
- `title` (String, Required)
- `content` (Text, Required)
- `tags` (String, Optional)
- `game_date` (String, Optional)
- `is_important` (Boolean)
- `created_at` (DateTime)
- `updated_at` (DateTime)
- `embedding` (ARRAY, Week 2) - 384-dimensional vector for semantic search
- `text_searchable` (tsvector, Week 2) - PostgreSQL full-text search index

## RAG System Architecture (Week 2)

### How It Works

1. **Hybrid Retrieval**:
   - Keyword Search: PostgreSQL tsvector with ts_rank scoring (40% weight)
   - Semantic Search: Cosine similarity with embeddings (60% weight)
   - Combines both scores to find most relevant notes

2. **Embeddings**:
   - Model: all-MiniLM-L6-v2 (384 dimensions)
   - Generated automatically when notes are created/updated
   - Stored as PostgreSQL REAL[] arrays (no pgvector required)

3. **Answer Generation**:
   - Uses Google Gemini (models/gemini-2.5-flash)
   - Temperature: 0.3 (factual responses)
   - Grounded in retrieved notes only (no hallucination)
   - Every claim cited with [1], [2], etc.

4. **Citation System**:
   - Citations extracted from answer using regex
   - Linked back to original note IDs
   - Interactive UI allows clicking citations to view sources

5. **Confidence Assessment**:
   - **High**: 3+ citations from 3+ notes
   - **Medium**: 1-2 citations
   - **Low**: No citations or insufficient information detected

## Development

### Code Style
- Backend: Follow PEP 8 guidelines
- Frontend: ESLint configuration included

### Git Workflow
- Create a new branch for each week: `week-1`, `week-2`, `week-3`
- Make small, focused commits with clear messages
- Open a Pull Request against `main` when ready for review

## Troubleshooting

### Docker Issues
- **Cannot connect to Docker daemon**: Ensure Docker Desktop is running
- **Port already in use**: Check if ports 5173, 8000, 5433 are available
- **Build errors**: Try `docker-compose down -v && docker-compose up --build`
- **Database not initializing**: Run `docker-compose down -v` to reset volumes

### Backend Won't Start
- Check if PostgreSQL is running
- Verify DATABASE_URL in .env
- Ensure all Python dependencies installed
- Check backend logs: `docker-compose logs backend`

### Frontend Won't Connect to Backend
- Check if backend is running on port 8000
- Verify VITE_API_URL in frontend/.env
- Check browser console for CORS errors
- Clear browser cache and reload

### RAG Not Working
- Verify GOOGLE_API_KEY is set correctly in .env
- Check if embeddings are generated (run backfill script)
- Ensure database migration ran: `python scripts/add_rag_columns_simple.py`
- Check Gemini model name is correct: `models/gemini-2.5-flash`

### Database Connection Issues (Manual Setup)
- Verify PostgreSQL is running: `pg_isready`
- Check database credentials in `.env`
- Ensure database exists: `psql -l`

### Port Already in Use (Manual Setup)
- Backend (8000): Change port in uvicorn command
- Frontend (5173): Change port in `vite.config.ts`

### Module Not Found
- Backend: Ensure virtual environment is activated
- Frontend: Run `npm install`

## License

This project is part of the Sooch Readiness Take-Home Assessment.

## Author

Shashank Achanta
