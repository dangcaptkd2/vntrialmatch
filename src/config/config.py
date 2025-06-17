import os

from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# API Keys and URLs
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
ELASTICSEARCH_URL = os.getenv("ELASTICSEARCH_URL")
REDIS_URL = os.getenv("REDIS_URL")
POSTGRES_URL = os.getenv("POSTGRES_URL")

# LLM Settings
LLM_MODEL = "gpt-4-turbo-preview"  # or "ollama/llama2" for local model
TEMPERATURE = 0.0

# Redis Settings
REDIS_TRIAL_CRITERIA_KEY = "trial_criteria"

# Elasticsearch Settings
ES_INDEX_NAME = "clinical_trials"

# Streamlit Settings
STREAMLIT_TITLE = "Clinical Trial Matching System"
STREAMLIT_DESCRIPTION = """
This application helps match patients with appropriate clinical trials using advanced AI techniques.
Enter a patient profile to find matching clinical trials.
"""

# SQL Settings
SQL_HOST = os.getenv("SQL_HOST")
SQL_PORT = os.getenv("SQL_PORT")
SQL_DATABASE_AACT = os.getenv("SQL_DATABASE_AACT")
SQL_USERNAME = os.getenv("SQL_USERNAME")
SQL_PASSWORD = os.getenv("SQL_PASSWORD")
