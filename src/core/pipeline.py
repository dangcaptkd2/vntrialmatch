"""
Main pipeline orchestrator for trial matching system.

This module coordinates the execution of preprocessing, target identification,
and criterion matching components to provide a complete trial matching solution.
"""

import logging
import time
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from src.core.criterion_matching.matcher import CriteriaMatcher
from src.core.target_identification.search import ClinicalTrialSearcher
from src.models.schemas import (
    CriteriaMatch,
    MatchingResponse,
    PatientProfile,
    TrialMatchResult,
)
from src.utils import aact_utils

logger = logging.getLogger(__name__)


@dataclass
class PipelineConfig:
    """Configuration for the trial matching pipeline."""

    max_trials: int = 10
    max_criteria_per_trial: int = 10
    skip_masking: bool = False
    include_reasoning: bool = True
    search_size: int = 20


class TrialMatchingPipeline:
    """Main orchestrator for the trial matching pipeline."""

    def __init__(self, config: Optional[PipelineConfig] = None):
        """Initialize the pipeline with configuration."""
        self.config = config or PipelineConfig()
        self.searcher = ClinicalTrialSearcher()
        self.matcher = CriteriaMatcher()
        self.logger = logging.getLogger(__name__)

    def run_pipeline(self, patient_profile: str) -> MatchingResponse:
        """
        Execute the complete trial matching pipeline.

        Args:
            patient_profile: Patient profile text

        Returns:
            MatchingResponse with complete results
        """
        start_time = time.time()

        try:
            self.logger.info("Starting trial matching pipeline")

            # Step 1: Target Identification - Search for relevant trials
            self.logger.info(
                "Step 1: Target Identification - Searching for relevant trials"
            )
            search_results = self._search_trials(patient_profile)

            if not search_results["trials"]:
                self.logger.warning("No trials found matching the patient profile")
                return self._create_empty_response(
                    patient_profile, time.time() - start_time
                )

            # Step 2: Criterion Matching - Evaluate patient against trial criteria
            self.logger.info("Step 2: Criterion Matching - Evaluating trial criteria")
            matching_results = self._match_criteria(
                patient_profile, search_results["trials"]
            )

            # Step 3: Compile final results
            self.logger.info("Step 3: Compiling final results")
            final_results = self._compile_results(search_results, matching_results)

            processing_time = time.time() - start_time
            self.logger.info(f"Pipeline completed in {processing_time:.2f} seconds")

            return MatchingResponse(
                request_id=f"req_{int(time.time())}",
                patient_profile=PatientProfile(
                    patient_id="patient_1", medical_history=patient_profile
                ),
                results=final_results,
                summary=self._create_summary(final_results),
                processing_time=processing_time,
            )

        except Exception as e:
            self.logger.error(f"Pipeline execution failed: {str(e)}")
            raise

    def _search_trials(self, patient_profile: str) -> Dict[str, Any]:
        """
        Search for relevant clinical trials.

        Args:
            patient_profile: Patient profile text

        Returns:
            Dictionary containing search results
        """
        search_results = self.searcher.run_full_pipeline(
            patient_profile_text=patient_profile,
            size=self.config.search_size,
            skip_masking=self.config.skip_masking,
        )

        formatted_results = self.searcher.format_search_results(
            search_results["search_results"]
        )

        trials = [
            trial["nct_id"] for trial in formatted_results[: self.config.max_trials]
        ]

        return {
            "trials": trials,
            "search_results": search_results,
            "formatted_results": formatted_results,
        }

    def _match_criteria(
        self, patient_profile: str, trial_ids: List[str]
    ) -> List[TrialMatchResult]:
        """
        Match patient against trial criteria.

        Args:
            patient_profile: Patient profile text
            trial_ids: List of trial NCT IDs

        Returns:
            List of trial matching results
        """
        results = []

        for i, nct_id in enumerate(trial_ids):
            self.logger.info(f"Processing trial {i + 1}/{len(trial_ids)}: {nct_id}")

            # Get criteria for this trial
            criteria = aact_utils.get_criteria_by_nct_id(nct_id)
            criteria_list = aact_utils.parse_clinical_trial_criteria(criteria)

            # Limit criteria per trial
            if len(criteria_list) > self.config.max_criteria_per_trial:
                criteria_list = criteria_list[: self.config.max_criteria_per_trial]

            # Match patient against criteria
            matching_results = self.matcher.match_all_criteria(
                patient_profile, criteria_list
            )

            # Convert to structured format
            criteria_matches = []
            for match in matching_results:
                criteria_matches.append(
                    CriteriaMatch(
                        criteria_id=f"{nct_id}_{len(criteria_matches)}",
                        criteria_text=match["criterion"],
                        criteria_type="inclusion"
                        if "inclusion" in match["criterion"].lower()
                        else "exclusion",
                        classification=match["result"]["classification"],
                        confidence=0.8,  # Default confidence
                        reasoning=match["result"]["explanation"]
                        if self.config.include_reasoning
                        else "",
                        extracted_info={},
                    )
                )

            # Calculate overall trial match score
            eligible_count = sum(
                1 for match in criteria_matches if match.classification == "eligible"
            )
            total_criteria = len(criteria_matches)
            match_score = eligible_count / total_criteria if total_criteria > 0 else 0

            # Create trial match result
            trial_result = TrialMatchResult(
                trial_id=nct_id,
                match_score=match_score,
                eligible_criteria=eligible_count,
                total_criteria=total_criteria,
                criteria_matches=criteria_matches,
            )

            results.append(trial_result)

        return results

    def _compile_results(
        self, search_results: Dict[str, Any], matching_results: List[TrialMatchResult]
    ) -> List[TrialMatchResult]:
        """
        Compile final results combining search and matching data.

        Args:
            search_results: Results from trial search
            matching_results: Results from criteria matching

        Returns:
            Compiled results with additional metadata
        """
        # Add trial data to matching results
        for result in matching_results:
            # Find corresponding trial data from search results
            for trial_data in search_results["formatted_results"]:
                if trial_data["nct_id"] == result.trial_id:
                    # Add trial data to result
                    result.trial_data = trial_data
                    break

        return matching_results

    def _create_summary(self, results: List[TrialMatchResult]) -> Dict[str, Any]:
        """
        Create summary statistics from results.

        Args:
            results: List of trial matching results

        Returns:
            Summary statistics dictionary
        """
        if not results:
            return {
                "total_trials": 0,
                "trials_with_matches": 0,
                "average_match_score": 0.0,
                "best_match_score": 0.0,
            }

        total_trials = len(results)
        trials_with_matches = sum(1 for r in results if r.match_score > 0)
        average_score = sum(r.match_score for r in results) / total_trials
        best_score = max(r.match_score for r in results)

        return {
            "total_trials": total_trials,
            "trials_with_matches": trials_with_matches,
            "average_match_score": average_score,
            "best_match_score": best_score,
        }

    def _create_empty_response(
        self, patient_profile: str, processing_time: float
    ) -> MatchingResponse:
        """
        Create empty response when no trials are found.

        Args:
            patient_profile: Patient profile text
            processing_time: Processing time

        Returns:
            Empty matching response
        """
        return MatchingResponse(
            request_id=f"req_{int(time.time())}",
            patient_profile=PatientProfile(
                patient_id="patient_1", medical_history=patient_profile
            ),
            results=[],
            summary=self._create_summary([]),
            processing_time=processing_time,
        )


def run_trial_matching_pipeline(
    patient_profile: str,
    max_trials: int = 10,
    max_criteria_per_trial: int = 10,
    skip_masking: bool = False,
    include_reasoning: bool = True,
) -> MatchingResponse:
    """
    Convenience function to run the trial matching pipeline.

    Args:
        patient_profile: Patient profile text
        max_trials: Maximum number of trials to analyze
        max_criteria_per_trial: Maximum criteria to evaluate per trial
        skip_masking: Whether to skip patient data masking
        include_reasoning: Whether to include reasoning in results

    Returns:
        MatchingResponse with complete results
    """
    config = PipelineConfig(
        max_trials=max_trials,
        max_criteria_per_trial=max_criteria_per_trial,
        skip_masking=skip_masking,
        include_reasoning=include_reasoning,
    )

    pipeline = TrialMatchingPipeline(config)
    return pipeline.run_pipeline(patient_profile)


if __name__ == "__main__":
    run_trial_matching_pipeline(
        patient_profile="data/patient_data/patient.1.1.txt",
        max_trials=2,
        max_criteria_per_trial=2,
        skip_masking=True,
        include_reasoning=True,
    )
