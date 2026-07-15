# Getting Started — Step by Step

**You only need your OpenAI API key to begin. Everything else is added later.**

---

## What You Are Building (Quick Recap)

```
Customer (Instagram/Facebook)
        ↓ message
   FastAPI (receives webhook)
        ↓
   LangGraph Agent (reasons, calls tools)
        ↓                    ↓
   OpenAI GPT-4o        CRM API (price, booking)
        ↓
   Meta API (sends reply)
        ↓
   Customer gets answer
```

**Right now you can build and test the middle part (LangGraph Agent + GPT-4o) without Meta or CRM.**

---

## Step 1 — Set Up Python Environment

Open a terminal in the project root and run:

```bash
# Create a virtual environment
python -m venv venv

# Activate it (Windows PowerShell)
.\venv\Scripts\Activate.ps1

# Activate it (Mac/Linux)
source venv/bin/activate

# Install all dependencies
pip install -r requirements.txt
```

---

## Step 2 — Add Your OpenAI API Key

```bash
# Copy the template
copy .env.example .env
```

Open `.env` and add your key:

```
OPENAI_API_KEY=sk-your-actual-key-here
```

That is the only thing you need for Step 3.

---

## Step 3 — Run the Agent (Terminal Test)

```bash
python scripts/test_agent.py
```

You will see an interactive chat. Try these conversations:

**Test 1 — Price query (tool calling)**
```
You: How much is box braids?
Agent: [calls get_service_price tool] Box braids are $180...
```

**Test 2 — Unknown service (triggers escalation)**
```
You: How much for passion twists?
Agent: [tool returns not_found] escalates to human
```

**Test 3 — Full booking**
```
You: I want to book box braids for Saturday
You: 10am works
You: My name is Sarah, 555-0192
Agent: [creates booking] Here is your confirmation...
```

**Test 4 — Explicit escalation**
```
You: Can I speak to the owner?
Agent: [immediately escalates] Connecting you with our team...
```

**Test 5 — Multi-turn context**
```
You: What services do you offer?
You: How much is the second one?   ← agent remembers the list
```

---

## Step 4 — Understand What Just Happened

After running the test, open these files and read them in order:

| File | What to understand |
|---|---|
| `app/agent/state.py` | What data flows through the agent |
| `app/agent/prompts.py` | What instructions the agent runs on |
| `app/agent/tools.py` | What tools exist, what mock data they return |
| `app/agent/nodes.py` | What each step in the graph does |
| `app/agent/graph.py` | How the steps connect to each other |

The key insight: **the agent loops between `run_agent` and `execute_tools` until it has enough information to give a final answer.**

---

## Step 5 — Add Mock Services or Modify the Prompt

Now that the agent is running, experiment:

**Add a new service to the mock CRM:**
Open `app/agent/tools.py` and add to `MOCK_SERVICES`:

```python
"passion twists": {
    "price": 190,
    "currency": "USD",
    "duration_hours": 5,
    "includes_hair": True,
    "description": "Passion twists with included hair",
},
```

Test it — the agent will now quote the correct price instead of escalating.

**Change the salon info:**
Open `scripts/test_agent.py` and modify `DEMO_SALON`:

```python
DEMO_SALON = {
    "salon_name": "Your Actual Salon Name",
    "salon_address": "Your actual address",
    ...
}
```

---

## Step 6 — Next Build Steps (In Order)

Once you are comfortable with the agent, build the rest in this order:

### Step 6a — PostgreSQL (Persistent Storage)
**Goal:** Store conversations and messages in a real database.

Files to implement:
- `app/db/connection.py` — asyncpg connection pool
- `app/db/repositories/conversation.py` — save/load conversations
- `app/db/repositories/salon.py` — load salon config from DB instead of mock

```bash
# Start PostgreSQL with Docker
docker-compose up postgres -d

# Run migrations (after implementing connection.py)
alembic upgrade head
```

### Step 6b — Redis (Fast Session Cache)
**Goal:** Fast session lookups — no DB query on every message.

