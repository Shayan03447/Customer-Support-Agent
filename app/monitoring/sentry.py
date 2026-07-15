# TODO (Step 6 — Error Tracking)
#
# Sentry Error Tracking
#
# What Sentry does:
#   Captures every unhandled exception in production with full stack trace.
#   Shows you exactly which file, line, and function caused the error.
#   Includes context: sender_id, salon_id, conversation_id.
#   Sends email/Slack alerts when new errors occur.
#
# How to implement:
#
#   import sentry_sdk
#   from app.config import settings
#
#   def init_sentry() -> None:
#       """Call once at app startup in app/main.py lifespan."""
#       if not settings.sentry_dsn:
#           return  # Skip in development if DSN not set
#
#       sentry_sdk.init(
#           dsn=settings.sentry_dsn,
#           environment=settings.app_env,
#           traces_sample_rate=0.1,   # Track 10% of requests for performance
#           profiles_sample_rate=0.1,
#       )
#
# Adding context to Sentry errors:
#
#   with sentry_sdk.push_scope() as scope:
#       scope.set_tag("salon_id", state["salon_id"])
#       scope.set_tag("channel", state["channel"])
#       scope.set_user({"id": state["sender_id"]})
#       scope.set_extra("conversation_id", state["conversation_id"])
#       sentry_sdk.capture_exception(error)
