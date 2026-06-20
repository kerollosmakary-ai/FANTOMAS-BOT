from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    APP_NAME: str = "Advanced AI Bot"
    ENV: str = "dev"
    ADMIN_KEY: str = "change-me-admin-key"
    DATABASE_URL: str = "sqlite:///./data/app.db"
    CORS_ORIGINS: str = "http://localhost:3000,http://localhost:5173"

    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-4o-mini"

    GROQ_API_KEY: str = ""
    GROQ_MODEL: str = "llama-3.1-8b-instant"

    OPENROUTER_API_KEY: str = ""
    OPENROUTER_MODEL: str = "meta-llama/llama-3.1-8b-instruct:free"

    DEEPSEEK_API_KEY: str = ""
    DEEPSEEK_MODEL: str = "deepseek-chat"

    DEFAULT_PROVIDER: str = "groq"
    FALLBACK_PROVIDERS: str = "groq,openrouter,deepseek,openai"
    REQUEST_BASE_COST: int = 5
    RAG_ADDON_COST: int = 3

    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()
