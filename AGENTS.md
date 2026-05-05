# Repository Guidelines

## Project Structure

This is a full-stack finance tracker application.

- `frontend/` — Vue 3 + TypeScript client
  - `src/` — source code (components, stores, router)
  - `src/__tests__/` — unit tests
  - `e2e/` — Playwright end-to-end tests
  - `public/` — static assets
- `backend/finance_tracker_project/` — Django 6 project
  - `manage.py` — Django management entry point
  - `finance_tracker_project/` — project settings and URLs

## Build, Test, and Development Commands

### Frontend
Run these from the `frontend/` directory:

- `npm run dev` — start the Vite development server
- `npm run build` — type-check and build for production
- `npm run test:unit` — run Vitest unit tests
- `npm run test:e2e` — run Playwright end-to-end tests
- `npm run lint` — run Oxlint and ESLint with auto-fix
- `npm run format` — run Prettier on `src/`

### Backend
Run these from the `backend/finance_tracker_project/` directory:

- `python manage.py runserver` — start the Django development server
- `python manage.py migrate` — apply database migrations

## Coding Style & Naming Conventions

- **Frontend**: 2-space indentation, LF line endings, no semicolons, single quotes, 100-character line width. Follow the existing `.editorconfig`, `.prettierrc.json`, and `eslint.config.ts`.
- **Backend**: Follow PEP 8. Use `snake_case` for Python variables and functions.
- **File naming**: Use PascalCase for Vue components (e.g., `App.vue`) and camelCase for TypeScript modules (e.g., `counter.ts`).

## Testing Guidelines

- **Unit tests**: Vitest with Vue Test Utils. Place tests alongside source or in `src/__tests__/`. Name test files `*.spec.ts`.
- **E2E tests**: Playwright. Place tests in `frontend/e2e/`. Name files `*.spec.ts`.
- Run the full suite with `npm run test:unit` and `npm run test:e2e` before submitting changes.

## Commit & Pull Request Guidelines

- Use clear, imperative commit messages (e.g., `Add user authentication flow`, `Fix rounding bug in totals`).
- Reference related issues in PR descriptions.
- Keep PRs focused on a single feature or fix.
- Ensure `npm run lint` and `npm run test:unit` pass before requesting review.

## Security & Configuration Tips

- Never commit `.env` files or the Django `SECRET_KEY`. Both are ignored by `.gitignore`.
- Activate the backend virtual environment before running Django commands:
  ```bash
  source backend/.venv/bin/activate
  ```
