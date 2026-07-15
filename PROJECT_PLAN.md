# AI Chat Support Agent — MVP 1 Project Plan

**Client:** The Fine Dudes
**Stack:** FastAPI + LangGraph + OpenAI SDK + PostgreSQL + Redis + Docker
**Prepared by:** Atrium Solution
**Date:** July 14, 2026
**Version:** 2.0

---

## Table of Contents

1. [Project Overview](#1-project-overview)
2. [Complete Tech Stack](#2-complete-tech-stack)
3. [How Everything Works Together](#3-how-everything-works-together)
4. [File & Folder Structure](#4-file--folder-structure)
5. [Phase 1 — Project Setup & Meta Webhook (Day 1)](#5-phase-1--project-setup--meta-webhook-day-1)
6. [Phase 2 — LangGraph Agent & OpenAI Tool Calling (Day 2–3)](#6-phase-2--langgraph-agent--openai-tool-calling-day-23)
7. [Phase 3 — CRM Integration & Booking APIs (Day 4)](#7-phase-3--crm-integration--booking-apis-day-4)
8. [Phase 4 — PostgreSQL Schema, Redis & Error Handling (Day 5)](#8-phase-4--postgresql-schema-redis--error-handling-day-5)
9. [Phase 5 — Human Handoff & Logging (Day 6)](#9-phase-5--human-handoff--logging-day-6)
10. [Phase 6 — Docker Deployment, Monitoring & QA (Day 7)](#10-phase-6--docker-deployment-monitoring--qa-day-7)
11. [PostgreSQL Data Model](#11-postgresql-data-model)
12. [Redis — What Gets Stored](#12-redis--what-gets-stored)
13. [API Endpoints Reference](#13-api-endpoints-reference)
14. [Environment Variables](#14-environment-variables)
15. [What We Need From Client](#15-what-we-need-from-client)

---

## 1. Project Overview

### What We Are Building

An AI-powered customer support agent for US-based hair braiding salon clients. The agent operates across Meta platforms (Instagram DM, Facebook Messenger, and public comments), handles inbound customer conversations end-to-end, fetches real-time prices from the CRM, drives bookings, and writes all data back into the CRM.

### Non-Negotiable Rules

- Prices are **never** quoted from memory or assumption — a CRM API call is mandatory every single time
- If a price is not found in the CRM → automatic human handoff, no exceptions
- If the customer complains or requests to speak to a person → automatic human handoff
- Every conversation's full transcript must be saved to the CRM — nothing lives only in the inbox

### MVP 1 Scope

| # | Feature | Priority |
|---|---|---|
| 1 | Handle Instagram Direct Messages | Must Have |
| 2 | Handle Facebook Messenger | Must Have |
| 3 | Public comment → DM redirect | Must Have |
| 4 | FAQ answers (services, hours, location, policies) | Must Have |
| 5 | Real-time price fetch from CRM | Critical |
| 6 | Availability check | Must Have |
| 7 | Booking creation + confirmation message | Must Have |
| 8 | CRM write-back (contact, transcript, lead status) | Must Have |
| 9 | Human handoff / escalation | Must Have |
| 10 | Human-in-Loop draft approval (pilot phase) | Must Have |
| 11 | Multi-salon support (per-salon config) | Must Have |

---

## 2. Complete Tech Stack

### Core Stack

| Layer | Technology | Why |
|---|---|---|
| **API Framework** | FastAPI | Async-first, fast, automatic docs, Pydantic validation |
| **Agent Orchestration** | LangGraph | State-machine-based agent — conversation flow is clearly defined, retry built-in |
| **LLM** | OpenAI SDK (GPT-4o) | Best-in-class tool calling, reliable JSON outputs |
| **Database** | PostgreSQL | Persistent storage — conversations, bookings, salon config |
| **Cache / Session** | Redis | Fast conversation state cache, rate limiting, session store |
| **Deployment** | Docker + Docker Compose | Consistent environment, portable, easy to deploy anywhere |

### Supporting Libraries

| Library | Purpose |
|---|---|
| `httpx` | Async HTTP client — Meta Graph API calls and CRM API calls |
| `pydantic-settings` | Load config from `.env` file, type-safe |
| `asyncpg` | PostgreSQL async driver |
| `redis-py` (async) | Redis async client |
| `sentry-sdk` | Error tracking — alerts on production errors |
| `structlog` | Structured JSON logging |
| `uvicorn` | ASGI server for FastAPI |
| `alembic` | Database migrations |

### Deferred to Later (Not in MVP 1)

| Tool | Reason Deferred |
|---|---|
| `LangSmith` | Agent tracing — add after pilot is stable |
| `Celery` | Background task queue — add when message volume increases |

---

## 3. How Everything Works Together

### Request Flow — What Happens When a Message Arrives

```
Customer sends IG DM: "How much is box braids?"
                │
                ▼
    ┌─────────────────────┐
    │   Meta Platform     │
    │   (Instagram)       │
    └──────────┬──────────┘
               │ POST webhook event
               ▼
    ┌─────────────────────┐
    │   FastAPI           │  Step 1: Receive webhook
    │   POST /webhook/meta│         Verify HMAC signature
    └──────────┬──────────┘         Return 200 OK immediately to Meta
               │
               ▼
    ┌─────────────────────┐
    │   Redis Session     │  Step 2: Check if sender has an active session
    │   Check             │         If human_handling = true → stop, leave in inbox
    └──────────┬──────────┘
               │
               ▼
    ┌──────────────────────────────────────────────────┐
    │   LangGraph Agent (State Machine)                │  Step 3: Agent runs
    │                                                  │
    │  check_session → load_salon_config               │
    │      → load_history → run_agent                  │
    │          → execute_tools (if tool call)          │
    │              → run_agent (loop until final reply)│
    │          → send_reply                            │
    │          → write_to_crm                          │
    │          → END                                   │
    └──────────┬───────────────────────────────────────┘
               │
               ▼
    ┌─────────────────────┐
    │   Tool Execution    │  Step 4: When agent calls a tool
    │                     │
    │  get_service_price  │ → CRM API → price returned to agent
    │  check_availability │ → CRM API → available slots returned
    │  create_booking     │ → CRM API → booking ID returned
    │  capture_contact    │ → PostgreSQL → contact saved
    │  escalate_to_human  │ → Human handoff flow triggered
    └──────────┬──────────┘
               │
    ┌──────────▼──────────┐
    │   PostgreSQL        │  Permanent storage
    │   Redis             │  Fast session cache
    └─────────────────────┘
```

### LangGraph State Machine — Concept

LangGraph defines the agent as a **graph of nodes and edges**.
Each node performs one specific task. Each edge determines where to go next.
The `AgentState` is a shared dictionary available to every node throughout the conversation.

```
┌──────────┐     ┌────────────────┐     ┌──────────────────┐
│  START   │────▶│ check_session  │────▶│ load_salon_config │
└──────────┘     └────────────────┘     └────────┬─────────┘
                                                  │
                                                  ▼
                                         ┌────────────────┐
                                         │  load_history  │
                                         └────────┬───────┘
                                                  │
                                                  ▼
                                         ┌────────────────┐
                                         │   run_agent    │◀─────────┐
                                         └───────┬────────┘          │
                                                 │                   │
                         ┌───────────────────────┤                   │
                         │                       │                   │
                         ▼                       ▼                   │
               ┌──────────────────┐   ┌──────────────────┐          │
               │  execute_tools   │──▶│  tool results    │──────────┘
               └──────────────────┘   └──────────────────┘
                         │ (if escalate tool)
                         ▼
               ┌──────────────────┐
               │ escalate_to_human│
               └──────────────────┘

               (if reply ready)
                         ▼
               ┌──────────────────┐
               │   send_reply     │
               └────────┬─────────┘
                        │
                        ▼
               ┌──────────────────┐
               │  write_to_crm    │
               └────────┬─────────┘
                        │
                        ▼
                    ┌───────┐
                    │  END  │
                    └───────┘
```

### Redis Role — What Gets Cached and Why

```
Redis = Fast in-memory store (data in milliseconds, no database roundtrip)

Session Store:
  key:   "session:{sender_id}"
  value: { salon_id, conversation_id, human_handling, pilot_mode, last_active }
  TTL:   24 hours

Conversation History Cache:
  key:   "history:{conversation_id}"
  value: [ { role, content, timestamp }, ... ]  ← last 20 messages
  TTL:   2 hours (reload from PostgreSQL after expiry)

Salon Config Cache:
  key:   "salon:{page_id}"
  value: { salon_id, name, address, hours, crm_url, pilot_mode }
  TTL:   1 hour

Rate Limiting:
  key:   "rate:{sender_id}"
  value: message count (incremented per message)
  TTL:   60 seconds (max 10 messages per minute)
```

---

## 4. File & Folder Structure

```
customer-support-agent/
│
├── docker-compose.yml              ← Start all services with one command
├── Dockerfile                      ← Application container definition
├── .env.example                    ← Environment variable template (committed to git)
├── .env                            ← Actual secrets (never committed to git)
├── requirements.txt                ← Python dependencies
├── alembic.ini                     ← Database migration configuration
│
├── app/
│   │
│   ├── main.py                     ← FastAPI application entry point
│   ├── config.py                   ← pydantic-settings — all env vars loaded here
│   │
│   ├── api/                        ← FastAPI route handlers
│   │   ├── __init__.py
│   │   ├── webhook.py              ← POST /webhook/meta (receives all Meta events)
│   │   ├── health.py               ← GET /health (deployment health check)
│   │   └── internal.py             ← Internal APIs (draft approve, conversation resume)
│   │
│   ├── agent/                      ← LangGraph agent — core AI logic
│   │   ├── __init__.py
│   │   ├── graph.py                ← Graph definition: nodes, edges, entry point
│   │   ├── nodes.py                ← Implementation of each node function
│   │   ├── state.py                ← AgentState TypedDict — shared conversation context
│   │   ├── tools.py                ← OpenAI tool schemas + execution functions
│   │   └── prompts.py              ← System prompt templates (salon info injected at runtime)
│   │
│   ├── channels/                   ← Meta platform integration
│   │   ├── __init__.py
│   │   ├── meta_client.py          ← httpx async client — send messages via Meta Graph API
│   │   ├── webhook_parser.py       ← Raw Meta event → normalized message object
│   │   └── signature.py            ← HMAC-SHA256 webhook signature verification
│   │
│   ├── crm/                        ← CRM integration
│   │   ├── __init__.py
│   │   ├── client.py               ← httpx async CRM API client
│   │   ├── models.py               ← CRM request/response Pydantic models
│   │   └── endpoints.py            ← CRM endpoint URL constants
│   │
│   ├── db/                         ← PostgreSQL
│   │   ├── __init__.py
│   │   ├── connection.py           ← asyncpg connection pool setup
│   │   ├── repositories/           ← All database operations (no raw SQL in business logic)
│   │   │   ├── conversation.py
│   │   │   ├── salon.py
│   │   │   ├── booking.py
│   │   │   ├── contact.py
│   │   │   └── draft.py
│   │   └── migrations/             ← Alembic migration files
│   │       └── versions/
│   │
│   ├── cache/                      ← Redis
│   │   ├── __init__.py
│   │   ├── connection.py           ← Redis async connection setup
│   │   ├── session.py              ← Session store (sender_id → session data)
│   │   ├── history.py              ← Conversation history cache
│   │   └── rate_limit.py           ← Per-sender rate limiting
│   │
│   ├── handoff/                    ← Human escalation
│   │   ├── __init__.py
│   │   ├── escalation.py           ← Escalation logic, trigger conditions, DB updates
│   │   └── notifier.py             ← Slack / Email alert sender
│   │
│   ├── monitoring/                 ← Error tracking and logging
│   │   ├── __init__.py
│   │   ├── sentry.py               ← Sentry SDK initialization
│   │   └── logger.py               ← structlog setup — structured JSON logs
│   │
│   └── utils/
│       ├── __init__.py
│       └── helpers.py
│
├── tests/
│   ├── test_webhook.py
│   ├── test_agent.py
│   ├── test_crm.py
│   └── test_tools.py
│
└── scripts/
    ├── create_assistant.py         ← One-time: create OpenAI Assistant with tools defined
    └── seed_salon.py               ← Insert test salon data into PostgreSQL
```

---

## 5. Phase 1 — Project Setup & Meta Webhook (Day 1)

### Goal

Initialize the project structure, set up Docker, get FastAPI running, and reliably receive Meta webhook events.

### Key Concept: Meta Webhooks

> When a customer sends a message on Instagram or Facebook, Meta sends an HTTP POST to your server.
> Your server **must return 200 OK within 5 seconds** — otherwise Meta will retry the event repeatedly.
> The correct pattern: receive the webhook → verify HMAC signature → return 200 OK immediately → process the message in the background (or as a fast async task in FastAPI).

### Tasks

#### 1.1 Project Initialization

```bash
mkdir -p app/{api,agent,channels,crm,db/repositories,db/migrations/versions,cache,handoff,monitoring,utils}
touch app/__init__.py app/main.py app/config.py
# Create requirements.txt and .env.example
```

#### 1.2 Docker Setup

`docker-compose.yml` will define three services:

| Service | Image | Port |
|---|---|---|
| `app` | Custom (Dockerfile) | 8000 |
| `postgres` | postgres:15 | 5432 |
| `redis` | redis:7-alpine | 6379 |

#### 1.3 `app/config.py` — Configuration

Using `pydantic-settings` to load and validate all environment variables:

```
OPENAI_API_KEY, OPENAI_MODEL
META_APP_ID, META_APP_SECRET, META_VERIFY_TOKEN
DATABASE_URL, REDIS_URL
DEFAULT_CRM_BASE_URL, DEFAULT_CRM_API_KEY
SLACK_WEBHOOK_URL, ALERT_EMAIL
SENTRY_DSN
APP_ENV, LOG_LEVEL
```

#### 1.4 `app/channels/signature.py` — HMAC Verification

Meta includes an `X-Hub-Signature-256` header with every webhook. This is an HMAC-SHA256 hash of the request body, signed with your `META_APP_SECRET`. Your server must verify this on every incoming request to confirm it genuinely came from Meta.

```
Process:
1. Read raw request body (before JSON parsing)
2. Compute HMAC-SHA256 using META_APP_SECRET
3. Compare against X-Hub-Signature-256 header (constant-time comparison)
4. Mismatch → return 403 Forbidden, log the attempt
```

#### 1.5 `app/channels/webhook_parser.py` — Message Normalization

Meta's raw webhook payload is deeply nested. The parser converts it into a flat, consistent format used throughout the application.

```
Input (Meta raw event):
{
  "entry": [{
    "messaging": [{
      "sender": { "id": "17841234567890" },
      "recipient": { "id": "page_456" },
      "message": { "mid": "mid.xxx", "text": "How much is box braids?" }
    }]
  }]
}

Output (normalized):
{
  "sender_id": "17841234567890",
  "channel": "instagram_dm",
  "page_id": "page_456",
  "text": "How much is box braids?",
  "message_id": "mid.xxx",
  "timestamp": "2026-07-14T14:30:00Z",
  "event_type": "dm"   // dm / comment
}
```

#### 1.6 `app/api/webhook.py` — Webhook Endpoint

```
GET  /webhook/meta  → Meta sends this once during initial setup (hub.challenge verification)
POST /webhook/meta  → All live events (DMs, Messenger, comments)

Flow for POST:
1. Read raw body
2. Verify HMAC signature → 403 if invalid
3. Return 200 OK immediately
4. Parse event and trigger agent asynchronously
```

#### Phase 1 Deliverables

- [ ] `docker-compose up` starts all three services without errors
- [ ] `GET /health` returns `{ "status": "ok" }`
- [ ] Meta webhook verification passes (GET /webhook/meta with hub.challenge)
- [ ] Instagram DM events received and logged to console
- [ ] Facebook Messenger events received and logged
- [ ] Comment events received and logged
- [ ] HMAC verification rejects requests with invalid signatures
- [ ] Normalized message schema flowing correctly through the parser

---

## 6. Phase 2 — LangGraph Agent & OpenAI Tool Calling (Day 2–3)

### Goal

Build the LangGraph agent that manages multi-turn conversations, calls CRM tools when needed, and sends replies back to customers.

### Key Concept: LangGraph

> LangGraph defines an agent as a **state machine** — a directed graph of nodes and edges.
>
> - **Node** = a discrete step (detect intent, call a tool, send a reply)
> - **Edge** = the transition rule (go to tool execution if tool call detected, go to send_reply if final answer ready)
> - **AgentState** = a shared dictionary passed through every node; it holds the entire conversation context
>
> Unlike a simple LLM call ("send message, get reply"), LangGraph lets you define exactly what the agent can do, in what order, and what happens on each outcome — making behavior predictable and debuggable.

### Key Concept: Tool Calling

> You define a set of functions (tools) that GPT-4o is allowed to call.
> The model decides autonomously when a tool is needed.
> When GPT-4o responds with a tool call (not a text reply), your code executes that function, returns the result to the model, and the model generates the final response with real data.
>
> For this project: GPT-4o cannot guess a price. It must call `get_service_price`, receive the CRM result, then respond.

### Day 2 Tasks

#### 2.1 `app/agent/state.py` — Agent State

```python
class AgentState(TypedDict):
    messages: list            # Full conversation history (human + AI + tool messages)
    sender_id: str            # Customer's Meta sender ID
    channel: str              # "instagram_dm" or "facebook_messenger"
    page_id: str              # Meta page ID (used to resolve salon)
    salon_id: str             # Which salon this conversation belongs to
    salon_config: dict        # Salon info: name, address, hours, policies
    conversation_id: str      # PostgreSQL conversations table row ID
    human_handling: bool      # If True → agent stops, human takes over
    pilot_mode: bool          # If True → agent drafts reply, does not send
    booking_details: dict     # Populated during booking flow
    escalation_reason: str    # Why escalation was triggered (for logs/alerts)
```

#### 2.2 `app/agent/tools.py` — Tool Definitions

Five tools are defined and passed to GPT-4o:

| Tool | Arguments | Returns | Action |
|---|---|---|---|
| `get_service_price` | `service_name`, `salon_id` | `price`, `currency`, `includes_hair` or `null` | CRM API call |
| `check_availability` | `salon_id`, `date`, `time`, `service_name` | `available: bool`, `next_slots[]` | CRM API call |
| `create_booking` | `salon_id`, `customer_name`, `phone`, `service`, `date`, `time` | `booking_id`, `confirmation_code`, `deposit_amount` | CRM API call |
| `capture_contact` | `name`, `handle`, `phone`, `email` | `contact_id` | PostgreSQL write |
| `escalate_to_human` | `reason` | `escalation_id` | Triggers handoff flow |

#### 2.3 `app/agent/prompts.py` — System Prompt

The base prompt is a template. Salon-specific data is injected at runtime from `salon_config`:

```
You are a friendly and professional customer support agent for {salon_name},
a hair braiding salon based in the US.

CRITICAL RULES:
1. NEVER quote a price from memory or assumption. ALWAYS call get_service_price.
   If the tool returns null, immediately call escalate_to_human — do not guess.
2. To complete a booking you MUST collect: customer name, preferred service,
   date, time, and phone number or email.
3. If the customer asks to speak to the owner, manager, or a person →
   call escalate_to_human immediately.
4. If the customer is upset or complaining → call escalate_to_human immediately.
5. Keep replies short and conversational — this is chat, not email.
6. After a booking is confirmed, send one message with all details:
   service, date, time, location, and deposit information.

SALON INFORMATION:
- Name: {salon_name}
- Address: {salon_address}
- Hours: {salon_hours}
- Deposit policy: {deposit_policy}
- Cancellation policy: {cancellation_policy}
```

#### 2.4 `app/agent/nodes.py` — Node Implementations

**`check_session`**
```
Purpose: Load sender's session from Redis, determine if agent should proceed
Input:   sender_id
Output:  human_handling flag, existing conversation_id, salon_id
Logic:   If human_handling = True → return END (agent does nothing)
```

**`load_salon_config`**
```
Purpose: Load salon configuration for this conversation
Input:   page_id
Process:
  1. Check Redis: "salon:{page_id}" (TTL: 1 hour)
  2. Cache miss → query PostgreSQL salon_config table
  3. Store result in Redis
Output:  salon_config dict injected into AgentState
```

**`load_history`**
```
Purpose: Load prior conversation messages for context
Input:   conversation_id
Process:
  1. Check Redis: "history:{conversation_id}" (TTL: 2 hours)
  2. Cache miss → query PostgreSQL messages table (last 20 messages)
  3. Store in Redis
Output:  messages list appended to AgentState
```

**`run_agent`**
```
Purpose: Call GPT-4o with current messages and tools, get response or tool call
Input:   messages, salon_config (injected into system prompt), tools list
Output:  AI message — either a text reply or one/more tool_calls
Note:    This node loops back on itself via execute_tools until a final reply is ready
```

**`execute_tools`**
```
Purpose: Execute each tool call the agent requested
Input:   tool_calls list from run_agent
Process:
  For each tool_call:
    Switch on tool name:
      get_service_price  → await crm_client.get_service_price(...)
      check_availability → await crm_client.check_availability(...)
      create_booking     → await crm_client.create_booking(...)
      capture_contact    → await db.contacts.upsert(...)
      escalate_to_human  → trigger handoff flow
  Collect all tool_outputs
Output:  tool_outputs appended to messages → return to run_agent
```

**`send_reply`**
```
Purpose: Deliver the final reply to the customer
Input:   final_text, sender_id, channel, pilot_mode
Logic:
  pilot_mode = True  → Save as draft in PostgreSQL
                        Send Slack notification with [APPROVE] / [EDIT] / [DISCARD]
                        Do NOT send to customer yet
  pilot_mode = False → POST to Meta Graph API → message delivered to customer
```

**`write_to_crm`**
```
Purpose: Log all conversation data to CRM (runs after every reply)
Input:   full AgentState
Actions:
  1. Upsert contact (name, handle, phone, email)
  2. Create/update conversation record
  3. Save full message transcript
  4. Update lead status (new → interested → qualified → booked / escalated)
  5. Save booking details if booking was created
```

#### 2.5 `app/agent/graph.py` — Graph Definition

```python
graph = StateGraph(AgentState)

# Register nodes
graph.add_node("check_session",       check_session)
graph.add_node("load_salon_config",   load_salon_config)
graph.add_node("load_history",        load_history)
graph.add_node("run_agent",           run_agent)
graph.add_node("execute_tools",       execute_tools)
graph.add_node("send_reply",          send_reply)
graph.add_node("write_to_crm",        write_to_crm)
graph.add_node("escalate",            escalate_to_human)

# Linear flow
graph.set_entry_point("check_session")
graph.add_edge("check_session",     "load_salon_config")
graph.add_edge("load_salon_config", "load_history")
graph.add_edge("load_history",      "run_agent")

# Conditional: did the agent return tool calls or a final reply?
graph.add_conditional_edges("run_agent", route_after_agent, {
    "tools":    "execute_tools",
    "reply":    "send_reply",
    "escalate": "escalate",
})

# Tool results loop back to agent for next reasoning step
graph.add_edge("execute_tools", "run_agent")

# Final steps
graph.add_edge("send_reply",  "write_to_crm")
graph.add_edge("write_to_crm", END)
graph.add_edge("escalate",     END)
```

### Day 3 Tasks

#### 2.6 Multi-Turn Conversation Testing

```
Test sequence:
Turn 1: "What services do you offer?"
Turn 2: "How much is the second one?"    ← agent must use context from Turn 1
Turn 3: "Book me for Saturday"
Turn 4: "10am works"
Turn 5: "My name is Sarah, 555-0192"
Expected: create_booking called → confirmation message sent
```

#### Phase 2 Deliverables

- [ ] LangGraph graph compiles and runs without errors
- [ ] Single-turn: question → CRM price fetch → correct reply
- [ ] Multi-turn: agent retains context across multiple messages
- [ ] `get_service_price` tool makes real CRM API call
- [ ] `check_availability` tool working
- [ ] `create_booking` tool creates booking in CRM
- [ ] `escalate_to_human` tool triggers correctly
- [ ] Full booking conversation works end-to-end
- [ ] Agent escalates (does not guess) when CRM returns null price

---

## 7. Phase 3 — CRM Integration & Booking APIs (Day 4)

### Goal

Build a robust async CRM client, complete the booking flow, and handle all CRM error cases gracefully.

### Key Concept: Async CRM Client

> The CRM client (`app/crm/client.py`) is a dedicated class that handles all communication with the CRM REST API.
> No other part of the application makes direct HTTP calls to the CRM — all CRM interaction goes through this client.
> This means if the CRM's URL, auth method, or endpoints change, only `client.py` needs updating.
>
> `httpx` is used instead of the `requests` library because FastAPI is async. A synchronous HTTP call would block the entire event loop and prevent other requests from being served concurrently.

### Tasks

#### 3.1 `app/crm/client.py` — Async CRM Client Interface

```python
class CRMClient:

    async def get_service_price(
        salon_id: str, service_name: str
    ) -> PriceResponse | None:
        """
        Fetch service price from CRM.
        Returns None if service not found (404) — agent will escalate.
        Raises CRMUnavailableError on 5xx or timeout — agent will escalate.
        """

    async def check_availability(
        salon_id: str, date: str, time: str, service_name: str
    ) -> AvailabilityResponse:
        """
        Returns available time slots for the given date and service.
        """

    async def create_booking(
        booking_data: BookingRequest
    ) -> BookingResponse:
        """
        Creates a booking in the CRM.
        Returns booking_id and deposit details on success.
        """

    async def upsert_contact(
        contact_data: ContactRequest
    ) -> str:
        """
        Creates a new contact or updates an existing one.
        Returns crm_contact_id.
        """

    async def log_conversation(
        conversation_data: ConversationLog
    ) -> None:
        """
        Saves full conversation transcript and metadata to CRM.
        """

    async def update_lead_status(
        lead_id: str, status: str
    ) -> None:
        """
        Updates lead stage: new → interested → qualified → booked / escalated
        """
```

#### 3.2 CRM Error Handling Contract

Every CRM call must follow this contract — the agent is never given ambiguous or partial data:

| CRM Response | Client Behavior | Agent Behavior |
|---|---|---|
| `200 OK` with data | Return typed response object | Use data normally |
| `404 Not Found` | Return `None` | Call `escalate_to_human` |
| `500 Server Error` | Raise `CRMServerError`, log to Sentry | Call `escalate_to_human` |
| Timeout (> 10s) | Raise `CRMTimeoutError`, log to Sentry | Call `escalate_to_human` |
| Auth error `401/403` | Raise `CRMAuthError`, alert team | Call `escalate_to_human` |

**Rule:** The agent either receives correct data or a clear error. It never receives partial or guessed data.

#### 3.3 Complete Booking Conversation Flow

```
Customer: "I want to get box braids"
Agent:    [calls get_service_price("box_braids", salon_id)]
          "Box braids are $180 and take about 4 hours. Hair is included.
           When would you like to come in?"

Customer: "Saturday the 19th"
Agent:    [calls check_availability(salon_id, "2026-07-19", service="box_braids")]
          "We have 10:00 AM and 2:00 PM available on Saturday. Which works for you?"

Customer: "10am"
Agent:    "Perfect! May I have your name and a phone number to complete the booking?"

Customer: "Sarah, 555-0192"
Agent:    [calls create_booking({ service: "box_braids", date: "2026-07-19",
                                   time: "10:00", name: "Sarah", phone: "555-0192" })]
          "You're all set, Sarah! Here's your confirmation:
           ✓ Service: Box Braids
           ✓ Date: Saturday, July 19
           ✓ Time: 10:00 AM
           ✓ Location: [salon address]
           ✓ Deposit: $30 — pay here: [link]
           See you then!"
```

#### Phase 3 Deliverables

- [ ] CRM client handles all endpoint interactions
- [ ] Price fetch returns exact CRM price
- [ ] Price 404 returns `None` without crashing
- [ ] Availability check returns correct slots
- [ ] Booking creates entry in CRM and returns `booking_id`
- [ ] Booking confirmation message sent in same DM thread immediately after creation
- [ ] All CRM errors caught, logged to Sentry, and trigger escalation
- [ ] CRM timeout triggers escalation

---

## 8. Phase 4 — PostgreSQL Schema, Redis & Error Handling (Day 5)

### Goal

Run database migrations, implement Redis session and history caching, add rate limiting, and establish application-wide error handling.

### Key Concept: PostgreSQL vs Redis

| | PostgreSQL | Redis |
|---|---|---|
| **Type** | Persistent relational database | In-memory cache |
| **Speed** | Milliseconds to seconds | Sub-millisecond |
| **Durability** | Data survives restarts | Data can expire (TTL) |
| **Use for** | Conversations, bookings, contacts, audit trail | Session state, conversation history cache, rate limits |
| **When to query** | For permanent reads/writes | For fast repeated reads |

**Pattern:** Check Redis first → on miss, query PostgreSQL → store result in Redis with TTL.

### Tasks

#### 4.1 Database Migrations

```bash
alembic revision --autogenerate -m "initial_schema"
alembic upgrade head
```

Tables created: `salon_config`, `contacts`, `conversations`, `messages`, `bookings`, `drafts`, `escalations`
(Full schema in Section 11)

#### 4.2 `app/cache/session.py` — Session Store

```
On every incoming message:
  1. Check Redis: "session:{sender_id}"
  2. Found → extract salon_id, conversation_id, human_handling, pilot_mode
  3. Not found → query PostgreSQL → store in Redis (TTL: 24 hours)

Session structure:
{
  "salon_id": "salon_abc",
  "conversation_id": "uuid-xxx",
  "human_handling": false,
  "pilot_mode": true,
  "last_active": "2026-07-14T14:30:00Z"
}

Session update triggers:
  - New conversation created
  - human_handling flag changes
  - pilot_mode changes
  - Booking completed
```

#### 4.3 `app/cache/rate_limit.py` — Rate Limiting

```
Purpose: Prevent a single sender from flooding the system

Implementation:
  key:       "rate:{sender_id}"
  operation: INCR (atomic) + EXPIRE 60 on first call
  threshold: > 10 messages per 60 seconds

If threshold exceeded:
  → Return: "You're sending messages too quickly. Please wait a moment."
  → Skip agent invocation entirely (saves OpenAI API cost)
```

#### 4.4 Application-Wide Error Handling

Three levels of error handling:

**Level 1 — Tool Level (CRM errors)**
```python
try:
    price = await crm_client.get_service_price(salon_id, service_name)
except CRMTimeoutError:
    return ToolResult(error="service_unavailable")
except CRMNotFoundError:
    return ToolResult(price=None, error="not_found")
# Agent receives structured error → decides to escalate
```

**Level 2 — Agent Level (LangGraph node failures)**
```python
# If any node raises an unhandled exception:
# → Log full context to Sentry (sender_id, salon_id, conversation_id, error)
# → Trigger escalation: agent cannot continue safely
# → Notify customer: "We're having a technical issue. Our team will follow up shortly."
```

**Level 3 — API Level (FastAPI global handler)**
```python
@app.exception_handler(Exception)
async def global_error_handler(request, exc):
    # Log to Sentry
    # Return 200 (not 5xx) — Meta will retry on 5xx which causes duplicate messages
    return JSONResponse(status_code=200, content={"status": "error_handled"})
```

#### Phase 4 Deliverables

- [ ] Alembic migrations run cleanly, all tables created
- [ ] Redis session store: save and retrieve session across requests
- [ ] Conversation history cache: Redis hit on repeat, PostgreSQL on miss
- [ ] Salon config cache: served from Redis within 1-hour TTL
- [ ] Rate limiting: 11th message within 60s returns rate limit response
- [ ] CRM errors caught at tool level and structured error returned to agent
- [ ] Unhandled exceptions logged to Sentry with full context
- [ ] Global FastAPI handler returns 200 on unexpected errors

---

## 9. Phase 5 — Human Handoff & Logging (Day 6)

### Goal

Implement all escalation paths, build draft approval mode for the pilot phase, and add structured logging throughout the application.

### Key Concept: Human Handoff Flow

```
1. Agent calls escalate_to_human(reason="price_not_found")
2. app/handoff/escalation.py:
   a. PostgreSQL: UPDATE conversations SET human_handling = true
   b. Redis:      UPDATE session human_handling = true
   c. Meta API:   Send message to customer:
                  "Connecting you with our team. Someone will be with you shortly!"
   d. Slack:      Send alert to team with full context
3. Next message from same customer:
   → check_session reads human_handling = true from Redis
   → Agent node returns END immediately — message stays in inbox
4. Human team member resolves the conversation
5. Team calls POST /internal/resume-conversation/{id}
   → human_handling = false in PostgreSQL and Redis
   → Agent handles next message normally
```

### Key Concept: Draft Approval (Pilot Mode)

```
When pilot_mode = true on a salon:

  Agent generates reply → send_reply node runs → pilot_mode check:

  pilot_mode = true:
    → Save draft to PostgreSQL drafts table
    → Slack notification to team:
        "Draft ready for [Customer] on [Salon]"
        Reply: "[draft text]"
        Buttons: [APPROVE] [EDIT & SEND] [DISCARD]
    → Message NOT sent to customer yet
    → Wait for team action via webhook

  Team clicks [APPROVE]:
    → POST /internal/approve-draft/{id}
    → Original draft sent to customer via Meta API
    → Draft marked approved in PostgreSQL
    → CRM write-back triggered

  Team clicks [EDIT & SEND]:
    → POST /internal/edit-draft/{id} with edited_text
    → Edited text sent to customer
    → Draft updated with sent_text in PostgreSQL

  Team clicks [DISCARD]:
    → POST /internal/discard-draft/{id}
    → Draft discarded
    → Escalation triggered (human takes over)

To graduate from pilot to full-auto:
  UPDATE salon_config SET pilot_mode = false WHERE salon_id = 'xxx'
  → No code change required. Agent starts sending directly.
```

### Tasks

#### 5.1 `app/handoff/escalation.py`

```python
async def trigger_escalation(
    conversation_id: str,
    sender_id: str,
    channel: str,
    reason: str,
    last_message: str,
    salon_config: dict
) -> None:
    # 1. Update PostgreSQL conversations table
    # 2. Update Redis session cache
    # 3. Send customer notification via Meta API
    # 4. Call notifier.send_alert()
    # 5. Log escalation event to escalations table

async def resume_conversation(conversation_id: str) -> None:
    # 1. UPDATE conversations SET human_handling = false
    # 2. Update Redis session cache
    # Agent will handle the customer's next message normally
```

#### 5.2 Escalation Triggers

| Trigger | Source |
|---|---|
| Customer requests owner / person / manager | GPT-4o intent → `escalate_to_human` tool |
| Customer is upset or complaining | GPT-4o intent → `escalate_to_human` tool |
| Price not found in CRM | Tool returns `null` → GPT-4o calls `escalate_to_human` |
| CRM unavailable (timeout / 5xx) | CRMError → tool returns error → GPT-4o escalates |
| Agent run fails or exceeds polling limit | LangGraph error handler |
| Low-confidence answer | GPT-4o decides to escalate proactively |

#### 5.3 `app/handoff/notifier.py` — Slack Alert Format

```
Human Needed — Salon: {salon_name}
Customer:      {sender_id} on {channel}
Reason:        {reason}
Last message:  "{last_message}"
Time:          {timestamp}
CRM:           {crm_conversation_link}

Actions:
  [Resume Agent] → POST /internal/resume-conversation/{conversation_id}
```

#### 5.4 `app/api/internal.py` — Internal Action Endpoints

| Method | Path | Action |
|---|---|---|
| POST | `/internal/resume-conversation/{id}` | Set `human_handling = false`, agent resumes |
| POST | `/internal/approve-draft/{id}` | Send original draft via Meta API |
| POST | `/internal/edit-draft/{id}` | Send edited text, body: `{ "text": "..." }` |
| POST | `/internal/discard-draft/{id}` | Discard draft, trigger escalation |

#### 5.5 `app/monitoring/logger.py` — Structured JSON Logging

Every significant event is logged as a structured JSON object:

```json
{ "timestamp": "2026-07-14T14:30:00Z", "level": "INFO",
  "event": "message_received", "sender_id": "123",
  "channel": "instagram_dm", "salon_id": "salon_abc" }

{ "timestamp": "2026-07-14T14:30:01Z", "level": "INFO",
  "event": "tool_called", "tool": "get_service_price",
  "service": "box_braids", "result": "found", "price": 180 }

{ "timestamp": "2026-07-14T14:30:02Z", "level": "INFO",
  "event": "reply_sent", "channel": "instagram_dm",
  "pilot_mode": false, "draft_id": null }

{ "timestamp": "2026-07-14T14:30:03Z", "level": "WARNING",
  "event": "escalation_triggered", "reason": "price_not_found",
  "conversation_id": "uuid-xxx" }

{ "timestamp": "2026-07-14T14:30:04Z", "level": "ERROR",
  "event": "crm_timeout", "endpoint": "get_service_price",
  "salon_id": "salon_abc", "elapsed_ms": 10500 }
```

#### Phase 5 Deliverables

- [ ] Human handoff triggers on all 6 defined conditions
- [ ] Team receives Slack alert with full conversation context
- [ ] Agent stops responding immediately when `human_handling = true`
- [ ] `/internal/resume-conversation` restores agent to active
- [ ] Draft saved to PostgreSQL when `pilot_mode = true`
- [ ] Team receives Slack draft notification with action buttons
- [ ] `[APPROVE]` → message sent to customer
- [ ] `[EDIT & SEND]` → edited message sent to customer
- [ ] `[DISCARD]` → draft removed, escalation triggered
- [ ] `pilot_mode = false` database toggle enables direct-send mode
- [ ] Structured JSON logs emitted for all key events

---

## 10. Phase 6 — Docker Deployment, Monitoring & QA (Day 7)

### Goal

Finalize the Docker production setup, configure Sentry error tracking, run the complete QA test suite, and perform the pilot salon launch checklist.

### Key Concept: Docker Compose in Production

```
docker-compose up -d launches:
  ┌─────────────────────────────────────────────┐
  │  app (FastAPI)   ←──── PORT 8000            │
  │  postgres        ←──── PORT 5432 (internal) │
  │  redis           ←──── PORT 6379 (internal) │
  └─────────────────────────────────────────────┘
  All services share one internal Docker network.
  Only the app port is exposed to the outside world.
  A single .env file configures everything.
  `docker-compose down` stops everything cleanly.
  Volumes persist PostgreSQL and Redis data across restarts.
```

### Tasks

#### 10.1 `Dockerfile`

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
```

#### 10.2 `docker-compose.yml` — Production Configuration

```yaml
version: "3.9"

services:
  app:
    build: .
    ports:
      - "8000:8000"
    env_file: .env
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    restart: unless-stopped

  postgres:
    image: postgres:15-alpine
    environment:
      POSTGRES_DB: salon_agent
      POSTGRES_USER: ${DB_USER}
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${DB_USER}"]
      interval: 10s
      retries: 5
    restart: unless-stopped

  redis:
    image: redis:7-alpine
    volumes:
      - redis_data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      retries: 5
    restart: unless-stopped

volumes:
  postgres_data:
  redis_data:
```

#### 10.3 `app/monitoring/sentry.py` — Error Tracking

```python
import sentry_sdk

sentry_sdk.init(
    dsn=config.SENTRY_DSN,
    environment=config.APP_ENV,          # "development" or "production"
    traces_sample_rate=0.1,              # Trace 10% of requests for performance
    profiles_sample_rate=0.1,
)
```

Sentry captures:
- All unhandled exceptions with full stack trace
- Context: sender_id, salon_id, conversation_id, channel
- CRM timeout and error events
- Agent failures

#### 10.4 `GET /health` — Health Endpoint

```json
{
  "status": "ok",
  "services": {
    "postgres": "connected",
    "redis": "connected",
    "openai": "reachable"
  },
  "version": "1.0.0",
  "environment": "production"
}
```

#### 10.5 Full QA Test Suite

| # | Test | Input | Expected | Fail Condition |
|---|---|---|---|---|
| 1 | Price query | "How much is box braids?" | `get_service_price` called → exact CRM price quoted | Any number quoted without tool call |
| 2 | Price not in CRM | "How much for [unknown service]?" | Tool returns null → `escalate_to_human` → Slack alert | Agent guesses a price |
| 3 | Full booking flow | Complete booking conversation | Booking in CRM → confirmation message sent → transcript logged | Any step missing |
| 4 | Explicit escalation | "Can I speak to the owner?" | Handoff triggered → Slack alert → agent stops → customer notified | Agent continues responding |
| 5 | Complaint escalation | "This is ridiculous" | Escalation within 1 message | Agent attempts to resolve |
| 6 | Comment → DM flow | IG comment: "How much for box braids?" | Public reply → DM opened → agent continues in DM | No DM initiated |
| 7 | Multi-turn context | Turn 2 refers to Turn 1 content | Agent uses prior context correctly | Agent loses context |
| 8 | Draft approval | `pilot_mode = true` | Agent generates → Slack draft → APPROVE → sent | Message sent before approval |
| 9 | Rate limiting | 15 messages in 30 seconds | After 10th → rate limit response, no agent call | Agent called on every message |
| 10 | CRM timeout | CRM returns timeout | Escalation triggered, Sentry logged, customer notified | Agent crashes or guesses |
| 11 | Human handling block | `human_handling = true` | Agent does NOT respond | Agent responds to blocked sender |
| 12 | Redis session persistence | Message → restart app → next message | Context restored from PostgreSQL | History lost after restart |

#### 10.6 Pilot Launch Checklist

- [ ] All 12 QA tests passing
- [ ] Pilot salon Meta pages connected and verified
- [ ] `pilot_mode = true` set for pilot salon in `salon_config`
- [ ] Team has received and tested the Slack draft approval workflow
- [ ] Team understands how to resume a conversation after human handoff
- [ ] Sentry dashboard accessible and receiving test events
- [ ] `/health` endpoint returns all green
- [ ] Docker containers stable after 1-hour uptime test
- [ ] Rollback procedure documented and tested:
  - Step 1: Remove Meta webhook subscription → all messages go directly to inbox
  - Step 2: Fix issue in code
  - Step 3: Redeploy and re-register webhook

#### Phase Progression Gates

| Gate | Requirement | Approver |
|---|---|---|
| Pilot Phase 1 → Phase 2 (full auto) | 95%+ price accuracy, zero hallucinated prices across 50 conversations | Client + Atrium |
| Phase 2 → Phase 3 (comments enabled) | Full auto DMs stable for 1 week, under 2 escalation errors per day | Client |
| Phase 3 → Phase 4 (all salons) | Comment replies tested, zero public-facing errors on pilot salon | Client |

---

## 11. PostgreSQL Data Model

```sql
-- Salon configuration (one row per salon client)
CREATE TABLE salon_config (
  id                  UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
  salon_id            VARCHAR(100) UNIQUE NOT NULL,
  salon_name          VARCHAR(255) NOT NULL,
  fb_page_id          VARCHAR(100),
  ig_page_id          VARCHAR(100),
  page_access_token   TEXT,
  crm_base_url        TEXT NOT NULL,
  crm_api_key         TEXT NOT NULL,
  salon_address       TEXT,
  salon_hours         JSONB,              -- { "mon": "9am-6pm", "sat": "10am-4pm" }
  deposit_policy      TEXT,
  cancellation_policy TEXT,
  pilot_mode          BOOLEAN     DEFAULT TRUE,
  active              BOOLEAN     DEFAULT TRUE,
  created_at          TIMESTAMP   DEFAULT NOW(),
  updated_at          TIMESTAMP   DEFAULT NOW()
);

-- Customer contacts
CREATE TABLE contacts (
  id              UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
  salon_id        VARCHAR(100) NOT NULL REFERENCES salon_config(salon_id),
  ig_sender_id    VARCHAR(255),
  fb_sender_id    VARCHAR(255),
  name            VARCHAR(255),
  phone           VARCHAR(50),
  email           VARCHAR(255),
  crm_contact_id  VARCHAR(255),
  created_at      TIMESTAMP   DEFAULT NOW(),
  updated_at      TIMESTAMP   DEFAULT NOW()
);

-- Conversations (one per customer-channel session)
CREATE TABLE conversations (
  id              UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
  contact_id      UUID        REFERENCES contacts(id),
  salon_id        VARCHAR(100) NOT NULL REFERENCES salon_config(salon_id),
  channel         VARCHAR(50) NOT NULL,      -- instagram_dm / facebook_messenger
  human_handling  BOOLEAN     DEFAULT FALSE,
  pilot_mode      BOOLEAN     DEFAULT TRUE,
  lead_status     VARCHAR(50) DEFAULT 'new', -- new / interested / qualified / booked / escalated
  service_interest VARCHAR(255),
  crm_lead_id     VARCHAR(255),
  booking_id      VARCHAR(255),
  created_at      TIMESTAMP   DEFAULT NOW(),
  last_message_at TIMESTAMP   DEFAULT NOW()
);

-- Individual messages (complete transcript)
CREATE TABLE messages (
  id              UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
  conversation_id UUID        NOT NULL REFERENCES conversations(id),
  role            VARCHAR(20) NOT NULL,   -- user / assistant / tool
  content         TEXT        NOT NULL,
  tool_name       VARCHAR(100),           -- populated if role = tool
  tool_result     JSONB,                  -- tool output payload
  created_at      TIMESTAMP   DEFAULT NOW()
);

-- Bookings
CREATE TABLE bookings (
  id                UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
  conversation_id   UUID        NOT NULL REFERENCES conversations(id),
  salon_id          VARCHAR(100) NOT NULL,
  crm_booking_id    VARCHAR(255),
  service_name      VARCHAR(255),
  booking_date      DATE,
  booking_time      TIME,
  customer_name     VARCHAR(255),
  customer_phone    VARCHAR(50),
  deposit_status    VARCHAR(50) DEFAULT 'pending',
  confirmation_sent BOOLEAN     DEFAULT FALSE,
  created_at        TIMESTAMP   DEFAULT NOW()
);

-- Draft messages (pilot mode — pending human approval)
CREATE TABLE drafts (
  id              UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
  conversation_id UUID        NOT NULL REFERENCES conversations(id),
  draft_text      TEXT        NOT NULL,
  sent_text       TEXT,
  status          VARCHAR(20) DEFAULT 'pending', -- pending / approved / edited / discarded
  approved_by     VARCHAR(255),
  approved_at     TIMESTAMP,
  created_at      TIMESTAMP   DEFAULT NOW()
);

-- Escalation audit log
CREATE TABLE escalations (
  id              UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
  conversation_id UUID        NOT NULL REFERENCES conversations(id),
  reason          TEXT        NOT NULL,
  triggered_by    VARCHAR(100),           -- tool_name / timeout / intent / error
  resolved        BOOLEAN     DEFAULT FALSE,
  resolved_by     VARCHAR(255),
  resolved_at     TIMESTAMP,
  created_at      TIMESTAMP   DEFAULT NOW()
);
```

---

## 12. Redis — What Gets Stored

| Key Pattern | Value | TTL | Used When |
|---|---|---|---|
| `session:{sender_id}` | JSON: `{ salon_id, conversation_id, human_handling, pilot_mode, last_active }` | 24 hours | Every incoming message — fast session lookup |
| `history:{conversation_id}` | JSON array: last 20 messages `[{ role, content, timestamp }]` | 2 hours | Feed conversation history to agent without DB query |
| `salon:{page_id}` | JSON: full `salon_config` object | 1 hour | Resolve salon from page_id on every event |
| `rate:{sender_id}` | Integer: message count (atomic INCR) | 60 seconds | Rate limiting — max 10 messages per minute |
| `draft:{draft_id}` | JSON: `{ draft_text, status, conversation_id }` | 24 hours | Quick lookup during draft approval flow |

**Cache Invalidation Rules:**
- `session:{sender_id}` — invalidated when `human_handling` or `pilot_mode` changes
- `salon:{page_id}` — invalidated when `salon_config` is updated
- `history:{conversation_id}` — appended after every message, rebuilt from DB after TTL expiry

---

## 13. API Endpoints Reference

### Public Endpoints (Called by Meta)

| Method | Path | Purpose |
|---|---|---|
| `GET` | `/webhook/meta` | Meta webhook verification — returns `hub.challenge` |
| `POST` | `/webhook/meta` | Receives all Meta events: DMs, Messenger messages, comments |
| `GET` | `/health` | Health check for load balancers and uptime monitors |

### Internal Endpoints (Called by Team via Slack or Dashboard)

| Method | Path | Purpose |
|---|---|---|
| `POST` | `/internal/resume-conversation/{id}` | Human resolved — set `human_handling = false`, agent resumes |
| `POST` | `/internal/approve-draft/{id}` | Send original agent draft to customer |
| `POST` | `/internal/edit-draft/{id}` | Body: `{ "text": "..." }` — send edited version |
| `POST` | `/internal/discard-draft/{id}` | Remove draft, trigger escalation |

### Meta Graph API (Called by Application)

| Method | URL | Purpose |
|---|---|---|
| `POST` | `https://graph.facebook.com/v19.0/me/messages` | Send DM (works for both Instagram and Facebook) |
| `POST` | `https://graph.facebook.com/v19.0/{comment_id}/replies` | Reply to public comment |
| `GET` | `https://graph.facebook.com/v19.0/{user_id}?fields=name` | Fetch customer profile |

### OpenAI Assistants API (Reference — used by LangGraph nodes)

| Method | URL | Purpose |
|---|---|---|
| `POST` | `/v1/chat/completions` | Main LLM call with tools (GPT-4o) |

---

## 14. Environment Variables

```bash
# .env.example — commit this file (no actual values)
# Copy to .env and fill in real values before running

# ── OpenAI ──────────────────────────────────────
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4o

# ── Meta ────────────────────────────────────────
META_APP_ID=...
META_APP_SECRET=...               # Used for HMAC webhook signature verification
META_VERIFY_TOKEN=...             # Set this during webhook registration in Meta dashboard

# ── Database ────────────────────────────────────
DB_USER=salon_user
DB_PASSWORD=...
DB_HOST=postgres                  # Docker service name
DB_PORT=5432
DB_NAME=salon_agent
DATABASE_URL=postgresql+asyncpg://${DB_USER}:${DB_PASSWORD}@${DB_HOST}:${DB_PORT}/${DB_NAME}

# ── Redis ────────────────────────────────────────
REDIS_URL=redis://redis:6379/0

# ── CRM ─────────────────────────────────────────
# Per-salon CRM credentials are stored in the salon_config table.
# These defaults are used as fallback if not overridden per salon.
DEFAULT_CRM_BASE_URL=https://your-crm.com/api/v1
DEFAULT_CRM_API_KEY=...

# ── Human Handoff Alerts ─────────────────────────
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/...
ALERT_EMAIL=team@atrium.com       # Fallback if Slack not configured

# ── Error Tracking ───────────────────────────────
SENTRY_DSN=https://...@sentry.io/...

# ── Application ──────────────────────────────────
APP_ENV=production                # development / production
LOG_LEVEL=INFO
```

---

## 15. What We Need From Client

### Meta Access — Required Before Day 1

| Item | Details | Why |
|---|---|---|
| Facebook Page Admin Access | For each salon's Facebook Page | Connect webhook, send messages |
| Instagram Professional Account | Must be linked to the Facebook Page | Instagram DM access via Graph API |
| Meta Business Verification | Business verified on Meta Business Manager | Required for messaging permissions — allow 3–5 business days |
| Long-Lived Page Access Tokens | Per salon, 60-day validity | API authentication for sending messages |
| App Review Scopes | `pages_messaging`, `instagram_manage_messages`, `pages_read_engagement`, `instagram_manage_comments` | All messaging and comment features |

### CRM Access — Required Before Day 4

| Item | Details | Why |
|---|---|---|
| CRM API Base URL | Root URL for all API calls | Configure `CRM_BASE_URL` per salon |
| Authentication Method | Bearer token / API key / OAuth 2.0 | Authenticate all CRM requests |
| `GET` Service Price Endpoint | Takes service name + salon ID, returns price | `get_service_price` tool |
| `GET` Availability Endpoint | Takes date, time, service → returns slots | `check_availability` tool |
| `POST` Booking Endpoint | Creates booking, returns `booking_id` | `create_booking` tool |
| `POST/PUT` Contact Endpoint | Create or update a contact record | CRM write-back |
| `POST` Conversation Log Endpoint | Accepts full transcript JSON | CRM write-back |
| `PUT` Lead Status Endpoint | Updates lead stage field | CRM write-back |
| Salon IDs | Unique identifier per salon in CRM | Route each conversation to correct salon |

### Content — Required Before Day 2

| Item | Details |
|---|---|
| Full service list (all salons) | Service names exactly as they appear in the CRM |
| Salon addresses | One per salon |
| Operating hours | Per salon, including any holiday exceptions |
| Deposit policy | Fixed amount or percentage, when it is charged |
| Cancellation policy | Required notice period, refund rules |
| Slack workspace invite | For human handoff and draft approval notifications |

### Training Data — Required Before Day 6

| Item | Format | Why |
|---|---|---|
| Real chat transcripts | JSON or CSV: `timestamp`, `sender_type` (customer/agent), `message_text` | Used as few-shot examples in system prompt |
| Volume | Minimum 50 conversations; 200+ preferred | Covers edge cases, objections, booking flows |
| Intent labels (if available) | Label per customer message | Improves prompt engineering quality |

---

*Document Version: 2.0 | Stack: FastAPI + LangGraph + OpenAI SDK + PostgreSQL + Redis + Docker*
*Last Updated: July 14, 2026 | Prepared by: Atrium Solution*
