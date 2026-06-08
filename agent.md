# AI Agent Guidelines for ChargeHub

Welcome to the ChargeHub repository. If you are an AI assistant or a developer resuming work on this project, please follow these guidelines to maintain architectural consistency and code quality.

## 1. Tech Stack & Tools
- **Frontend**: Use React + TypeScript. The build tool is Vite.
  - **Styling**: Do NOT use Tailwind CSS unless explicitly configured. The project uses standard CSS (`index.css`). Follow the existing sleek, dark-mode, glassmorphic design system.
  - **Icons**: Use `lucide-react`.
  - **Charts**: Use `recharts`.
- **Backend**: Use Python 3.11+ and FastAPI.
  - **Database**: Use async SQLAlchemy 2.0+ (`sqlalchemy.ext.asyncio`). Do not use synchronous database calls.
  - **Hardware**: LAN communication is handled via the Python-Kasa / Tapo library.

## 2. Architectural Rules
- **No Cloud Dependency for Plugs**: The core tenet of ChargeHub is local LAN control of TP-Link Tapo P110 plugs. Do not introduce cloud-based APIs for controlling the hardware.
- **Background Tasks**: For any periodic background tasks (like polling plugs or updating session states), use the existing `APScheduler` setup in `backend/scheduler.py`. Do not spin up separate Celery/Redis workers unless the scale strictly demands it.
- **API Design**: Keep business logic in `backend/services/` and routing/HTTP handling in `backend/routers/`. Keep routers clean.
- **Docker**: Ensure any new dependencies or environment variables are correctly mapped in `docker-compose.yml`, `backend/Dockerfile`, and `frontend/Dockerfile`.

## 3. Key Files to Understand Before Modifying
- `backend/main.py`: Entry point for FastAPI, includes CORS and router setup.
- `backend/scheduler.py`: Vital for real-time plug polling. If you break this, sessions won't track energy correctly.
- `backend/models/session.py` & `plug.py`: Core domain models tracking hardware state.
- `frontend/src/App.tsx`: React routing and main layout.
- `docker-compose.yml`: Network config is tricky here (especially for Windows/Mac) to allow UDP discovery or direct LAN IP connection (`host.docker.internal`). Be careful modifying network settings.

## 4. Development Workflow
- When running locally, you can use `docker compose up --build`.
- The `.env` file is required. Check `.env.example` for required keys (`TAPO_USERNAME`, `TAPO_PASSWORD`, etc.).
- When making frontend changes, you can run `npm run dev` in the `/frontend` directory for HMR (ensure backend is running on `localhost:8000`).

## 5. UI/UX Philosophy
- The UI should feel premium, dynamic, and responsive.
- Utilize smooth gradients, micro-animations, and hover effects.
- Ensure all new components respect the dark mode aesthetic established in `frontend/src/index.css`.
