# FastAPI application entry point.
#
# To implement:
#   1. Create FastAPI app with lifespan context manager
#   2. In lifespan startup:
#        - init_db_pool()   (Step 3 — PostgreSQL)
#        - init_redis()     (Step 4 — Redis)
#        - init_sentry()    (Step 7 — Error tracking)
#   3. Include routers:
#        - webhook_router   (app/api/webhook.py)
#        - internal_router  (app/api/internal.py)
#   4. GET /health endpoint — check all service connections
