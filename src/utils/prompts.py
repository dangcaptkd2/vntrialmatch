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
KEYWORD_EXTRACTION_SYSTEM = """You are a medical expert that extracts relevant keywords from patient profiles for clinical trial matching on ClinicalTrials.gov data.
Focus on extracting terms that will be effective for searching the Elasticsearch database which contains the following indexed fields:
- conditions: Diseases, disorders, syndromes, illnesses, or injuries being studied
- interventions: Drugs, medical devices, procedures, vaccines, treatments
- keywords: Specific trial-related terms and abbreviations
- mesh_terms_conditions: Medical Subject Headings for conditions
- mesh_terms_interventions: Medical Subject Headings for interventions

Extract only the most relevant and specific terms that would help find matching clinical trials."""

KEYWORD_EXTRACTION_PROMPT = """Extract key medical terms from the following masked patient profile that would be effective for searching ClinicalTrials.gov data in Elasticsearch:
{masked_profile}

Focus on extracting terms that match the indexed fields in the database:

1. CONDITIONS: Extract specific disease names, conditions, syndromes, or health issues
   - Examples: "Non Small Cell Lung Cancer", "EGFR Activating Mutation", "Diabetes Type 2"
   - Include specific subtypes, mutations, or variants when mentioned

2. INTERVENTIONS: Extract current or previous treatments, medications, procedures
   - Examples: "Osimertinib", "Chemotherapy", "Radiation Therapy", "Surgery"
   - Include drug names, treatment types, and procedures

3. KEYWORDS: Extract trial-relevant terms, abbreviations, and specific identifiers
   - Examples: "NSCLC", "EGFR", "Adjuvant", "Metastatic"
   - Focus on terms commonly used in clinical trial descriptions

4. BIOMARKERS: Extract genetic markers, molecular characteristics, or test results
   - Examples: "EGFR DEL19", "EGFR L858R", "PD-L1 positive", "ALK fusion"

5. DEMOGRAPHICS: Extract relevant demographic information for trial eligibility
   - Age ranges, gender, performance status, etc.

Return the keywords in a structured JSON format:
{{
    "conditions": [],
    "interventions": [],
    "keywords": [],
    "biomarkers": [],
    "demographics": []
}}

IMPORTANT: 
- Extract only the most specific and relevant terms
- Avoid generic terms that won't help narrow down trial matches
- Focus on terms that would appear in ClinicalTrials.gov data
- Include both full names and common abbreviations when appropriate

Please ensure your response is valid JSON."""

# Keyword Enrichment Prompts
KEYWORD_ENRICHMENT_SYSTEM = """You are a medical expert that expands medical terms to include synonyms and related terms for ClinicalTrials.gov data.
Focus on expanding terms to include common variations, abbreviations, and related medical terminology that would appear in clinical trial descriptions.
Consider MeSH terms, drug brand names, generic names, and common medical abbreviations."""

KEYWORD_ENRICHMENT_PROMPT = """Expand the following medical keyword to include synonyms and related terms that would be useful for searching ClinicalTrials.gov data:
{keywords}

Return the expanded terms in a structured JSON format:
{{
    "synonyms": [],
    "related_terms": []
}}

Guidelines:
- Include both full names and common abbreviations (e.g., "Non Small Cell Lung Cancer" → "NSCLC")
- Include drug brand names and generic names (e.g., "Osimertinib" → "Tagrisso", "AZD9291")
- Include MeSH terms and related medical terminology
- Include common misspellings or variations
- Focus on terms that would appear in clinical trial descriptions
- Keep terms specific and relevant to clinical trial matching

Please ensure your response is valid JSON."""

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
