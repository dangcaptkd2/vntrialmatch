import json

import redis
import streamlit as st
from elasticsearch import Elasticsearch

from config.config import (
    ELASTICSEARCH_URL,
    ES_INDEX_NAME,
    REDIS_TRIAL_CRITERIA_KEY,
    REDIS_URL,
    STREAMLIT_DESCRIPTION,
    STREAMLIT_TITLE,
)
from criterion_matching.matcher import CriteriaMatcher
from target_identification.keyword_enrichment import KeywordEnricher
from target_identification.keyword_extraction import KeywordExtractor
from target_identification.patient_masking import PatientMasker

# Initialize components
patient_masker = PatientMasker()
keyword_extractor = KeywordExtractor()
keyword_enricher = KeywordEnricher()
criteria_matcher = CriteriaMatcher()

# Initialize connections
es = Elasticsearch(ELASTICSEARCH_URL)
try:
    redis_client = redis.from_url(REDIS_URL) if REDIS_URL else None
except Exception as e:
    st.warning(f"Redis connection failed: {e}")
    redis_client = None


def search_trials(keywords_dict, enriched_keywords=None):
    """Search clinical trials using structured keywords from different categories."""
    # Create a more sophisticated search query using the specific Elasticsearch fields
    should_clauses = []
    
    # Search in conditions field
    if keywords_dict.get("conditions"):
        for condition in keywords_dict["conditions"]:
            should_clauses.append({"match": {"conditions": condition}})
            # Add enriched terms if available
            if enriched_keywords and condition in enriched_keywords:
                for synonym in enriched_keywords[condition].get("synonyms", []):
                    should_clauses.append({"match": {"conditions": synonym}})
    
    # Search in interventions field
    if keywords_dict.get("interventions"):
        for intervention in keywords_dict["interventions"]:
            should_clauses.append({"match": {"interventions": intervention}})
            # Add enriched terms if available
            if enriched_keywords and intervention in enriched_keywords:
                for synonym in enriched_keywords[intervention].get("synonyms", []):
                    should_clauses.append({"match": {"interventions": synonym}})
    
    # Search in keywords field
    if keywords_dict.get("keywords"):
        for keyword in keywords_dict["keywords"]:
            should_clauses.append({"match": {"keywords": keyword}})
            # Add enriched terms if available
            if enriched_keywords and keyword in enriched_keywords:
                for synonym in enriched_keywords[keyword].get("synonyms", []):
                    should_clauses.append({"match": {"keywords": synonym}})
    
    # Search in mesh_terms_conditions field
    if keywords_dict.get("biomarkers"):
        for biomarker in keywords_dict["biomarkers"]:
            should_clauses.append({"match": {"mesh_terms_conditions": biomarker}})
            # Add enriched terms if available
            if enriched_keywords and biomarker in enriched_keywords:
                for synonym in enriched_keywords[biomarker].get("synonyms", []):
                    should_clauses.append({"match": {"mesh_terms_conditions": synonym}})
    
    # Search in brief_title and official_title
    all_terms = []
    for category in keywords_dict.values():
        if isinstance(category, list):
            all_terms.extend(category)
    
    for term in all_terms:
        should_clauses.append({"match": {"brief_title": term}})
        should_clauses.append({"match": {"official_title": term}})
        # Add enriched terms if available
        if enriched_keywords and term in enriched_keywords:
            for synonym in enriched_keywords[term].get("synonyms", []):
                should_clauses.append({"match": {"brief_title": synonym}})
                should_clauses.append({"match": {"official_title": synonym}})
    
    # Create the search query
    search_query = {
        "query": {
            "bool": {
                "should": should_clauses,
                "minimum_should_match": 1,
            }
        },
        "size": 20,  # Limit results
        "_source": ["nct_id", "brief_title", "official_title", "conditions", "interventions", "keywords"]
    }

    # Execute search
    response = es.search(index=ES_INDEX_NAME, body=search_query)
    return response["hits"]["hits"]


def get_trial_criteria(nct_id):
    """Get trial criteria from Redis."""
    if redis_client is None:
        return None
    try:
        criteria = redis_client.hget(REDIS_TRIAL_CRITERIA_KEY, nct_id)
        return json.loads(criteria) if criteria else None
    except Exception as e:
        st.warning(f"Failed to get trial criteria: {e}")
        return None


def main():
    st.title(STREAMLIT_TITLE)
    st.write(STREAMLIT_DESCRIPTION)

    # Patient profile input
    patient_profile = st.text_area("Enter Patient Profile", height=200)

    if st.button("Find Matching Trials"):
        if patient_profile:
            with st.spinner("Processing..."):
                # Step 1: Mask patient data
                masked_profile = patient_masker.mask_patient_data(patient_profile)

                # Step 2: Extract keywords
                keywords = keyword_extractor.extract_keywords(masked_profile)
                
                # Display extracted keywords for debugging
                st.subheader("Extracted Keywords")
                for category, terms in keywords.items():
                    if terms:  # Only show non-empty categories
                        st.write(f"**{category.title()}:** {', '.join(terms)}")

                # Step 3: Enrich keywords
                enriched_keywords = keyword_enricher.enrich_keywords(keywords)

                # Step 4: Search trials using the structured keywords
                trial_results = search_trials(keywords, enriched_keywords)

                # Display results
                st.subheader(f"Found {len(trial_results)} Matching Trials")
                
                for trial in trial_results:
                    trial_data = trial["_source"]
                    nct_id = trial_data["nct_id"]
                    score = trial["_score"]

                    with st.expander(f"{trial_data['brief_title']} (Score: {score:.2f})"):
                        st.write(f"**NCT ID:** {nct_id}")
                        st.write(f"**Official Title:** {trial_data.get('official_title', 'N/A')}")
                        
                        # Display relevant fields
                        if trial_data.get('conditions'):
                            st.write(f"**Conditions:** {', '.join(trial_data['conditions'])}")
                        if trial_data.get('interventions'):
                            st.write(f"**Interventions:** {', '.join(trial_data['interventions'])}")
                        if trial_data.get('keywords'):
                            st.write(f"**Keywords:** {', '.join(trial_data['keywords'])}")

                        # Get and display criteria
                        criteria = get_trial_criteria(nct_id)
                        if criteria:
                            st.subheader("Eligibility Criteria")

                            # Match criteria
                            matching_results = criteria_matcher.match_all_criteria(
                                patient_profile,
                                criteria["inclusion_criteria"]
                                + criteria["exclusion_criteria"],
                            )

                            # Display results
                            for result in matching_results:
                                criterion = result["criterion"]
                                match_result = result["result"]

                                # Color coding based on classification
                                color = {
                                    "eligible": "green",
                                    "ineligible": "red",
                                    "unknown": "orange",
                                }.get(match_result["classification"], "gray")

                                st.markdown(
                                    f"**{criterion}** - "
                                    f":{color}[{match_result['classification'].upper()}]"
                                )
                                st.write(match_result["explanation"])
                                st.write("---")
        else:
            st.warning("Please enter a patient profile.")


if __name__ == "__main__":
    main()
