# Build Progress

## Step 1 — Core Agent (Only OpenAI API Needed)
- [x] Virtual environment setup
- [x] pip install -r requirements.txt
- [x] .env file created with OPENAI_API_KEY
- [x] app/config.py — Settings class with openai_api_key
- [ ] app/agent/state.py — AgentState TypedDict
- [ ] app/agent/prompts.py — System prompt template
- [ ] app/agent/tools.py — Tool schemas + mock functions
- [ ] app/agent/nodes.py — run_agent, execute_tools, send_reply, escalate
- [ ] app/agent/graph.py — LangGraph graph compiled
- [ ] scripts/test_agent.py — CLI test passing

## Step 2 — PostgreSQL
- [ ] docker-compose up postgres
- [ ] app/db/connection.py
- [ ] app/db/repositories/conversation.py
- [ ] app/db/repositories/salon.py
- [ ] alembic upgrade head (migrations)

## Step 3 — Redis
- [ ] docker-compose up redis
- [ ] app/cache/connection.py
- [ ] app/cache/session.py
- [ ] app/cache/history.py
- [ ] app/cache/rate_limit.py

## Step 4 — FastAPI + Meta Webhook
- [ ] app/channels/signature.py
- [ ] app/channels/webhook_parser.py
- [ ] app/channels/meta_client.py
- [ ] app/api/webhook.py
- [ ] Meta app setup + page access token

## Step 5 — Real CRM Integration
- [ ] app/crm/client.py
- [ ] app/crm/models.py
- [ ] Replace mock tools with real CRM calls

## Step 6 — Human Handoff + Deploy
- [ ] app/handoff/escalation.py
- [ ] app/handoff/notifier.py
- [ ] app/api/internal.py
- [ ] docker-compose up --build (full deploy)
- [ ] Sentry + structured logging