Files to implement:
- `app/cache/connection.py` — Redis async connection
- `app/cache/session.py` — session store (sender_id → session data)
- `app/cache/history.py` — conversation history cache
- `app/cache/rate_limit.py` — rate limiting

```bash
# Start Redis with Docker
docker-compose up redis -d
```

### Step 6c — FastAPI Webhook (Meta Integration)
**Goal:** Receive real Instagram/Facebook messages.

Files to implement:
- `app/channels/signature.py` — HMAC verification
- `app/channels/webhook_parser.py` — normalize Meta events
- `app/channels/meta_client.py` — send replies via Meta API
- `app/api/webhook.py` — POST /webhook/meta endpoint

What you need from Meta before starting this step:
- Facebook Page Admin access for the pilot salon
- Instagram Professional Account linked to the Facebook Page
- Meta Business Verification completed
- Long-lived Page Access Token
- App Review: `pages_messaging`, `instagram_manage_messages`

### Step 6d — Real CRM Integration
**Goal:** Replace mock tools with real CRM API calls.

Files to implement:
- `app/crm/client.py` — async CRM HTTP client
- `app/crm/models.py` — request/response Pydantic models
- Update `app/agent/tools.py` — replace `execute_tool()` to call `crm_client` instead of mock functions

What you need before starting:
- CRM API base URL
- CRM API key or auth token
- CRM endpoint documentation (price, availability, booking, contacts)

### Step 6e — Human Handoff
**Goal:** Alert the team when escalation is triggered, and pause the agent.

Files to implement:
- `app/handoff/escalation.py` — trigger + resume logic
- `app/handoff/notifier.py` — Slack/Email alerts
- `app/api/internal.py` — resume + draft approval endpoints

What you need:
- Slack webhook URL (from Slack App setup)
- OR email SMTP credentials as fallback

### Step 6f — Docker Deployment
**Goal:** Deploy everything as a production-ready container.

```bash
# Build and start everything
docker-compose up --build -d

# Check logs
docker-compose logs -f app

# Run DB migrations inside container
docker-compose exec app alembic upgrade head
```

---

## Project Structure Reference

```
customer-support-agent/
├── app/
│   ├── agent/          ← AI brain (FULLY IMPLEMENTED — start here)
│   │   ├── state.py    ← Shared state between all nodes
│   │   ├── prompts.py  ← System prompt template
│   │   ├── tools.py    ← Tool schemas + mock implementations
│   │   ├── nodes.py    ← Node functions (run_agent, execute_tools, etc.)
│   │   └── graph.py    ← LangGraph graph definition
│   │
│   ├── api/            ← FastAPI route handlers (TODO)
│   ├── channels/       ← Meta webhook + message sender (TODO)
│   ├── crm/            ← CRM API client (TODO)
│   ├── db/             ← PostgreSQL + repositories (TODO)
│   ├── cache/          ← Redis session + history (TODO)
│   ├── handoff/        ← Human escalation + Slack alerts (TODO)
│   ├── monitoring/     ← Logging + Sentry (TODO)
│   ├── config.py       ← All settings from .env
│   └── main.py         ← FastAPI app entry point
│
├── scripts/
│   └── test_agent.py   ← Run this to test agent in terminal (NOW)
│
├── tests/              ← Automated tests (add as you build)
├── docker-compose.yml  ← Start all services
├── Dockerfile          ← App container definition
├── requirements.txt    ← Python dependencies
├── .env.example        ← Environment variable template
└── GETTING_STARTED.md  ← This file
```

---

## Checklist — Right Now (Only OpenAI Key Needed)

- [ ] Virtual environment created and activated
- [ ] `pip install -r requirements.txt` completed
- [ ] `.env` file created with `OPENAI_API_KEY`
- [ ] `python scripts/test_agent.py` runs successfully
- [ ] Price query test passes (tool called, correct price returned)
- [ ] Unknown service test passes (escalation triggered)
- [ ] Full booking test passes (booking created, confirmation sent)
- [ ] Read and understand `app/agent/nodes.py`
- [ ] Read and understand `app/agent/graph.py`
- [ ] Add one new service to `MOCK_SERVICES` and verify it works

When all boxes are checked, you are ready for Step 6a (PostgreSQL).
