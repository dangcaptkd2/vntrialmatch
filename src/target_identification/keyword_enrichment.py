import json

from src.utils.llm_utils import get_structured_llm_response
from src.utils.prompts import KEYWORD_ENRICHMENT_PROMPT, KEYWORD_ENRICHMENT_SYSTEM


class KeywordEnricher:
    def __init__(self):
        self.system_message = KEYWORD_ENRICHMENT_SYSTEM
        self.prompt_template = KEYWORD_ENRICHMENT_PROMPT
        self.response_format = {"type": "json_object"}

    def enrich_keywords(self, keywords):
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
        prompt = self.prompt_template.format(keywords=keywords_text)

        response = get_structured_llm_response(
            prompt, self.system_message, self.response_format
        )

        # Parse the response which should contain enrichment for all keywords
        enriched_terms = json.loads(response)

        return enriched_terms
