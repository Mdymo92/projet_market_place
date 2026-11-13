"""JWT creation and checks shared by all services.

Usage in a route:
    @router.get("/v1/orders")
    def list_orders(user: Principal = Depends(require("orders:read"))): ...

- no token, bad signature, expired token -> 401
- valid token but role not in the RBAC matrix for this action -> 403
Every refusal is logged with who, what and when (brief: "chaque refus est enregistre").
"""

import logging
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

import bcrypt
import jwt
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from .config import get_settings
from .rbac import MATRIX, allowed

log = logging.getLogger("security")
_bearer = HTTPBearer(auto_error=False)


@dataclass(frozen=True)
class Principal:
    subject: str
    roles: tuple[str, ...]


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt(rounds=12)).decode()


def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode(), hashed.encode())


def create_access_token(subject: str, roles: list[str], ttl_minutes: int | None = None) -> str:
    s = get_settings()
    now = datetime.now(UTC)
    claims = {
        "sub": subject,
        "roles": roles,
        "iss": s.jwt_issuer,  # Kong matches this against its consumer key
        "iat": now,
        "exp": now + timedelta(minutes=ttl_minutes if ttl_minutes is not None else s.jwt_ttl_minutes),
    }
    return jwt.encode(claims, s.jwt_secret, algorithm="HS256")


def decode_token(token: str) -> Principal:
    s = get_settings()
    claims = jwt.decode(
        token,
        s.jwt_secret,
        algorithms=["HS256"],
        issuer=s.jwt_issuer,
        options={"require": ["exp", "sub", "iss"]},
    )
    return Principal(subject=str(claims["sub"]), roles=tuple(claims.get("roles", [])))


def _refuse(request: Request, code: int, detail: str, subject: str | None = None) -> HTTPException:
    log.warning(
        "access refused",
        extra={"status_code": code, "subject": subject, "action": f"{request.method} {request.url.path}"},
    )
    headers = {"WWW-Authenticate": "Bearer"} if code == status.HTTP_401_UNAUTHORIZED else None
    return HTTPException(status_code=code, detail=detail, headers=headers)


def current_principal(request: Request, creds: HTTPAuthorizationCredentials | None = Depends(_bearer)) -> Principal:
    if creds is None:
        raise _refuse(request, 401, "missing bearer token")
    try:
        return decode_token(creds.credentials)
    except jwt.ExpiredSignatureError:
        raise _refuse(request, 401, "token expired") from None
    except jwt.PyJWTError:
        raise _refuse(request, 401, "invalid token") from None


def require(action: str):
    """FastAPI dependency: the caller must hold a role allowed for `action`."""
    if action not in MATRIX:
        raise ValueError(f"unknown action {action!r}, add it to rbac.MATRIX")

    def checker(request: Request, principal: Principal = Depends(current_principal)) -> Principal:
        if not allowed(action, principal.roles):
            raise _refuse(request, 403, f"role not allowed for {action}", principal.subject)
        return principal

    return checker
