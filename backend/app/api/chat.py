from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import ApiToken, Message
from app.schemas import ChatRequest, ChatResponse
from app.config import settings
from app.utils.security import get_current_api_token
from app.utils.token_meter import ensure_balance, charge
from app.addons.registry import addon_registry
from app.services.llm_router import llm_router

router = APIRouter(tags=["chat"])

@router.post("/chat", response_model=ChatResponse)
async def chat(payload: ChatRequest, db: Session = Depends(get_db), api_token: ApiToken = Depends(get_current_api_token)):
    allowed = [p.strip() for p in api_token.allowed_providers.split(",") if p.strip()]
    addon_cost = addon_registry.estimate_cost(payload.addons)
    total_cost = settings.REQUEST_BASE_COST + addon_cost
    ensure_balance(api_token, total_cost)

    addon_result = await addon_registry.run_before_chat(payload.message, {"token_id": api_token.id}, payload.addons)
    messages = [
        {"role": "system", "content": "You are a helpful assistant. Normal chat must always work. Optional addon context may be missing or unreliable."},
        {"role": "system", "content": f"Optional context:\n{addon_result['context']}"},
        {"role": "user", "content": payload.message},
    ]
    result = await llm_router.complete_with_fallback(payload.provider, allowed, messages, payload.model)
    remaining = charge(db, api_token, total_cost, result["provider"], payload.model or "")

    db.add(Message(api_token_id=api_token.id, role="user", content=payload.message, provider=result["provider"]))
    db.add(Message(api_token_id=api_token.id, role="assistant", content=result["content"], provider=result["provider"]))
    db.commit()

    return ChatResponse(response=result["content"], provider=result["provider"], tokens_remaining=remaining, addon_errors=addon_result["errors"] + result["errors"])
