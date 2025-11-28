from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    # Database (MariaDB)
    database_url: str = (
        "mysql+pymysql://salad_user:salad_password@localhost:3306/saladoverflow"
    )
    test_database_url: str = (
        "mysql+pymysql://salad_user:salad_password@localhost:3306/saladoverflow_test"
    )

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # JWT
    secret_key: str = "dev-secret-key-change-in-production-please"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30

    # Application
    debug: bool = True
    api_version: str = "v1"
    app_name: str = "SaladOverflow API"

    # CORS
    allowed_origins: List[str] = [
        "https://overflow.saladsync.ca",
        "http://overflow.saladsync.ca",
        "http://localhost:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:3001",
        "http://192.168.1.242:5050",
        "https://192.168.1.242:5443",
    ]

    # Email Configuration
    smtp_host: str = "smtp.gmail.com"
    smtp_port: int = 587
    smtp_username: str = ""
    smtp_password: str = ""
    smtp_from_email: str = ""
    smtp_from_name: str = "SaladOverflow Team"
    smtp_use_tls: bool = True
    frontend_url: str = "https://overflow.saladsync.ca"
    backend_url: str = "https://overflow.saladsync.ca"

    # GitHub OAuth
    github_client_id: str = ""
    github_client_secret: str = ""
    github_redirect_uri: str = (
        "https://overflow.saladsync.ca/api/v1/auth/github/callback"
    )

    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()
