# AI Chat Support Agent — MVP 1 Project Plan
**Client:** The Fine Dudes | **Prepared by:** Atrium Solution | **Date:** July 14, 2026

---

## Table of Contents
1. [Project Overview](#1-project-overview)
2. [Architecture Decision](#2-architecture-decision)
3. [Architecture Pros & Cons](#3-architecture-pros--cons)
4. [System Components](#4-system-components)
5. [Phase 1 — Foundation & Channel Integration (Day 1–2)](#5-phase-1--foundation--channel-integration-day-12)
6. [Phase 2 — AI Brain & CRM Integration (Day 3–4)](#6-phase-2--ai-brain--crm-integration-day-34)
7. [Phase 3 — Booking, Handoff & Write-Back (Day 5–6)](#7-phase-3--booking-handoff--write-back-day-56)
8. [Phase 4 — Human-in-Loop, Testing & Pilot Launch (Day 7–8)](#8-phase-4--human-in-loop-testing--pilot-launch-day-78)
9. [What We Need From Client](#9-what-we-need-from-client)
10. [Database Schema](#10-database-schema)
11. [API Reference Map](#11-api-reference-map)
12. [Rollout Sequence](#12-rollout-sequence)
13. [Cost Estimate](#13-cost-estimate)

---

## 1. Project Overview

An AI-powered customer support agent for US-based hair braiding salon clients. The agent operates across Meta platforms (Instagram DM, Facebook Messenger, and public comments), handles inbound customer conversations end-to-end, fetches prices from the CRM, drives bookings, and writes everything back into the CRM.

### Core Capabilities Required
| # | Capability | Priority |
|---|---|---|
| 1 | Answer standard salon FAQs | Must Have |
| 2 | Fetch real-time prices from CRM (no hallucination) | Critical |
| 3 | Create confirmed bookings | Must Have |
| 4 | Write all data back to CRM | Must Have |
| 5 | Escalate to human when needed | Must Have |
| 6 | Handle Instagram DM | Must Have |
| 7 | Handle Facebook Messenger | Must Have |
| 8 | Handle public comments → move to DM | Must Have |
| 9 | Human-in-Loop draft/approval mode (Phase 1 pilot) | Must Have |
| 10 | Send booking confirmation message | Must Have |

---

## 2. Architecture Decision

**Selected Stack: n8n + OpenAI Assistants API**

```
Meta Platforms (IG/FB)
        │
        ▼
  n8n Workflows              ← Orchestration, Routing, CRM HTTP calls
        │
        ▼
OpenAI Assistants API        ← AI Brain, Conversation State, Tool Calling
        │
        ▼
  CRM REST API               ← Price Fetch, Booking Create, Data Write-Back
        │
        ▼
  Postgres / Supabase        ← Thread ID mapping, Conversation State, Drafts
```

### Why This Stack

- **n8n** handles all webhook events, routing, HTTP calls, and workflow orchestration visually — fast to build, easy to debug
- **OpenAI Assistants API** provides stateful conversation threads (no custom memory layer needed), structured tool calling, and reliable JSON responses
- **Postgres/Supabase** stores the mapping between Meta sender IDs and OpenAI Thread IDs, plus draft messages for human approval
- **Meta Graph API** used directly via HTTP Request nodes for sending replies

---

## 3. Architecture Pros & Cons

### Pros

| # | Pro | Detail |
|---|---|---|
| 1 | Fast to ship | Visual workflows mean less code — 8-day MVP is realistic |
| 2 | No-code friendly | Any team member can read and understand workflows |
| 3 | Conversation state built-in | OpenAI Threads automatically manage history — no extra infra |
| 4 | Reliable tool calling | OpenAI Assistant tools enforce structured CRM calls — no price hallucination |
| 5 | Self-hosted n8n | Client data stays on your server after Meta/OpenAI processing |
| 6 | Multi-salon scalable | Adding a new salon = new salon ID + CRM endpoint config only |
| 7 | Human-in-Loop native | n8n draft → approval → send pattern is straightforward to implement |
| 8 | Cost effective | n8n self-hosted is free; only pay OpenAI API usage |
| 9 | Built-in monitoring | n8n execution logs every step with full payload history |
| 10 | Retry logic available | n8n has built-in error handling and retry nodes |

### Cons

| # | Con | Impact | Mitigation |
|---|---|---|---|
| 1 | OpenAI vendor lock-in | Threads API is OpenAI-only; switching LLMs requires rework | Acceptable for MVP — revisit at scale |
| 2 | Polling latency | n8n polls for run completion → 2–5 sec response delay | Send "typing…" indicator to customer |
| 3 | Workflow sprawl at scale | Many workflows become hard to manage | Strict naming conventions + folder structure |
| 4 | Thread storage cost | OpenAI bills for thread storage on high volume | Schedule thread cleanup after 30 days |
| 5 | CRM failure handling | If CRM is down, agent must escalate gracefully | Add fallback → human handoff on CRM timeout |
| 6 | No fine-tuning pipeline here | Training data benefit = few-shot in prompt only | Fine-tuning is a separate Phase 5 scope |
| 7 | Comment→DM rate limits | Meta limits comment reply rates | Batch comment processing + delay nodes |
| 8 | Postgres dependency | Need managed DB for state | Supabase free tier covers MVP easily |

### When to Move Off This Stack

| Trigger | Next Step |
|---|---|
| 50+ active salons | Migrate orchestration to custom Python/Node backend |
| Need Claude/Gemini | Replace Assistants API with LangGraph + custom thread store |
| Fine-tuning required | Add separate MLOps pipeline |

---

## 4. System Components

### Component Map

```
┌─────────────────────────────────────────────────────────────┐
│                    META PLATFORMS                            │
│  Instagram DM │ Facebook Messenger │ IG/FB Comments         │
└──────────────────────┬──────────────────────────────────────┘
                       │ Webhooks
┌──────────────────────▼──────────────────────────────────────┐
│                    n8n LAYER                                 │
│                                                              │
│  WF-01: Webhook Receiver & Normalizer                        │
│  WF-02: Comment Handler (Comment → DM redirect)             │
│  WF-03: Message Router & Thread Manager                      │
│  WF-04: Tool Call Dispatcher (CRM calls)                     │
│  WF-05: Response Sender (Meta API reply)                     │
│  WF-06: CRM Write-Back                                       │
│  WF-07: Human Handoff                                        │
│  WF-08: Draft Approval (Phase 1 pilot)                       │
└──────────────────────┬──────────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────────┐
│              OPENAI ASSISTANTS API                           │
│                                                              │
│  Assistant: Salon Support Agent                              │
│  Tools: get_price │ check_availability │ create_booking      │
│          capture_contact │ escalate_to_human                 │
│  Threads: Per-customer conversation state                    │
└──────────────────────┬──────────────────────────────────────┘
                       │
        ┌──────────────┴──────────────┐
        │                             │
┌───────▼────────┐          ┌────────▼────────┐
│  CRM REST API  │          │  Postgres/      │
│                │          │  Supabase       │
│  /prices       │          │                 │
│  /availability │          │  conversations  │
│  /bookings     │          │  drafts         │
│  /contacts     │          │  salon_config   │
│  /logs         │          └─────────────────┘
└────────────────┘
```

### n8n Workflows List

| ID | Workflow Name | Trigger | Purpose |
|---|---|---|---|
| WF-01 | Webhook Receiver | Meta POST webhook | Receive and normalize all incoming messages |
| WF-02 | Comment Handler | WF-01 (comment type) | Reply to comment, open DM conversation |
| WF-03 | Thread Manager | WF-01 (DM type) | Manage OpenAI threads, run assistant |
| WF-04 | Tool Call Dispatcher | WF-03 (requires_action) | Execute CRM API calls for assistant tools |
| WF-05 | Response Sender | WF-03 (completed) | Send final reply via Meta API |
| WF-06 | CRM Write-Back | WF-05 (post-send) | Log all data to CRM |
| WF-07 | Human Handoff | escalate_to_human tool | Alert team, pause agent |
| WF-08 | Draft Approval | WF-03 (completed, pilot mode) | Save draft, wait for team approval |

### OpenAI Assistant Tools

| Tool Name | Input | Output | CRM Endpoint |
|---|---|---|---|
| `get_service_price` | `service_name`, `salon_id` | `price`, `currency`, `includes_hair` | `GET /salons/{id}/services/{name}/price` |
| `check_availability` | `salon_id`, `date`, `time`, `service_name` | `available: bool`, `next_slots[]` | `GET /salons/{id}/availability` |
| `create_booking` | `salon_id`, `customer_name`, `phone`, `service`, `date`, `time` | `booking_id`, `confirmation_code`, `deposit_amount` | `POST /bookings` |
| `capture_contact` | `name`, `handle`, `phone`, `email` | `contact_id` | `POST /contacts` |
| `escalate_to_human` | `reason`, `conversation_id` | `escalation_id` | Triggers WF-07 |

---

## 5. Phase 1 — Foundation & Channel Integration (Day 1–2)

### Goal
Set up all infrastructure, receive Meta messages reliably, and normalize them into a standard format.

### Day 1 Tasks

#### 1.1 Infrastructure Setup
- [ ] Provision n8n instance (Railway / Render / VPS)
- [ ] Provision Postgres / Supabase instance
- [ ] Set up environment variables in n8n:
  - `OPENAI_API_KEY`
  - `META_PAGE_ACCESS_TOKEN` (per salon)
  - `META_VERIFY_TOKEN`
  - `CRM_BASE_URL`
  - `CRM_API_KEY`
- [ ] Create database tables (see Section 10)

#### 1.2 Meta App Configuration
- [ ] Register n8n webhook URL with Meta (Instagram + Facebook)
- [ ] Set webhook verify token
- [ ] Subscribe to webhook fields:
  - `messages` (DMs)
  - `messaging_postbacks`
  - `comments`
  - `feed` (for comment detection on posts/ads)
- [ ] Test webhook verification (Meta sends GET with hub.challenge)

#### 1.3 WF-01: Webhook Receiver Build
```
Nodes:
  [Webhook Node] 
    → [Switch Node: channel type?]
      → Instagram DM branch
      → Facebook Messenger branch  
      → Comment branch
    → [Function Node: normalize message]
      Output: { sender_id, channel, salon_id, text, timestamp, raw_event }
    → [Set Node: route to next workflow]
```

**Normalized Message Schema:**
```json
{
  "sender_id": "17841234567890",
  "channel": "instagram_dm",
  "salon_id": "salon_abc_123",
  "text": "How much is box braids?",
  "timestamp": "2026-07-14T14:30:00Z",
  "message_id": "mid.xxx",
  "raw_event": {}
}
```

### Day 2 Tasks

#### 2.1 WF-02: Comment Handler Build
```
Nodes:
  [Webhook Node: comment trigger]
    → [HTTP Request: get commenter's Instagram/FB user ID]
    → [HTTP Request: send DM to commenter]
      Message: "Hi! Thanks for your comment. I've sent you a DM to answer your question."
    → [HTTP Request: reply to comment publicly]
      Message: "Hey! Slid into your DMs :)"
    → [Postgres Node: create new conversation record]
```

**Comment Handler Rules:**
- Only trigger on comments that contain question keywords (price, book, available, cost, how much, appointment)
- Skip comments from own page
- Skip duplicate DMs (check if DM already sent in last 24 hours)

#### 2.2 Salon ID Resolution
- Each Meta page maps to one salon
- Maintain `salon_config` table in Postgres:
  ```
  page_id → salon_id → CRM credentials → salon name
  ```
- WF-01 resolves salon_id from page_id on every incoming event

#### 2.3 Phase 1 Deliverables Checklist
- [ ] n8n instance live and accessible
- [ ] Meta webhook receiving Instagram DM events
- [ ] Meta webhook receiving Facebook Messenger events
- [ ] Meta webhook receiving comment events
- [ ] Comment-to-DM redirect working
- [ ] Normalized message schema flowing correctly
- [ ] Postgres tables created and connected

---

## 6. Phase 2 — AI Brain & CRM Integration (Day 3–4)

### Goal
Wire up OpenAI Assistant with tool calling, connect CRM price fetching, and have the agent hold a real multi-turn conversation.

### Day 3 Tasks

#### 3.1 OpenAI Assistant Creation
Create the assistant via OpenAI API (one-time setup):

```json
{
  "name": "Salon Support Agent",
  "model": "gpt-4o",
  "instructions": "[See system prompt below]",
  "tools": [
    { "type": "function", "function": { "name": "get_service_price", ... } },
    { "type": "function", "function": { "name": "check_availability", ... } },
    { "type": "function", "function": { "name": "create_booking", ... } },
    { "type": "function", "function": { "name": "capture_contact", ... } },
    { "type": "function", "function": { "name": "escalate_to_human", ... } }
  ]
}
```

**System Prompt (Base Template):**
```
You are a friendly and professional customer support agent for {{salon_name}}, 
a hair braiding salon based in the US.

CRITICAL RULES:
1. NEVER quote a price from memory or assumption. ALWAYS use the get_service_price 
   tool to fetch the price from our system. If the tool returns no price, 
   immediately call escalate_to_human.
2. To complete a booking, you MUST collect: customer name, service name, 
   preferred date, preferred time, and phone number or email.
3. If the customer asks to speak to a person, owner, or manager — call 
   escalate_to_human immediately.
4. If the customer is upset or complaining — call escalate_to_human immediately.
5. Keep responses short and conversational — this is a chat, not an email.
6. After confirming a booking, send the full confirmation details in one message: 
   service, date, time, location, deposit amount.

SALON INFO:
- Name: {{salon_name}}
- Location: {{salon_address}}
- Hours: {{salon_hours}}
- Deposit policy: {{deposit_policy}}
- Cancellation policy: {{cancellation_policy}}
```

#### 3.2 WF-03: Thread Manager & Message Router Build
```
Nodes:
  [Webhook/Execute Trigger: receives normalized message]
    → [Postgres Node: SELECT thread_id WHERE sender_id = ?]
    → [IF Node: thread exists?]
      YES → skip to message add
      NO  → [HTTP Request: POST https://api.openai.com/v1/threads]
           → [Postgres Node: INSERT sender_id, thread_id, salon_id]
    → [HTTP Request: POST /threads/{thread_id}/messages]
        body: { role: "user", content: message.text }
    → [HTTP Request: POST /threads/{thread_id}/runs]
        body: { assistant_id: ASSISTANT_ID, 
                additional_instructions: "Salon: {{salon_name}} ..." }
    → [Loop: Poll run status every 1.5 seconds]
        → [HTTP Request: GET /threads/{thread_id}/runs/{run_id}]
        → [Switch: status?]
            "completed"       → Fetch messages → Send response
            "requires_action" → Trigger WF-04 (Tool Dispatcher)
            "failed"          → Trigger WF-07 (Human Handoff)
            "queued/running"  → Wait 1.5s → Poll again
```

**Polling Strategy:**
- Max poll attempts: 20 (30 seconds total)
- If exceeded: auto-escalate to human
- On `requires_action`: pause main loop, dispatch tools, resume

### Day 4 Tasks

#### 4.1 WF-04: Tool Call Dispatcher Build
```
Nodes:
  [Execute Trigger: receives run_id, tool_calls[]]
    → [Loop over tool_calls]
      → [Switch: tool_name?]
          "get_service_price"   → [HTTP Request: CRM GET /prices]
          "check_availability"  → [HTTP Request: CRM GET /availability]
          "create_booking"      → [HTTP Request: CRM POST /bookings]
          "capture_contact"     → [HTTP Request: CRM POST /contacts]
          "escalate_to_human"   → [Execute WF-07]
      → [Collect tool_outputs[]]
    → [HTTP Request: POST /threads/{id}/runs/{run_id}/submit_tool_outputs]
        body: { tool_outputs: [...] }
    → [Return to WF-03 polling loop]
```

**CRM Error Handling in Tool Dispatcher:**
```
If CRM returns 404 (price not found):
  → return { price: null, error: "not_found" }
  → Assistant will see this and call escalate_to_human

If CRM returns 500 or timeout:
  → return { price: null, error: "service_unavailable" }
  → Assistant will call escalate_to_human

Never let the assistant guess — always return structured error.
```

#### 4.2 WF-05: Response Sender Build
```
Nodes:
  [Execute Trigger: receives final_text, sender_id, channel]
    → [Switch: channel?]
        "instagram_dm"    → [HTTP Request: Instagram Send API]
        "facebook_messenger" → [HTTP Request: FB Send API]
    → [Postgres Node: UPDATE conversation status, last_reply_at]
    → [Trigger WF-06: CRM Write-Back]
```

**Meta Send API Calls:**
- Instagram: `POST https://graph.facebook.com/v19.0/me/messages`
- Facebook: `POST https://graph.facebook.com/v19.0/me/messages`
- Both use page access token, differ in recipient ID format

#### 4.3 Phase 2 Deliverables Checklist
- [ ] OpenAI Assistant created with all 5 tools defined
- [ ] Thread creation and storage working
- [ ] Multi-turn conversation holding context correctly
- [ ] `get_service_price` tool calling CRM and returning real price
- [ ] `check_availability` tool working
- [ ] Agent refusing to quote price when CRM returns null
- [ ] Responses being sent back to Instagram DM
- [ ] Responses being sent back to Facebook Messenger
- [ ] End-to-end test: Customer asks price → CRM fetched → Agent replies with correct price

---

## 7. Phase 3 — Booking, Handoff & Write-Back (Day 5–6)

### Goal
Complete the booking flow, implement human handoff, and ensure all data is written back to CRM.

### Day 5 Tasks

#### 5.1 Booking Flow Implementation

**Lead Qualification Checklist (Agent must collect all before booking):**
```
✓ Service name confirmed
✓ Date confirmed
✓ Time confirmed
✓ Customer name captured
✓ Phone number OR email captured
```

**Booking Conversation Flow:**
```
Customer: "I want to get box braids"
Agent: uses get_service_price → "Box braids are $180 and take about 4 hours. 
        Hair is included. When would you like to come in?"
Customer: "Saturday the 19th"
Agent: uses check_availability → "We have 10am and 2pm available on Saturday. 
        Which works for you?"
Customer: "10am"
Agent: "Perfect! Can I get your name and a phone number to complete the booking?"
Customer: "Sarah, 555-0192"
Agent: uses create_booking → booking created
Agent: "You're all set, Sarah! Here's your confirmation:
        ✓ Service: Box Braids
        ✓ Date: Saturday, July 19
        ✓ Time: 10:00 AM
        ✓ Location: [salon address]
        ✓ Deposit: $30 due at booking link: [link]
        See you then!"
```

#### 5.2 WF-07: Human Handoff Build
```
Nodes:
  [Execute Trigger: receives reason, conversation_id, sender_id, thread_id]
    → [Postgres Node: UPDATE conversations SET human_handling = true]
    → [HTTP Request: Slack/Email → Team notification]
        Message: "🚨 Human needed | Reason: {reason}
                  Customer: {sender_id} on {channel}
                  Salon: {salon_name}
                  Last message: {last_message}
                  CRM link: {crm_conversation_link}"
    → [HTTP Request: Meta API → Customer message]
        Message: "I'm connecting you with our team right now. 
                  Someone will be with you shortly!"
    → [Postgres Node: log escalation event]
```

**Human Handoff Triggers:**
| Trigger | Source |
|---|---|
| Customer asks for owner/person | Intent detected by assistant |
| Customer is complaining | Intent detected by assistant |
| Price not found in CRM | Tool returns null price |
| CRM is unreachable | HTTP timeout in tool dispatcher |
| Run fails or times out | WF-03 error path |
| Low confidence answer | Assistant calls escalate_to_human |

**Resume After Human:**
- Team member marks conversation resolved in CRM
- CRM webhook notifies n8n
- n8n sets `human_handling = false` in Postgres
- Agent resumes handling new messages

### Day 6 Tasks

#### 6.1 WF-06: CRM Write-Back Build
```
Nodes:
  [Execute Trigger: receives full conversation context]
    → [HTTP Request: CRM POST/PUT /contacts]
        body: { name, instagram_handle, fb_handle, phone, email }
    → [HTTP Request: CRM POST /conversations]
        body: { 
          contact_id, salon_id, channel, 
          lead_status, service_interest,
          conversation_transcript,
          booking_id (if booked)
        }
    → [HTTP Request: CRM PUT /conversations/{id}/transcript]
        body: { messages: [...full thread...] }
    → [HTTP Request: CRM PUT /leads/{id}/status]
        body: { status: "new|qualified|booked|escalated" }
```

**Data Written to CRM on Every Conversation:**
```
Contact Record:
  - Full name (if captured)
  - Instagram handle / Facebook profile
  - Phone number (if captured)
  - Email (if captured)
  - Channel (instagram_dm / facebook_messenger)

Lead Record:
  - Salon ID
  - Service interested in
  - Lead status: new → interested → qualified → booked / escalated
  - Source channel

Conversation Record:
  - Full message transcript (all turns)
  - Timestamps per message
  - Agent messages vs customer messages labeled
  - Any tool calls made (price fetched, availability checked)

Booking Record (if booked):
  - Booking ID from CRM
  - Service name
  - Date & time
  - Deposit status
  - Confirmation sent: yes/no
```

#### 6.2 Phase 3 Deliverables Checklist
- [ ] Full booking flow working end-to-end (question → qualify → book → confirm message)
- [ ] Booking confirmation message sent in same thread immediately after creation
- [ ] Human handoff triggering correctly on all 6 trigger conditions
- [ ] Team receiving Slack/Email alerts with conversation context
- [ ] Agent pausing correctly when human_handling = true
- [ ] Agent resuming after human marks resolved
- [ ] All contact data writing to CRM
- [ ] Full conversation transcript saving to CRM
- [ ] Lead status updating correctly through stages
- [ ] Booking details saving to CRM

---

## 8. Phase 4 — Human-in-Loop, Testing & Pilot Launch (Day 7–8)

### Goal
Implement draft approval mode for Phase 1 pilot, run full QA, and go live on the pilot salon.

### Day 7 Tasks

#### 8.1 WF-08: Draft Approval Mode Build

This workflow replaces WF-05 (direct send) for the pilot salon during Phase 1.

```
Nodes:
  [Execute Trigger: receives agent_response, conversation_id, sender_id]
    → [Postgres Node: INSERT into drafts table]
        body: { conversation_id, draft_text, created_at, approved: false }
    → [HTTP Request: Slack/Email → Team notification]
        Message: "📝 Draft ready for review
                  Customer: {sender_id} | Salon: {salon_name}
                  Draft: {agent_response}
                  [APPROVE] {approve_webhook_url}
                  [EDIT & SEND] {edit_webhook_url}
                  [DISCARD] {discard_webhook_url}"
    → [Wait Node: wait for webhook callback]
```

**Approval Webhook Handler:**
```
Nodes:
  [Webhook Node: /approve/{draft_id}]
    → [Postgres Node: SELECT draft WHERE id = ?]
    → [IF: action = "approve"]
        → [HTTP Request: Meta API send original draft]
        → [Postgres Node: UPDATE draft SET approved = true]
    → [IF: action = "edit"]
        → [Receive edited text from team]
        → [HTTP Request: Meta API send edited text]
        → [Postgres Node: UPDATE draft SET sent_text, approved = true]
    → [IF: action = "discard"]
        → [Postgres Node: DELETE draft]
        → [Trigger WF-07: human handoff if needed]
    → [Trigger WF-06: CRM Write-Back with final sent text]
```

#### 8.2 Pilot Mode Configuration
- Add `pilot_mode: boolean` to `salon_config` table
- WF-03 checks this flag after getting agent response:
  - `pilot_mode = true` → route to WF-08 (draft)
  - `pilot_mode = false` → route to WF-05 (direct send)

### Day 8 Tasks

#### 8.3 Full QA Test Suite

**Test Scenario 1: Basic Price Query**
```
Input:  "How much does it cost for knotless braids?"
Expected: Agent calls get_service_price → returns CRM price → quotes exact price
Fail:   Agent quotes any number without tool call
```

**Test Scenario 2: Price Not in CRM**
```
Input:  "How much for [service not in CRM]?"
Expected: Agent calls get_service_price → gets null → calls escalate_to_human → human notified
Fail:   Agent guesses a price
```

**Test Scenario 3: Full Booking Flow**
```
Input:  Customer goes through complete booking conversation
Expected: Booking created in CRM → confirmation message sent → all data logged to CRM
Check:  booking_id present in CRM, confirmation received in DM, transcript saved
```

**Test Scenario 4: Human Escalation — Explicit**
```
Input:  "Can I speak to the owner?"
Expected: Human handoff triggered → team alerted → agent stops responding → customer notified
```

**Test Scenario 5: Human Escalation — Complaint**
```
Input:  "This is ridiculous, I've been waiting for a response for days"
Expected: Escalation triggered within 1 message
```

**Test Scenario 6: Comment → DM Flow**
```
Input:  Comment on IG post: "How much for box braids?"
Expected: Public reply sent → DM opened → agent starts conversation in DM
```

**Test Scenario 7: Multi-turn Context**
```
Turn 1: "What services do you offer?"
Turn 2: "How much is the second one?" ← must use context from turn 1
Expected: Agent remembers conversation, answers correctly
```

**Test Scenario 8: Draft Approval (Pilot Mode)**
```
Expected: Agent generates reply → team receives Slack with [APPROVE] button → 
          team approves → message sent to customer → not before
```

**Test Scenario 9: CRM Write-Back Verification**
```
After any conversation: open CRM manually
Check: contact created/updated, transcript saved, lead status updated, 
       booking present if booked
```

**Test Scenario 10: Cross-Channel**
```
Same customer messages on both IG DM and FB Messenger
Expected: Separate threads, both log to same CRM contact (matched by name/phone)
```

#### 8.4 Pilot Launch Checklist
- [ ] All 10 test scenarios passing
- [ ] Pilot salon Meta pages connected
- [ ] `pilot_mode = true` set for pilot salon
- [ ] Team trained on draft approval interface (Slack buttons)
- [ ] Team trained on human handoff resolution (CRM)
- [ ] Monitoring: n8n execution error alerts set up
- [ ] Monitoring: OpenAI API error alerts set up
- [ ] Monitoring: CRM write-back failure alerts set up
- [ ] Rollback plan documented (disable webhook → all messages go to inbox directly)

#### 8.5 Phase Progression Gates

| Gate | Requirement | Who Approves |
|---|---|---|
| Phase 1 → Phase 2 | 95%+ price accuracy, no hallucinated prices in 50 conversations | Client + Atrium |
| Phase 2 → Phase 3 | Full auto DMs stable for 1 week, <2 escalation errors/day | Client |
| Phase 3 → Phase 4 | Comment replies tested, no public errors on client accounts | Client |
| Phase 4 | All salons onboarded, multi-tenant verified | Client |

---

## 9. What We Need From Client

### Meta Access (Needed Before Day 1)
| Item | Details | Why Needed |
|---|---|---|
| Facebook Page Admin Access | For each salon page | Connect webhook, send messages |
| Instagram Professional Account | Linked to Facebook Page | IG DM access via Graph API |
| Meta Business Verification | Business verified on Meta | Required for messaging permissions |
| Page Access Tokens | Long-lived, per salon | API authentication |
| App Review Scopes Needed | `pages_messaging`, `instagram_manage_messages`, `pages_read_engagement`, `instagram_manage_comments` | All messaging features |

### CRM Access (Needed Before Day 3)
| Item | Details | Why Needed |
|---|---|---|
| CRM API Base URL | Base endpoint for all calls | HTTP integrations |
| CRM API Key / Auth Method | Bearer token, API key, OAuth | Authentication |
| Endpoint: Get Service Price | `GET /salons/{id}/services` or equivalent | Pricing tool |
| Endpoint: Check Availability | `GET /salons/{id}/availability` | Availability tool |
| Endpoint: Create Booking | `POST /bookings` | Booking tool |
| Endpoint: Create/Update Contact | `POST /contacts` | Write-back |
| Endpoint: Log Conversation | `POST /conversations` | Write-back |
| Endpoint: Update Lead Status | `PUT /leads/{id}` | Write-back |
| Salon IDs | ID for each salon in CRM | Multi-tenant routing |

### Training Data (Needed Before Day 7)
| Item | Format Required | Why Needed |
|---|---|---|
| Real chat transcripts | JSON or CSV with: timestamp, sender_type (customer/agent), message_text | Few-shot examples in system prompt |
| Volume | Minimum 50 conversations, 200+ preferred | Coverage of edge cases |
| Labels (if possible) | Intent label per customer message | Better prompt engineering |

### Content From Client
| Item | Details |
|---|---|
| Service list (all salons) | Full list with service names exactly as in CRM |
| Salon addresses (all) | Per salon location |
| Operating hours (all) | Per salon, including holidays |
| Deposit policy | Amount or percentage, when charged |
| Cancellation policy | Notice period, refund policy |
| Human handoff contact | Slack workspace invite or email for alerts |

---

## 10. Database Schema

### `salon_config` Table
```sql
CREATE TABLE salon_config (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  salon_id        VARCHAR(100) UNIQUE NOT NULL,
  salon_name      VARCHAR(255) NOT NULL,
  fb_page_id      VARCHAR(100),
  ig_page_id      VARCHAR(100),
  page_access_token TEXT,
  crm_base_url    TEXT,
  crm_api_key     TEXT,
  salon_address   TEXT,
  salon_hours     TEXT,
  deposit_policy  TEXT,
  cancellation_policy TEXT,
  pilot_mode      BOOLEAN DEFAULT TRUE,
  active          BOOLEAN DEFAULT TRUE,
  created_at      TIMESTAMP DEFAULT NOW()
);
```

### `conversations` Table
```sql
CREATE TABLE conversations (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  sender_id       VARCHAR(255) NOT NULL,
  channel         VARCHAR(50) NOT NULL,    -- instagram_dm / facebook_messenger
  salon_id        VARCHAR(100) NOT NULL,
  thread_id       VARCHAR(255) UNIQUE,     -- OpenAI Thread ID
  crm_contact_id  VARCHAR(255),
  crm_lead_id     VARCHAR(255),
  lead_status     VARCHAR(50) DEFAULT 'new', -- new/interested/qualified/booked/escalated
  service_interest VARCHAR(255),
  human_handling  BOOLEAN DEFAULT FALSE,
  booking_id      VARCHAR(255),
  created_at      TIMESTAMP DEFAULT NOW(),
  last_message_at TIMESTAMP DEFAULT NOW(),
  FOREIGN KEY (salon_id) REFERENCES salon_config(salon_id)
);
```

### `drafts` Table (Phase 1 Pilot)
```sql
CREATE TABLE drafts (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  conversation_id UUID NOT NULL,
  draft_text      TEXT NOT NULL,
  sent_text       TEXT,
  approved        BOOLEAN DEFAULT FALSE,
  approved_by     VARCHAR(255),
  approved_at     TIMESTAMP,
  discarded       BOOLEAN DEFAULT FALSE,
  created_at      TIMESTAMP DEFAULT NOW(),
  FOREIGN KEY (conversation_id) REFERENCES conversations(id)
);
```

### `escalations` Table
```sql
CREATE TABLE escalations (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  conversation_id UUID NOT NULL,
  reason          TEXT NOT NULL,
  triggered_by    VARCHAR(100),   -- tool_name / intent / timeout
  resolved        BOOLEAN DEFAULT FALSE,
  resolved_by     VARCHAR(255),
  resolved_at     TIMESTAMP,
  created_at      TIMESTAMP DEFAULT NOW(),
  FOREIGN KEY (conversation_id) REFERENCES conversations(id)
);
```

---

## 11. API Reference Map

### Meta Graph API Endpoints Used

| Action | Method | Endpoint |
|---|---|---|
| Send DM (IG/FB) | POST | `https://graph.facebook.com/v19.0/me/messages` |
| Reply to comment | POST | `https://graph.facebook.com/v19.0/{comment_id}/replies` |
| Get user profile | GET | `https://graph.facebook.com/v19.0/{user_id}?fields=name` |
| Webhook verification | GET | Handled by n8n Webhook node |
| Webhook events | POST | Received by n8n Webhook node |

### OpenAI Assistants API Endpoints Used

| Action | Method | Endpoint |
|---|---|---|
| Create thread | POST | `https://api.openai.com/v1/threads` |
| Add message | POST | `https://api.openai.com/v1/threads/{id}/messages` |
| Run assistant | POST | `https://api.openai.com/v1/threads/{id}/runs` |
| Poll run status | GET | `https://api.openai.com/v1/threads/{id}/runs/{run_id}` |
| Submit tool outputs | POST | `https://api.openai.com/v1/threads/{id}/runs/{run_id}/submit_tool_outputs` |
| Get messages | GET | `https://api.openai.com/v1/threads/{id}/messages` |

---

## 12. Rollout Sequence

| Phase | Mode | Salons | Agent Behavior | Duration |
|---|---|---|---|---|
| Phase 1 | Human-in-Loop | 1 (pilot) | Agent drafts, team reviews & sends | Until quality proven (est. 1–2 weeks) |
| Phase 2 | Full Auto DMs | 1 (pilot) | Agent sends directly, team monitors | 1 week stable |
| Phase 3 | Comments Enabled | 1 (pilot) | Comments + DMs fully auto | After Phase 2 stable |
| Phase 4 | Full Rollout | All salons | All channels, all salons | Per client readiness |

### Rollback Plan
If agent causes a client-facing incident at any phase:
1. Disable n8n webhook (Meta messages go directly to inbox)
2. Team handles conversations manually
3. Debug + fix in n8n
4. Re-enable webhook after fix verified

---

## 13. Cost Estimate

### Infrastructure (Monthly)

| Service | Plan | Est. Cost |
|---|---|---|
| n8n (self-hosted on Railway) | Hobby plan | ~$5–20/mo |
| Supabase / Postgres | Free tier (up to 500MB) | $0–25/mo |
| Server / VPS (if self-host n8n) | 1GB RAM minimum | ~$6–12/mo |

### OpenAI API (Per Conversation Estimate)

| Item | Estimate |
|---|---|
| Avg tokens per conversation | ~2,000 tokens (input + output) |
| GPT-4o price | ~$0.01–0.02 per conversation |
| 500 conversations/month (pilot) | ~$5–10/mo |
| Thread storage | Minimal (< $1/mo at pilot scale) |

### Total Estimated Monthly Cost (Pilot — 1 Salon)
```
n8n hosting:      $10/mo
Supabase:         $0/mo (free tier)
OpenAI API:       $10/mo
─────────────────────────
Total:            ~$20/mo
```

---

*Document Version: 1.0 | Last Updated: July 14, 2026 | Atrium Solution*
