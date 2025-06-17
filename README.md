# Clinical Trial Matching System

This project implements an end-to-end pipeline for matching patients with clinical trials using LLM-based components.

## Components

1. **Data Processing**
   - PostgreSQL to Elasticsearch transformation (existing)
   - Redis storage for trial criteria

2. **Target Trial Identification**
   - Patient data masking
   - Keyword extraction
   - Keyword enrichment
   - Elasticsearch-based trial search

3. **Criterion-Level Matching**
   - LLM-based criteria matching
   - Classification: eligible/ineligible/unknown

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set up environment variables in `.env`:
```
OPENAI_API_KEY=your_api_key
ELASTICSEARCH_URL=your_es_url
REDIS_URL=your_redis_url
POSTGRES_URL=your_postgres_url
```

3. Run the Streamlit app:
```bash
streamlit run app.py
```

## Project Structure

```
.
├── app.py                    # Streamlit application
├── config/
│   └── config.py            # Configuration settings
├── data_processing/
│   └── redis_loader.py      # Redis data loading utilities
├── target_identification/
│   ├── patient_masking.py   # Patient data masking
│   ├── keyword_extraction.py # Keyword extraction
│   └── keyword_enrichment.py # Keyword enrichment
├── criterion_matching/
│   └── matcher.py           # Criteria matching logic
└── utils/
    ├── llm_utils.py         # LLM utility functions
    └── prompts.py           # LLM prompts
``` 