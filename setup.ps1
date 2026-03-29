param (
    [switch]$SkipEnvCheck
)

Write-Host "=========================================" -ForegroundColor Cyan
Write-Host "        ChargeHub Setup Script           " -ForegroundColor Cyan
Write-Host "=========================================" -ForegroundColor Cyan

# 1. Environment file check
if (-not (Test-Path ".env")) {
    Write-Host "[!] .env file not found. Creating from .env.example..." -ForegroundColor Yellow
    Copy-Item ".env.example" ".env"
    Write-Host "[*] Please update the TAPO_USERNAME and TAPO_PASSWORD inside .env before proceeding!" -ForegroundColor Red
    Write-Host "Opening .env for you..."
    notepad .env
    Pause
} else {
    Write-Host "[OK] .env file exists." -ForegroundColor Green
}

# 2. Build and start containers
Write-Host "[*] Building and starting Docker containers..." -ForegroundColor Cyan
docker compose up --build -d

if ($LASTEXITCODE -ne 0) {
    Write-Host "[X] Docker compose failed. Make sure Docker Desktop is running." -ForegroundColor Red
    exit 1
}

Write-Host "[*] Waiting for PostgreSQL database to initialize (10s)..." -ForegroundColor Yellow
Start-Sleep -Seconds 10

# 3. Seed Database
Write-Host "[*] Running Database Setup & Seeding..." -ForegroundColor Cyan
docker exec chargehub_api python seed.py

Write-Host "=========================================" -ForegroundColor Green
Write-Host "    ChargeHub is successfully running!   " -ForegroundColor Green
Write-Host "=========================================" -ForegroundColor Green
Write-Host "Frontend:  http://localhost:5173"
Write-Host "API Docs:  http://localhost:8000/docs"
Write-Host "Admin user: admin@chargehub.local / admin123"
