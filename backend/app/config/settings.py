"""Core application settings schema and environment variable loader."""
from typing import List, Union
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
import json


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )

    APP_NAME: str = "CrashSense AI Backend"
    APP_VERSION: str = "1.0.0"
    APP_ENV: str = Field(default="development")
    LOG_LEVEL: str = Field(default="INFO")

    HOST: str = "0.0.0.0"
    PORT: int = 8000
    API_V1_PREFIX: str = "/api/v1"

    CORS_ORIGINS: Union[List[str], str] = ["http://localhost:3000", "http://127.0.0.1:3000"]

    # MongoDB Atlas credentials
    MONGODB_URI: str = Field(default="")
    MONGODB_DATABASE: str = Field(default="crashsense")

    # Redis credentials
    REDIS_URL: str = Field(default="redis://localhost:6379/0")

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str):
            if v.startswith("[") and v.endswith("]"):
                try:
                    return json.loads(v)
                except Exception:
                    pass
            return [i.strip() for i in v.split(",") if i.strip()]
        return v


settings = Settings()

