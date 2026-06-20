from app.addons.base import BaseAddon, AddonResult

class RAGAddon(BaseAddon):
    name = "rag"
    timeout_seconds = 5
    cost = 3

    async def before_chat(self, user_message: str, metadata: dict) -> AddonResult:
        # Placeholder: safe by design. Replace later with Chroma/Google Drive RAG.
        return AddonResult(
            ok=True,
            context="RAG addon is enabled, but no documents are indexed yet. Answer normally if context is empty."
        )
