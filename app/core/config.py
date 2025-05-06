import os
from dotenv import load_dotenv
from pydantic_settings import BaseSettings

# Carrega as variáveis do .env para o ambiente
load_dotenv()

class Settings(BaseSettings):
    DB_USER: str = os.getenv("DB_USER", "postgres")
    DB_PASSWORD: str = os.getenv("DB_PASSWORD", "password")
    DB_HOST: str = os.getenv("DB_HOST", "localhost")
    DB_PORT: int = int(os.getenv("DB_PORT", 5432))
    DB_NAME: str = os.getenv("DB_NAME", "mentoria_db")

    DATABASE_URL: str = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

    SECRET_KEY: str = os.getenv("SECRET_KEY", "a_very_secret_key")
    ALGORITHM: str = os.getenv("ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 30))

settings = Settings()

# Para teste rápido, imprima as configurações ao carregar o módulo
# print(f"DATABASE_URL: {settings.DATABASE_URL}")
# print(f"SECRET_KEY: {settings.SECRET_KEY}")