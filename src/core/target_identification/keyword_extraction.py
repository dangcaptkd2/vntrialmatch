import json
import logging
from typing import Any, Dict

from src.utils.cache_manager import cache_manager
from src.utils.openai_utils import get_structured_llm_response
from src.utils.prompts import KEYWORD_EXTRACTION_PROMPT, KEYWORD_EXTRACTION_SYSTEM

logger = logging.getLogger(__name__)


class KeywordExtractor:
    def __init__(self, use_cache: bool = True):
        """
        Initialize the keyword extractor.

        Args:
            use_cache: Whether to use caching for keyword extraction
        """
        self.system_message = KEYWORD_EXTRACTION_SYSTEM
        self.prompt_template = KEYWORD_EXTRACTION_PROMPT
        self.response_format = {"type": "json_object"}
        self.use_cache = use_cache
        self.logger = logging.getLogger(__name__)

    def extract_keywords(self, masked_profile: str) -> Dict[str, Any]:
        """
        Extract relevant keywords from masked patient profile.

        Args:
            masked_profile (str): Masked patient profile text

        Returns:
            dict: Extracted keywords in structured format
        """
        # Check cache first if enabled
        if self.use_cache:
            cached_result = cache_manager.get_cached_result(
                masked_profile, "extraction"
            )
            if cached_result:
                self.logger.info("Using cached keyword extraction result")
                return cached_result

        # Perform keyword extraction
        self.logger.info("Performing keyword extraction")
        prompt = self.prompt_template.format(masked_profile=masked_profile)
        response = get_structured_llm_response(
            prompt, self.system_message, self.response_format
        )

        try:
            result = json.loads(response)

            # Cache the result if enabled
            if self.use_cache:
                cache_manager.set_cached_result(masked_profile, "extraction", result)

            return result
        except json.JSONDecodeError as e:
            self.logger.error(f"Failed to parse keyword extraction response: {e}")
            return {
                "conditions": [],
                "interventions": [],
                "keywords": [],
                "biomarkers": [],
                "demographics": [],
            }


if __name__ == "__main__":
    extractor = KeywordExtractor()
    with open("data/patient_data/patient.1.1.txt", "r") as f:
        masked_profile = f.read()
    print(extractor.extract_keywords(masked_profile))
