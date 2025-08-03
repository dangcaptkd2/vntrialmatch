import json

from src.utils.openai_utils import get_structured_llm_response
from src.utils.prompts import CRITERIA_MATCHING_PROMPT, CRITERIA_MATCHING_SYSTEM


class CriteriaMatcher:
    def __init__(self):
        self.system_message = CRITERIA_MATCHING_SYSTEM
        self.prompt_template = CRITERIA_MATCHING_PROMPT

    def match_criterion(self, patient_profile, criterion):
        """
        Evaluate whether a patient meets a specific criterion.

        Args:
            patient_profile (str): Patient profile text
            criterion (str): Clinical trial criterion to evaluate

        Returns:
            dict: Matching result with classification and explanation
        """
        prompt = self.prompt_template.format(
            patient_profile=patient_profile, criterion=criterion
        )

        response_format = {"type": "json_object"}
        response = get_structured_llm_response(
            prompt, self.system_message, response_format
        )

        # Parse the JSON response
        if response is None:
            return {
                "classification": "unknown",
                "explanation": "No response from LLM",
            }

        try:
            result = json.loads(response)
            return {
                "classification": result.get("classification", "unknown"),
                "explanation": result.get("explanation", "No explanation provided"),
            }
        except json.JSONDecodeError:
            return {
                "classification": "unknown",
                "explanation": "Invalid JSON response",
            }

    def match_all_criteria(self, patient_profile, criteria_list):
        """
        Evaluate patient against all criteria.

        Args:
            patient_profile (str): Patient profile text
            criteria_list (list): List of clinical trial criteria

        Returns:
            list: List of matching results for each criterion
        """
        results = []
        for criterion in criteria_list:
            result = self.match_criterion(patient_profile, criterion)
            results.append({"criterion": criterion, "result": result})
        return results
