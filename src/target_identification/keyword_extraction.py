import json

from utils.llm_utils import get_structured_llm_response
from utils.prompts import KEYWORD_EXTRACTION_PROMPT, KEYWORD_EXTRACTION_SYSTEM


class KeywordExtractor:
    def __init__(self):
        self.system_message = KEYWORD_EXTRACTION_SYSTEM
        self.prompt_template = KEYWORD_EXTRACTION_PROMPT
        self.response_format = {
            "type": "json_object",
            "properties": {
                "medical_conditions": {"type": "array", "items": {"type": "string"}},
                "biomarkers": {"type": "array", "items": {"type": "string"}},
                "treatments": {"type": "array", "items": {"type": "string"}},
                "demographics": {"type": "array", "items": {"type": "string"}},
                "other_relevant_info": {"type": "array", "items": {"type": "string"}},
            },
        }

    def extract_keywords(self, masked_profile):
        """
        Extract relevant keywords from masked patient profile.

        Args:
            masked_profile (str): Masked patient profile text

        Returns:
            dict: Extracted keywords in structured format
        """
        prompt = self.prompt_template.format(masked_profile=masked_profile)
        response = get_structured_llm_response(
            prompt, self.system_message, self.response_format
        )
        return json.loads(response)
