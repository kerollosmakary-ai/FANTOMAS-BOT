import asyncio
from app.addons.rag_addon import RAGAddon

class AddonRegistry:
    def __init__(self):
        self.addons = {}

    def register(self, addon):
        self.addons[addon.name] = addon

    def get_enabled(self, names: list[str] | None):
        if not names:
            return []
        return [self.addons[n] for n in names if n in self.addons and self.addons[n].enabled]

    def estimate_cost(self, names: list[str] | None) -> int:
        return sum(addon.cost for addon in self.get_enabled(names))

    async def run_before_chat(self, message: str, metadata: dict, names: list[str] | None):
        contexts = []
        errors = []
        for addon in self.get_enabled(names):
            try:
                result = await asyncio.wait_for(addon.before_chat(message, metadata), timeout=addon.timeout_seconds)
                if result.ok and result.context:
                    contexts.append(f"[{addon.name}]\n{result.context}")
                elif not result.ok:
                    errors.append({"addon": addon.name, "error": result.error})
            except Exception as e:
                errors.append({"addon": addon.name, "error": str(e)})
        return {"context": "\n\n".join(contexts), "errors": errors}

addon_registry = AddonRegistry()
addon_registry.register(RAGAddon())
