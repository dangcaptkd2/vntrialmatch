#!/usr/bin/env python3
"""
Streamlit app for clinical trial matching system.
Provides a beautiful interface for:
1. Inputting patient profiles
2. Searching for relevant clinical trials
3. Matching patient against trial criteria
4. Displaying results with expandable components
"""

import json
import logging
import sys
from pathlib import Path
from typing import Dict, List

import streamlit as st

# Add src to path for imports
sys.path.append(str(Path(__file__).parent / "src"))

from src.criterion_matching.matcher import CriteriaMatcher
from src.target_identification.search import ClinicalTrialSearcher
from src.utils import aact_utils

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Page configuration
st.set_page_config(
    page_title="Clinical Trial Matching System",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS for better styling
st.markdown(
    """
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .trial-card {
        background-color: #f8f9fa;
        border: 1px solid #dee2e6;
        border-radius: 10px;
        padding: 1rem;
        margin-bottom: 1rem;
    }
    .criteria-item {
        background-color: white;
        border: 1px solid #e9ecef;
        border-radius: 5px;
        padding: 0.5rem;
        margin: 0.25rem 0;
    }
    .eligible { border-left: 4px solid #28a745; }
    .ineligible { border-left: 4px solid #dc3545; }
    .unknown { border-left: 4px solid #ffc107; }
    .metric-card {
        background-color: #f8f9fa;
        border-radius: 10px;
        padding: 1rem;
        text-align: center;
    }
</style>
""",
    unsafe_allow_html=True,
)


def get_eligibility_icon(classification: str) -> str:
    """Get appropriate icon for eligibility classification."""
    icons = {"eligible": "✅", "ineligible": "❌", "unknown": "❓"}
    return icons.get(classification, "❓")


def get_eligibility_color(classification: str) -> str:
    """Get appropriate color for eligibility classification."""
    colors = {"eligible": "#28a745", "ineligible": "#dc3545", "unknown": "#ffc107"}
    return colors.get(classification, "#6c757d")


def match_patient_to_trials(patient_profile: str, trials: List[str]) -> List[Dict]:
    """
    Match patient against all trial criteria.

    Args:
        patient_profile: Patient profile text
        trials: List of trial NCT IDs

    Returns:
        List of trial matching results
    """
    matcher = CriteriaMatcher()
    results = []

    progress_bar = st.progress(0)
    status_text = st.empty()

    for i, nct_id in enumerate(trials):
        status_text.text(f"Processing trial {i + 1}/{len(trials)}: {nct_id}")
        progress_bar.progress((i + 1) / len(trials))

        # Get criteria for this trial
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

    progress_bar.empty()
    status_text.empty()
    return results


def display_trial_results(results: List[Dict]):
    """Display trial matching results in an expandable format."""

    # Sort results by match score
    sorted_results = sorted(results, key=lambda x: x["match_score"], reverse=True)

    # Display summary metrics
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Total Trials", len(results))
    with col2:
        st.metric(
            "Trials with Matches", sum(1 for r in results if r["match_score"] > 0)
        )
    with col3:
        avg_score = (
            sum(r["match_score"] for r in results) / len(results) if results else 0
        )
        st.metric("Average Match Score", f"{avg_score:.1%}")
    with col4:
        best_score = max(r["match_score"] for r in results) if results else 0
        st.metric("Best Match Score", f"{best_score:.1%}")

    # Style metric cards (removed dependency)

    st.markdown("---")

    # Display each trial
    for i, result in enumerate(sorted_results):
        # Trial header with basic info
        st.markdown(
            f"### 🏥 **{result['trial_id']}** - Match Score: {result['match_score']:.1%} ({result['eligible_criteria']}/{result['total_criteria']} criteria)"
        )

        col1, col2 = st.columns([2, 1])

        with col1:
            st.markdown(f"**Trial ID:** {result['trial_id']}")
            st.markdown(f"**Match Score:** {result['match_score']:.1%}")
            st.markdown(
                f"**Eligible Criteria:** {result['eligible_criteria']}/{result['total_criteria']}"
            )

        with col2:
            # Progress bar for match score
            st.progress(result["match_score"])

            # Color-coded match score
            if result["match_score"] >= 0.7:
                st.success("High Match")
            elif result["match_score"] >= 0.4:
                st.warning("Medium Match")
            else:
                st.error("Low Match")

        # Display criteria matches in a simple list
        st.markdown("#### Criteria Analysis")

        for criteria_match in result["criteria_matches"]:
            criterion = criteria_match["criterion"]
            match_result = criteria_match["result"]
            classification = match_result["classification"]
            explanation = match_result["explanation"]

            icon = get_eligibility_icon(classification)

            # Display as simple text with icons
            st.write(
                f"{icon} **{criterion[:60]}{'...' if len(criterion) > 60 else ''}**"
            )
            st.write(f"**Status:** {classification.title()}")
            st.write(f"**Reason:** {explanation}")
            st.write("---")

        st.markdown("---")


def main():
    """Main Streamlit app function."""

    # Header
    st.markdown(
        '<h1 class="main-header">🏥 Clinical Trial Matching System</h1>',
        unsafe_allow_html=True,
    )

    # Sidebar for configuration
    with st.sidebar:
        st.header("⚙️ Configuration")

        max_trials = st.slider("Maximum Trials to Analyze", 1, 10, 5)
        max_criteria = st.slider("Maximum Criteria per Trial", 5, 20, 10)

        st.markdown("---")
        st.markdown("### 📊 About")
        st.markdown("""
        This system helps match patients with appropriate clinical trials using:
        - **AI-powered keyword extraction**
        - **Semantic search** in clinical trial database
        - **Intelligent criteria matching**
        """)

    # Main content area
    col1, col2 = st.columns([1, 1])

    with col1:
        st.header("👤 Patient Profile")

        # Patient profile input
        patient_profile = st.text_area(
            "Enter patient profile:",
            height=400,
            placeholder="Enter the patient's medical profile, including diagnosis, treatments, demographics, etc...",
        )

        # Load sample profile button
        if st.button("📄 Load Sample Profile"):
            try:
                with open("data/patient_data/patient.1.1.txt", "r") as f:
                    patient_profile = f.read()
                st.success("Sample profile loaded!")
            except FileNotFoundError:
                st.error("Sample profile file not found!")

        # Search button
        search_button = st.button(
            "🔍 Search Clinical Trials", type="primary", use_container_width=True
        )

    with col2:
        st.header("📋 Results")

        if search_button and patient_profile.strip():
            with st.spinner("Searching for clinical trials..."):
                # Initialize searcher
                searcher = ClinicalTrialSearcher()

                search_results = searcher.run_full_pipeline(
                    patient_profile_text=patient_profile,
                    size=max_trials,
                    skip_masking=True,
                )
                formatted_results = searcher.format_search_results(
                    search_results["search_results"]
                )
                trials = [trial["nct_id"] for trial in formatted_results]

                if not trials:
                    st.warning("No trials found matching the patient profile.")
                    return

                st.success(f"Found {len(trials)} clinical trials!")

                # Match patient against criteria
                with st.spinner("Analyzing trial criteria..."):
                    results = match_patient_to_trials(patient_profile, trials)

                # Display results
                display_trial_results(results)

                # Download results
                results_json = json.dumps(results, indent=2)
                st.download_button(
                    label="📥 Download Results (JSON)",
                    data=results_json,
                    file_name="trial_matching_results.json",
                    mime="application/json",
                )

        elif search_button and not patient_profile.strip():
            st.warning("Please enter a patient profile before searching.")

        else:
            st.info(
                "Enter a patient profile and click 'Search Clinical Trials' to begin."
            )


if __name__ == "__main__":
    main()
