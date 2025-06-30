import json

from src.utils.llm_utils import get_structured_llm_response
from src.utils.prompts import KEYWORD_EXTRACTION_PROMPT, KEYWORD_EXTRACTION_SYSTEM


class KeywordExtractor:
    def __init__(self):
        self.system_message = KEYWORD_EXTRACTION_SYSTEM
        self.prompt_template = KEYWORD_EXTRACTION_PROMPT
        self.response_format = {"type": "json_object"}

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


if __name__ == "__main__":
    extractor = KeywordExtractor()
    with open("data/patient_data/patient.1.1.txt", "r") as f:
        masked_profile = f.read()
    print(extractor.extract_keywords(masked_profile))