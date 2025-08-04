"""
Search evaluation module for clinical trial matching system.

This module evaluates the search performance using ground truth data from CSV files.
It compares search results with and without keyword enrichment.
"""

import json
import logging
import time
from pathlib import Path
from typing import Dict, List, Optional

import pandas as pd
from tqdm import tqdm

from src.core.target_identification.search import ClinicalTrialSearcher

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SearchEvaluator:
    """Evaluates search performance using ground truth data."""

    def __init__(
        self,
        data_dir: str = "data/csv",
        results_dir: str = "results/eval",
        use_cache: bool = True,
    ):
        """
        Initialize the search evaluator.

        Args:
            data_dir: Directory containing CSV data files
            results_dir: Directory to save evaluation results
            use_cache: Whether to use caching for keyword operations
        """
        self.data_dir = Path(data_dir)
        self.results_dir = Path(results_dir)
        self.results_dir.mkdir(parents=True, exist_ok=True)
        self.use_cache = use_cache

        # Initialize searchers for both modes
        self.searcher_enriched = ClinicalTrialSearcher(
            use_cache=use_cache, use_enriched_keywords=True
        )
        self.searcher_basic = ClinicalTrialSearcher(
            use_cache=use_cache, use_enriched_keywords=False
        )

    def load_ground_truth_data(self) -> pd.DataFrame:
        """
        Load all ground truth data from CSV files.

        Returns:
            Combined DataFrame with all data
        """
        logger.info("Loading ground truth data...")

        # Load all CSV files
        train_df = pd.read_csv(self.data_dir / "train.csv")
        test_df = pd.read_csv(self.data_dir / "test.csv")
        validation_df = pd.read_csv(self.data_dir / "validation.csv")

        # Combine all data
        combined_df = pd.concat([train_df, test_df, validation_df], ignore_index=True)

        logger.info(f"Loaded {len(combined_df)} total records")
        logger.info(f"Unique topics: {combined_df['topic_id'].nunique()}")
        logger.info(f"Unique trials: {combined_df['NCT_id'].nunique()}")

        return combined_df

    def get_ground_truth_for_topic(self, df: pd.DataFrame, topic_id: int) -> List[str]:
        """
        Get ground truth NCT IDs for a specific topic.

        Args:
            df: DataFrame with ground truth data
            topic_id: Topic ID to get ground truth for

        Returns:
            List of NCT IDs that are ground truth for this topic
        """
        topic_data = df[df["topic_id"] == topic_id]
        return topic_data["NCT_id"].unique().tolist()

    def calculate_metrics(
        self, retrieved_trials: List[str], ground_truth_trials: List[str], k: int = 20
    ) -> Dict[str, float]:
        """
        Calculate evaluation metrics.

        Args:
            retrieved_trials: List of retrieved trial IDs
            ground_truth_trials: List of ground truth trial IDs
            k: Number of top results to consider for precision@k

        Returns:
            Dictionary with evaluation metrics
        """
        if not retrieved_trials:
            return {"precision@k": 0.0, "recall@k": 0.0, "f1@k": 0.0}

        # Calculate precision@k and recall@k
        top_k_retrieved = retrieved_trials[:k]
        relevant_in_top_k = len(set(top_k_retrieved) & set(ground_truth_trials))

        precision_at_k = (
            relevant_in_top_k / len(top_k_retrieved) if top_k_retrieved else 0.0
        )
        recall_at_k = (
            relevant_in_top_k / len(ground_truth_trials) if ground_truth_trials else 0.0
        )
        f1_at_k = (
            2 * (precision_at_k * recall_at_k) / (precision_at_k + recall_at_k)
            if (precision_at_k + recall_at_k) > 0
            else 0.0
        )

        return {"precision@k": precision_at_k, "recall@k": recall_at_k, "f1@k": f1_at_k}

    def evaluate_search_mode(
        self,
        df: pd.DataFrame,
        use_enriched: bool = True,
        max_topics: Optional[int] = None,
        top_k: int = 20,
    ) -> Dict:
        """
        Evaluate search performance for a specific mode.

        Args:
            df: Ground truth DataFrame
            use_enriched: Whether to use enriched keywords
            max_topics: Maximum number of topics to evaluate (for testing)

        Returns:
            Dictionary with evaluation results
        """
        searcher = self.searcher_enriched if use_enriched else self.searcher_basic
        mode_name = "enriched" if use_enriched else "basic"

        logger.info(f"Evaluating {mode_name} search mode...")

        # Get unique topics
        unique_topics = df["topic_id"].unique()
        if max_topics:
            unique_topics = unique_topics[:max_topics]

        all_metrics = []
        topic_results = []

        for topic_id in tqdm(unique_topics, desc=f"Evaluating {mode_name}"):
            # Get patient profile for this topic
            topic_data = df[df["topic_id"] == topic_id].iloc[0]
            patient_profile = topic_data["statement_medical"]

            # Get ground truth
            ground_truth_trials = self.get_ground_truth_for_topic(df, topic_id)

            try:
                # Run search
                search_results = searcher.run_full_pipeline(
                    patient_profile_text=patient_profile, size=top_k, skip_masking=True
                )

                # Extract retrieved trial IDs
                retrieved_trials = [
                    hit["_source"]["nct_id"]
                    for hit in search_results["search_results"]["hits"]["hits"]
                ]

                # Calculate metrics
                metrics = self.calculate_metrics(retrieved_trials, ground_truth_trials)

                # Store results
                topic_result = {
                    "topic_id": int(topic_id),  # Convert numpy int64 to Python int
                    "patient_profile": (
                        patient_profile[:200] + "..."
                        if len(patient_profile) > 200
                        else patient_profile
                    ),
                    "ground_truth_trials": ground_truth_trials,
                    "retrieved_trials": retrieved_trials,
                    "metrics": metrics,
                }

                all_metrics.append(metrics)
                topic_results.append(topic_result)

            except Exception as e:
                logger.error(f"Error evaluating topic {topic_id}: {e}")
                # Add default metrics for failed cases
                all_metrics.append(
                    {
                        "precision@k": 0.0,
                        "recall@k": 0.0,
                        "f1@k": 0.0,
                    }
                )

        # Calculate average metrics
        avg_metrics = {}
        for metric in ["precision@k", "recall@k", "f1@k"]:
            avg_metrics[metric] = sum(m[metric] for m in all_metrics) / len(all_metrics)

        return {
            "mode": mode_name,
            "total_topics": len(unique_topics),
            "average_metrics": avg_metrics,
            "topic_results": topic_results,
        }

    def run_evaluation(
        self,
        max_topics: Optional[int] = None,
        save_detailed_results: bool = True,
        top_k: int = 20,
    ) -> Dict:
        """
        Run complete evaluation comparing both search modes.

        Args:
            max_topics: Maximum number of topics to evaluate (for testing)
            save_detailed_results: Whether to save detailed results to files

        Returns:
            Dictionary with complete evaluation results
        """
        logger.info("Starting search evaluation...")
        start_time = time.time()

        # Load ground truth data
        df = self.load_ground_truth_data()

        # Evaluate both modes
        enriched_results = self.evaluate_search_mode(
            df, use_enriched=True, max_topics=max_topics, top_k=top_k
        )
        basic_results = self.evaluate_search_mode(
            df, use_enriched=False, max_topics=max_topics, top_k=top_k
        )

        # Compile final results
        evaluation_results = {
            "evaluation_timestamp": time.time(),
            "total_topics_evaluated": enriched_results["total_topics"],
            "enriched_mode": enriched_results,
            "basic_mode": basic_results,
            "comparison": {
                "precision@k": {
                    "enriched": enriched_results["average_metrics"]["precision@k"],
                    "basic": basic_results["average_metrics"]["precision@k"],
                    "improvement": enriched_results["average_metrics"]["precision@k"]
                    - basic_results["average_metrics"]["precision@k"],
                },
                "recall@k": {
                    "enriched": enriched_results["average_metrics"]["recall@k"],
                    "basic": basic_results["average_metrics"]["recall@k"],
                    "improvement": enriched_results["average_metrics"]["recall@k"]
                    - basic_results["average_metrics"]["recall@k"],
                },
                "f1@k": {
                    "enriched": enriched_results["average_metrics"]["f1@k"],
                    "basic": basic_results["average_metrics"]["f1@k"],
                    "improvement": enriched_results["average_metrics"]["f1@k"]
                    - basic_results["average_metrics"]["f1@k"],
                },
            },
        }

        # Save results
        if save_detailed_results:
            self.save_evaluation_results(evaluation_results)

        evaluation_time = time.time() - start_time
        logger.info(f"Evaluation completed in {evaluation_time:.2f} seconds")

        return evaluation_results

    def save_evaluation_results(self, results: Dict):
        """Save evaluation results to files."""
        timestamp = int(time.time())

        # Convert numpy types to native Python types for JSON serialization
        def convert_numpy_types(obj):
            if isinstance(obj, dict):
                return {k: convert_numpy_types(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [convert_numpy_types(item) for item in obj]
            elif hasattr(obj, "item"):  # numpy types
                return obj.item()
            else:
                return obj

        # Convert results
        results_converted = convert_numpy_types(results)

        # Save summary results
        summary_file = self.results_dir / f"search_evaluation_summary_{timestamp}.json"
        with open(summary_file, "w") as f:
            json.dump(results_converted, f, indent=2)

        # Save detailed topic results
        detailed_file = (
            self.results_dir / f"search_evaluation_detailed_{timestamp}.json"
        )
        detailed_results = {
            "enriched_topic_results": results_converted["enriched_mode"][
                "topic_results"
            ],
            "basic_topic_results": results_converted["basic_mode"]["topic_results"],
        }
        with open(detailed_file, "w") as f:
            json.dump(detailed_results, f, indent=2)

        logger.info(f"Results saved to {summary_file} and {detailed_file}")

    def print_evaluation_summary(self, results: Dict):
        """Print a formatted summary of evaluation results."""
        print("\n" + "=" * 80)
        print("SEARCH EVALUATION RESULTS SUMMARY")
        print("=" * 80)

        print(f"\nTotal topics evaluated: {results['total_topics_evaluated']}")

        print("\n" + "-" * 40)
        print("AVERAGE METRICS")
        print("-" * 40)

        metrics = ["precision@k", "recall@k", "f1@k"]
        print(f"{'Metric':<15} {'Enriched':<10} {'Basic':<10} {'Improvement':<12}")
        print("-" * 50)

        for metric in metrics:
            enriched_val = results["enriched_mode"]["average_metrics"][metric]
            basic_val = results["basic_mode"]["average_metrics"][metric]
            improvement = results["comparison"][metric]["improvement"]

            print(
                f"{metric:<15} {enriched_val:<10.4f} {basic_val:<10.4f} {improvement:+<12.4f}"
            )

        print("\n" + "-" * 40)
        print("RECOMMENDATION")
        print("-" * 40)

        improvement_pct = abs(results["comparison"]["f1@k"]["improvement"]) * 100

        if results["comparison"]["f1@k"]["improvement"] > 0:
            print(f"✅ Enriched keyword mode performs better by {improvement_pct:.2f}%")
        else:
            print(f"✅ Basic keyword mode performs better by {improvement_pct:.2f}%")

        print("=" * 80)


def main():
    """Run the search evaluation."""
    evaluator = SearchEvaluator()

    # Run evaluation with a subset for testing (remove max_topics for full evaluation)
    results = evaluator.run_evaluation(
        max_topics=10, top_k=100
    )  # Change to None for full evaluation

    # Print summary
    evaluator.print_evaluation_summary(results)


if __name__ == "__main__":
    main()
