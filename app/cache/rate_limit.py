# TODO (Step 4 — Redis Setup)
#
# Rate Limiting
#
# Why rate limit?
#   A customer sending 50 messages in 10 seconds would trigger 50 OpenAI API calls.
#   Rate limiting protects against cost spikes and abuse.
#
# Implementation using Redis atomic increment:
#   key:       "rate:{sender_id}"
#   value:     integer message count
#   TTL:       60 seconds (window resets every minute)
#   Threshold: 10 messages per 60-second window
#
# How INCR + EXPIRE works:
#   First message → INCR creates key with value 1, then EXPIRE sets 60s TTL
#   Each subsequent message → INCR increments value
#   After 60 seconds → key expires, count resets automatically
#
# Function to implement:
#
#   async def check_rate_limit(redis, sender_id: str, max_per_minute=10) -> bool:
#       """
#       Increment message count for this sender.
#       Returns True if within limit (proceed normally).
#       Returns False if limit exceeded (return rate limit message, skip agent).
#       """
#       count = await redis.incr(f"rate:{sender_id}")
#       if count == 1:
#           await redis.expire(f"rate:{sender_id}", 60)
#       return count <= max_per_minute
