"""
Application settings using pydantic_settings.

This module defines all configuration settings for the trial matching system
using Pydantic BaseSettings for type safety and validation.
"""

from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings with environment variable support."""

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", case_sensitive=False
    )

    # API Keys and URLs
    openai_api_key: Optional[str] = None
    elasticsearch_url: Optional[str] = None
    redis_url: Optional[str] = None
    postgres_url: Optional[str] = None

    # LLM Settings
    llm_model: str = "gpt-4o"
    temperature: float = 0.0

    # Redis Settings
    redis_trial_criteria_key: str = "trial_criteria"

    # Elasticsearch Settings
    es_index_name: str = "aact_search"

    # Streamlit Settings
    streamlit_title: str = "Clinical Trial Matching System"
    streamlit_description: str = """
    This application helps match patients with appropriate clinical trials using advanced AI techniques.
    Enter a patient profile to find matching clinical trials.
    """

    # SQL Settings
    sql_host: Optional[str] = None
    sql_port: Optional[str] = None
    sql_database_aact: Optional[str] = None
    sql_username: Optional[str] = None
    sql_password: Optional[str] = None


# Create global settings instance
settings = Settings()
