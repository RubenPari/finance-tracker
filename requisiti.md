# 📊 Finance Tracker — Documento dei Requisiti

> App per la gestione delle finanze personali tramite import manuale di CSV esportati da Revolut.

---

## 1. Panoramica del Progetto

| Campo | Dettaglio |
|---|---|
| **Nome progetto** | Finance Tracker |
| **Versione** | 1.0.0 |
| **Stack Backend** | Django 5.x + Django REST Framework |
| **Stack Frontend** | Vue 3 + TypeScript + Vite |
| **Database** | PostgreSQL |
| **Autenticazione** | JWT (djangorestframework-simplejwt) |
| **Sorgente dati** | CSV esportati manualmente da Revolut |

---

## 2. Obiettivi

- Importare le transazioni Revolut tramite file CSV esportati dall'app
- Visualizzare statistiche e grafici sulle proprie spese
- Categorizzare le transazioni (automaticamente e manualmente)
- Ricevere suggerimenti intelligenti basati sui pattern di spesa
- Gestire budget mensili per categoria

---

## 3. Formato File Revolut (XLSX)

Revolut esporta un file **`.xlsx`** con una struttura non standard: tutte le 10 colonne sono compresse in **un'unica colonna Excel**, con i valori separati da virgola all'interno di ogni cella. Il parsing richiede quindi uno step di ricostruzione prima del normale parsing CSV.

### 3.1 Struttura reale del file

```
# Intestazione (nome dell'unica colonna Excel):
Tipo,Prodotto,Data di inizio,Data di completamento,Descrizione,Importo,Costo,Valuta,State,Saldo

# Esempio riga:
Pagamento con carta,Attuale,2026-01-07 19:27:32,2026-01-08 11:15:31,Trainline,-46.39,0.00,EUR,COMPLETATO,168.89
```

> ⚠️ **Attenzione parsing**: alcune descrizioni contengono virgole (es. `"PayPal (Europe) S.a r.l. et Cie, S.C.A."`). Queste sono già quotate nel file e vanno gestite correttamente con un parser CSV che rispetti le virgolette RFC 4180.

### 3.2 Colonne e mapping al modello interno

| Colonna XLSX | Campo interno | Tipo | Note |
|---|---|---|---|
| `Tipo` | `transaction_type` | `string` | Vedi tipi rilevati sotto |
| `Prodotto` | — | `string` | Sempre `Attuale`, ignorato |
| `Data di inizio` | `started_at` | `datetime` | Data in cui l'utente ha avviato la transazione |
| `Data di completamento` | `completed_at` | `datetime` | Data effettiva di addebito (usata come `date`) |
| `Descrizione` | `description` | `string` | Nome merchant o causale |
| `Importo` | `amount` | `decimal` | Negativo = spesa, positivo = entrata/ricarica |
| `Costo` | `fee` | `decimal` | Commissioni Revolut (tipicamente `0.00`) |
| `Valuta` | `currency` | `string` | Es. `EUR` |
| `State` | `state` | `string` | Vedi stati rilevati sotto |
| `Saldo` | `balance_after` | `decimal` | Saldo dopo la transazione (assente se annullata) |

### 3.3 Tipi di transazione rilevati

| Valore `Tipo` | Significato | Trattamento |
|---|---|---|
| `Pagamento con carta` | Pagamento con carta fisica/virtuale | ✅ Importato |
| `Pagamento` | Pagamento p2p, abbonamenti, PayPal, Robo portfolio | ✅ Importato |
| `Pagamento Revolut` | Pagamento interno tra utenti Revolut | ✅ Importato |
| `Ricarica` | Ricarica del conto (es. da Google Pay) | ✅ Importato |
| `Rimborso su carta` | Storno / rimborso da merchant | ✅ Importato |
| `Prelievo` | Prelievo contanti da ATM | ✅ Importato |
| `Cambia valuta` | Conversione valuta interna | ✅ Importato |
| `Addebita` | Addebito diretto / domiciliazione | ✅ Importato |

### 3.4 Stati della transazione

