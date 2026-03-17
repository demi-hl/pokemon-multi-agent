# CLAUDE.md — LO TCG Pokemon Multi-Agent System

## Project Overview

A high-speed, stealth multi-agent system for scanning Pokemon TCG card stock across retailers (Target, Walmart, Best Buy, GameStop, Costco, Pokemon Center), analyzing prices, and auto-buying deals. Includes a multi-user Discord bot and a React dashboard frontend.

## Tech Stack

### Backend (Python)
- **Framework**: Flask (API server at `agents/agents_server.py`)
- **Database**: SQLite (`pokemon_tcg.db`, `pokemon_tasks.db`)
- **Discord Bot**: discord.py with slash commands
- **AI**: Anthropic Claude SDK (`anthropic>=0.39.0`) for vision/grading
- **Web Scraping**: BeautifulSoup4, lxml, httpx
- **Security**: Fernet encryption for payment data
- **Deployment**: Render (gunicorn), see `render.yaml` and `Procfile`

### Frontend (React/TypeScript)
- **Build**: Vite + TypeScript
- **UI**: React 19, Tailwind CSS v4, Framer Motion
- **State**: Zustand
- **Data Fetching**: TanStack React Query
- **Maps**: Leaflet / React-Leaflet
- **Charts**: Recharts
- **Routing**: React Router v7
- **Source**: `frontend/` directory

### Static Dashboard
- `dashboard.html` — standalone HTML dashboard (deployed to Vercel via `vercel.json`)

## Project Structure

```
agents/                    # Core Python backend
  agents_server.py         # Main Flask API server (entry point)
  scanners/                # Retailer-specific scrapers (Target, Walmart, etc.)
  buyers/                  # Auto-buy logic
  graders/                 # AI visual card grading
  market/                  # Market analysis
  discord_bot/             # Multi-user Discord bot (bot.py, user_db.py, notifier.py)
  price_agent.py           # Price analysis agent
  grading_agent.py         # ROI & grading evaluation agent
  buy_agent.py             # Purchase decision agent
  retail_agent.py          # Retail scanning coordinator
  db.py                    # SQLite database layer
  tasks/                   # Task runner system
  stealth/                 # Anti-detection (UA rotation, jitter, proxy)
  auth/                    # Authentication
  notifications/           # Alert dispatch
  vision/                  # Vision/image analysis
  utils/                   # Shared utilities
  scheduler.py             # Scan scheduling

api/                       # Card dashboard Flask API
  app.py                   # Flask app factory (flask --app api.app:create_app run)

frontend/                  # React dashboard (Vite + TS)
  src/
    components/            # React components
    pages/                 # Route pages
    hooks/                 # Custom React hooks
    api/                   # API client layer
    store/                 # Zustand stores
    types/                 # TypeScript types
    lib/                   # Utility functions

db/                        # SQLite schema/migrations
market/                    # Set/card price data
search/                    # Card search
collection/                # Collection manager
alerts/                    # Price alert tracker
grading/                   # Grade estimator
agent/                     # Agent settings (budget, autonomy)
scripts/                   # Utility scripts
workflows/                 # n8n workflow JSON
config.json                # Watchlist, thresholds, autobuy, notifications config
```

## Running the Project

```bash
# Backend API server
python3 agents/agents_server.py              # Dev (port 5000)
gunicorn agents.agents_server:app --bind 0.0.0.0:$PORT  # Prod

# Card dashboard API
flask --app api.app:create_app run

# Task runner (stock monitoring loop)
python3 agents/run_task_runner.py

# Discord bot
python3 agents/discord_bot/bot.py

# Frontend dev server
cd frontend && npm run dev

# Frontend build
cd frontend && npm run build
```

## Key API Endpoints

- `POST /scanner/{target|walmart|bestbuy|gamestop|costco|all}` — Scan retailers
- `POST /scanner/local` — ZIP-code local stock scan
- `POST /agent/{price|grading|autobuy}` — Processing agents
- `POST /grader/{analyze|batch}`, `GET /grader/standards` — AI visual grading
- `POST /pipeline/full` — Full scan + analysis pipeline
- `GET /health` — Health check
- `GET /scanner/captcha-stats` — CAPTCHA detection stats

## Architecture Principles

### 3-Layer Model
1. **Directive** — SOPs and config define *what* to do (`config.json`, markdown docs)
2. **Orchestration** — Route work, sequence agents, handle errors
3. **Execution** — Deterministic scripts handle APIs, scraping, DB ops

### Agent Pipeline
Scanners (per-retailer) -> Merge Results -> Price Agent -> Grading Agent -> Auto-Buy Agent -> Discord Notifications

### Stealth/Anti-Detection
- User-agent rotation, request jitter (1.5-4s), header spoofing
- Adaptive rate limiting, proxy rotation support
- CAPTCHA detection (CloudFlare, DataDome, PerimeterX, reCAPTCHA, hCaptcha, Akamai)
- Falls back to cached/demo data when blocked

## Development Guidelines

### Before Writing Code
- Check existing scripts/tools in `agents/` before creating new ones
- Reuse utilities from `agents/utils/` and `agents/stealth/`
- Follow the existing scanner pattern in `agents/scanners/` for new retailers

### Security (Always Check Before Completing Work)
- Never hardcode secrets or credentials — use environment variables
- Sanitize all user inputs (SQL injection, XSS, path traversal)
- Validate auth/permission boundaries
- Encrypted storage for sensitive data (Fernet)
- Run tests when available

### Code Style
- Python: Standard Python conventions, type hints encouraged
- Frontend: TypeScript strict, React functional components with hooks
- Use Zustand for state management (not Redux/Context)
- Use TanStack Query for server state
- Tailwind CSS for styling (v4 with `@tailwindcss/vite` plugin)

### Environment Variables
Key env vars (see `env.example` for full list):
- `POKEMON_PRICE_API_KEY`, `POKEMON_TCG_API_KEY` — Price data APIs
- `DISCORD_BOT_TOKEN`, `DISCORD_GUILD_ID` — Discord bot
- `ANTHROPIC_API_KEY` or `OPENAI_API_KEY` — AI vision grading
- `POKEMON_AUTOBUY_ENABLED`, `POKEMON_SIMULATION_MODE` — Auto-buy controls
- `PROXY_SERVICE_URL` — Proxy rotation
- Retailer credentials (`TARGET_USERNAME`, etc.)

### Testing
- Test files at project root: `test_blocking.py`, `test_proxy.py`, `test_delta.py`, etc.
- Run with: `python3 -m pytest test_*.py`
- Frontend: `cd frontend && npm run lint`

### Deployment
- **Backend**: Render (`render.yaml`) — Python 3.11, gunicorn, 2 workers
- **Static dashboard**: Vercel (`vercel.json`) — serves `dashboard.html`
- **Frontend**: Build with `npm run build` in `frontend/`

## Important Notes

- Auto-buy is **disabled by default** and runs in **simulation mode** — never enable in dev
- SQLite DB files (`*.db`) are gitignored and contain user data — never commit them
- `.env` files are gitignored — use `env.example` as reference
- The `codex_skills/` directory contains vendored OpenAI Codex skills (legacy from Cursor setup) — not used by Claude Code
- The `workflows/` directory contains n8n workflow JSON for orchestration
