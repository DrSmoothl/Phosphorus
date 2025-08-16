"""Configuration management for Phosphorus."""

from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings."""

    # Server configuration
    host: str = Field("0.0.0.0", description="Server host")
    port: int = Field(8000, description="Server port")
    debug: bool = Field(False, description="Debug mode")

    # Logging configuration
    log_level: str = Field("INFO", description="Log level")
    log_file: str | None = Field(None, description="Log file path")

    # API configuration
    api_title: str = Field("Phosphorus", description="API title")
    api_description: str = Field(
        "JPlag based Plagiarism Checker Server for Hydro", description="API description"
    )
    api_version: str = Field("0.1.0", description="API version")

    # JPlag configuration
    jplag_jar_path: str = Field(
        "lib/jplag-6.2.0.jar", description="Path to JPlag JAR file"
    )
    jplag_timeout: int = Field(300, description="JPlag execution timeout in seconds")

    model_config = {"env_file": ".env", "env_prefix": "PHOSPHORUS_"}


# Global settings instance
settings = Settings()