| Valore `State` | Significato | Trattamento |
|---|---|---|
| `COMPLETATO` | Transazione completata | ✅ Importata |
| `OPERAZIONE ANNULLATA` | Transazione annullata (campo Saldo assente) | ❌ Scartata |
| `In sospeso` | Transazione non ancora finalizzata | ❌ Scartata |

### 3.5 Algoritmo di parsing (Django / pandas)

```python
import pandas as pd
from io import StringIO

def parse_revolut_xlsx(file_path: str) -> pd.DataFrame:
    """
    Revolut XLSX: i 10 campi sono embedded come CSV
    in un'unica colonna Excel. Ricostruzione necessaria.
    """
    df_raw = pd.read_excel(file_path, header=0, engine='openpyxl')
    col_header = df_raw.columns[0]          # intestazione CSV come nome colonna
    csv_rows   = df_raw[col_header].astype(str)
    csv_text   = col_header + '\n' + '\n'.join(csv_rows)

    df = pd.read_csv(
        StringIO(csv_text),
        dtype={'Importo': float, 'Costo': float, 'Saldo': float},
        parse_dates=['Data di inizio', 'Data di completamento'],
    )

    # Filtro: solo COMPLETATO
    df = df[df['State'] == 'COMPLETATO'].copy()
    return df
```

### 3.6 Statistiche dal file di esempio reale

Periodo: **01/01/2026 – 05/05/2026** — 541 transazioni totali, di cui:

| | Valore |
|---|---|
| Transazioni `COMPLETATO` | 528 |
| Transazioni scartate | 13 (`ANNULLATA` o `In sospeso`) |
| Totale spese | -7.438,20 EUR (472 transazioni) |
| Totale entrate/ricariche | +7.490,63 EUR (52 transazioni) |
| Merchant con spesa maggiore | Amazon (-1.511,48 EUR) |

---

## 4. Requisiti Funzionali

### 4.1 Autenticazione

- **RF-01** — Registrazione utente con email e password
- **RF-02** — Login con restituzione di access token e refresh token JWT
- **RF-03** — Logout con invalidazione del refresh token
- **RF-04** — Ogni utente vede solo i propri dati (isolamento per `user_id`)

### 4.2 Import CSV

- **RF-05** — Upload di file **XLSX** (`.xlsx`) tramite interfaccia drag & drop
- **RF-06** — Validazione del formato XLSX prima dell'import: presenza dell'unica colonna con intestazione CSV attesa (`Tipo,Prodotto,Data di inizio,...`)
- **RF-07** — Parsing con ricostruzione del CSV embedded: lettura colonna unica → ricostruzione header + righe → `pd.read_csv` con gestione virgolette RFC 4180
- **RF-08** — Deduplicazione: transazioni già presenti non vengono reimportate (controllo su `started_at + description + amount`)
- **RF-09** — Importazione solo delle transazioni con `State = COMPLETATO`; scartate le `OPERAZIONE ANNULLATA` e `In sospeso`
- **RF-10** — Feedback all'utente: numero di transazioni importate, duplicate scartate, annullate/sospese escluse, errori di parsing
- **RF-11** — Storico degli import con data, nome file, esito e conteggi

### 4.3 Transazioni

- **RF-12** — Lista transazioni con paginazione e ordinamento per data
- **RF-13** — Ricerca full-text per descrizione / merchant
- **RF-14** — Filtri per: intervallo di date, categoria, tipo (`CARD_PAYMENT`, `TRANSFER`, ecc.), segno (spesa/entrata)
- **RF-15** — Dettaglio singola transazione
- **RF-16** — Modifica manuale della categoria di una transazione
- **RF-17** — Aggiunta di note personali a una transazione
- **RF-18** — Eliminazione manuale di una transazione

### 4.4 Categorie

