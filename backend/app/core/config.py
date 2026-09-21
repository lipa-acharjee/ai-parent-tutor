from functools import lru_cache

from pydantic_settings import (
    BaseSettings,
    SettingsConfigDict,
)


class Settings(BaseSettings):

    # =====================================================
    # Application
    # =====================================================

    app_name: str = "AI Parent Tutor"

    environment: str = "development"

    debug: bool = False

    secret_key: str

    access_token_minutes: int = 30

    refresh_token_days: int = 30

    # =====================================================
    # Database
    # =====================================================

    database_url: str = (
        "postgresql+asyncpg://"
        "postgres:postgres@db:5432/parent_tutor"
    )

    # =====================================================
    # Redis
    # =====================================================

    redis_url: str = (
        "redis://redis:6379/0"
    )

    # =====================================================
    # AI / LLM
    # =====================================================

    groq_api_key: str

    llm_model: str = (
        "openai/gpt-oss-120b"
    )

    embedding_model: str = (
        "sentence-transformers/"
        "all-MiniLM-L6-v2"
    )

    # =====================================================
    # Object Storage / MinIO
    # =====================================================

    s3_endpoint_url: str | None = None

    s3_public_endpoint_url: str | None = None

    s3_bucket: str = "parent-tutor"

    s3_access_key: str | None = None

    s3_secret_key: str | None = None

    aws_region: str = "ap-south-1"

    # =====================================================
    # Uploads
    # =====================================================

    max_upload_mb: int = 50

    # =====================================================
    # CORS
    # =====================================================

    allowed_origins: str = (
        "http://localhost:3000,"
        "http://localhost:8080"
    )

    # =====================================================
    # Observability
    # =====================================================

    otel_enabled: bool = True

    prometheus_enabled: bool = True

    # =====================================================
    # Video
    # =====================================================

    video_provider: str = "local"

    video_storage: str = "minio"

    video_max_duration_seconds: int = 600

    video_default_voice: str = (
        "en-US-JennyNeural"
    )

    video_width: int = 1280

    video_height: int = 720

    video_fps: int = 30

    # =====================================================
    # Google OAuth
    # =====================================================

    google_client_id: str | None = None

    google_client_secret: str | None = None

    google_redirect_uri: str = (
        "http://localhost:8000/"
        "api/v1/auth/google/callback"
    )

    # =====================================================
    # Pydantic Settings
    # =====================================================

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()