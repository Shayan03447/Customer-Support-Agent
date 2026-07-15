# TODO (Step 5 — Human Handoff & Draft Approval)
#
# Internal API endpoints — called by the team (via Slack buttons or a dashboard).
# These are NOT called by Meta — they are called by your own team members.
#
# Endpoints:
#   POST /internal/resume-conversation/{conversation_id}
#        Sets human_handling = False in PostgreSQL and Redis.
#        Agent will handle the customer's next message normally.
#
#   POST /internal/approve-draft/{draft_id}
#        Sends the original agent draft to the customer via Meta API.
#        Marks draft as approved in PostgreSQL.
#
#   POST /internal/edit-draft/{draft_id}
#        Body: { "text": "..." }
#        Sends the edited text to the customer via Meta API.
#        Saves both original draft and sent text in PostgreSQL.
#
#   POST /internal/discard-draft/{draft_id}
#        Discards the draft.
#        Triggers human handoff so team takes over.
#
# router = APIRouter(prefix="/internal")
