# Getting Started - GCC Lightweight CLM

This project includes:
- FastAPI backend (`backend/app`)
- React + Vite frontend (`frontend`)
- PostgreSQL + Redis via Docker Compose

## 1) Prerequisites

- Python 3.11+
- Node.js 18+
- npm 9+
- Docker + Docker Compose

## 2) Start infrastructure

From project root:

- `docker compose up -d`

This starts:
- PostgreSQL on `localhost:5432`
- Redis on `localhost:6379`

## 3) Backend setup

From project root:

1. Create virtual environment and activate it
2. Install dependencies:
   - `pip install -r requirements.txt`
3. Create environment file:
   - copy `.env.example` to `.env`
4. Run API server:
   - `uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8000`

Backend URLs:
- Health check: `http://localhost:8000/health`
- OpenAPI docs: `http://localhost:8000/docs`

## 4) Frontend setup

From `frontend` folder:

1. Install dependencies:
   - `npm install`
2. Start dev server:
   - `npm run dev`

Frontend URL:
- `http://localhost:5173`

Vite is configured to proxy `/api/*` to backend at `http://localhost:8000`.

## 5) First login

Use default seeded admin credentials on login screen:
- Email: `admin@example.com`
- Password: `Admin@123`

The app seeds this admin user through API if not present.

## 6) Implemented modules (UI + API)

- Authentication
- Contract Repository
- Workflow & Approval
- Document Management (versions + clause library)
- Obligation Management
- Risk & Compliance (lightweight rule-based)
- Reporting & Analytics

## 7) Reusable frontend enhancements included

- Reusable `DataTable` component
- Reusable `PaginationControls` component
- Form validation utilities for IDs, required fields, year, and amount checks
- Route-based navigation using `react-router-dom`

## 8) Common troubleshooting

### Backend import errors
- Ensure backend is started from project root and dependencies are installed in active virtual environment.

### Database connection errors
- Confirm Docker containers are running:
  - `docker ps`
- Verify `DATABASE_URL` in `.env`.

### Frontend API errors
- Confirm backend is running on `:8000`.
- Confirm frontend is running on `:5173`.
- Check browser devtools network tab for failed `/api` requests.

## 9) Suggested next steps

- Add automated tests (API + frontend)
- Add role-specific UI guards
- Add file upload storage integration for documents
- Add migrations using Alembic instead of metadata auto-create
