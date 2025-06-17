from utils.llm_utils import get_llm_response
from utils.prompts import CRITERIA_MATCHING_PROMPT, CRITERIA_MATCHING_SYSTEM


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

        response = get_llm_response(prompt, self.system_message)

        # Parse the response to extract classification and explanation
        lines = response.strip().split("\n")
        classification = None
        explanation = []

        for line in lines:
            if line.lower().startswith(("eligible", "ineligible", "unknown")):
                classification = line.split(":")[0].strip().lower()
            else:
                explanation.append(line.strip())

        return {"classification": classification, "explanation": " ".join(explanation)}

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
