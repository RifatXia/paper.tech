from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    supermemory_key: str = ""
    actian_db_url: str = ""
    modal_token_id: str = ""
    modal_token_secret: str = ""
    modal_llm_endpoint: str = ""
    modal_embed_endpoint: str = ""
    openalex_email: str = ""
    openai_api_key: str = ""
    github_token: str = ""
    google_api_key: str = ""
    groq_api_key: str = ""
    frontend_url: str = "http://localhost:5173"
    environment: str = "development"

    model_config = {"env_file": ["../.env", ".env"], "extra": "ignore"}


settings = Settings()
