from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    ollama_url: str = "http://localhost:11434"
    ollama_model: str = "llama3.1:8b"
    ollama_fast_model: str = ""
    ollama_reasoning_model: str = ""
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    boris_api_key: str = "change-this-for-local-use"
    boris_data_dir: Path = Path("./data")
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
settings = Settings()
