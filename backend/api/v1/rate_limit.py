"""
Shared rate limiter instance for GathaAI Studio API.

Uses slowapi (a limits-based rate limiter for Starlette/FastAPI).
The limiter is keyed by client IP address and applied selectively
to expensive or abuse-prone endpoints.

Limits are intentionally generous for single-user local use —
they guard against accidental loops, not malicious traffic.

Usage in route handlers:
    from backend.api.v1.rate_limit import limiter

    @router.post("/some-route")
    @limiter.limit("20/minute")
    async def my_route(request: Request, ...):
        ...

Note: The `request: Request` parameter MUST be present in the handler
signature for slowapi to extract the client IP. It doesn't need to be
used explicitly.
"""

from __future__ import annotations

from slowapi import Limiter
from slowapi.util import get_remote_address

# Single shared limiter — imported by routes and registered in main.py
limiter = Limiter(key_func=get_remote_address)
