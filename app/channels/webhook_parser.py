# TODO (Step 2 — Meta Integration)
#
# Webhook Event Parser
#
# Meta's raw webhook payload is deeply nested JSON.
# This parser normalizes it into a flat, consistent format
# that the rest of the application uses.
#
# Input (Meta raw event — DM example):
#   {
#     "object": "instagram",
#     "entry": [{
#       "id": "page_456",
#       "messaging": [{
#         "sender": { "id": "17841234567890" },
#         "recipient": { "id": "page_456" },
#         "timestamp": 1720958400000,
#         "message": { "mid": "mid.xxx", "text": "How much is box braids?" }
#       }]
#     }]
#   }
#
# Output (normalized):
#   {
#     "sender_id": "17841234567890",
#     "channel": "instagram_dm",
#     "page_id": "page_456",
#     "text": "How much is box braids?",
#     "message_id": "mid.xxx",
#     "timestamp": "2026-07-14T14:30:00Z",
#     "event_type": "dm"   # dm | comment
#   }
#
# This normalized format flows into the agent graph as the initial user message.
