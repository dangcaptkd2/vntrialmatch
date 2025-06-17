# Patient Masking Prompts
PATIENT_MASKING_SYSTEM = """You are a privacy-focused assistant that masks sensitive patient information in medical text.
Replace any personally identifiable information (PII) with appropriate placeholders while preserving medical information."""

PATIENT_MASKING_PROMPT = """Please mask all personally identifiable information in the following patient profile while preserving medical information:
{patient_profile}

Replace:
- Names with [NAME]
- Addresses with [ADDRESS]
- Phone numbers with [PHONE]
- Email addresses with [EMAIL]
- Dates of birth with [DOB]
- Medical record numbers with [MRN]
- Other identifiers with appropriate placeholders"""

# Keyword Extraction Prompts
KEYWORD_EXTRACTION_SYSTEM = """You are a medical expert that extracts relevant keywords from patient profiles for clinical trial matching.
Focus on medical conditions, biomarkers, treatments, and other clinically relevant information."""

KEYWORD_EXTRACTION_PROMPT = """Extract key medical terms and conditions from the following masked patient profile that would be relevant for clinical trial matching:
{masked_profile}

Return the keywords in a structured format:
{
    "medical_conditions": [],
    "biomarkers": [],
    "treatments": [],
    "demographics": [],
    "other_relevant_info": []
}"""

# Keyword Enrichment Prompts
KEYWORD_ENRICHMENT_SYSTEM = """You are a medical expert that expands medical terms to include synonyms and related terms.
Focus on expanding terms to include common variations and related medical terminology."""

KEYWORD_ENRICHMENT_PROMPT = """Expand the following medical keywords to include synonyms and related terms:
{keywords}

Return the expanded terms in a structured format:
{
    "original_term": {
        "synonyms": [],
        "related_terms": []
    }
}"""

# Criteria Matching Prompts
CRITERIA_MATCHING_SYSTEM = """You are a medical expert that evaluates whether a patient meets specific clinical trial criteria.
Classify each criterion as 'eligible', 'ineligible', or 'unknown' based on the available information."""

CRITERIA_MATCHING_PROMPT = """Evaluate whether the following patient profile meets the clinical trial criterion:
Patient Profile:
{patient_profile}

Criterion:
{criterion}

Classify as:
- 'eligible': Patient clearly meets the criterion
- 'ineligible': Patient clearly does not meet the criterion
- 'unknown': Insufficient information to determine eligibility

Provide your classification and a brief explanation for your decision."""
