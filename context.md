# ChargeHub Project Context

## System Overview
ChargeHub is a local EV charging management platform designed for apartment complexes. It controls TP-Link Tapo P110 smart plugs over the Local Area Network (LAN) to bypass cloud dependency, providing a full-stack solution to manage charging sessions, virtual coin-based billing, user authentication, and multi-tenant access.

## Architecture & Tech Stack
- **Frontend**: React + Vite, TypeScript, Recharts (for analytics), Lucide React (icons), and Axios for API communication. It relies on standard CSS (`index.css`) rather than Tailwind.
- **Backend**: Python 3.11 with FastAPI. It uses asynchronous SQLAlchemy 2 for ORM, and PostgreSQL for the database.
- **Hardware Integration**: Uses the Python-Kasa / Tapo library to communicate with TP-Link Tapo plugs (`backend/services/tapo_service.py`).
- **Deployment**: Fully containerized using Docker and Docker Compose (`docker-compose.yml`), defining three services: `postgres`, `backend`, and `frontend`.
- **Background Tasks**: Uses `APScheduler` in `backend/scheduler.py` to poll active plugs asynchronously for real-time power metrics and session management.

## Core Domain Models
- **Users**: Differentiated by roles (Residents vs. Admins).
- **Plugs**: Represents the physical Tapo P110 devices on the LAN.
- **Sessions**: Tracks active or completed EV charging sessions, linking a User, a Plug, and the energy consumed.
- **Coins & Payments**: Users maintain a virtual "coin" balance. Charging depletes coins based on configurable rates (`COINS_PER_KWH`, `COINS_PER_MINUTE`). Users can top up their balance, potentially via Stripe integration.

## Key Mechanisms
1. **Local LAN Control**: The system talks directly to the local IPs of the smart plugs. Docker networking (`host.docker.internal:host-gateway`) is configured to allow the backend container to reach the host's LAN.
2. **Real-time Monitoring**: The APScheduler polls active sessions every configured interval (e.g., 10s). It reads the current power (Watts), updates the database, calculates energy consumed (kWh), and detects when a charging session is complete (e.g., power drops below 5W for consecutive reads).
3. **Coin Billing**: Charging is billed using a virtual currency. This prevents direct micro-transactions for every charge. Admins can manually credit balances, or Stripe can be configured for automatic top-ups.

## Directory Structure
- `/backend`: FastAPI application.
  - `/models`: SQLAlchemy ORM models (`user.py`, `plug.py`, `session.py`, etc.).
  - `/routers`: API endpoints (`auth.py`, `plugs.py`, `sessions.py`, `coins.py`, etc.).
  - `/services`: Business logic and external integrations.
  - `main.py`: FastAPI application entry point.
  - `scheduler.py`: Background polling loop.
- `/frontend`: React SPA.
  - `/src/components`: Reusable UI components.
  - `/src/pages`: Page views (Dashboard, Admin, Login, etc.).
  - `/src/api`: Axios API clients.
  - `/src/context`: React Context for state (like Auth context).
- `/docker-compose.yml`: Local orchestrator.
- `/setup.sh` & `/setup.ps1`: 1-click deployment scripts that clone `.env`, and spin up docker.
