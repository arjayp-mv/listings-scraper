# =============================================================================
# Amazon Reviews Scraper - Global Configuration
# =============================================================================
# Purpose: Load and validate environment variables for the application
# Public API: settings (Settings instance)
# Dependencies: pydantic-settings, python-dotenv
# =============================================================================

from functools import lru_cache
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.

    All settings can be overridden via .env file or environment variables.
    """

    # ===== Server Configuration =====
    host: str = "0.0.0.0"
    port: int = 8080

    # ===== Apify Configuration =====
    apify_api_key: str = ""

    # ===== Database Configuration =====
    db_host: str = "localhost"
    db_port: int = 3306
    db_user: str = "root"
    db_password: str = ""
    db_name: str = "amazon_reviews_scraper"

    # ===== Worker Configuration =====
    worker_interval_seconds: int = 30
    apify_delay_seconds: int = 10

    # ===== Pagination =====
    max_page_size: int = 50
    default_page_size: int = 20

    @property
    def database_url(self) -> str:
        """
        Generate SQLAlchemy database URL for MySQL.

        Returns:
            MySQL connection string with pymysql driver
        """
        password_part = f":{self.db_password}" if self.db_password else ""
        return (
            f"mysql+pymysql://{self.db_user}{password_part}"
            f"@{self.db_host}:{self.db_port}/{self.db_name}"
            "?charset=utf8mb4"
        )

    class Config:
        env_file = "../.env"
        env_file_encoding = "utf-8"
        case_sensitive = False


@lru_cache
def get_settings() -> Settings:
    """
    Get cached settings instance.

    Returns:
        Settings: Application settings loaded from environment
    """
    return Settings()


# Global settings instance
settings = get_settings()
