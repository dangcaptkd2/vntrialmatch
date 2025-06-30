import logging
from typing import Dict, List, Optional, Union

from elasticsearch import Elasticsearch

from src.config.config import ELASTICSEARCH_URL, ES_INDEX_NAME
from src.target_identification.keyword_enrichment import KeywordEnricher
from src.target_identification.keyword_extraction import KeywordExtractor
from src.target_identification.patient_masking import PatientMasker

# Set up logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class ClinicalTrialSearcher:
    def __init__(self, es_url: Optional[str] = None, index_name: str = ES_INDEX_NAME):
        """
        Initialize the clinical trial searcher.

        Args:
            es_url: Elasticsearch URL
            index_name: Name of the Elasticsearch index
        """
        if es_url is None:
            es_url = ELASTICSEARCH_URL or "http://localhost:9200"
        self.es = Elasticsearch([es_url])
        self.index_name = index_name
        self.keyword_extractor = KeywordExtractor()
        self.keyword_enricher = KeywordEnricher()
        self.patient_masker = PatientMasker()

    def check_index_exists(self) -> bool:
        """Check if the Elasticsearch index exists."""
        try:
            return self.es.indices.exists(index=self.index_name)
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
            # Handle enriched keywords structure
            all_terms = []
            if isinstance(keywords, dict):
                for keyword, enrichment in keywords.items():
                    all_terms.append(keyword)
                    if isinstance(enrichment, dict):
                        if "synonyms" in enrichment:
                            all_terms.extend(enrichment["synonyms"])
                        if "related_terms" in enrichment:
                            all_terms.extend(enrichment["related_terms"])
        else:
            # Handle extracted keywords structure
            all_terms = []
            if isinstance(keywords, dict):
                for category, terms in keywords.items():
                    if isinstance(terms, list):
                        all_terms.extend(terms)
                    elif isinstance(terms, str):
                        all_terms.append(terms)
            elif isinstance(keywords, list):
                all_terms = keywords

        # Remove duplicates and filter out empty strings
        all_terms = list(set([term.strip() for term in all_terms if term.strip()]))

        if not all_terms:
            logger.warning("No valid keywords found for search")
            return {"match_all": {}}

        # Build multi-field search query
        should_clauses = []

        # Search in different fields with different weights
        for term in all_terms:
            should_clauses.extend(
                [
                    {"match": {"brief_title": {"query": term, "boost": 3.0}}},
                    {"match": {"official_title": {"query": term, "boost": 2.5}}},
                    {"match": {"conditions": {"query": term, "boost": 2.0}}},
                    {"match": {"interventions": {"query": term, "boost": 2.0}}},
                    {"match": {"keywords": {"query": term, "boost": 1.5}}},
                    {"match": {"mesh_terms_conditions": {"query": term, "boost": 1.5}}},
                    {
                        "match": {
                            "mesh_terms_interventions": {"query": term, "boost": 1.5}
                        }
                    },
                    {"match": {"brief_summary": {"query": term, "boost": 1.0}}},
                ]
            )

        query = {"bool": {"should": should_clauses, "minimum_should_match": 1}}

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
            return response
        except Exception as e:
            logger.error(f"Error searching Elasticsearch: {e}")
            raise

    def run_full_pipeline(
        self,
        patient_profile_path: str = "data/patient_data/patient.1.1.txt",
        size: int = 20,
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

        # Step 1: Read patient profile
        try:
            with open(patient_profile_path, "r") as f:
                patient_profile = f.read()
        except FileNotFoundError:
            raise FileNotFoundError(
                f"Patient profile file not found: {patient_profile_path}"
            )

        # Step 2: Patient masking
        logger.info("Step 1: Masking patient data")
        masked_profile = self.patient_masker.mask_patient_data(patient_profile)

        # Step 3: Keyword extraction
        logger.info("Step 2: Extracting keywords")
        extracted_keywords = self.keyword_extractor.extract_keywords(masked_profile)

        # Step 4: Keyword enrichment
        logger.info("Step 3: Enriching keywords")
        enriched_keywords = self.keyword_enricher.enrich_keywords(extracted_keywords)

        # Step 5: Search
        logger.info("Step 4: Searching clinical trials")
        search_results = self.search_trials(
            enriched_keywords, use_enriched=True, size=size
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


def main():
    """Main function for testing the search functionality."""
    searcher = ClinicalTrialSearcher()

    # # Test 1: Full pipeline
    # print("=== Testing Full Pipeline ===")
    # try:
    #     results = searcher.run_full_pipeline(size=5)
    #     print(f"Found {len(results['search_results']['hits']['hits'])} trials")
    #     formatted_results = searcher.format_search_results(results['search_results'])
    #     for i, trial in enumerate(formatted_results[:3]):
    #         print(f"\n{i+1}. {trial['title']} (Score: {trial['score']:.2f})")
    #         print(f"   NCT ID: {trial['nct_id']}")
    #         print(f"   Conditions: {', '.join(trial['conditions'][:3])}")
    # except Exception as e:
    #     print(f"Full pipeline test failed: {e}")

    # Test 2: Direct search with result from keyword extraction
    print("\n=== Testing Direct Search ===")
    with open("data/patient_data/patient.1.1.txt", "r") as f:
        patient_profile = f.read()
    extracted_keywords = searcher.keyword_extractor.extract_keywords(patient_profile)

    print("=" * 50)
    print(extracted_keywords)
    print("=" * 50)

    try:
        results = searcher.search_with_extracted_keywords(extracted_keywords, size=3)
        formatted_results = searcher.format_search_results(results)
        for i, trial in enumerate(formatted_results):
            print(f"\n{i + 1}. {trial['title']} (Score: {trial['score']:.2f})")
            print(f"   NCT ID: {trial['nct_id']}")
    except Exception as e:
        print(f"Direct search test failed: {e}")


if __name__ == "__main__":
    main()
