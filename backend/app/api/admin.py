from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import ApiToken, UsageLog
from app.schemas import CreateTokenRequest, RechargeRequest
from app.utils.security import require_admin, generate_plain_token, hash_token, token_preview

router = APIRouter(prefix="/admin", tags=["admin"])

@router.post("/tokens")
def create_token(payload: CreateTokenRequest, db: Session = Depends(get_db), _: bool = Depends(require_admin)):
    plain = generate_plain_token()
    expires_at = datetime.utcnow() + timedelta(days=payload.expires_days) if payload.expires_days else None
    row = ApiToken(
        owner_name=payload.owner_name,
        token_hash=hash_token(plain),
        prefix=token_preview(plain),
        balance=payload.balance,
        allowed_providers=payload.allowed_providers,
        expires_at=expires_at,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return {"id": row.id, "owner_name": row.owner_name, "api_token": plain, "balance": row.balance, "prefix": row.prefix}

@router.get("/tokens")
def list_tokens(db: Session = Depends(get_db), _: bool = Depends(require_admin)):
    rows = db.query(ApiToken).order_by(ApiToken.id.desc()).all()
    return [{"id": r.id, "owner_name": r.owner_name, "prefix": r.prefix, "balance": r.balance, "status": r.status, "allowed_providers": r.allowed_providers, "created_at": r.created_at} for r in rows]

@router.post("/tokens/{token_id}/recharge")
def recharge(token_id: int, payload: RechargeRequest, db: Session = Depends(get_db), _: bool = Depends(require_admin)):
    row = db.get(ApiToken, token_id)
    if not row:
        raise HTTPException(404, "Token not found")
    row.balance += payload.amount
    db.commit()
    return {"id": row.id, "balance": row.balance}

@router.post("/tokens/{token_id}/revoke")
def revoke(token_id: int, db: Session = Depends(get_db), _: bool = Depends(require_admin)):
    row = db.get(ApiToken, token_id)
    if not row:
        raise HTTPException(404, "Token not found")
    row.status = "revoked"
    db.commit()
    return {"id": row.id, "status": row.status}

@router.get("/usage")
def usage(db: Session = Depends(get_db), _: bool = Depends(require_admin)):
    rows = db.query(UsageLog).order_by(UsageLog.id.desc()).limit(100).all()
    return [{"id": r.id, "api_token_id": r.api_token_id, "provider": r.provider, "model": r.model, "charged_tokens": r.charged_tokens, "success": r.success, "error": r.error, "created_at": r.created_at} for r in rows]
