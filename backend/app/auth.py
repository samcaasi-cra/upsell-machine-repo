"""Shared-password gate for deployed instances.

The dashboard shows real customer names, their security scores, decision-maker
names and supplier relationships -- none of which should sit on a public URL.

Deliberately simple: one shared password, a signed token, no user accounts. That's
proportionate for a hackathon demo and still keeps the data off the open internet.

When APP_PASSWORD is unset the gate is disabled entirely, so local development is
unaffected. It's only ever active where it's been explicitly configured.
"""

import hmac
import os
import secrets
import time
from hashlib import sha256

from fastapi import Request
from fastapi.responses import JSONResponse

# Paths reachable without a token: the health check (so the host can probe the
# service) and login itself.
_PUBLIC_PATHS = {"/health", "/login", "/docs", "/openapi.json", "/redoc"}

_TOKEN_TTL_SECONDS = 60 * 60 * 12  # a working day


def is_enabled() -> bool:
    return bool(os.getenv("APP_PASSWORD"))


def _secret() -> bytes:
    # Falls back to the password itself if no separate signing secret is set, which
    # is fine here -- both live in the same env and the token is short-lived.
    return (os.getenv("APP_SECRET") or os.getenv("APP_PASSWORD") or "dev").encode()


def issue_token() -> str:
    """token = expiry.signature -- stateless, so restarts don't log everyone out."""
    expires_at = int(time.time()) + _TOKEN_TTL_SECONDS
    signature = hmac.new(_secret(), str(expires_at).encode(), sha256).hexdigest()
    return f"{expires_at}.{signature}"


def verify_token(token: str) -> bool:
    try:
        expiry_str, signature = token.split(".", 1)
        expires_at = int(expiry_str)
    except (ValueError, AttributeError):
        return False
    if expires_at < time.time():
        return False
    expected = hmac.new(_secret(), expiry_str.encode(), sha256).hexdigest()
    return hmac.compare_digest(expected, signature)


def check_password(candidate: str) -> bool:
    expected = os.getenv("APP_PASSWORD") or ""
    # Constant-time compare so the endpoint doesn't leak the password by timing.
    return bool(expected) and secrets.compare_digest(candidate, expected)


async def auth_middleware(request: Request, call_next):
    if not is_enabled() or request.method == "OPTIONS" or request.url.path in _PUBLIC_PATHS:
        return await call_next(request)

    header = request.headers.get("authorization", "")
    token = header[7:] if header.lower().startswith("bearer ") else ""
    if not verify_token(token):
        return JSONResponse(status_code=401, content={"detail": "Not authenticated"})

    return await call_next(request)
