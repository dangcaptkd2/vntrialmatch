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

import streamlit as st

# Add src to path for imports
sys.path.append(str(Path(__file__).parent.parent.parent))

from src.core.pipeline import run_trial_matching_pipeline
from src.settings import settings

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Page configuration
st.set_page_config(
    page_title=settings.streamlit_title,
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


def display_trial_results(pipeline_response):
    """Display trial matching results in an expandable format."""

    results = pipeline_response.results

    if not results:
        st.warning("No trials found matching the patient profile.")
        return

    # Sort results by match score
    sorted_results = sorted(results, key=lambda x: x.match_score, reverse=True)

    # Display summary metrics
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Total Trials", len(results))
    with col2:
        st.metric("Trials with Matches", sum(1 for r in results if r.match_score > 0))
    with col3:
        avg_score = sum(r.match_score for r in results) / len(results) if results else 0
        st.metric("Average Match Score", f"{avg_score:.1%}")
    with col4:
        best_score = max(r.match_score for r in results) if results else 0
        st.metric("Best Match Score", f"{best_score:.1%}")

    st.markdown("---")

    # Display each trial
    for i, result in enumerate(sorted_results):
        # Trial header with basic info
        st.markdown(
            f"### 🏥 **{result.trial_id}** - Match Score: {result.match_score:.1%} ({result.eligible_criteria}/{result.total_criteria} criteria)"
        )

        col1, col2 = st.columns([2, 1])

        with col1:
            st.markdown(f"**Trial ID:** {result.trial_id}")
            st.markdown(f"**Match Score:** {result.match_score:.1%}")
            st.markdown(
                f"**Eligible Criteria:** {result.eligible_criteria}/{result.total_criteria}"
            )

        with col2:
            # Progress bar for match score
            st.progress(result.match_score)

            # Color-coded match score
            if result.match_score >= 0.7:
                st.success("High Match")
            elif result.match_score >= 0.4:
                st.warning("Medium Match")
            else:
                st.error("Low Match")

        # Display criteria matches in a simple list
        st.markdown("#### Criteria Analysis")

        for criteria_match in result.criteria_matches:
            icon = get_eligibility_icon(criteria_match.classification)

            # Display as simple text with icons
            if criteria_match.criteria_type == "whole":
                st.write(f"{icon} **Complete Eligibility Criteria**")
                st.write(f"**Status:** {criteria_match.classification.title()}")
                if criteria_match.reasoning:
                    st.write(f"**Overall Assessment:** {criteria_match.reasoning}")

                # Display additional whole criteria information
                if criteria_match.extracted_info:
                    info = criteria_match.extracted_info
                    if "overall_score" in info:
                        st.write(f"**Overall Score:** {info['overall_score']:.1%}")
                    if "key_factors" in info and info["key_factors"]:
                        st.write(
                            f"**Key Factors:** {', '.join(info['key_factors'][:3])}"
                        )
                    if "missing_information" in info and info["missing_information"]:
                        st.write(
                            f"**Missing Info:** {', '.join(info['missing_information'][:2])}"
                        )
            else:
                st.write(
                    f"{icon} **{criteria_match.criteria_text[:60]}{'...' if len(criteria_match.criteria_text) > 60 else ''}**"
                )
                st.write(f"**Status:** {criteria_match.classification.title()}")
                if criteria_match.reasoning:
                    st.write(f"**Reason:** {criteria_match.reasoning}")

            st.write("---")

        st.markdown("---")


def main():
    """Main Streamlit app function."""

    # Header
    st.markdown(
        f'<h1 class="main-header">🏥 {settings.streamlit_title}</h1>',
        unsafe_allow_html=True,
    )

    # Sidebar for configuration
    with st.sidebar:
        st.header("⚙️ Configuration")

        max_trials = st.slider("Maximum Trials to Analyze", 1, 10, 5)
        max_criteria = st.slider("Maximum Criteria per Trial", 5, 20, 10)

        # Classification mode selection
        classification_mode = st.selectbox(
            "Classification Mode",
            ["individual", "whole"],
            format_func=lambda x: "Individual Criteria"
            if x == "individual"
            else "Whole Criteria",
            help="Individual: Evaluate each criterion separately. Whole: Evaluate all criteria together.",
        )

        st.markdown("---")
        st.markdown("### 📊 About")
        st.markdown(settings.streamlit_description)

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
            with st.spinner("Running trial matching pipeline..."):
                try:
                    # Run the complete pipeline
                    pipeline_response = run_trial_matching_pipeline(
                        patient_profile=patient_profile,
                        max_trials=max_trials,
                        max_criteria_per_trial=max_criteria,
                        skip_masking=True,
                        include_reasoning=True,
                        classification_mode=classification_mode,
                    )

                    st.success(
                        f"Pipeline completed in {pipeline_response.processing_time:.2f} seconds!"
                    )

                    # Display results
                    display_trial_results(pipeline_response)

                    # Download results
                    results_dict = {
                        "request_id": pipeline_response.request_id,
                        "processing_time": pipeline_response.processing_time,
                        "summary": pipeline_response.summary,
                        "results": [
                            {
                                "trial_id": result.trial_id,
                                "match_score": result.match_score,
                                "eligible_criteria": result.eligible_criteria,
                                "total_criteria": result.total_criteria,
                                "criteria_matches": [
                                    {
                                        "criteria_text": match.criteria_text,
                                        "classification": match.classification,
                                        "reasoning": match.reasoning,
                                    }
                                    for match in result.criteria_matches
                                ],
                            }
                            for result in pipeline_response.results
                        ],
                    }

                    results_json = json.dumps(results_dict, indent=2)
                    st.download_button(
                        label="📥 Download Results (JSON)",
                        data=results_json,
                        file_name="trial_matching_results.json",
                        mime="application/json",
                    )

                except Exception as e:
                    st.error(f"Pipeline execution failed: {str(e)}")
                    logger.error(f"Pipeline error: {e}")

        elif search_button and not patient_profile.strip():
            st.warning("Please enter a patient profile before searching.")

        else:
            st.info(
                "Enter a patient profile and click 'Search Clinical Trials' to begin."
            )


if __name__ == "__main__":
    main()
