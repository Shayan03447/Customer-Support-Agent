# TODO (Step 2 — Meta Integration)
#
# HMAC-SHA256 Webhook Signature Verification
#
# Why this is needed:
#   Meta signs every webhook POST request with your APP_SECRET.
#   The signature is in the X-Hub-Signature-256 header.
#   You must verify it to confirm the request is genuinely from Meta
#   and not from an attacker sending fake webhook payloads.
#
# How to implement:
#
#   import hmac
#   import hashlib
#   from app.config import settings
#
#   def verify_signature(raw_body: bytes, signature_header: str) -> bool:
#       """
#       Verify X-Hub-Signature-256 header.
#       Returns True if valid, False if invalid.
#       """
#       if not signature_header or not signature_header.startswith("sha256="):
#           return False
#
#       expected_sig = signature_header[7:]  # Remove "sha256=" prefix
#       computed_sig = hmac.new(
#           key=settings.meta_app_secret.encode("utf-8"),
#           msg=raw_body,
#           digestmod=hashlib.sha256,
#       ).hexdigest()
#
#       # Use constant-time comparison to prevent timing attacks
#       return hmac.compare_digest(expected_sig, computed_sig)
