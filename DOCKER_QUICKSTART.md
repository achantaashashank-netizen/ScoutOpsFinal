# Docker Quick Start Guide

## Prerequisites

1. Install Docker Desktop: https://www.docker.com/products/docker-desktop/
2. Make sure Docker Desktop is running

## Start ScoutOps (One Command!)

### Option 1: Using Start Script (Windows)
```bash
# Just double-click start.bat
# OR run in terminal:
start.bat
```

### Option 2: Using Docker Compose
```bash
docker-compose up
```

### Option 3: Run in Background
```bash
docker-compose up -d
```

## Access the Application

Once started, open your browser:

- **Frontend (Main App)**: http://localhost:5173
- **Backend API Docs**: http://localhost:8000/docs
- **Backend Health Check**: http://localhost:8000/health

## Seed Sample Data

Open a new terminal and run:

```bash
curl -X POST http://localhost:8000/api/seed
```

Or visit http://localhost:8000/docs and click on `/api/seed` → Try it out → Execute

This will create:
- 3 sample players (Stephen Curry, LeBron James, Kevin Durant)
- 3 sample scouting notes

## Stop ScoutOps

### Option 1: Using Stop Script (Windows)
```bash
# Double-click stop.bat
# OR run in terminal:
stop.bat
```

### Option 2: Using Docker Compose
```bash
docker-compose down
```

### To Also Remove Database Data
```bash
docker-compose down -v
```

## View Logs

```bash
# All services
docker-compose logs -f

# Just backend
docker-compose logs -f backend

# Just frontend
docker-compose logs -f frontend

# Just database
docker-compose logs -f db
```

Press `Ctrl+C` to stop viewing logs.

## Restart Services

```bash
# Rebuild and restart everything
docker-compose up --build

# Restart specific service
docker-compose restart backend
```

## Troubleshooting

### "Cannot connect to Docker daemon"
- Open Docker Desktop application
- Wait for it to fully start (whale icon in taskbar should be steady)

### "Port already in use"
Something else is using ports 5173, 8000, or 5433.

**Check what's using a port:**
```bash
# Check port 8000
netstat -ano | findstr :8000

# Check port 5173
netstat -ano | findstr :5173

# Check port 5433
netstat -ano | findstr :5433
```

**Kill the process:**
```bash
# Replace <PID> with the Process ID from above
taskkill /PID <PID> /F
```

### Services won't start
```bash
# Clean everything and rebuild
docker-compose down -v
docker-compose up --build
```

### RAG (Ask ScoutOps) not working
1. Check if Gemini API key is correct in `backend/.env`
2. Check backend logs: `docker-compose logs backend`
3. Look for errors related to Google API or embeddings

### Database changes not appearing
```bash
# Reset database
docker-compose down -v
docker-compose up
```

## What's Running?

| Service | Description | Port | URL |
|---------|-------------|------|-----|
| **frontend** | React app | 5173 | http://localhost:5173 |
| **backend** | FastAPI server | 8000 | http://localhost:8000 |
| **db** | PostgreSQL database | 5433 | localhost:5433 |

## Development Workflow

1. **Start services**:
   ```bash
   docker-compose up
   ```

2. **Make code changes**:
   - Backend changes auto-reload (FastAPI --reload)
   - Frontend changes auto-reload (Vite HMR)

3. **View changes**:
   - Refresh browser (frontend usually auto-refreshes)

4. **View logs if errors**:
   ```bash
   docker-compose logs -f backend
   docker-compose logs -f frontend
   ```

5. **Stop when done**:
   ```bash
   docker-compose down
   ```

## Tips

- **First time setup takes longer** - Docker needs to download images and build
- **Subsequent starts are fast** - Docker reuses cached images
- **Code changes reflect immediately** - Both frontend and backend have hot-reload enabled
- **Database data persists** - Stored in Docker volume, survives restarts
- **To start fresh** - Use `docker-compose down -v` to wipe database

## Next Steps

1. Visit http://localhost:5173
2. Seed sample data (see above)
3. Explore the Players page
4. Try the "Ask ScoutOps" RAG feature
5. View API docs at http://localhost:8000/docs
