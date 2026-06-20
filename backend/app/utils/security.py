import hashlib
import secrets
from datetime import datetime, timedelta
from fastapi import Header, HTTPException, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import ApiToken
from app.config import settings

TOKEN_PREFIX = "sk_live_"

def generate_plain_token() -> str:
    return TOKEN_PREFIX + secrets.token_urlsafe(32)

def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()

def token_preview(token: str) -> str:
    return token[:16]

def require_admin(x_admin_key: str = Header(default="")):
    if x_admin_key != settings.ADMIN_KEY:
        raise HTTPException(status_code=401, detail="Invalid admin key")
    return True

def get_api_token_from_value(raw_token: str, db: Session) -> ApiToken:
    token_hash = hash_token(raw_token)
    api_token = db.query(ApiToken).filter(ApiToken.token_hash == token_hash).first()
    if not api_token:
        raise HTTPException(status_code=401, detail="Invalid API token")
    if api_token.status != "active":
        raise HTTPException(status_code=403, detail="API token is not active")
    if api_token.expires_at and datetime.utcnow() > api_token.expires_at:
        raise HTTPException(status_code=403, detail="API token expired")
    return api_token

def get_current_api_token(authorization: str = Header(default=""), db: Session = Depends(get_db)) -> ApiToken:
    if not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="Missing Bearer token")
    raw = authorization.split(" ", 1)[1].strip()
    return get_api_token_from_value(raw, db)
