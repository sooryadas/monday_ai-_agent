# Monday.com BI Agent

An AI-powered Business Intelligence agent that answers natural language questions
about your Monday.com Deals and Work Orders boards — with live API calls every time.

---

## Architecture

```
User Question → FastAPI → Groq (tool-calling loop) → Monday.com API (live) → Answer + Trace
```

## Quick Start

### 1. Clone & Install

```bash
cd monday-ai-agent
pip install -r requirements.txt
```

### 2. Configure

```bash
cp .env.example .env
# Edit .env with your keys
```

**Where to get keys:**
- `GROQ_API_KEY` → https://console.groq.com/
- `MONDAY_API_TOKEN` → Monday.com → Avatar (top right) → Admin → API
- `DEALS_BOARD_ID` → Open board in Monday.com, grab the number from the URL
- `WORK_ORDERS_BOARD_ID` → Same as above for your work orders board

### 3. Import CSV Data

1. Go to Monday.com → `+ New Board`
2. Create **"Deals"** board → Import your deals CSV
3. Create **"Work Orders"** board → Import your work orders CSV
4. Copy board IDs into `.env`

### 4. Run

```bash
cd backend
python main.py
```

Open http://localhost:8000 in your browser.

---

## How It Works

1. User submits a question via the chat UI
2. FastAPI sends it to the Groq agent
3. Groq decides which Monday.com tools to call
4. Each tool makes a **live** GraphQL API call to Monday.com
5. Groq synthesizes the data into a natural language answer
6. The answer + full tool trace are returned to the UI

The sidebar shows every tool call in real-time — tool name, inputs, and results.

---

## Available Tools

| Tool | Description |
|------|-------------|
| `get_board_columns` | Inspect schema of a board |
| `get_board_items` | Fetch items/rows from a board |
| `search_board_items` | Keyword search across a board |
| `get_item_details` | Deep dive on a single item |

---

## Sample Questions

- "What is our total ARR across all deals?"
- "Show pipeline breakdown by stage"
- "Which accounts have both open deals and work orders?"
- "What are our highest priority work orders right now?"
- "How many deals closed this quarter?"
- "Which deals are in the energy sector?"

---

## Deploy to Railway

```bash
# Install Railway CLI
npm install -g @railway/cli

# Login and deploy
railway login
railway init
railway up
```

Set environment variables in Railway dashboard (same as .env).

---

## Project Structure

```
monday-ai-agent/
├── backend/
│   ├── main.py          # FastAPI server
│   ├── agent.py         # Groq tool-calling loop
│   ├── tools.py         # Tool definitions for Groq
│   ├── monday_api.py    # Monday.com API wrapper
│   └── config.py        # Config & system prompt
├── frontend/
│   └── index.html       # Chat UI
├── requirements.txt
└── .env.example
```