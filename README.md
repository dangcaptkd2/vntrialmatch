# Clinical Trial Matching System

This system helps match patients with appropriate clinical trials using advanced AI techniques.

## Features

- **Patient Profile Processing**: Masks sensitive information and extracts relevant medical keywords
- **Trial Search**: Searches ClinicalTrials.gov data using Elasticsearch
- **Criteria Matching**: Uses LLM to evaluate patient eligibility against trial criteria
- **Comprehensive Results**: Provides detailed matching scores and explanations

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set up environment variables in `.env`:
```
OPENAI_API_KEY=your_openai_api_key
ELASTICSEARCH_URL=http://localhost:9200
```

3. Ensure Elasticsearch is running with the AACT data indexed

## Usage

### Command Line Interface

Run the main matching pipeline:

```bash
python main.py
```

With custom parameters:

```bash
python main.py \
  --patient-profile data/patient_data/patient.1.1.txt \
  --output results/my_results.json \
  --max-trials 30 \
  --max-criteria 10
```

### Parameters

- `--patient-profile`: Path to patient profile file (default: `data/patient_data/patient.1.1.txt`)
- `--output`: Path to save results (default: `results/trial_matching_results.json`)
- `--max-trials`: Maximum number of trials to analyze (default: 20)
- `--max-criteria`: Maximum criteria to evaluate per trial (default: 5)

### Output

The system generates:
1. **Console Summary**: Top 5 matching trials with scores
2. **JSON Results**: Detailed results saved to specified file
3. **Log File**: `trial_matching.log` with detailed execution logs

### Example Output

```
================================================================================
CLINICAL TRIAL MATCHING RESULTS SUMMARY
================================================================================

Total trials analyzed: 20
Trials with at least one eligible criterion: 15

Top 5 matching trials:
--------------------------------------------------------------------------------
1. Study of Osimertinib in Patients With EGFR Mutation Positive NSCLC...
   Trial ID: NCT02546986
   Match Score: 80.00% (4/5 criteria)

2. A Study of AZD9291 in Patients With EGFR Mutation Positive NSCLC...
   Trial ID: NCT01802632
   Match Score: 60.00% (3/5 criteria)
...
```

## Architecture

- `main.py`: Main orchestration script
- `src/target_identification/search.py`: Trial search functionality
- `src/criterion_matching/matcher.py`: Criteria matching using LLM
- `src/utils/`: Utility functions for LLM, prompts, and data processing

## Requirements

- Python 3.8+
- Elasticsearch with AACT data indexed
- OpenAI API key
- Required Python packages (see requirements.txt) 