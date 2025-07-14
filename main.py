#!/usr/bin/env python3
"""
Main script for clinical trial matching system.
This script orchestrates the process of:
1. Searching for relevant clinical trials using patient profile
2. Matching patient against trial criteria
"""

import json
import logging
import sys
from pathlib import Path
from typing import Dict, List

# Add src to path for imports
sys.path.append(str(Path(__file__).parent / "src"))

from src.criterion_matching.matcher import CriteriaMatcher
from src.target_identification.search import ClinicalTrialSearcher
from src.utils import aact_utils

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("trial_matching.log"),
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger(__name__)


def load_patient_profile(profile_path: str) -> str:
    """
    Load patient profile from file.

    Args:
        profile_path: Path to patient profile file

    Returns:
        Patient profile text
    """
    try:
        with open(profile_path, "r", encoding="utf-8") as f:
            return f.read().strip()
    except FileNotFoundError:
        logger.error(f"Patient profile file not found: {profile_path}")
        raise
    except Exception as e:
        logger.error(f"Error reading patient profile: {e}")
        raise


def match_patient_to_trials(
    patient_profile: str, trials: List[str], max_criteria_per_trial: int = 5
) -> List[Dict]:
    """
    Match patient against all trial criteria.

    Args:
        patient_profile: Patient profile text
        trials: List of trial dictionaries
        max_criteria_per_trial: Maximum number of criteria to evaluate per trial

    Returns:
        List of trial matching results
    """
    matcher = CriteriaMatcher()
    results = []

    for i, nct_id in enumerate(trials):
        logger.info(f"Processing trial {i + 1}/{len(trials)}: {nct_id}")

        print("nct_id", nct_id)
        criteria = aact_utils.get_criteria_by_nct_id(nct_id)
        criteria_list = aact_utils.parse_clinical_trial_criteria(criteria)

        # Match patient against criteria
        matching_results = matcher.match_all_criteria(patient_profile, criteria_list)

        # Calculate overall trial match score
        eligible_count = sum(
            1
            for result in matching_results
            if result["result"]["classification"] == "eligible"
        )
        total_criteria = len(matching_results)
        match_score = eligible_count / total_criteria if total_criteria > 0 else 0

        results.append(
            {
                "trial_id": nct_id,
                "match_score": match_score,
                "eligible_criteria": eligible_count,
                "total_criteria": total_criteria,
                "criteria_matches": matching_results,
            }
        )
    return results


def save_results(results: List[Dict], output_path: str):
    """
    Save matching results to JSON file.

    Args:
        results: List of trial matching results
        output_path: Path to save results
    """
    try:
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        logger.info(f"Results saved to {output_path}")
    except Exception as e:
        logger.error(f"Error saving results: {e}")
        raise


def print_summary(results: List[Dict]):
    """
    Print a summary of matching results.

    Args:
        results: List of trial matching results
    """
    print("\n" + "=" * 80)
    print("CLINICAL TRIAL MATCHING RESULTS SUMMARY")
    print("=" * 80)

    # Sort by match score
    sorted_results = sorted(results, key=lambda x: x["match_score"], reverse=True)

    print(f"\nTotal trials analyzed: {len(results)}")
    print(
        f"Trials with at least one eligible criterion: {sum(1 for r in results if r['match_score'] > 0)}"
    )

    print("\nTop 5 matching trials:")
    print("-" * 80)

    for i, result in enumerate(sorted_results[:5]):
        print(f"   Trial ID: {result['trial_id']}")
        print(
            f"   Match Score: {result['match_score']:.2%} ({result['eligible_criteria']}/{result['total_criteria']} criteria)"
        )
        print()

    print("=" * 80)


def main(
    patient_profile_path: str = "data/patient_data/patient.1.1.txt",
    output_path: str = "results/trial_matching_results.json",
    max_trials: int = 2,
    max_criteria_per_trial: int = 5,
):
    """
    Main function to run the clinical trial matching pipeline.

    Args:
        patient_profile_path: Path to patient profile file
        output_path: Path to save results
        max_trials: Maximum number of trials to analyze
        max_criteria_per_trial: Maximum criteria to evaluate per trial
    """
    try:
        logger.info("Starting clinical trial matching pipeline")

        # Load patient profile
        logger.info(f"Loading patient profile from {patient_profile_path}")
        patient_profile = load_patient_profile(patient_profile_path)
        logger.info(f"Patient profile loaded ({len(patient_profile)} characters)")

        # Initialize trial searcher
        logger.info("Initializing trial searcher")
        searcher = ClinicalTrialSearcher()

        # Run full search pipeline
        logger.info("Running trial search pipeline")
        search_results = searcher.run_full_pipeline(
            patient_profile_path=patient_profile_path,
            size=max_trials,
            skip_masking=True,
        )
        formatted_results = searcher.format_search_results(
            search_results["search_results"]
        )
        trials = [trial["nct_id"] for trial in formatted_results]
        logger.info(f"Found {len(trials)} trials")

        if not trials:
            logger.warning("No trials found matching the patient profile")
            return

        # Match patient against trial criteria
        logger.info("Matching patient against trial criteria")
        results = match_patient_to_trials(
            patient_profile=patient_profile,
            trials=trials,
            max_criteria_per_trial=max_criteria_per_trial,
        )

        # Create output directory if it doesn't exist
        output_dir = Path(output_path).parent
        output_dir.mkdir(parents=True, exist_ok=True)

        # Save results
        save_results(results, output_path)

        # Print summary
        print_summary(results)

        logger.info("Clinical trial matching pipeline completed successfully")

    except Exception as e:
        logger.error(f"Error in main pipeline: {e}")
        raise


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Clinical Trial Matching System")
    parser.add_argument(
        "--patient-profile",
        default="data/patient_data/patient.1.1.txt",
        help="Path to patient profile file",
    )
    parser.add_argument(
        "--output",
        default="results/trial_matching_results.json",
        help="Path to save results",
    )
    parser.add_argument(
        "--max-trials", type=int, default=2, help="Maximum number of trials to analyze"
    )
    parser.add_argument(
        "--max-criteria",
        type=int,
        default=10,
        help="Maximum criteria to evaluate per trial",
    )

    args = parser.parse_args()

    main(
        patient_profile_path=args.patient_profile,
        output_path=args.output,
        max_trials=args.max_trials,
        max_criteria_per_trial=args.max_criteria,
    )
