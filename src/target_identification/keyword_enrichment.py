import json

from utils.llm_utils import get_structured_llm_response
from utils.prompts import KEYWORD_ENRICHMENT_PROMPT, KEYWORD_ENRICHMENT_SYSTEM


class KeywordEnricher:
    def __init__(self):
        self.system_message = KEYWORD_ENRICHMENT_SYSTEM
        self.prompt_template = KEYWORD_ENRICHMENT_PROMPT
        self.response_format = {
            "type": "json_object",
            "properties": {
                "original_term": {
                    "type": "object",
                    "properties": {
                        "synonyms": {"type": "array", "items": {"type": "string"}},
                        "related_terms": {"type": "array", "items": {"type": "string"}},
                    },
                }
            },
        }

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
            all_keywords.extend(category)

        # Process each keyword
        enriched_terms = {}
        for keyword in all_keywords:
            prompt = self.prompt_template.format(keywords=keyword)
            response = get_structured_llm_response(
                prompt, self.system_message, self.response_format
            )
            enriched_terms[keyword] = json.loads(response)

        return enriched_terms
