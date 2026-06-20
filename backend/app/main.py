import json
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from app.config import settings
from app.database import init_db, SessionLocal
from app.models import Message
from app.api.admin import router as admin_router
from app.api.chat import router as chat_router
from app.routers.whatsapp import router as whatsapp_router
from app.utils.security import get_api_token_from_value
from app.utils.token_meter import ensure_balance, charge
from app.addons.registry import addon_registry
from app.services.llm_router import llm_router

app = FastAPI(title=settings.APP_NAME, version="1.0.0")

origins = [x.strip() for x in settings.CORS_ORIGINS.split(",") if x.strip()]
app.add_middleware(CORSMiddleware, allow_origins=origins, allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

@app.on_event("startup")
def startup():
    init_db()

app.include_router(admin_router)
app.include_router(chat_router)
app.include_router(whatsapp_router)

@app.get("/health")
def health():
    return {
        "status": "ok",
        "providers": {
            "openai": "configured" if settings.OPENAI_API_KEY else "missing_key",
            "groq": "configured" if settings.GROQ_API_KEY else "missing_key",
            "openrouter": "configured" if settings.OPENROUTER_API_KEY else "missing_key",
            "deepseek": "configured" if settings.DEEPSEEK_API_KEY else "missing_key",
        },
        "addons": {name: "enabled" if addon.enabled else "disabled" for name, addon in addon_registry.addons.items()},
    }

@app.websocket("/ws/chat")
async def ws_chat(websocket: WebSocket):
    await websocket.accept()
    raw_token = websocket.query_params.get("token", "")
    db: Session = SessionLocal()
    try:
        api_token = get_api_token_from_value(raw_token, db)
        await websocket.send_json({"type": "ready", "tokens_remaining": api_token.balance})
        while True:
            data = json.loads(await websocket.receive_text())
            user_message = data.get("content") or data.get("message") or ""
            provider = data.get("provider", "auto")
            model = data.get("model")
            addons = data.get("addons", [])
            if not user_message.strip():
                await websocket.send_json({"type": "error", "message": "Empty message"})
                continue

            allowed = [p.strip() for p in api_token.allowed_providers.split(",") if p.strip()]
            total_cost = settings.REQUEST_BASE_COST + addon_registry.estimate_cost(addons)
            ensure_balance(api_token, total_cost)

            addon_result = await addon_registry.run_before_chat(user_message, {"token_id": api_token.id}, addons)
            messages = [
                {"role": "system", "content": "You are a helpful assistant. Normal chat must always work even if addons fail."},
                {"role": "system", "content": f"Optional context:\n{addon_result['context']}"},
                {"role": "user", "content": user_message},
            ]

            try:
                result = await llm_router.complete_with_fallback(provider, allowed, messages, model)
                for chunk in result["content"].split(" "):
                    await websocket.send_json({"type": "chunk", "content": chunk + " "})
                remaining = charge(db, api_token, total_cost, result["provider"], model or "")
                db.add(Message(api_token_id=api_token.id, role="user", content=user_message, provider=result["provider"]))
                db.add(Message(api_token_id=api_token.id, role="assistant", content=result["content"], provider=result["provider"]))
                db.commit()
                await websocket.send_json({"type": "done", "provider": result["provider"], "tokens_remaining": remaining, "addon_errors": addon_result["errors"] + result["errors"]})
            except Exception as e:
                await websocket.send_json({"type": "error", "message": str(e), "addon_errors": addon_result["errors"]})
    except WebSocketDisconnect:
        pass
    except Exception as e:
        await websocket.send_json({"type": "error", "message": str(e)})
    finally:
        db.close()
