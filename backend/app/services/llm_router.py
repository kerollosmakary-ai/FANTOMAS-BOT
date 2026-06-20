from typing import AsyncGenerator
import httpx
from app.config import settings

class ProviderError(Exception):
    pass

class LLMRouter:
    def model_for(self, provider: str, requested_model: str | None = None) -> str:
        if requested_model:
            return requested_model
        return {
            "openai": settings.OPENAI_MODEL,
            "groq": settings.GROQ_MODEL,
            "openrouter": settings.OPENROUTER_MODEL,
            "deepseek": settings.DEEPSEEK_MODEL,
        }.get(provider, settings.GROQ_MODEL)

    def configured(self, provider: str) -> bool:
        return {
            "openai": bool(settings.OPENAI_API_KEY),
            "groq": bool(settings.GROQ_API_KEY),
            "openrouter": bool(settings.OPENROUTER_API_KEY),
            "deepseek": bool(settings.DEEPSEEK_API_KEY),
        }.get(provider, False)

    def endpoint_and_headers(self, provider: str):
        if provider == "openai":
            return "https://api.openai.com/v1/chat/completions", {"Authorization": f"Bearer {settings.OPENAI_API_KEY}"}
        if provider == "groq":
            return "https://api.groq.com/openai/v1/chat/completions", {"Authorization": f"Bearer {settings.GROQ_API_KEY}"}
        if provider == "openrouter":
            return "https://openrouter.ai/api/v1/chat/completions", {
                "Authorization": f"Bearer {settings.OPENROUTER_API_KEY}",
                "HTTP-Referer": "http://localhost",
                "X-Title": settings.APP_NAME,
            }
        if provider == "deepseek":
            return "https://api.deepseek.com/chat/completions", {"Authorization": f"Bearer {settings.DEEPSEEK_API_KEY}"}
        raise ProviderError(f"Unknown provider: {provider}")

    async def complete(self, provider: str, messages: list[dict], model: str | None = None) -> str:
        if not self.configured(provider):
            raise ProviderError(f"Provider {provider} is not configured")
        url, headers = self.endpoint_and_headers(provider)
        payload = {"model": self.model_for(provider, model), "messages": messages, "temperature": 0.7}
        async with httpx.AsyncClient(timeout=60) as client:
            resp = await client.post(url, headers={**headers, "Content-Type": "application/json"}, json=payload)
        if resp.status_code >= 400:
            raise ProviderError(f"{provider} error {resp.status_code}: {resp.text[:300]}")
        data = resp.json()
        return data["choices"][0]["message"]["content"]

    async def complete_with_fallback(self, preferred: str, allowed: list[str], messages: list[dict], model: str | None = None):
        fallback = [p.strip() for p in settings.FALLBACK_PROVIDERS.split(",") if p.strip()]
        providers = []
        if preferred and preferred != "auto":
            providers.append(preferred)
        providers += fallback
        providers = [p for i, p in enumerate(providers) if p in allowed and p not in providers[:i]]

        errors = []
        for provider in providers:
            try:
                content = await self.complete(provider, messages, model if provider == preferred else None)
                return {"content": content, "provider": provider, "errors": errors}
            except Exception as e:
                errors.append({"provider": provider, "error": str(e)})
        raise ProviderError(f"All providers failed: {errors}")

    async def fake_stream_text(self, text: str) -> AsyncGenerator[str, None]:
        words = text.split(" ")
        for word in words:
            yield word + " "

llm_router = LLMRouter()
