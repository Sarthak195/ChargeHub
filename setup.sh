#!/bin/bash
set -e

echo -e "\033[1;36m=========================================\033[0m"
echo -e "\033[1;36m        ChargeHub Setup Script           \033[0m"
echo -e "\033[1;36m=========================================\033[0m"

# 1. Environment file check
if [ ! -f .env ]; then
    echo -e "\033[1;33m[!] .env file not found. Creating from .env.example...\033[0m"
    cp .env.example .env
    echo -e "\033[1;31m[*] Please update the TAPO_USERNAME and TAPO_PASSWORD inside .env before proceeding!\033[0m"
    echo "Opening .env for editing..."
    if command -v nano &> /dev/null; then
        nano .env
    elif command -v vi &> /dev/null; then
        vi .env
    else
        echo "Please open .env in your text editor."
    fi
    read -p "Press Enter to continue when .env is configured..."
else
    echo -e "\033[1;32m[OK] .env file exists.\033[0m"
fi

# 2. Build and start containers
echo -e "\033[1;36m[*] Building and starting Docker containers...\033[0m"
docker compose up --build -d

if [ $? -ne 0 ]; then
    echo -e "\033[1;31m[X] Docker compose failed. Make sure Docker is running.\033[0m"
    exit 1
fi

echo -e "\033[1;33m[*] Waiting for PostgreSQL database to initialize (10s)...\033[0m"
sleep 10

# 3. Seed Database
echo -e "\033[1;36m[*] Running Database Setup & Seeding...\033[0m"
docker exec chargehub_api python seed.py

echo -e "\033[1;32m=========================================\033[0m"
echo -e "\033[1;32m    ChargeHub is successfully running!   \033[0m"
echo -e "\033[1;32m=========================================\033[0m"
echo -e "Frontend:  http://localhost:5173"
echo -e "API Docs:  http://localhost:8000/docs"
echo -e "Admin user: admin@chargehub.local / admin123"
