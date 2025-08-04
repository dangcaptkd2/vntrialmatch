import logging
from typing import Dict, List, Optional, Union

from elasticsearch import Elasticsearch

from src.core.target_identification.keyword_enrichment import KeywordEnricher
from src.core.target_identification.keyword_extraction import KeywordExtractor
from src.core.target_identification.patient_masking import PatientMasker
from src.settings import settings

# Set up logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class ClinicalTrialSearcher:
    def __init__(
        self,
        es_url: Optional[str] = None,
        index_name: str = None,
        use_cache: bool = True,
        use_enriched_keywords: bool = True,
    ):
        """
        Initialize the clinical trial searcher.

        Args:
            es_url: Elasticsearch URL
            index_name: Name of the Elasticsearch index
            use_cache: Whether to use caching for keyword extraction and enrichment
            use_enriched_keywords: Whether to use enriched keywords for search
        """
        if es_url is None:
            es_url = settings.elasticsearch_url or "http://localhost:9200"
        if index_name is None:
            index_name = settings.es_index_name
        self.es = Elasticsearch([es_url])
        self.index_name = index_name
        self.keyword_extractor = KeywordExtractor(use_cache=use_cache)
        self.keyword_enricher = KeywordEnricher(use_cache=use_cache)
        self.patient_masker = PatientMasker()
        self.use_cache = use_cache
        self.use_enriched_keywords = use_enriched_keywords

    def check_index_exists(self) -> bool:
        """Check if the Elasticsearch index exists."""
        try:
            response = self.es.indices.exists(index=self.index_name)
            # For exists check, response is already a boolean
            return response
        except Exception as e:
            logger.error(f"Error checking index existence: {e}")
            return False

    def build_search_query(
        self, keywords: Union[Dict, List[str]], use_enriched: bool = False
    ) -> Dict:
        """
        Build Elasticsearch query from keywords.

        Args:
            keywords: Keywords from extraction or enrichment
            use_enriched: Whether using enriched keywords (affects query structure)

        Returns:
            Elasticsearch query dictionary
        """
        if use_enriched:
            # Handle enriched keywords structure - prioritize original keywords
            primary_terms = []
            secondary_terms = []
            if isinstance(keywords, dict):
                for keyword, enrichment in keywords.items():
                    primary_terms.append(keyword)  # Original keyword is most important
                    if isinstance(enrichment, dict):
                        if "synonyms" in enrichment:
                            secondary_terms.extend(enrichment["synonyms"])
                        if "related_terms" in enrichment:
                            secondary_terms.extend(enrichment["related_terms"])
        else:
            # Handle extracted keywords structure
            primary_terms = []
            if isinstance(keywords, dict):
                for category, terms in keywords.items():
                    if isinstance(terms, list):
                        primary_terms.extend(terms)
                    elif isinstance(terms, str):
                        primary_terms.append(terms)
            elif isinstance(keywords, list):
                primary_terms = keywords
            secondary_terms = []

        # Remove duplicates and filter out empty strings
        primary_terms = list(
            set([term.strip() for term in primary_terms if term.strip()])
        )
        secondary_terms = list(
            set([term.strip() for term in secondary_terms if term.strip()])
        )

        if not primary_terms:
            logger.warning("No valid keywords found for search")
            return {"match_all": {}}

        # Build a much simpler query structure
        # Focus on the most important fields with a multi_match query
        query_terms = " ".join(primary_terms)

        # Primary query: Multi-match on most important fields
        primary_query = {
            "multi_match": {
                "query": query_terms,
                "fields": [
                    "brief_title^3",
                    "official_title^2.5",
                    "conditions^2",
                    "interventions^2",
                    "keywords^1.5",
                ],
                "type": "best_fields",
                "operator": "or",
            }
        }

        # If we have secondary terms (enriched), add them as a boost
        if secondary_terms:
            secondary_query_terms = " ".join(secondary_terms)
            secondary_query = {
                "multi_match": {
                    "query": secondary_query_terms,
                    "fields": [
                        "brief_title^1.5",
                        "official_title^1.2",
                        "conditions^1",
                        "interventions^1",
                        "keywords^0.8",
                    ],
                    "type": "best_fields",
                    "operator": "or",
                }
            }

            # Combine primary and secondary queries
            query = {
                "bool": {
                    "must": [primary_query],
                    "should": [secondary_query],
                    "minimum_should_match": 0,
                }
            }
        else:
            query = primary_query

        return query

    def search_trials(
        self,
        keywords: Union[Dict, List[str]],
        use_enriched: bool = False,
        size: int = 20,
        from_: int = 0,
    ) -> Dict:
        """
        Search for clinical trials using keywords.

        Args:
            keywords: Keywords from extraction or enrichment
            use_enriched: Whether using enriched keywords
            size: Number of results to return
            from_: Starting position for pagination

        Returns:
            Search results dictionary
        """
        if not self.check_index_exists():
            raise ValueError(f"Elasticsearch index '{self.index_name}' does not exist")

        query = self.build_search_query(keywords, use_enriched)

        search_body = {
            "query": query,
            "size": size,
            "from": from_,
            "_source": [
                "nct_id",
                "brief_title",
                "official_title",
                "conditions",
                "interventions",
                "keywords",
                "brief_summary",
            ],
        }

        try:
            response = self.es.search(index=self.index_name, body=search_body)
            # For search, response is already a dict
            return response
        except Exception as e:
            logger.error(f"Error searching Elasticsearch: {e}")
            raise

    def run_full_pipeline(
        self,
        patient_profile_path: Optional[str] = None,
        patient_profile_text: Optional[str] = None,
        size: int = 20,
        skip_masking: bool = False,
    ) -> Dict:
        """
        Run the complete pipeline: patient masking -> keyword extraction ->
        keyword enrichment -> search.

        Args:
            patient_profile_path: Path to patient profile file
            size: Number of search results to return

        Returns:
            Dictionary containing pipeline results
        """
        logger.info("Starting full pipeline execution")

        if patient_profile_path is None and patient_profile_text is None:
            raise ValueError(
                "Either patient_profile_path or patient_profile_text must be provided"
            )

        # Step 1: Read patient profile
        if patient_profile_text is None:
            try:
                with open(patient_profile_path, "r") as f:
                    patient_profile = f.read()
            except FileNotFoundError:
                raise FileNotFoundError(
                    f"Patient profile file not found: {patient_profile_path}"
                )
        else:
            patient_profile = patient_profile_text

        if not skip_masking:
            # Step 2: Patient masking
            logger.info("Step 1: Masking patient data")
            masked_profile = self.patient_masker.mask_patient_data(patient_profile)
        else:
            masked_profile = patient_profile

        # Step 3: Keyword extraction
        logger.info("Step 2: Extracting keywords")
        extracted_keywords = self.keyword_extractor.extract_keywords(masked_profile)

        # Step 4: Keyword enrichment
        logger.info("Step 3: Enriching keywords")
        enriched_keywords = self.keyword_enricher.enrich_keywords(extracted_keywords)

        # Step 5: Search
        logger.info("Step 4: Searching clinical trials")
        if self.use_enriched_keywords:
            search_results = self.search_trials(
                enriched_keywords, use_enriched=True, size=size
            )
        else:
            search_results = self.search_trials(
                extracted_keywords, use_enriched=False, size=size
            )

        return {
            "masked_profile": masked_profile,
            "extracted_keywords": extracted_keywords,
            "enriched_keywords": enriched_keywords,
            "search_results": search_results,
        }

    def search_with_extracted_keywords(self, keywords: Dict, size: int = 20) -> Dict:
        """
        Search using keywords from keyword extraction (for testing).

        Args:
            keywords: Keywords from keyword extraction
            size: Number of search results to return

        Returns:
            Search results dictionary
        """
        logger.info("Searching with extracted keywords")
        return self.search_trials(keywords, use_enriched=False, size=size)

    def search_with_enriched_keywords(self, keywords: Dict, size: int = 20) -> Dict:
        """
        Search using keywords from keyword enrichment (for testing).

        Args:
            keywords: Keywords from keyword enrichment
            size: Number of search results to return

        Returns:
            Search results dictionary
        """
        logger.info("Searching with enriched keywords")
        return self.search_trials(keywords, use_enriched=True, size=size)

    def format_search_results(self, search_results: Dict) -> List[Dict]:
        """
        Format search results for easy consumption.

        Args:
            search_results: Raw Elasticsearch search results

        Returns:
            List of formatted trial information
        """
        formatted_results = []

        for hit in search_results.get("hits", {}).get("hits", []):
            source = hit["_source"]
            formatted_trial = {
                "nct_id": source.get("nct_id"),
                "title": source.get("brief_title") or source.get("official_title"),
                "conditions": source.get("conditions", []),
                "interventions": source.get("interventions", []),
                "keywords": source.get("keywords", []),
                "summary": source.get("brief_summary"),
                "score": hit.get("_score", 0),
            }
            formatted_results.append(formatted_trial)

        return formatted_results


def demo():
    """Main function for testing the search functionality."""
    searcher = ClinicalTrialSearcher(use_enriched_keywords=False)

    patient_profile_text = "A 32-year-old woman comes to the hospital with vaginal spotting.  Her last menstrual period was 10 weeks ago. She has regular menses lasting for 6 days and repeating every 29 days. Medical history is significant for appendectomy and several complicated UTIs. She has multiple male partners, and she is inconsistent with using barrier contraceptives. Vital signs are normal.  Serum β-hCG level is 1800 mIU/mL, and a repeat level after 2 days shows an abnormal rise to 2100 mIU/mL.  Pelvic ultrasound reveals a thin endometrium with no gestational sac in the uterus."

    results = searcher.run_full_pipeline(
        patient_profile_text=patient_profile_text,
        size=100,
        skip_masking=True,
    )
    print(f"Found {len(results['search_results']['hits']['hits'])} trials")
    formatted_results = searcher.format_search_results(results["search_results"])
    # final_results = [[trial["nct_id"], trial["title"]] for trial in formatted_results]

    list_result_nct_id = [trial["nct_id"] for trial in formatted_results]
    print(list_result_nct_id)


if __name__ == "__main__":
    demo()