- **RF-19** — Categorie predefinite di sistema (non eliminabili): Alimentari, Trasporti, Ristoranti, Intrattenimento, Salute, Shopping, Abbonamenti, Investimenti, Stipendio, Trasferimenti, Prelievi ATM, Cambio Valuta, Altro
- **RF-20** — Creazione di categorie personalizzate con nome e colore
- **RF-21** — Categorizzazione automatica basata su regole keyword → categoria (es. `Netflix` → Abbonamenti, `Trainline` → Trasporti, `To Robo portfolio` → Investimenti, `Prelievo di contanti` → Prelievi ATM)
- **RF-22** — Gestione regole di auto-categorizzazione: creazione, modifica, eliminazione, priorità
- **RF-23** — Applicazione retroattiva delle regole a transazioni già importate

### 4.5 Dashboard e Statistiche

- **RF-24** — Riepilogo del mese corrente: totale spese, totale entrate, saldo netto
- **RF-25** — Grafico a torta / donut: distribuzione spese per categoria nel mese selezionato
- **RF-26** — Grafico a barre: andamento spese mensili negli ultimi 12 mesi
- **RF-27** — Grafico a linee: evoluzione del saldo nel tempo
- **RF-28** — Top 5 merchant per spesa nel periodo selezionato
- **RF-29** — Confronto mese corrente vs mese precedente per categoria
- **RF-30** — Filtro globale dashboard per periodo (mese, trimestre, anno, personalizzato)

### 4.6 Budget

- **RF-31** — Creazione di un budget mensile per categoria (es. Ristoranti: 200€/mese)
- **RF-32** — Visualizzazione avanzamento budget con barra di progresso
- **RF-33** — Alert visivo quando si supera l'80% e il 100% del budget
- **RF-34** — Storico budget mese per mese

### 4.7 Suggerimenti

- **RF-35** — Suggerimenti automatici generati analizzando i pattern di spesa:
  - Categoria con maggiore incremento rispetto al mese precedente
  - Abbonamenti ricorrenti rilevati automaticamente
  - Giorni / orari con picchi di spesa
  - Spese anomale (outlier statistici per categoria)
- **RF-36** — I suggerimenti vengono ricalcolati ad ogni nuovo import

- **RF-40 (nuovo)** — **Analisi AI del profilo di spesa**: il sistema invia un riepilogo strutturato aggregato delle transazioni utente (ultimi 6 mesi, per categoria e trend mensili) a **Vercel AI Gateway** con modello `gpt-5`, ricevendo insight narrativi personalizzati.
- **RF-41 (nuovo)** — **Fallback statistico automatico**: se l'AI Gateway non risponde (timeout, errore HTTP, rate limit), il sistema deve automaticamente degradare ai suggerimenti statistici legacy (`_detect_*`) senza fallire la richiesta.
- **RF-42 (nuovo)** — **Caching intelligente suggerimenti AI**: i suggerimenti generati dall'AI vengono cache-ati per 24 ore per utente (chiave Redis `suggestions:<user_id>`). La cache viene invalidata automaticamente dopo un nuovo import di transazioni.
- **RF-43 (nuovo)** — **Privacy e token limit**: i dati inviati a GPT-5 non devono includere informazioni personali identificabili (PII) delle singole transazioni (merchant, ID transazione), ma solo aggregati per categoria e trend mensili.

---

## 5. Requisiti Non Funzionali

- **RNF-01** — API RESTful con risposte in JSON
- **RNF-02** — Autenticazione stateless via JWT su tutte le rotte protette
- **RNF-03** — Import CSV asincrono (Celery + Redis) per file di grandi dimensioni (> 1000 righe)
- **RNF-04** — Risposta API < 300ms per le query di lista con paginazione
- **RNF-05** — Frontend responsive (desktop-first, supporto tablet)
- **RNF-06** — Gestione errori centralizzata con messaggi in italiano
- **RNF-07** — Variabili d'ambiente per tutti i parametri sensibili (nessuna chiave hardcoded)
- **RNF-08** — CORS configurato per accettare solo l'origine del frontend

---

## 6. Architettura

