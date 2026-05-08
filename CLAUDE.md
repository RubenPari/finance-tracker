# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Setup

### Prerequisites
- Docker and Docker Compose
- Node.js (version as specified in frontend/package.json: ^20.19.0 || >=22.12.0)
- Python (version as specified in backend/requirements.txt, but we use Docker so not strictly required locally)

### Environment
- Copy `.env.example` to `.env` and fill in the required variables (especially DB_PASSWORD and AI_GATEWAY_KEY)

### Running the project
- Use `docker-compose up` to start all services (backend, frontend, db, redis, celery, celery-beat)
- The frontend will be available at http://localhost:5173
- The backend API will be available at http://localhost:8000

## Backend (Django)

### Technology
- Django 6.0+
- Django REST Framework
- PostgreSQL
- Redis
- Celery

### Common Commands (inside backend container or with Docker Compose)
- Run migrations: `docker-compose run backend python manage.py migrate`
- Create superuser: `docker-compose run backend python manage.py createsuperuser`
- Run tests: `docker-compose run backend python manage.py test`
- Run the development server (already in docker-compose): `docker-compose up backend`
- Access Django shell: `docker-compose run backend python manage.py shell`

### Project Structure
- `backend/apps/` contains Django apps: authentication, budgets, categories, stats, suggestions, transactions
- `backend/config/` contains the Django project settings and URLs
- `backend/requirements.txt` lists Python dependencies

## Frontend (Vue 3 + Vite)

### Technology
- Vue 3
- Vite
- TypeScript
- Tailwind CSS
- Pinia (state management)
- Vue Router
- Vitest (unit testing)
- Playwright (end-to-end testing)

### Common Commands (from the frontend directory)
- Install dependencies: `npm install`
- Development server: `npm run dev`
- Build for production: `npm run build`
- Preview production build: `npm run preview`
- Run unit tests: `npm run test:unit`
- Run end-to-end tests: `npm run test:e2e`
- Lint: `npm run lint`
- Format: `npm run format`

### Project Structure
- `frontend/src/` contains the Vue source code
  - `frontend/src/views/` - Page-level components
  - `frontend/src/components/` - Reusable components
  - `frontend/src/stores/` - Pinia stores
  - `frontend/src/router/` - Vue Router configuration
  - `frontend/src/api/` - API service functions
  - `frontend/src/types/` - TypeScript type definitions
  - `frontend/src/assets/` - Static assets
  - `frontend/src/composables/` - Composables (Vue 3)

## Testing

### Backend
- We can run Django tests with: `docker-compose run backend python manage.py test`

### Frontend
- Unit tests: `npm run test:unit` (Vitest)
- End-to-end tests: `npm run test:e2e` (Playwright)

## Database
- We use PostgreSQL. The database is persisted in a Docker volume named `pgdata`.
- To reset the database, you can remove the volume: `docker-compose down -v` (note: this will delete all data)

## Important Notes
- The backend requires an AI_GATEWAY_KEY in the .env file to function properly.
- The frontend connects to the backend via VITE_API_URL (set in docker-compose to http://backend:8000, but when running locally without Docker, you may need to adjust).