@echo off
echo ================================================
echo ScoutOps - NBA Scouting Platform
echo ================================================
echo.
echo Starting all services with Docker...
echo.
echo Services:
echo - PostgreSQL Database: localhost:5433
echo - Backend API: http://localhost:8000
echo - Frontend: http://localhost:5173
echo.
echo ================================================
echo.

docker-compose up
