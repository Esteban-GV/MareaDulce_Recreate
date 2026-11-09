import os
from pydantic import BaseModel

class Settings(BaseModel):
    PROJECT_NAME: str = "Marea Dulce Cloud-Native API"
    VERSION: str = os.getenv("APP_VERSION", "1.0.0")
    ENV: str = os.getenv("ENV", "production")
    DEMO_MODE: bool = os.getenv("DEMO_MODE", "true").lower() in ("true", "1", "yes")
    
    # Base de datos SQLite
    DATABASE_PATH: str = os.getenv("DATABASE_PATH", "/data/marea_dulce.db")
    
    # Seguridad JWT y Roles
    JWT_SECRET: str = os.getenv("JWT_SECRET", "marea-dulce-secret-key-recreate-k8s-2026")
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "1440"))
    
    # Credenciales iniciales del Administrador (variables de entorno, nunca hardcodeadas en prod)
    ADMIN_EMAIL: str = os.getenv("ADMIN_EMAIL", "admin@mareadulce.com")
    ADMIN_PASSWORD: str = os.getenv("ADMIN_PASSWORD", "AdminMarea2026!")
    ADMIN_NAME: str = "Administrador Marea Dulce"

settings = Settings()
