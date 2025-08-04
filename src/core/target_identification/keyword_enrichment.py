import json
import logging
from typing import Any, Dict

from src.utils.cache_manager import cache_manager
from src.utils.openai_utils import get_structured_llm_response
from src.utils.prompts import KEYWORD_ENRICHMENT_PROMPT, KEYWORD_ENRICHMENT_SYSTEM

logger = logging.getLogger(__name__)


class KeywordEnricher:
    def __init__(self, use_cache: bool = True):
        """
        Initialize the keyword enricher.

        Args:
            use_cache: Whether to use caching for keyword enrichment
        """
        self.system_message = KEYWORD_ENRICHMENT_SYSTEM
        self.prompt_template = KEYWORD_ENRICHMENT_PROMPT
        self.response_format = {"type": "json_object"}
        self.use_cache = use_cache
        self.logger = logging.getLogger(__name__)

    def enrich_keywords(self, keywords: Dict[str, Any]) -> Dict[str, Any]:
        """
        Enrich keywords with synonyms and related terms.

        Args:
            keywords (dict): Dictionary of extracted keywords

        Returns:
            dict: Enriched keywords with synonyms and related terms
        """
        # Flatten keywords into a list
        all_keywords = []
        for category in keywords.values():
            if isinstance(category, list):
                all_keywords.extend(category)

        # Process all keywords in a single call
        if not all_keywords:
            return {}

        # Join all keywords with commas for the prompt
        keywords_text = ", ".join(all_keywords)

        # Create a cache key from the keywords
        cache_key = keywords_text

        # Check cache first if enabled
        if self.use_cache:
            cached_result = cache_manager.get_cached_result(cache_key, "enrichment")
            if cached_result:
                self.logger.info("Using cached keyword enrichment result")
                return cached_result

        # Perform keyword enrichment
        self.logger.info("Performing keyword enrichment")
        prompt = self.prompt_template.format(keywords=keywords_text)

        response = get_structured_llm_response(
            prompt, self.system_message, self.response_format
        )

        try:
            # Parse the response which should contain enrichment for all keywords
            enriched_terms = json.loads(response)

            # Cache the result if enabled
            if self.use_cache:
                cache_manager.set_cached_result(cache_key, "enrichment", enriched_terms)

            return enriched_terms
        except json.JSONDecodeError as e:
            self.logger.error(f"Failed to parse keyword enrichment response: {e}")
            return {}
