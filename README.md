# 🐳 AI Voice Assistant — Quick Start & Dev Guide

This repository contains a multi-component voice assistant project implementing several voice and telephony integrations for research and demo purposes. It includes:

- Frontend demo (Vite + React) under `labs/`
- Conversational assistant configuration and actions under `rasa/`
- Voice & telephony experiments under `twilio-experiment/` and `voice-future-assistant/`
- Helper scripts and audio utilities in the repo root (e.g., `realtime.py`)

The preferred way to run the full stack is via Docker; however, each sub-project can be run and developed locally.

---

## ⚙️ Prerequisites

Install the following tools:

- Docker Desktop or Docker Engine
- git
- Node.js and npm/yarn (for frontend local dev)
- Python 3.8+ (for running scripts and Rasa in dev)

Note: On Windows, using WSL2 is recommended when running the included shell scripts (`restart.sh`). If you prefer PowerShell, see the "Docker Compose" steps below.

---

## 🚀 Getting Started — Run with Docker

1. Clone the repository

```powershell
git clone https://github.com/FEUP-LGP-2025/LGP-12
cd LGP-12
```

2. Option A — Run the provided script (Unix-like environments or WSL):

```bash
chmod +x restart.sh
./restart.sh
```

3. Option B — Using Docker Compose directly (cross-platform):

```powershell
# Bring up the compose stack (if a top-level docker-compose.yml exists)
docker compose up --build -d

# Or run a service individually. Example: frontend (labs)
cd labs
docker compose up --build -d

# In another terminal, bring up Rasa
cd ../rasa
docker compose up --build -d
```

4. Open locally the application

http://localhost:5173/

---

## 🧭 Architecture & Components

- labs/: Frontend demo (Vite + React)
- rasa/: Rasa NLU and action server with domain, stories, and e2e tests
- twilio-experiment/: Twilio / telephony integration experiments (Python)
- voice-future-assistant/: Voice assistant components and pipelines for local and production
- realtime.py: small helper script for audio / local testing

Each module typically has its own `Dockerfile`, `docker-compose.yml`, and environment files. Run them as needed, either separately or as part of an integrated stack.

---

## 🔧 Local Development (examples)

Frontend (Vite):

```powershell
cd labs
npm install
npm run dev
# Open http://localhost:5173
```

Rasa (local development):

```powershell
cd rasa
pip install -r requirements.txt # or create a venv
# Start Rasa services (if not using Docker)
rasa run -m models --enable-api --cors "*"
rasa run actions
```

Voice/Telephony (local dev):

```powershell
cd twilio-experiment
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements-dev.txt
python pipeline.py  # or run specific scripts
```

---

## 🔎 Helpful Commands

- Rebuild and restart the main Docker Compose services:

```powershell
docker compose down
docker compose up --build -d
```

- Follow logs:

```powershell
docker compose logs -f         # all services
docker compose logs -f <name>  # per service
```

---

## ⚠️ Troubleshooting

- If `restart.sh` fails on Windows, either run it from WSL or use `docker compose` commands directly from PowerShell.
- Make sure environment variables and API credentials required by STT/TTS services are configured before starting those services.
- Check Docker logs for failing services and inspect the output to identify missing dependencies or misconfigurations.

---

## 🧾 Contributing

Contributions are welcome. Please open an issue for feature requests or bugs and send a PR for improvements. Keep changes scoped to relevant sub-projects and include tests or usage docs when appropriate.

---

## 📞 Contact & Support

Open an issue in the repository for questions, or contact a project maintainer directly if available.