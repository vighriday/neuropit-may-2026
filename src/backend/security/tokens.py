"""JWT helpers for the FastAPI gateway.

We avoid pulling a heavy auth framework into the project. The gateway only
needs to mint and verify short lived bearer tokens that the dashboard uses
to identify itself, plus a small role claim so the role based access rules
in `roles.py` have something to inspect.

Tokens are signed with HS256 by default. The secret comes from the
`API_JWT_SECRET` environment variable. Production deployments rotate this
value during the race weekend.
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Optional

from jose import JWTError, jwt

from src.backend.config import get_settings


@dataclass(frozen=True)
class TokenClaims:
    subject: str
    role: str
    issued_at: int
    expires_at: int


def issue_token(subject: str, role: str, expires_in_seconds: Optional[int] = None) -> str:
    settings = get_settings()
    now = int(time.time())
    expiry = now + (expires_in_seconds or settings.api_token_expiry_minutes * 60)
    payload = {
        "sub": subject,
        "role": role,
        "iat": now,
        "exp": expiry,
    }
    return jwt.encode(payload, settings.api_jwt_secret, algorithm=settings.api_jwt_algorithm)


def verify_token(token: str) -> TokenClaims:
    settings = get_settings()
    try:
        payload = jwt.decode(token, settings.api_jwt_secret, algorithms=[settings.api_jwt_algorithm])
    except JWTError as exc:
        raise ValueError(f"Invalid token: {exc}") from exc

    if "sub" not in payload or "role" not in payload:
        raise ValueError("Token is missing the subject or role claim")
    return TokenClaims(
        subject=payload["sub"],
        role=payload["role"],
        issued_at=int(payload.get("iat", 0)),
        expires_at=int(payload.get("exp", 0)),
    )
