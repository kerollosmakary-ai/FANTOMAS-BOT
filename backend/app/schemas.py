from pydantic import BaseModel
from typing import List, Optional

class CreateTokenRequest(BaseModel):
    owner_name: str
    balance: int = 1000
    allowed_providers: str = "groq,openrouter,deepseek,openai"
    expires_days: Optional[int] = None

class RechargeRequest(BaseModel):
    amount: int

class ChatRequest(BaseModel):
    message: str
    provider: str = "auto"
    model: Optional[str] = None
    addons: List[str] = []

class ChatResponse(BaseModel):
    response: str
    provider: str
    tokens_remaining: int
    addon_errors: list = []
