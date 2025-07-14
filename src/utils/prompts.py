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
   - LIMIT: Maximum 5 most important conditions

2. INTERVENTIONS: Extract current or previous treatments, medications, procedures
   - Examples: "Osimertinib", "Chemotherapy", "Radiation Therapy", "Surgery"
   - Include drug names, treatment types, and procedures
   - LIMIT: Maximum 5 most important interventions

3. KEYWORDS: Extract trial-relevant terms, abbreviations, and specific identifiers
   - Examples: "NSCLC", "EGFR", "Adjuvant", "Metastatic"
   - Focus on terms commonly used in clinical trial descriptions
   - LIMIT: Maximum 8 most important keywords

4. BIOMARKERS: Extract genetic markers, molecular characteristics, or test results
   - Examples: "EGFR DEL19", "EGFR L858R", "PD-L1 positive", "ALK fusion"
   - LIMIT: Maximum 5 most important biomarkers

5. DEMOGRAPHICS: Extract relevant demographic information for trial eligibility
   - Age ranges, gender, performance status, etc.
   - LIMIT: Maximum 3 most important demographic factors

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
- Prioritize terms that are most likely to appear in clinical trial titles and conditions
- Be selective - quality over quantity

Please ensure your response is valid JSON."""

# Keyword Enrichment Prompts
KEYWORD_ENRICHMENT_SYSTEM = """You are a medical expert that expands medical terms to include synonyms and related terms for ClinicalTrials.gov data.
Focus on expanding terms to include common variations, abbreviations, and related medical terminology that would appear in clinical trial descriptions.
Consider MeSH terms, drug brand names, generic names, and common medical abbreviations.
For terms that cannot be meaningfully enriched (e.g., generic terms, non-medical terms), return empty arrays."""

KEYWORD_ENRICHMENT_PROMPT = """Expand the following medical keywords to include synonyms and related terms that would be useful for searching ClinicalTrials.gov data:
{keywords}

Return the expanded terms in a structured JSON format where each keyword is a key:
{{
    "keyword1": {{
        "synonyms": [],
        "related_terms": []
    }},
    "keyword2": {{
        "synonyms": [],
        "related_terms": []
    }},
    ...
}}

Guidelines:
- Include both full names and common abbreviations (e.g., "Non Small Cell Lung Cancer" → "NSCLC")
- Include drug brand names and generic names (e.g., "Osimertinib" → "Tagrisso", "AZD9291")
- Include MeSH terms and related medical terminology
- Include common misspellings or variations
- Focus on terms that would appear in clinical trial descriptions
- Keep terms specific and relevant to clinical trial matching
- For terms that cannot be meaningfully enriched (generic terms, non-medical terms, etc.), return empty arrays for synonyms and related_terms
- Only enrich terms that have clear medical relevance and would benefit from expansion
- LIMIT: Maximum 3 synonyms and 3 related terms per keyword
- Prioritize the most commonly used variations in clinical trial literature

Please ensure your response is valid JSON."""

# Criteria Matching Prompts
CRITERIA_MATCHING_SYSTEM = """You are a medical expert that evaluates whether a patient meets specific clinical trial criteria.
Classify each criterion as 'eligible', 'ineligible', or 'unknown' based on the available information.
Always respond with valid JSON format containing classification and explanation."""

CRITERIA_MATCHING_PROMPT = """Evaluate whether the following patient profile meets the clinical trial criterion:

Patient Profile:
{patient_profile}

Criterion:
{criterion}

Classify the patient's eligibility for this criterion and provide a brief explanation.

Return your response in the following JSON format:
{{
    "classification": "eligible|ineligible|unknown",
    "explanation": "Brief explanation of your decision"
}}

Classification guidelines:
- 'eligible': Patient clearly meets the criterion based on available information
- 'ineligible': Patient clearly does not meet the criterion based on available information  
- 'unknown': Use this when you are unsure, when information is missing, or when the criterion is ambiguous

IMPORTANT: When in doubt, classify as 'unknown'. It is better to be conservative and request more information than to make assumptions.

Explanation guidelines:
- Be concise but specific about why you made your classification
- Reference specific information from the patient profile when possible
- If information is missing, clearly state what additional information would be needed
- If you are unsure about the interpretation of the criterion, explain why

Please ensure your response is valid JSON."""
