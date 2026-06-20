from dataclasses import dataclass, field
from typing import Any

@dataclass
class AddonResult:
    ok: bool
    context: str = ""
    data: dict[str, Any] = field(default_factory=dict)
    error: str = ""

class BaseAddon:
    name = "base"
    enabled = True
    timeout_seconds = 8
    cost = 0

    async def before_chat(self, user_message: str, metadata: dict) -> AddonResult:
        return AddonResult(ok=True)

    async def after_chat(self, ai_response: str, metadata: dict) -> AddonResult:
        return AddonResult(ok=True)
