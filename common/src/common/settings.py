import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    """Application settings loaded once at startup from environment variables."""

    app_environment: str
    database_url: str

    # Azure Services
    azure_foundry_endpoint: str
    azure_foundry_proj_default_api_key: str
    azure_blob_storage_connection_string: str
    azure_foundry_api_version: str = "2024-12-01-preview"

    # Optional settings
    log_level: str = "INFO"
    cors_allowed_origins: str = ""


def load_settings() -> Settings:
    """
    Load settings from environment variables once at startup.
    Fails fast with clear error messages if required variables are missing.
    """
    missing = []

    # Required environment variables
    required_vars = {
        "APP_ENVIRONMENT": "app_environment",
        "DATABASE_URL": "database_url",
        "AZURE_FOUNDRY_ENDPOINT": "azure_foundry_endpoint",
        "AZURE_FOUNDRY_PROJ_DEFAULT_API_KEY": "azure_foundry_proj_default_api_key",
        "AZURE_BLOB_STORAGE_CONNECTION_STRING": "azure_blob_storage_connection_string",
    }

    config = {}

    # Validate required vars
    for env_var, field_name in required_vars.items():
        value = os.getenv(env_var)
        if not value:
            missing.append(env_var)
        else:
            config[field_name] = value

    if missing:
        raise ValueError(
            f"Missing required environment variables: {', '.join(missing)}"
        )

    # Optional vars with defaults
    config["log_level"] = os.getenv("LOG_LEVEL", "INFO")
    config["cors_allowed_origins"] = os.getenv("CORS_ALLOWED_ORIGINS", "")

    return Settings(**config)
