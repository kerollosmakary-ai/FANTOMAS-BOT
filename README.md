# Advanced AI Bot Web Service

Real-time AI chat service with customer API tokens, provider fallback, safe addons, and a React UI.

## Features

- FastAPI backend
- WebSocket real-time chat
- Customer API tokens like `sk_live_...`
- Token balance and usage charging
- Admin token creation, recharge, revoke
- Multi-provider router: Groq, OpenRouter, DeepSeek, OpenAI
- Provider fallback: if one provider fails, the bot tries the next one
- Safe addon system: normal chat keeps working even if an addon fails
- RAG addon placeholder ready for Chroma/Google Drive later
- Docker Compose setup
- React/Vite frontend

## Quick Start

### 1. Create environment file

```bash
cp .env.example .env
```

Edit `.env` and add at least one API key:

```env
GROQ_API_KEY=your_groq_key
# or
OPENROUTER_API_KEY=your_openrouter_key
# or
DEEPSEEK_API_KEY=your_deepseek_key
# or
OPENAI_API_KEY=your_openai_key
```

### 2. Run with Docker

```bash
docker compose up --build
```

Open:

- Frontend: http://localhost:3000
- Backend docs: http://localhost:8000/docs
- Health: http://localhost:8000/health

## Create a Customer API Token

From the UI, use the Admin section.

Default admin key:

```text
change-me-admin-key
```

You should change it in `.env`:

```env
ADMIN_KEY=your-secure-admin-key
```

Or use curl:

```bash
curl -X POST http://localhost:8000/admin/tokens \
  -H "Content-Type: application/json" \
  -H "x-admin-key: change-me-admin-key" \
  -d '{"owner_name":"client_a","balance":1000}'
```

Copy the returned `api_token`. It is shown only once.

## Chat over HTTP

```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer sk_live_xxx" \
  -d '{"message":"Hello","provider":"auto","addons":[]}'
```

## Chat over WebSocket

Connect to:

```text
ws://localhost:8000/ws/chat?token=sk_live_xxx
```

Send:

```json
{
  "content": "Hello, explain RAG simply",
  "provider": "auto",
  "addons": ["rag"]
}
```

Receive:

```json
{"type":"chunk","content":"Hello "}
{"type":"chunk","content":"there..."}
{"type":"done","provider":"groq","tokens_remaining":992}
```

## Token Charging

Default costs:

- Base chat request: 5 tokens
- RAG addon: 3 additional tokens

Change in `.env`:

```env
REQUEST_BASE_COST=5
RAG_ADDON_COST=3
```

## Addons Safety Rule

Addons are optional. If an addon fails, the bot logs the error and continues normal chat.

This keeps the core chat working even when RAG, Google Drive, or future integrations break.

## Project Structure

```text
ai-bot/
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── config.py
│   │   ├── database.py
│   │   ├── models.py
│   │   ├── schemas.py
│   │   ├── api/
│   │   ├── addons/
│   │   ├── services/
│   │   └── utils/
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── src/App.jsx
│   ├── src/style.css
│   ├── package.json
│   └── Dockerfile
├── docker-compose.yml
├── .env.example
└── README.md
```

## Next Steps

- Replace SQLite with Postgres for production
- Add real Chroma RAG indexing
- Add Google Drive sync
- Add Telegram webhook integration
- Add rate limiting
- Add customer dashboard login
# CI/CD test deploy 2026-06-20_10:02:19Z
# CI deploy attempt 1782003644
