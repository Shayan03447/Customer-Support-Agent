# TODO (Step 5 — Human Handoff)
#
# Team Notification Sender
#
# Sends alerts to the team via Slack (and email as fallback).
# Used by escalation.py when human intervention is needed.
#
# Slack alert format:
#   Human Needed — Salon: Glamour Braids Studio
#   Customer:      ig_user_123 on instagram_dm
#   Reason:        price_not_found
#   Last message:  "How much for passion twists?"
#   Time:          2026-07-14 14:30 UTC
#   CRM:           https://crm.example.com/conversations/uuid-xxx
#
#   [Resume Agent] → POST /internal/resume-conversation/uuid-xxx
#
# Draft approval alert format (pilot mode):
#   Draft Ready — Salon: Glamour Braids Studio
#   Customer:  ig_user_123
#   Draft:     "Box braids are $180 and take about 4 hours..."
#
#   [APPROVE] → POST /internal/approve-draft/draft-id
#   [EDIT & SEND] → POST /internal/edit-draft/draft-id
#   [DISCARD] → POST /internal/discard-draft/draft-id
#
# Functions to implement:
#
#   async def send_escalation_alert(
#       salon_name: str, sender_id: str, channel: str,
#       reason: str, last_message: str, conversation_id: str
#   ) -> None:
#       """POST to SLACK_WEBHOOK_URL with escalation details."""
#
#   async def send_draft_alert(
#       salon_name: str, sender_id: str,
#       draft_text: str, draft_id: str
#   ) -> None:
#       """POST to SLACK_WEBHOOK_URL with draft and action buttons."""
