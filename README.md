# 📊 Finance Tracker

> A full-stack personal finance management application that imports transaction data from Revolut XLSX exports, provides interactive dashboards, AI-powered spending insights, budget tracking, and smart transaction categorization.

---

## 🌐 Language / Lingua

- [🇬🇧 English](#english)
- [🇮🇹 Italiano](#italiano)

---

<a name="english"></a>

## 🇬🇧 English

### Overview

Finance Tracker is a modern web application designed to give you complete control over your personal finances. Simply export your transaction history from Revolut as an XLSX file, upload it, and the application handles the rest — parsing, deduplication, automatic categorization, and generating actionable insights powered by AI.

### Key Features

#### 🔐 Authentication
- User registration with email and password
- JWT-based authentication (access + refresh tokens)
- Secure logout with token invalidation
- Complete data isolation per user

#### 📥 Transaction Import
- Drag & drop upload of Revolut XLSX files
- Smart parsing of Revolut's non-standard XLSX format (embedded CSV in a single column)
- Automatic deduplication — already imported transactions are never re-imported
- Only completed transactions are imported; cancelled and pending ones are filtered out
- Detailed import feedback: imported, duplicates, cancelled, errors
- Import batch history with timestamps and statistics
- Asynchronous processing via Celery for large files

#### 💳 Transaction Management
- Paginated transaction list with date-based sorting
- Full-text search by description/merchant
- Advanced filters: date range, category, transaction type, expense/income
- Editable categories and personal notes per transaction
- Manual transaction deletion

#### 🏷️ Smart Categorization
- Pre-built system categories: Groceries, Transport, Restaurants, Entertainment, Health, Shopping, Subscriptions, Investments, Salary, Transfers, ATM Withdrawals, Currency Exchange, Other
- Custom category creation with name and color
- Keyword-based auto-categorization rules (e.g., `Netflix` → Subscriptions, `Trainline` → Transport)
- Rule priority management and retroactive application
- **AI-powered categorization** — intelligent category assignment via Vercel AI Gateway

#### 📊 Dashboard & Statistics
- Monthly summary: total expenses, income, net balance
- Donut chart: expense distribution by category
- Bar chart: monthly expense trends (last 12 months)
- Line chart: balance evolution over time
- Top 5 merchants by spending
- Month-over-month comparison by category
- Global period filter (month, quarter, year, custom)

#### 💰 Budget Management
- Monthly budget per category (e.g., Restaurants: €200/month)
- Visual progress bars with percentage indicators
- Warning alerts at 80% and 100% thresholds
- Historical budget tracking month by month

#### 🤖 AI-Powered Insights
- **Spending profile analysis** — aggregated transaction data sent to AI Gateway (`xai/grok-4.1-fast-non-reasoning`) for personalized narrative insights
- Automatic detection of recurring subscriptions
- Spending spike identification by day/time
- Statistical outlier detection for unusual expenses
- Category trend analysis with month-over-month growth
- **Automatic fallback** — if AI is unavailable, statistical suggestions are generated locally
- **Intelligent caching** — AI suggestions cached for 24 hours via Redis, invalidated on new import
- **Privacy-first** — only aggregated data (no PII) is sent to the AI

### Tech Stack

#### Backend
| Technology | Purpose |
|---|---|
| Django 6.0 | Web framework |
| Django REST Framework | RESTful API |
| djangorestframework-simplejwt | JWT authentication |
| PostgreSQL 16 | Database |
| Celery + Redis | Asynchronous task processing |
| pandas + openpyxl | XLSX parsing and data processing |
| httpx + openai | AI Gateway communication |
| django-cors-headers | CORS management |
| django-filter | API filtering |

#### Frontend
| Technology | Purpose |
|---|---|
| Vue 3 | UI framework |
| TypeScript | Type safety |
| Vite 7 | Build tool & dev server |
| Tailwind CSS 4 | Utility-first styling |
| shadcn-vue | Component library |
| Pinia | State management |
| Vue Router 5 | SPA routing |
| Chart.js + vue-chartjs | Interactive charts |
| Lucide Vue Next | Icon system |
| VueUse | Composable utilities |
| Axios | HTTP client |
| Vitest | Unit testing |
| Playwright | End-to-end testing |
| Oxlint + ESLint | Linting |
| Prettier | Code formatting |

### Architecture

```
┌─────────────────────────────────────────────────────┐
│                    FRONTEND                         │
│     Vue 3 · TypeScript · Vite · Tailwind CSS        │
│     Pinia · Vue Router · Chart.js · shadcn-vue      │
│     http://localhost:5173                           │
└────────────────────┬────────────────────────────────┘
                     │ HTTP / REST (JSON)
                     │ JWT Bearer Token
┌────────────────────▼────────────────────────────────┐
│                     BACKEND                         │
│           Django 6 + Django REST Framework          │
│           http://localhost:8000                     │
│                                                     │
│  /api/auth/          — Authentication (JWT)         │
│  /api/transactions/  — CRUD + XLSX import           │
│  /api/categories/    — Categories + rules           │
│  /api/budgets/       — Monthly budgets              │
│  /api/stats/         — Statistical aggregations     │
│  /api/suggestions/   — AI-powered insights          │
└───────┬──────────────────────┬──────────────────────┘
        │                      │ Async tasks
┌───────▼──────┐      ┌────────▼──────────┐
│  PostgreSQL   │      │  Celery + Redis   │
│  pgdata vol.  │      │  (import, beat)   │
└──────────────┘      └───────────────────┘
```

### Getting Started

#### Prerequisites
- **Docker** and **Docker Compose**
- **Node.js** `^20.19.0` or `>=22.12.0` (for local frontend development)

#### Quick Start with Docker

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd finance-tracker
   ```

2. **Set up environment variables**
   ```bash
   cp .env.example .env
   ```
   Edit `.env` and set at minimum:
   ```env
   DJANGO_SECRET_KEY=your-random-secret-key
   DB_PASSWORD=your-database-password
   AI_GATEWAY_KEY=your-ai-gateway-key
   ```

3. **Start all services**
   ```bash
   docker-compose up -d
   ```

4. **Run database migrations**
   ```bash
   docker-compose exec backend python manage.py migrate
   ```

5. **Create a superuser (optional)**
   ```bash
   docker-compose exec backend python manage.py createsuperuser
   ```

6. **Access the application**
   - Frontend: http://localhost:5173
   - Backend API: http://localhost:8000
   - Django Admin: http://localhost:8000/admin

#### Local Development (without Docker)

**Backend:**
```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
# Update .env DB_HOST to localhost
python manage.py migrate
python manage.py runserver
```

**Frontend:**
```bash
cd frontend
npm install
# Update VITE_API_URL in .env or vite config
npm run dev
```

### Docker Services

| Service | Port | Description |
|---|---|---|
| `db` | 5432 | PostgreSQL 16 database |
| `redis` | 6379 | Redis broker for Celery |
| `backend` | 8000 | Django API server |
| `celery` | — | Celery worker for async tasks |
| `celery-beat` | — | Celery scheduler for periodic tasks |
| `frontend` | 5173 | Vue 3 development server |

### Environment Variables

| Variable | Required | Description |
|---|---|---|
| `DJANGO_SECRET_KEY` | ✅ | Django secret key for cryptographic signing |
| `DJANGO_DEBUG` | — | Set to `true` for development (default: `true`) |
| `DJANGO_ALLOWED_HOSTS` | — | Comma-separated allowed hosts |
| `DB_NAME` | — | Database name (default: `finance_tracker`) |
| `DB_USER` | — | Database user (default: `postgres`) |
| `DB_PASSWORD` | ✅ | Database password |
| `DB_HOST` | — | Database host (default: `db` in Docker) |
| `DB_PORT` | — | Database port (default: `5432`) |
| `CELERY_BROKER_URL` | — | Redis broker URL |
| `CELERY_RESULT_BACKEND` | — | Redis result backend URL |
| `FRONTEND_URL` | — | Frontend URL for CORS |
| `AI_GATEWAY_KEY` | ✅ | Vercel AI Gateway API key |
| `AI_GATEWAY_URL` | — | AI Gateway endpoint URL |
| `AI_GATEWAY_MODEL` | — | AI model identifier (default: `xai/grok-4.1-fast-non-reasoning`) |
| `AI_SUGGESTIONS_TIMEOUT` | — | Timeout in seconds for AI suggestions (default: `10`) |
| `AI_CATEGORIZATION_ENABLED` | — | Enable AI categorization (default: `true`) |
| `AI_CATEGORIZATION_BATCH_SIZE` | — | Batch size for AI categorization (default: `20`) |
| `AI_CATEGORIZATION_TIMEOUT` | — | Timeout for AI categorization in seconds (default: `15`) |
| `AI_CATEGORIZATION_CACHE_TTL` | — | Cache TTL for AI categorization in seconds (default: `2592000` = 30 days) |

### Development Commands

**Backend:**
```bash
# Run migrations
docker-compose exec backend python manage.py migrate

# Run tests
docker-compose exec backend python manage.py test

# Access Django shell
docker-compose exec backend python manage.py shell

# Create superuser
docker-compose exec backend python manage.py createsuperuser
```

**Frontend:**
```bash
cd frontend

# Development server
npm run dev

# Type-check and build for production
npm run build

# Run unit tests
npm run test:unit

# Run end-to-end tests
npm run test:e2e

# Lint (Oxlint + ESLint with auto-fix)
npm run lint

# Format code (Prettier)
npm run format

# Preview production build
npm run preview
```

### API Endpoints

#### Authentication
```
POST   /api/auth/register/       User registration
POST   /api/auth/login/          Login → {access, refresh}
POST   /api/auth/refresh/        Refresh access token
POST   /api/auth/logout/         Logout (blacklist refresh token)
```

#### Transactions
```
GET    /api/transactions/        List (paginated, filterable)
GET    /api/transactions/{id}/   Detail
PATCH  /api/transactions/{id}/   Update category / notes
DELETE /api/transactions/{id}/   Delete
POST   /api/transactions/import/ Upload XLSX → starts async import
GET    /api/transactions/import/ Import batch history
```

#### Categories
```
GET    /api/categories/          List (system + custom)
POST   /api/categories/          Create custom category
PATCH  /api/categories/{id}/     Update
DELETE /api/categories/{id}/     Delete (custom only)
GET    /api/categories/rules/    List auto-categorization rules
POST   /api/categories/rules/    Create rule
DELETE /api/categories/rules/{id}/ Delete rule
```

#### Budgets
```
GET    /api/budgets/             List (filter by year/month)
POST   /api/budgets/             Create budget
PATCH  /api/budgets/{id}/        Update limit
DELETE /api/budgets/{id}/        Delete
```

#### Statistics
```
GET    /api/stats/summary/       Period summary (expenses, income, net)
GET    /api/stats/by-category/   Aggregated expenses by category
GET    /api/stats/monthly/       Monthly trend (last N months)
GET    /api/stats/top-merchants/ Top merchants by amount
GET    /api/stats/balance/       Balance evolution over time
```

#### Suggestions
```
GET    /api/suggestions/         Active suggestions (AI + statistical)
```

### Data Model

```
User
  id, email, password_hash, created_at

Transaction
  id, user_id (FK), started_at, completed_at, description, amount, fee,
  currency, transaction_type, state, balance_after, category_id (FK),
  notes, import_batch_id (FK), created_at

Category
  id, user_id (FK, NULL = system), name, color, icon, is_system

CategoryRule
  id, user_id (FK), keyword, category_id (FK), priority, created_at

Budget
  id, user_id (FK), category_id (FK), year, month, amount_limit

ImportBatch
  id, user_id (FK), filename, imported_at, total_rows,
  imported_count, skipped_count, error_count
```

### Import Flow

```
User uploads XLSX file
        │
        ▼
[Frontend] Validates file extension (.xlsx)
        │
        ▼
[POST /api/transactions/import/] Multipart upload
        │
        ▼
[Backend] Validates XLSX structure:
  - Opens with openpyxl
  - Checks that the single column contains the expected CSV header
        │
        ├── ❌ Invalid format → 400 Bad Request + error details
        │
        ▼
[Celery Task] Asynchronous parsing
  - Reconstructs embedded CSV (header + rows)
  - pd.read_csv with RFC 4180 quote handling
  - Filters State != 'COMPLETATO'
  - Deduplication (started_at + description + amount)
  - Auto-categorization via CategoryRule
  - AI categorization (if enabled)
  - Saves batch to PostgreSQL
        │
        ▼
[Frontend] Polling → displays import result
  - N imported / N duplicates / N cancelled / N errors
```

### Testing

```bash
# Backend tests
docker-compose exec backend python manage.py test

# Frontend unit tests
cd frontend && npm run test:unit

# Frontend e2e tests
cd frontend && npm run test:e2e
```

### Database Reset

To completely reset the database (⚠️ **deletes all data**):
```bash
docker-compose down -v
docker-compose up -d
docker-compose exec backend python manage.py migrate
```

---

<a name="italiano"></a>

## 🇮🇹 Italiano

### Panoramica

Finance Tracker è una moderna applicazione web progettata per darti il controllo completo sulle tue finanze personali. Basta esportare la cronologia delle transazioni da Revolut come file XLSX, caricarlo e l'applicazione si occupa del resto — parsing, deduplicazione, categorizzazione automatica e generazione di insight azionabili potenziati dall'AI.

### Funzionalità Principali

#### 🔐 Autenticazione
- Registrazione utente con email e password
- Autenticazione basata su JWT (token di accesso + refresh)
- Logout sicuro con invalidazione del token
- Isolamento completo dei dati per utente

#### 📥 Import Transazioni
- Upload drag & drop di file XLSX da Revolut
- Parsing intelligente del formato non standard di Revolut (CSV embedded in un'unica colonna)
- Deduplicazione automatica — le transazioni già importate non vengono mai reimportate
- Solo le transazioni completate vengono importate; quelle annullate e in sospeso vengono filtrate
- Feedback dettagliato sull'import: importate, duplicate, annullate, errori
- Cronologia dei batch di import con timestamp e statistiche
- Elaborazione asincrona tramite Celery per file di grandi dimensioni

#### 💳 Gestione Transazioni
- Lista transazioni paginata con ordinamento per data
- Ricerca full-text per descrizione/merchant
- Filtri avanzati: intervallo date, categoria, tipo transazione, spesa/entrata
- Categoria e note personali modificabili per ogni transazione
- Eliminazione manuale delle transazioni

#### 🏷️ Categorizzazione Intelligente
- Categorie di sistema precaricate: Alimentari, Trasporti, Ristoranti, Intrattenimento, Salute, Shopping, Abbonamenti, Investimenti, Stipendio, Trasferimenti, Prelievi ATM, Cambio Valuta, Altro
- Creazione categorie personalizzate con nome e colore
- Regole di auto-categorizzazione basate su keyword (es. `Netflix` → Abbonamenti, `Trainline` → Trasporti)
- Gestione priorità delle regole e applicazione retroattiva
- **Categorizzazione AI** — assegnazione intelligente delle categorie tramite Vercel AI Gateway

#### 📊 Dashboard e Statistiche
- Riepilogo mensile: totale spese, entrate, saldo netto
- Grafico a ciambella: distribuzione spese per categoria
- Grafico a barre: andamento spese mensili (ultimi 12 mesi)
- Grafico a linee: evoluzione del saldo nel tempo
- Top 5 merchant per spesa
- Confronto mese su mese per categoria
- Filtro periodo globale (mese, trimestre, anno, personalizzato)

#### 💰 Gestione Budget
- Budget mensile per categoria (es. Ristoranti: €200/mese)
- Barre di progresso visive con indicatori percentuali
- Alert visivi alle soglie dell'80% e del 100%
- Cronologia budget mese per mese

#### 🤖 Insight basati sull'AI
- **Analisi del profilo di spesa** — dati aggregati delle transazioni inviati a AI Gateway (`xai/grok-4.1-fast-non-reasoning`) per insight narrativi personalizzati
- Rilevamento automatico degli abbonamenti ricorrenti
- Identificazione dei picchi di spesa per giorno/ora
- Rilevamento di outlier statistici per spese anomale
- Analisi dei trend per categoria con crescita mese su mese
- **Fallback automatico** — se l'AI non è disponibile, i suggerimenti statistici vengono generati localmente
- **Caching intelligente** — suggerimenti AI memorizzati nella cache per 24 ore via Redis, invalidati al nuovo import
- **Privacy-first** — solo dati aggregati (nessuna PII) vengono inviati all'AI

### Stack Tecnologico

#### Backend
| Tecnologia | Scopo |
|---|---|
| Django 6.0 | Framework web |
| Django REST Framework | API RESTful |
| djangorestframework-simplejwt | Autenticazione JWT |
| PostgreSQL 16 | Database |
| Celery + Redis | Elaborazione asincrona dei task |
| pandas + openpyxl | Parsing XLSX e elaborazione dati |
| httpx + openai | Comunicazione con AI Gateway |
| django-cors-headers | Gestione CORS |
| django-filter | Filtri API |

#### Frontend
| Tecnologia | Scopo |
|---|---|
| Vue 3 | Framework UI |
| TypeScript | Tipizzazione |
| Vite 7 | Build tool e dev server |
| Tailwind CSS 4 | Styling utility-first |
| shadcn-vue | Libreria componenti |
| Pinia | Gestione dello stato |
| Vue Router 5 | Routing SPA |
| Chart.js + vue-chartjs | Grafici interattivi |
| Lucide Vue Next | Sistema icone |
| VueUse | Utility composables |
| Axios | Client HTTP |
| Vitest | Test unitari |
| Playwright | Test end-to-end |
| Oxlint + ESLint | Linting |
| Prettier | Formattazione codice |

### Architettura

```
┌─────────────────────────────────────────────────────┐
│                    FRONTEND                         │
│     Vue 3 · TypeScript · Vite · Tailwind CSS        │
│     Pinia · Vue Router · Chart.js · shadcn-vue      │
│     http://localhost:5173                           │
└────────────────────┬────────────────────────────────┘
                     │ HTTP / REST (JSON)
                     │ JWT Bearer Token
┌────────────────────▼────────────────────────────────┐
│                     BACKEND                         │
│           Django 6 + Django REST Framework          │
│           http://localhost:8000                     │
│                                                     │
│  /api/auth/          — Autenticazione (JWT)         │
│  /api/transactions/  — CRUD + import XLSX           │
│  /api/categories/    — Categorie + regole           │
│  /api/budgets/       — Budget mensili               │
│  /api/stats/         — Aggregazioni statistiche     │
│  /api/suggestions/   — Insight AI                   │
└───────┬──────────────────────┬──────────────────────┘
        │                      │ Task asincroni
┌───────▼──────┐      ┌────────▼──────────┐
│  PostgreSQL   │      │  Celery + Redis   │
│  Volume pgdata│      │  (import, beat)   │
└──────────────┘      └───────────────────┘
```

### Guida Rapida

#### Prerequisiti
- **Docker** e **Docker Compose**
- **Node.js** `^20.19.0` o `>=22.12.0` (per sviluppo frontend locale)

#### Avvio Rapido con Docker

1. **Clona il repository**
   ```bash
   git clone <repository-url>
   cd finance-tracker
   ```

2. **Configura le variabili d'ambiente**
   ```bash
   cp .env.example .env
   ```
   Modifica `.env` e imposta almeno:
   ```env
   DJANGO_SECRET_KEY=la-tua-chiave-segreta
   DB_PASSWORD=la-tua-password-database
   AI_GATEWAY_KEY=la-tua-chiave-ai-gateway
   ```

3. **Avvia tutti i servizi**
   ```bash
   docker-compose up -d
   ```

4. **Applica le migrazioni del database**
   ```bash
   docker-compose exec backend python manage.py migrate
   ```

5. **Crea un superuser (opzionale)**
   ```bash
   docker-compose exec backend python manage.py createsuperuser
   ```

6. **Accedi all'applicazione**
   - Frontend: http://localhost:5173
   - Backend API: http://localhost:8000
   - Django Admin: http://localhost:8000/admin

#### Sviluppo Locale (senza Docker)

**Backend:**
```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
# Aggiorna DB_HOST in .env a localhost
python manage.py migrate
python manage.py runserver
```

**Frontend:**
```bash
cd frontend
npm install
# Aggiorna VITE_API_URL in .env o vite config
npm run dev
```

### Servizi Docker

| Servizio | Porta | Descrizione |
|---|---|---|
| `db` | 5432 | Database PostgreSQL 16 |
| `redis` | 6379 | Broker Redis per Celery |
| `backend` | 8000 | Server API Django |
| `celery` | — | Worker Celery per task asincroni |
| `celery-beat` | — | Scheduler Celery per task periodici |
| `frontend` | 5173 | Server di sviluppo Vue 3 |

### Variabili d'Ambiente

| Variabile | Obbligatoria | Descrizione |
|---|---|---|
| `DJANGO_SECRET_KEY` | ✅ | Chiave segreta Django per la firma crittografica |
| `DJANGO_DEBUG` | — | Impostare a `true` per sviluppo (default: `true`) |
| `DJANGO_ALLOWED_HOSTS` | — | Host consentiti separati da virgola |
| `DB_NAME` | — | Nome del database (default: `finance_tracker`) |
| `DB_USER` | — | Utente del database (default: `postgres`) |
| `DB_PASSWORD` | ✅ | Password del database |
| `DB_HOST` | — | Host del database (default: `db` in Docker) |
| `DB_PORT` | — | Porta del database (default: `5432`) |
| `CELERY_BROKER_URL` | — | URL del broker Redis |
| `CELERY_RESULT_BACKEND` | — | URL del backend risultati Redis |
| `FRONTEND_URL` | — | URL del frontend per CORS |
| `AI_GATEWAY_KEY` | ✅ | Chiave API Vercel AI Gateway |
| `AI_GATEWAY_URL` | — | URL endpoint AI Gateway |
| `AI_GATEWAY_MODEL` | — | Identificativo modello AI (default: `xai/grok-4.1-fast-non-reasoning`) |
| `AI_SUGGESTIONS_TIMEOUT` | — | Timeout in secondi per suggerimenti AI (default: `10`) |
| `AI_CATEGORIZATION_ENABLED` | — | Abilita categorizzazione AI (default: `true`) |
| `AI_CATEGORIZATION_BATCH_SIZE` | — | Dimensione batch per categorizzazione AI (default: `20`) |
| `AI_CATEGORIZATION_TIMEOUT` | — | Timeout per categorizzazione AI in secondi (default: `15`) |
| `AI_CATEGORIZATION_CACHE_TTL` | — | TTL cache per categorizzazione AI in secondi (default: `2592000` = 30 giorni) |

### Comandi di Sviluppo

**Backend:**
```bash
# Applica migrazioni
docker-compose exec backend python manage.py migrate

# Esegui test
docker-compose exec backend python manage.py test

# Accedi alla shell Django
docker-compose exec backend python manage.py shell

# Crea superuser
docker-compose exec backend python manage.py createsuperuser
```

**Frontend:**
```bash
cd frontend

# Server di sviluppo
npm run dev

# Type-check e build per produzione
npm run build

# Esegui test unitari
npm run test:unit

# Esegui test end-to-end
npm run test:e2e

# Lint (Oxlint + ESLint con auto-fix)
npm run lint

# Formatta codice (Prettier)
npm run format

# Anteprima build di produzione
npm run preview
```

### Endpoint API

#### Autenticazione
```
POST   /api/auth/register/       Registrazione utente
POST   /api/auth/login/          Login → {access, refresh}
POST   /api/auth/refresh/        Aggiorna token di accesso
POST   /api/auth/logout/         Logout (blacklist refresh token)
```

#### Transazioni
```
GET    /api/transactions/        Lista (paginata, filtrabile)
GET    /api/transactions/{id}/   Dettaglio
PATCH  /api/transactions/{id}/   Aggiorna categoria / note
DELETE /api/transactions/{id}/   Elimina
POST   /api/transactions/import/ Upload XLSX → avvia import asincrono
GET    /api/transactions/import/ Cronologia batch import
```

#### Categorie
```
GET    /api/categories/          Lista (sistema + personalizzate)
POST   /api/categories/          Crea categoria personalizzata
PATCH  /api/categories/{id}/     Aggiorna
DELETE /api/categories/{id}/     Elimina (solo personalizzate)
GET    /api/categories/rules/    Lista regole auto-categorizzazione
POST   /api/categories/rules/    Crea regola
DELETE /api/categories/rules/{id}/ Elimina regola
```

#### Budget
```
GET    /api/budgets/             Lista (filtro anno/mese)
POST   /api/budgets/             Crea budget
PATCH  /api/budgets/{id}/        Aggiorna limite
DELETE /api/budgets/{id}/        Elimina
```

#### Statistiche
```
GET    /api/stats/summary/       Riepilogo periodo (spese, entrate, netto)
GET    /api/stats/by-category/   Spese aggregate per categoria
GET    /api/stats/monthly/       Trend mensile (ultimi N mesi)
GET    /api/stats/top-merchants/ Top merchant per importo
GET    /api/stats/balance/       Evoluzione saldo nel tempo
```

#### Suggerimenti
```
GET    /api/suggestions/         Suggerimenti attivi (AI + statistici)
```

### Modello dei Dati

```
User
  id, email, password_hash, created_at

Transaction
  id, user_id (FK), started_at, completed_at, description, amount, fee,
  currency, transaction_type, state, balance_after, category_id (FK),
  notes, import_batch_id (FK), created_at

Category
  id, user_id (FK, NULL = sistema), name, color, icon, is_system

CategoryRule
  id, user_id (FK), keyword, category_id (FK), priority, created_at

Budget
  id, user_id (FK), category_id (FK), year, month, amount_limit

ImportBatch
  id, user_id (FK), filename, imported_at, total_rows,
  imported_count, skipped_count, error_count
```

### Flusso di Import

```
L'utente carica file XLSX
        │
        ▼
[Frontend] Valida estensione file (.xlsx)
        │
        ▼
[POST /api/transactions/import/] Upload multipart
        │
        ▼
[Backend] Valida struttura XLSX:
  - Apre con openpyxl
  - Verifica che la colonna unica contenga l'intestazione CSV attesa
        │
        ├── ❌ Formato non valido → 400 Bad Request + dettaglio errore
        │
        ▼
[Celery Task] Parsing asincrono
  - Ricostruisce CSV embedded (header + righe)
  - pd.read_csv con gestione virgolette RFC 4180
  - Filtra State != 'COMPLETATO'
  - Deduplicazione (started_at + description + amount)
  - Auto-categorizzazione tramite CategoryRule
  - Categorizzazione AI (se abilitata)
  - Salvataggio batch su PostgreSQL
        │
        ▼
[Frontend] Polling → visualizza risultato import
  - N importate / N duplicate / N annullate / N errori
```

### Testing

```bash
# Test backend
docker-compose exec backend python manage.py test

# Test unitari frontend
cd frontend && npm run test:unit

# Test e2e frontend
cd frontend && npm run test:e2e
```

### Reset del Database

Per resettare completamente il database (⚠️ **elimina tutti i dati**):
```bash
docker-compose down -v
docker-compose up -d
docker-compose exec backend python manage.py migrate
```

---

## 📜 License

This project is private and proprietary. All rights reserved.
