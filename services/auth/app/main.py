"""Auth service: login, refresh, service-account tokens, user admin. Contract: contracts/openapi/auth.yaml"""

import hashlib
import secrets
from datetime import UTC, datetime, timedelta

from fastapi import Depends, Header, HTTPException, Request, status
from pydantic import BaseModel, Field

from market_common.app_factory import create_app
from market_common.config import get_settings
from market_common.security import (
    Principal,
    create_access_token,
    current_principal,
    hash_password,
    require,
    verify_password,
)

from . import db

app = create_app("auth", "Market Auth API")
app.router.on_shutdown.append(db.close)


class LoginRequest(BaseModel):
    email: str = Field(pattern=r"^[^@\s]+@[^@\s]+$")
    password: str = Field(min_length=8)


class RefreshRequest(BaseModel):
    refresh_token: str


class TokenRequest(BaseModel):
    client_id: str


class UserCreate(BaseModel):
    email: str = Field(pattern=r"^[^@\s]+@[^@\s]+$")
    password: str = Field(min_length=12)
    roles: list[str] = Field(min_length=1)


def _sha256(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()


def _issue_pair(user_id: int, email: str, roles: list[str]) -> dict:
    s = get_settings()
    refresh = secrets.token_urlsafe(48)
    db.store_refresh_token(user_id, _sha256(refresh), datetime.now(UTC) + timedelta(days=s.refresh_ttl_days))
    return {
        "access_token": create_access_token(str(user_id), roles),  # sub = id: no email in the token
        "refresh_token": refresh,
        "token_type": "bearer",
        "expires_in": s.jwt_ttl_minutes * 60,
    }


@app.post("/v1/auth/login")
def login(body: LoginRequest):
    user = db.get_user_by_email(body.email)
    # same message whether the email or the password is wrong
    if not user or not user["is_active"] or not verify_password(body.password, user["password_hash"]):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "invalid credentials")
    return _issue_pair(user["id"], user["email"], user["roles"])


@app.post("/v1/auth/refresh")
def refresh(body: RefreshRequest):
    user = db.consume_refresh_token(_sha256(body.refresh_token))  # one-time use
    if not user:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "invalid or expired refresh token")
    return _issue_pair(user["id"], user["email"], user["roles"])


@app.post("/v1/auth/token")
def service_token(body: TokenRequest, x_api_key: str = Header(alias="X-API-Key")):
    account = db.get_service_account(body.client_id)
    if not account or not secrets.compare_digest(account["api_key_hash"], _sha256(x_api_key)):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "invalid service credentials")
    s = get_settings()
    return {
        "access_token": create_access_token(f"svc:{body.client_id}", [account["role"]]),
        "token_type": "bearer",
        "expires_in": s.jwt_ttl_minutes * 60,
    }


@app.get("/v1/auth/me")
def me(principal: Principal = Depends(current_principal)):
    if principal.subject.startswith("svc:"):
        return {"id": None, "email": None, "roles": list(principal.roles)}
    user = db.get_user_by_id(int(principal.subject))
    if not user:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "unknown user")
    return {"id": user["id"], "email": user["email"], "roles": user["roles"]}


@app.get("/v1/admin/users")
def list_users(_: Principal = Depends(require("users:read"))):
    return db.list_users()


@app.post("/v1/admin/users", status_code=201)
def create_user(body: UserCreate, request: Request, _: Principal = Depends(require("users:write"))):
    if db.get_user_by_email(body.email):
        raise HTTPException(status.HTTP_409_CONFLICT, "email already used")
    return db.create_user(body.email, hash_password(body.password), body.roles)


class RolesAssign(BaseModel):
    user_id: int
    roles: list[str] = Field(min_length=1)


@app.post("/v1/admin/roles")
def assign_roles(body: RolesAssign, _: Principal = Depends(require("roles:write"))):
    if not db.get_user_by_id(body.user_id):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "unknown user")
    return db.set_roles(body.user_id, body.roles)
