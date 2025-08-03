import json

from src.utils.openai_utils import get_structured_llm_response
from src.utils.prompts import (
    CRITERIA_MATCHING_PROMPT,
    CRITERIA_MATCHING_SYSTEM,
    WHOLE_CRITERIA_MATCHING_PROMPT,
    WHOLE_CRITERIA_MATCHING_SYSTEM,
)


class CriteriaMatcher:
    def __init__(self):
        self.system_message = CRITERIA_MATCHING_SYSTEM
        self.prompt_template = CRITERIA_MATCHING_PROMPT
        self.whole_criteria_system = WHOLE_CRITERIA_MATCHING_SYSTEM
        self.whole_criteria_prompt = WHOLE_CRITERIA_MATCHING_PROMPT

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

    def match_whole_criteria(self, patient_profile, eligibility_criteria):
        """
        Evaluate whether a patient meets the entire eligibility criteria as a whole.

        Args:
            patient_profile (str): Patient profile text
            eligibility_criteria (str): Complete eligibility criteria text

        Returns:
            dict: Matching result with classification and explanation
        """
        prompt = self.whole_criteria_prompt.format(
            patient_profile=patient_profile, eligibility_criteria=eligibility_criteria
        )

        response_format = {"type": "json_object"}
        response = get_structured_llm_response(
            prompt, self.whole_criteria_system, response_format
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
                "overall_score": result.get("overall_score", 0.0),
                "eligible_criteria_count": result.get("eligible_criteria_count", 0),
                "total_criteria_count": result.get("total_criteria_count", 0),
            }
        except json.JSONDecodeError:
            return {
                "classification": "unknown",
                "explanation": "Invalid JSON response",
                "overall_score": 0.0,
                "eligible_criteria_count": 0,
                "total_criteria_count": 0,
            }

    def match_all_criteria(
        self, patient_profile, criteria_list, classification_mode="individual"
    ):
        """
        Evaluate patient against criteria using specified classification mode.

        Args:
            patient_profile (str): Patient profile text
            criteria_list (list): List of clinical trial criteria
            classification_mode (str): "individual" for per-criterion or "whole" for entire criteria

        Returns:
            list: List of matching results
        """
        if classification_mode == "whole":
            # Join all criteria into one text and evaluate as a whole
            eligibility_criteria = "\n".join(criteria_list)
            result = self.match_whole_criteria(patient_profile, eligibility_criteria)
            return [{"criterion": "whole_eligibility_criteria", "result": result}]

        elif classification_mode == "individual":
            # Evaluate each criterion individually
            results = []
            for criterion in criteria_list:
                result = self.match_criterion(patient_profile, criterion)
                results.append({"criterion": criterion, "result": result})
            return results

        else:
            raise ValueError("classification_mode must be 'individual' or 'whole'")
