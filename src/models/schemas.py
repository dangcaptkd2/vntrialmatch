"""
Data models and schemas for the trial matching system.

This module defines Pydantic models for input/output data structures
used throughout the application.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field


class PatientProfile(BaseModel):
    """Patient profile data model."""

    patient_id: str = Field(..., description="Unique patient identifier")
    age: Optional[int] = Field(None, description="Patient age")
    gender: Optional[str] = Field(None, description="Patient gender")
    medical_conditions: List[str] = Field(
        default_factory=list, description="List of medical conditions"
    )
    medications: List[str] = Field(
        default_factory=list, description="List of current medications"
    )
    allergies: List[str] = Field(default_factory=list, description="List of allergies")
    symptoms: List[str] = Field(default_factory=list, description="List of symptoms")
    medical_history: Optional[str] = Field(None, description="Medical history text")
    current_treatments: List[str] = Field(
        default_factory=list, description="Current treatments"
    )
    lab_results: Optional[Dict[str, Any]] = Field(
        None, description="Laboratory results"
    )
    vital_signs: Optional[Dict[str, Any]] = Field(None, description="Vital signs")
    created_at: datetime = Field(
        default_factory=datetime.now, description="Profile creation timestamp"
    )


class TrialCriteria(BaseModel):
    """Clinical trial criteria data model."""

    nct_id: str = Field(..., description="NCT identifier")
    criteria_text: str = Field(..., description="Raw criteria text")
    criteria_type: str = Field(
        ..., description="Type of criteria (inclusion/exclusion)"
    )
    parsed_criteria: Optional[List[Dict[str, Any]]] = Field(
        None, description="Parsed criteria structure"
    )
    created_at: datetime = Field(
        default_factory=datetime.now, description="Criteria creation timestamp"
    )


class TrialData(BaseModel):
    """Clinical trial data model."""

    nct_id: str = Field(..., description="NCT identifier")
    brief_title: Optional[str] = Field(None, description="Brief trial title")
    official_title: Optional[str] = Field(None, description="Official trial title")
    description: Optional[str] = Field(None, description="Trial description")
    condition: Optional[str] = Field(None, description="Medical condition")
    intervention: Optional[str] = Field(None, description="Intervention type")
    status: Optional[str] = Field(None, description="Trial status")
    phase: Optional[str] = Field(None, description="Trial phase")
    enrollment: Optional[int] = Field(None, description="Enrollment target")
    criteria: Optional[List[TrialCriteria]] = Field(
        None, description="Eligibility criteria"
    )
    created_at: datetime = Field(
        default_factory=datetime.now, description="Trial data creation timestamp"
    )


class CriteriaMatch(BaseModel):
    """Criteria matching result model."""

    criteria_id: str = Field(..., description="Unique criteria identifier")
    criteria_text: str = Field(..., description="Original criteria text")
    criteria_type: str = Field(..., description="Inclusion or exclusion criteria")
    classification: str = Field(
        ..., description="Match classification (eligible/ineligible/unknown)"
    )
    confidence: float = Field(..., description="Confidence score (0-1)")
    reasoning: str = Field(..., description="Reasoning for classification")
    extracted_info: Optional[Dict[str, Any]] = Field(
        None, description="Extracted patient information"
    )
    created_at: datetime = Field(
        default_factory=datetime.now, description="Match creation timestamp"
    )


class TrialMatchResult(BaseModel):
    """Trial matching result model."""

    trial_id: str = Field(..., description="Trial NCT ID")
    match_score: float = Field(..., description="Overall match score (0-1)")
    eligible_criteria: int = Field(..., description="Number of eligible criteria")
    total_criteria: int = Field(..., description="Total number of criteria")
    criteria_matches: List[CriteriaMatch] = Field(
        default_factory=list, description="Individual criteria matches"
    )
    trial_data: Optional[TrialData] = Field(None, description="Trial information")
    created_at: datetime = Field(
        default_factory=datetime.now, description="Result creation timestamp"
    )


class SearchQuery(BaseModel):
    """Search query model."""

    query_text: str = Field(..., description="Search query text")
    patient_profile: Optional[PatientProfile] = Field(
        None, description="Patient profile for context"
    )
    max_results: int = Field(default=10, description="Maximum number of results")
    filters: Optional[Dict[str, Any]] = Field(None, description="Search filters")
    created_at: datetime = Field(
        default_factory=datetime.now, description="Query creation timestamp"
    )


class SearchResult(BaseModel):
    """Search result model."""

    trial_id: str = Field(..., description="Trial NCT ID")
    relevance_score: float = Field(..., description="Relevance score (0-1)")
    trial_data: TrialData = Field(..., description="Trial information")
    highlights: Optional[Dict[str, List[str]]] = Field(
        None, description="Search highlights"
    )
    created_at: datetime = Field(
        default_factory=datetime.now, description="Result creation timestamp"
    )


class MatchingRequest(BaseModel):
    """Trial matching request model."""

    patient_profile: PatientProfile = Field(..., description="Patient profile")
    trial_ids: List[str] = Field(..., description="List of trial NCT IDs to match")
    max_criteria_per_trial: int = Field(
        default=5, description="Maximum criteria to evaluate per trial"
    )
    include_reasoning: bool = Field(
        default=True, description="Include reasoning in results"
    )
    created_at: datetime = Field(
        default_factory=datetime.now, description="Request creation timestamp"
    )


class MatchingResponse(BaseModel):
    """Trial matching response model."""

    request_id: str = Field(..., description="Unique request identifier")
    patient_profile: PatientProfile = Field(..., description="Patient profile used")
    results: List[TrialMatchResult] = Field(
        default_factory=list, description="Matching results"
    )
    summary: Dict[str, Any] = Field(
        default_factory=dict, description="Summary statistics"
    )
    processing_time: float = Field(..., description="Processing time in seconds")
    created_at: datetime = Field(
        default_factory=datetime.now, description="Response creation timestamp"
    )


class PreprocessingRequest(BaseModel):
    """Data preprocessing request model."""

    data_type: str = Field(..., description="Type of data to preprocess")
    raw_data: Union[str, Dict[str, Any]] = Field(..., description="Raw data to process")
    preprocessing_options: Optional[Dict[str, Any]] = Field(
        None, description="Preprocessing options"
    )
    created_at: datetime = Field(
        default_factory=datetime.now, description="Request creation timestamp"
    )


class PreprocessingResponse(BaseModel):
    """Data preprocessing response model."""

    request_id: str = Field(..., description="Unique request identifier")
    processed_data: Dict[str, Any] = Field(..., description="Processed data")
    preprocessing_stats: Dict[str, Any] = Field(
        default_factory=dict, description="Preprocessing statistics"
    )
    processing_time: float = Field(..., description="Processing time in seconds")
    created_at: datetime = Field(
        default_factory=datetime.now, description="Response creation timestamp"
    )


class ErrorResponse(BaseModel):
    """Error response model."""

    error_code: str = Field(..., description="Error code")
    error_message: str = Field(..., description="Error message")
    details: Optional[Dict[str, Any]] = Field(
        None, description="Additional error details"
    )
    timestamp: datetime = Field(
        default_factory=datetime.now, description="Error timestamp"
    )


class HealthCheck(BaseModel):
    """Health check response model."""

    status: str = Field(..., description="Service status")
    version: str = Field(..., description="Service version")
    timestamp: datetime = Field(
        default_factory=datetime.now, description="Health check timestamp"
    )
    components: Dict[str, str] = Field(
        default_factory=dict, description="Component status"
    )
