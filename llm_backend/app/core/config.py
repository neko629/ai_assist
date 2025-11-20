from pydantic_settings import BaseSettings
from enum import Enum
from pathlib import Path

ROOT_DIR = Path(__file__).parent.parent.parent
ENV_FILE = ROOT_DIR / ".env"

class ServiceType(str, Enum):
    DEEPSEEK = "deepseek"
    OLLAMA = "ollama"

class Settings(BaseSettings):
    # Database settings
    DB_HOST: str
    DB_PORT: int
    DB_USER: str
    DB_PASSWORD: str
    DB_NAME: str

    # JWT settings
    SECRET_KEY: str = "your-secret-key"  # 在生产环境中使用安全的密钥
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    @property
    def DATABASE_URL(self) -> str:
        return f"mysql+aiomysql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"

    class Config:
        env_file = ENV_FILE
        env_file_encoding = 'utf-8'
        case_sensitive = True

    # Redis settings
    REDIS_HOST: str
    REDIS_PORT: int
    REDIS_DB: int = 0
    REDIS_PASSWORD: str = ''
    REDIS_CACHE_EXPIRE: int = 3600  # 缓存过期时间，单位秒
    REDIS_CACHE_THRESHOLD: float = 0.8  # 语义相似度阈值

    @property
    def REDIS_URL(self) -> str:
        """构建Redis URL"""
        auth = f":{self.REDIS_PASSWORD}@" if self.REDIS_PASSWORD else ""
        return f"redis://{auth}{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"

    # Ollama settings
    OLLAMA_BASE_URL: str
    OLLAMA_CHAT_MODEL: str
    OLLAMA_REASON_MODEL: str
    OLLAMA_EMBEDDING_MODEL: str
    OLLAMA_AGENT_MODEL: str

    # Deepseek settings
    DEEPSEEK_API_KEY: str
    DEEPSEEK_BASE_URL: str
    DEEPSEEK_MODEL: str

    # Service selection
    CHAT_SERVICE: ServiceType = ServiceType.DEEPSEEK
    REASON_SERVICE: ServiceType = ServiceType.OLLAMA
    AGENT_SERVICE: ServiceType = ServiceType.DEEPSEEK

settings = Settings()
