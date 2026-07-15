# TODO (Step 2 — Meta Integration)
#
# Meta Graph API Client
#
# This async httpx client handles all outbound calls to Meta.
# Sends messages back to customers on Instagram and Facebook.
#
# Methods to implement:
#
#   async def send_dm(page_access_token: str, recipient_id: str, text: str) -> None:
#       """Send a Direct Message via Instagram or Facebook Messenger."""
#       # POST https://graph.facebook.com/v19.0/me/messages
#       # Body: { "recipient": {"id": recipient_id}, "message": {"text": text} }
#       # Header: Authorization: Bearer {page_access_token}
#
#   async def reply_to_comment(page_access_token: str, comment_id: str, text: str) -> None:
#       """Reply publicly to an Instagram or Facebook comment."""
#       # POST https://graph.facebook.com/v19.0/{comment_id}/replies
#       # Body: { "message": text }
#
#   async def get_user_profile(page_access_token: str, user_id: str) -> dict:
#       """Fetch a user's name and profile info."""
#       # GET https://graph.facebook.com/v19.0/{user_id}?fields=name,profile_pic
#
# All methods use httpx.AsyncClient for non-blocking HTTP.
# Initialize a single client instance and reuse it (don't create a new client per request).