```
┌─────────────────────────────────────────────────────┐
│                     CLIENT                          │
│         Vue 3 + TypeScript + Vite                   │
│   Pinia · Vue Router · Chart.js · Axios             │
└────────────────────┬────────────────────────────────┘
                     │ HTTP / REST (JSON)
                     │ JWT Bearer Token
┌────────────────────▼────────────────────────────────┐
│                    BACKEND                          │
│           Django 5 + Django REST Framework          │
│                                                     │
│  /api/auth/         Auth (JWT)                      │
│  /api/transactions/ CRUD transazioni + import CSV   │
│  /api/categories/   Categorie + regole              │
│  /api/budgets/      Budget mensili                  │
│  /api/stats/        Aggregazioni statistiche        │
│  /api/suggestions/  Suggerimenti                    │
└───────┬──────────────────────┬──────────────────────┘
        │                      │ Task asincroni
┌───────▼──────┐      ┌────────▼──────────┐
│  PostgreSQL  │      │  Celery + Redis   │
│  (dati)      │      │  (import CSV)     │
└──────────────┘      └───────────────────┘
```

---

## 7. Modello dei Dati

### User
```
id, email, password_hash, created_at
```

### Transaction
```
id, user_id (FK), started_at, completed_at, description, amount, fee,
currency, transaction_type, state, balance_after, category_id (FK),
notes, import_batch_id (FK), created_at
```
> `transaction_type` ∈ {`Pagamento con carta`, `Pagamento`, `Pagamento Revolut`, `Ricarica`, `Rimborso su carta`, `Prelievo`, `Cambia valuta`, `Addebita`}

### Category
```
id, user_id (FK, NULL = sistema), name, color, icon, is_system
```

### CategoryRule
```
id, user_id (FK), keyword, category_id (FK), priority, created_at
```

### Budget
```
id, user_id (FK), category_id (FK), year, month, amount_limit
```

### ImportBatch
```
id, user_id (FK), filename, imported_at, total_rows,
imported_count, skipped_count, error_count
```

---

## 8. Endpoint API

### Auth
```
POST   /api/auth/register/       Registrazione
POST   /api/auth/login/          Login → {access, refresh}
POST   /api/auth/refresh/        Rinnovo access token
POST   /api/auth/logout/         Logout (blacklist refresh)
```

### Transazioni
```
GET    /api/transactions/        Lista (paginata, filtrabile)
GET    /api/transactions/{id}/   Dettaglio
PATCH  /api/transactions/{id}/   Modifica categoria / note
DELETE /api/transactions/{id}/   Eliminazione
POST   /api/transactions/import/ Upload XLSX → avvia import
GET    /api/transactions/import/ Storico import batch
```

### Categorie
```
GET    /api/categories/          Lista categorie (sistema + utente)
POST   /api/categories/          Crea categoria personalizzata
PATCH  /api/categories/{id}/     Modifica
DELETE /api/categories/{id}/     Elimina (solo custom)
GET    /api/categories/rules/    Lista regole auto-categorizzazione
POST   /api/categories/rules/    Crea regola
DELETE /api/categories/rules/{id}/ Elimina regola
```

### Budget
```
GET    /api/budgets/             Lista budget (filtro anno/mese)
POST   /api/budgets/             Crea budget
PATCH  /api/budgets/{id}/        Modifica importo
DELETE /api/budgets/{id}/        Elimina
```

### Statistiche
```
GET    /api/stats/summary/       Riepilogo periodo (spese, entrate, netto)
GET    /api/stats/by-category/   Spese aggregate per categoria
GET    /api/stats/monthly/       Trend mensile ultimi N mesi
GET    /api/stats/top-merchants/ Top merchant per importo
GET    /api/stats/balance/       Evoluzione saldo nel tempo
```

### Suggerimenti
```
GET    /api/suggestions/         Lista suggerimenti attivi
```

---

## 9. Stack Tecnologico Dettagliato

### Backend
| Libreria | Versione | Scopo |
|---|---|---|
| Django | 5.x | Framework web |
| djangorestframework | 3.15.x | API REST |
| djangorestframework-simplejwt | 5.x | Autenticazione JWT |
| psycopg2-binary | 2.x | Driver PostgreSQL |
| celery | 5.x | Task asincroni |
| redis | 5.x | Broker Celery |
| openpyxl | 3.x | Lettura file XLSX Revolut |
| pandas | 2.x | Parsing e validazione del CSV embedded |
| django-cors-headers | 4.x | Gestione CORS |
| django-filter | 24.x | Filtri API |

