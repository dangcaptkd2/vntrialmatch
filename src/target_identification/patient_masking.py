from utils.llm_utils import get_llm_response
from utils.prompts import PATIENT_MASKING_PROMPT, PATIENT_MASKING_SYSTEM


class PatientMasker:
    def __init__(self):
        self.system_message = PATIENT_MASKING_SYSTEM
        self.prompt_template = PATIENT_MASKING_PROMPT

    def mask_patient_data(self, patient_profile):
        """
        Mask sensitive patient information in the profile.

        Args:
            patient_profile (str): Original patient profile text

        Returns:
            str: Masked patient profile
        """
        prompt = self.prompt_template.format(patient_profile=patient_profile)
        masked_profile = get_llm_response(prompt, self.system_message)
        return masked_profile
