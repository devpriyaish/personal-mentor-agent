"""
Configuration settings for Personal Mentor Agent
"""
import os
from dataclasses import dataclass
from typing import Optional


@dataclass
class DatabaseConfig:
    """Database configuration settings"""
    qdrant_host: str = "localhost"
    qdrant_port: int = 6333
    qdrant_collection: str = "mentor_memories"
    sqlite_db_path: str = "mentor_data.db"
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    vector_size: int = 384


@dataclass
class LLMConfig:
    """LLM configuration settings"""
    model_name: str = "gpt-3.5-turbo"
    temperature: float = 0.7
    max_tokens: int = 1000
    api_key: Optional[str] = None


@dataclass
class AppConfig:
    """Application configuration settings"""
    app_title: str = "Personal Mentor Agent"
    page_icon: str = "🧠"
    layout: str = "wide"
    max_memory_context: int = 10
    reflection_interval_days: int = 1
    
    
class Config:
    """Main configuration class - Singleton Pattern"""
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.database = DatabaseConfig()
            cls._instance.llm = LLMConfig()
            cls._instance.app = AppConfig()
        return cls._instance
    
    @classmethod
    def load_from_env(cls):
        """Load configuration from environment variables"""
        instance = cls()
        instance.llm.api_key = os.getenv("OPENAI_API_KEY")
        instance.database.qdrant_host = os.getenv("QDRANT_HOST", "localhost")
        instance.database.qdrant_port = int(os.getenv("QDRANT_PORT", "6333"))
        return instance