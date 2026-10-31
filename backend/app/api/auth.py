from datetime import timedelta
from hmac import compare_digest
from uuid import UUID

import jwt
from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db import get_db
from app.models import LoginSession, User
from app.security import (
    create_access_token,
    csrf_token,
    decode_access_token,
    hash_password,
    hash_refresh_token,
    new_refresh_token,
    utcnow,
    verify_password,
)

router = APIRouter(prefix="/api/v1/auth", tags=["authentication"])
ACCESS_COOKIE = "career_access"
REFRESH_COOKIE = "career_refresh"
CSRF_COOKIE = "career_csrf"
ACCESS_SECONDS = 15 * 60


class Credentials(BaseModel):
    email: EmailStr
    password: str = Field(min_length=12, max_length=128)


class UserView(BaseModel):
    id: str
    email: EmailStr

    model_config = {"from_attributes": True}


def _same_origin(request: Request) -> None:
    origin = request.headers.get("origin")
    if origin not in get_settings().frontend_origins:
        raise HTTPException(status_code=403, detail="Request origin was not allowed.")


def _csrf(request: Request) -> None:
    cookie = request.cookies.get(CSRF_COOKIE, "")
    header = request.headers.get("x-csrf-token", "")
    if not cookie or not header or not compare_digest(cookie, header):
        raise HTTPException(status_code=403, detail="CSRF check failed. Refresh the page and retry.")


def _set_session_cookies(response: Response, session: LoginSession, user: User, refresh: str) -> None:
    settings = get_settings()
    refresh_seconds = settings.refresh_token_days * 24 * 60 * 60
    common = {"secure": settings.cookie_secure, "samesite": "lax", "path": "/"}
    response.set_cookie(ACCESS_COOKIE, create_access_token(user.id, session.id), max_age=ACCESS_SECONDS, httponly=True, **common)
    response.set_cookie(REFRESH_COOKIE, refresh, max_age=refresh_seconds, httponly=True, **common)
    response.set_cookie(CSRF_COOKIE, csrf_token(), max_age=refresh_seconds, httponly=False, **common)


def current_user(request: Request, db: Session = Depends(get_db)) -> User:
    token = request.cookies.get(ACCESS_COOKIE)
    if not token:
        raise HTTPException(status_code=401, detail="Sign in to continue.")
    try:
        claims = decode_access_token(token)
        user_id, session_id = str(UUID(claims["sub"])), str(UUID(claims["sid"]))
    except (jwt.InvalidTokenError, KeyError, ValueError, TypeError):
        raise HTTPException(status_code=401, detail="Sign in to continue.") from None
    session = db.get(LoginSession, session_id)
    if not session or session.user_id != user_id or session.revoked_at or session.expires_at <= utcnow():
        raise HTTPException(status_code=401, detail="Your session has expired. Sign in again.")
    user = db.get(User, user_id)
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="Sign in to continue.")
    return user


def _create_session(db: Session, user: User) -> tuple[LoginSession, str]:
    settings = get_settings()
    session = LoginSession(
        user_id=user.id,
        refresh_token_hash="pending",
        expires_at=utcnow() + timedelta(days=settings.refresh_token_days),
    )
    db.add(session)
    db.flush()
    refresh = new_refresh_token(session.id)
    session.refresh_token_hash = hash_refresh_token(refresh)
    return session, refresh


@router.post("/register", response_model=UserView, status_code=status.HTTP_201_CREATED)
def register(payload: Credentials, request: Request, response: Response, db: Session = Depends(get_db)):
    _same_origin(request)
    email = str(payload.email).strip().casefold()
    if db.scalar(select(User.id).where(User.email == email)):
        raise HTTPException(status_code=409, detail="Unable to create account with those details.")
    user = User(email=email, password_hash=hash_password(payload.password))
    db.add(user)
    try:
        db.flush()
        session, refresh = _create_session(db, user)
        db.commit()
    except IntegrityError:
        db.rollback()
        if db.scalar(select(User.id).where(User.email == email)):
            raise HTTPException(status_code=409, detail="Unable to create account with those details.") from None
        raise
    _set_session_cookies(response, session, user, refresh)
    return user


@router.post("/login", response_model=UserView)
def login(payload: Credentials, request: Request, response: Response, db: Session = Depends(get_db)):
    _same_origin(request)
    email = str(payload.email).strip().casefold()
    user = db.scalar(select(User).where(User.email == email))
    if not user or not user.is_active or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Email or password is incorrect.")
    session, refresh = _create_session(db, user)
    db.commit()
    _set_session_cookies(response, session, user, refresh)
    return user


@router.get("/me", response_model=UserView)
def me(user: User = Depends(current_user)):
    return user


@router.post("/refresh", response_model=UserView)
def refresh_session(request: Request, response: Response, db: Session = Depends(get_db)):
    _same_origin(request)
    _csrf(request)
    value = request.cookies.get(REFRESH_COOKIE, "")
    try:
        session_id, _secret = value.split(".", 1)
        session_id = str(UUID(session_id))
    except (ValueError, AttributeError):
        raise HTTPException(status_code=401, detail="Sign in again to continue.") from None
    session = db.get(LoginSession, session_id)
    if (
        not session
        or session.revoked_at
        or session.expires_at <= utcnow()
        or not compare_digest(session.refresh_token_hash, hash_refresh_token(value))
    ):
        raise HTTPException(status_code=401, detail="Sign in again to continue.")
    user = db.get(User, session.user_id)
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="Sign in again to continue.")
    refresh = new_refresh_token(session.id)
    session.refresh_token_hash = hash_refresh_token(refresh)
    db.commit()
    _set_session_cookies(response, session, user, refresh)
    return user


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(request: Request, response: Response, db: Session = Depends(get_db)):
    _same_origin(request)
    _csrf(request)
    value = request.cookies.get(REFRESH_COOKIE, "")
    try:
        session_id, _secret = value.split(".", 1)
        session_id = str(UUID(session_id))
    except (ValueError, AttributeError):
        session_id = ""
    session = db.get(LoginSession, session_id) if session_id else None
    if session and compare_digest(session.refresh_token_hash, hash_refresh_token(value)):
        session.revoked_at = utcnow()
        db.commit()
    for name in (ACCESS_COOKIE, REFRESH_COOKIE, CSRF_COOKIE):
        response.delete_cookie(name, path="/", samesite="lax")
    response.status_code = status.HTTP_204_NO_CONTENT
    return response
