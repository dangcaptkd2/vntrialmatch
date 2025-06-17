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
redis_client = redis.from_url(REDIS_URL)


def search_trials(keywords):
    """Search clinical trials using enriched keywords."""
    # Create search query from keywords
    search_query = {
        "query": {
            "bool": {
                "should": [{"match": {"title": keyword}} for keyword in keywords],
                "minimum_should_match": 1,
            }
        }
    }

    # Execute search
    response = es.search(index=ES_INDEX_NAME, body=search_query)
    return response["hits"]["hits"]


def get_trial_criteria(nct_id):
    """Get trial criteria from Redis."""
    criteria = redis_client.hget(REDIS_TRIAL_CRITERIA_KEY, nct_id)
    return json.loads(criteria) if criteria else None


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

                # Step 3: Enrich keywords
                enriched_keywords = keyword_enricher.enrich_keywords(keywords)

                # Flatten enriched keywords for search
                search_keywords = []
                for term_data in enriched_keywords.values():
                    search_keywords.extend(term_data["synonyms"])
                    search_keywords.extend(term_data["related_terms"])

                # Step 4: Search trials
                trial_results = search_trials(search_keywords)

                # Display results
                for trial in trial_results:
                    trial_data = trial["_source"]
                    nct_id = trial_data["nct_id"]

                    with st.expander(f"{trial_data['title']} (NCT ID: {nct_id})"):
                        st.write(f"**Brief Title:** {trial_data['brief_title']}")
                        st.write(f"**Official Title:** {trial_data['official_title']}")

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