### Frontend
| Libreria | Versione | Scopo |
|---|---|---|
| Vue | 3.x | Framework UI |
| TypeScript | 5.x | Tipizzazione |
| Vite | 5.x | Build tool |
| Vue Router | 4.x | Routing SPA |
| Pinia | 2.x | State management |
| Axios | 1.x | Client HTTP |
| Chart.js + vue-chartjs | 4.x | Grafici |
| Tailwind CSS | 3.x | Styling |
| VueUse | 10.x | Composables utility |

---

## 10. Struttura Directory

```
finance-tracker/
├── backend/
│   ├── config/                  # Settings Django (base, dev, prod)
│   ├── apps/
│   │   ├── authentication/      # Modelli e viste auth
│   │   ├── transactions/        # Modello Transaction + import CSV
│   │   ├── categories/          # Modelli Category + CategoryRule
│   │   ├── budgets/             # Modello Budget
│   │   ├── stats/               # Aggregazioni statistiche
│   │   └── suggestions/         # Logica suggerimenti
│   ├── manage.py
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── api/                 # Client Axios + tipi risposta
│   │   ├── components/          # Componenti riutilizzabili
│   │   ├── views/               # Pagine Vue
│   │   ├── stores/              # Store Pinia
│   │   ├── router/              # Configurazione route
│   │   └── types/               # Interfacce TypeScript
│   ├── vite.config.ts
│   └── tsconfig.json
├── docker-compose.yml
└── README.md
```

---

## 11. Flusso Import CSV

```
Utente carica file XLSX
        │
        ▼
[Frontend] Validazione estensione (.xlsx)
        │
        ▼
[POST /api/transactions/import/] Upload multipart
        │
        ▼
[Backend] Verifica struttura XLSX:
  - Apre con openpyxl
  - Controlla che la colonna unica contenga l'intestazione CSV attesa
        │
        ├── ❌ Formato non valido → 400 Bad Request + dettaglio errore
        │
        ▼
[Celery Task] Parsing asincrono
  - Ricostruisce CSV embedded (header + righe)
  - pd.read_csv con gestione virgolette RFC 4180
  - Filtra State != 'COMPLETATO'
  - Deduplicazione (started_at + description + amount)
  - Auto-categorizzazione via CategoryRule
  - Salvataggio batch su PostgreSQL
        │
        ▼
[Frontend] Polling → visualizza risultato import
  - N importate / N duplicate / N annullate scartate / N errori
```

---

## 12. MVP — Priorità di Sviluppo

**Fase 1 — Core (settimane 1-2)**
- Setup Django + DRF + PostgreSQL + JWT
- Setup Vue 3 + TypeScript + Vite + Router + Pinia
- Autenticazione completa (register, login, logout)
- Import CSV sincrono (senza Celery)
- Lista transazioni con filtri base

**Fase 2 — Funzionalità (settimane 3-4)**
- Categorie e regole di auto-categorizzazione
- Dashboard con grafici (torta, barre, linee)
- Budget mensili

**Fase 3 — Avanzato (settimane 5-6)**
- Import asincrono con Celery + Redis
- Suggerimenti automatici
- Confronto mese su mese
- Export dati

---

## 13. Docker Compose

```yaml
services:
  db:
    image: postgres:16
    environment:
      POSTGRES_DB: finance_tracker
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - pgdata:/var/lib/postgresql/data

  redis:
    image: redis:7-alpine

  backend:
    build: ./backend
    command: python manage.py runserver 0.0.0.0:8000
    volumes:
      - ./backend:/app
    ports:
      - "8000:8000"
    depends_on:
      - db
      - redis
    env_file: .env

  celery:
    build: ./backend
    command: celery -A config worker -l info
    volumes:
      - ./backend:/app
    depends_on:
      - db
      - redis
    env_file: .env

  frontend:
    build: ./frontend
    command: npm run dev
    volumes:
      - ./frontend:/app
    ports:
      - "5173:5173"
    depends_on:
      - backend

volumes:
  pgdata:
```
