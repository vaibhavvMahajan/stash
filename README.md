# Stash 🔖
A personal bookmark manager with an AI co-pilot.

## Live Demo
🌐 [https://stash-egl4.onrender.com](https://stash-egl4.onrender.com)

## Overview
Stash lets you save, search, and manage bookmarks through a natural language chat interface. The AI assistant talks to a backend MCP (Model Context Protocol) server to read and modify your bookmarks — it never queries the database directly.

**Example interactions:**
- "Save https://github.com under tag dev"
- "What did I save about Python?"
- "Delete the Notion bookmark"

---

## Features
- 🔐 **Authentication** — signup, login, logout with bcrypt password hashing
- 🔑 **Forgot password** — single-use, time-limited reset links via email
- 📧 **Transactional email** — welcome and password reset emails via Resend
- 🗄️ **SQL database** — Postgres on Neon, scoped per user
- 🤖 **AI co-pilot** — chat interface powered by Groq (Llama 3.1)
- 🔌 **MCP server** — all DB operations go through MCP tools, never direct queries
- 🚀 **Auto-deploy** — every push to `main` deploys to Render automatically

---

## Tech Stack

| Layer | Choice |
|---|---|
| Language | Python 3.11 |
| Web framework | FastAPI |
| Database | Postgres (Neon) |
| DB driver | psycopg2-binary |
| Auth | bcrypt + cookie sessions |
| LLM | Groq (llama-3.1-8b-instant) |
| MCP | mcp library (stdio JSON-RPC) |
| Email | Resend |
| Deploy | Render |

---

## Architecture

```
Browser (HTTPS)
    |
FastAPI (Render web service)
    ├── Web UI (login, signup, chat)
    ├── Chat handler
    │       └── Groq LLM API ──tool_calls──► MCP Bridge
    │                                              │ stdio JSON-RPC
    │                                              ▼
    │                                        MCP Server (subprocess)
    │                                              │ SQL scoped to user_id
    │                                              ▼
    │                                           Postgres (Neon)
    └── Mailer ──► Resend API ──► user inbox
```

---

## Project Structure

```
stash/
├── app/
│   ├── main.py        # FastAPI routes
│   ├── auth.py        # signup, login, forgot password
│   ├── database.py    # SQLAlchemy engine + init_db
│   ├── mailer.py      # Resend email integration
│   └── chat.py        # Groq LLM + MCP bridge
├── mcp_server/
│   └── server.py      # MCP tools: add/list/search/delete bookmark
├── templates/
│   ├── base.html
│   ├── login.html
│   ├── signup.html
│   ├── forgot.html
│   ├── reset.html
│   └── chat.html
├── .python-version    # 3.11.9
├── render.yaml
├── requirements.txt
└── .env               # not committed
```

---

## Database Schema

```sql
users (
    id, email, password_hash, created_at
)

bookmarks (
    id, user_id, url, title, tags, notes, created_at
)

password_reset_tokens (
    id, user_id, token, expires_at, used
)
```

Bookmarks are always scoped to `user_id` — a user can never read or modify another user's bookmarks, even via prompt injection.

---

## MCP Tools

| Tool | Description |
|---|---|
| `add_bookmark` | Save a URL with title, tags, notes |
| `list_bookmarks` | List all bookmarks (most recent first) |
| `search_bookmarks` | Search by keyword across URL, title, tags, notes |
| `delete_bookmark` | Delete by ID (scoped to logged-in user) |

---

## Local Setup

```bash
# Clone
git clone https://github.com/yourusername/stash.git
cd stash

# Virtual environment
python -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Environment variables
cp .env.example .env
# Fill in DATABASE_URL, RESEND_API_KEY, GROQ_API_KEY

# Run
uvicorn app.main:app --reload
```

Open [http://localhost:8000](http://localhost:8000)

---

## Environment Variables

| Variable | Description |
|---|---|
| `DATABASE_URL` | Neon Postgres connection string |
| `RESEND_API_KEY` | Resend API key for transactional email |
| `GROQ_API_KEY` | Groq API key for LLM inference |
| `BASE_URL` | Public URL (e.g. https://stash-egl4.onrender.com) |

---

## Security
- Passwords hashed with bcrypt (never stored plaintext)
- Password reset tokens are single-use and expire after 1 hour
- MCP tools are strictly scoped to the logged-in user's `user_id`
- All secrets stored in environment variables, never in Git
- `.env` is in `.gitignore`

---

## Trade-offs & What I'd Change
- **Session management** — currently uses a simple cookie with `user_id`. Would switch to signed JWT or server-side sessions for production.
- **MCP transport** — using stdio subprocess per request. Would use a persistent MCP server process with SSE transport for better performance.
- **Frontend** — minimal Jinja2 templates. Would build a proper React frontend with optimistic UI updates.
- **Error handling** — would add proper error boundaries and user-facing error messages.
