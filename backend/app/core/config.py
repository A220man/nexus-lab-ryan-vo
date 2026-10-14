from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field
from typing import Optional


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application
    app_name: str = "nexus-lab-ryan-vo"
    version: str = "1.0.0"
    host: str = "127.0.0.1"
    port: int = 8000
    log_level: str = "INFO"

    # Database
    database_url: str = "sqlite:///./data.db"

    # Security
    secret_key: str = Field(..., min_length=32)

    # Keycloak OIDC
    keycloak_url: str = "http://localhost:8080"
    keycloak_realm: str = "nexus-lab"
    keycloak_client_id: str = "nexus-lab"
    keycloak_client_secret: str = ""

    # LLM Provider
    llm_api_key: Optional[str] = None
    llm_provider: str = "openai-compatible"
    llm_model: str = "gpt-4o-mini"
    llm_base_url: str = "https://api.openai.com/v1"

    # ChromaDB
    chroma_url: str = "http://localhost:8001"

    # Demo mode
    demo_mode: bool = False

    # Frontend URL (for CORS)
    frontend_url: str = "http://localhost:5173"

    @property
    def keycloak_issuer(self) -> str:
        return f"{self.keycloak_url.rstrip('/')}/realms/{self.keycloak_realm}"

    @property
    def keycloak_jwks_url(self) -> str:
        return f"{self.keycloak_issuer}/protocol/openid-connect/certs"

    @property
    def keycloak_auth_url(self) -> str:
        return f"{self.keycloak_issuer}/protocol/openid-connect/auth"

    @property
    def keycloak_token_url(self) -> str:
        return f"{self.keycloak_issuer}/protocol/openid-connect/token"

    @property
    def keycloak_userinfo_url(self) -> str:
        return f"{self.keycloak_issuer}/protocol/openid-connect/userinfo"

    @property
    def keycloak_logout_url(self) -> str:
        return f"{self.keycloak_issuer}/protocol/openid-connect/logout"


@lru_cache
def get_settings() -> Settings:
    return Settings()