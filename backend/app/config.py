"""
RepoBlueprint AI - Configuration Settings
"""

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings with environment variable support."""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )
    
    # Application
    app_name: str = "RepoBlueprint AI"
    app_version: str = "3.0.0"
    debug: bool = False
    
    # Server
    host: str = "0.0.0.0"
    port: int = 8000
    
    # Ollama LLM Configuration
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "qwen2.5-coder:32b"
    ollama_timeout: int = 300  # 5 minutes for large repos
    
    # Analysis Settings
    max_repo_size_mb: int = 500
    max_files_to_parse: int = 1000
    analysis_timeout: int = 600  # 10 minutes
    
    # Paths
    repos_cache_dir: Path = Path(".repos")
    analysis_cache_dir: Path = Path(".analysis_cache")
    
    # Supported Languages
    supported_languages: list[str] = [
        "python",
        "typescript", 
        "javascript",
        "go",
        "rust",
        "java",
    ]
    
    # Audience Profiles
    audience_profiles: list[str] = [
        "executive",
        "engineer", 
        "security_analyst",
        "sales_engineer",
        "new_hire",
        "investor",
    ]
    
    def get_repos_path(self) -> Path:
        """Get or create repos cache directory."""
        self.repos_cache_dir.mkdir(parents=True, exist_ok=True)
        return self.repos_cache_dir
    
    def get_analysis_path(self) -> Path:
        """Get or create analysis cache directory."""
        self.analysis_cache_dir.mkdir(parents=True, exist_ok=True)
        return self.analysis_cache_dir


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
