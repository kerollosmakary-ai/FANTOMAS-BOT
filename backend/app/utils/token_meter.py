from fastapi import HTTPException
from sqlalchemy.orm import Session
from app.models import ApiToken, UsageLog

def ensure_balance(api_token: ApiToken, cost: int):
    if api_token.balance < cost:
        raise HTTPException(status_code=402, detail="Insufficient token balance")

def charge(db: Session, api_token: ApiToken, amount: int, provider: str, model: str = "", success: bool = True, error: str = ""):
    api_token.balance -= amount
    log = UsageLog(
        api_token_id=api_token.id,
        provider=provider,
        model=model or "",
        charged_tokens=amount,
        success=success,
        error=error or "",
    )
    db.add(log)
    db.add(api_token)
    db.commit()
    db.refresh(api_token)
    return api_token.balance
