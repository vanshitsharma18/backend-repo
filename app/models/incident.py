"""Pydantic models for incident-related request/response payloads."""

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Enumerations
# ---------------------------------------------------------------------------

class SeverityEnum(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"
    critical = "critical"


class StatusEnum(str, Enum):
    open = "open"
    investigating = "investigating"
    resolved = "resolved"


# ---------------------------------------------------------------------------
# Request models
# ---------------------------------------------------------------------------

class IncidentCreate(BaseModel):
    """Payload for POST /incidents."""

    service: str = Field(
        ...,
        min_length=1,
        max_length=128,
        description="Name of the affected service.",
        examples=["payment-service"],
    )
    severity: SeverityEnum = Field(
        ...,
        description="Incident severity level.",
        examples=["high"],
    )
    message: str = Field(
        ...,
        min_length=1,
        max_length=2048,
        description="Short description of the incident.",
        examples=["Database connection timeout"],
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "service": "payment-service",
                "severity": "high",
                "message": "Database connection timeout",
            }
        }
    }


class IncidentUpdate(BaseModel):
    """Payload for PATCH /incidents/{incident_id}."""

    status: StatusEnum = Field(
        ...,
        description="New status to assign to the incident.",
        examples=["resolved"],
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "status": "resolved",
            }
        }
    }


# ---------------------------------------------------------------------------
# Response models
# ---------------------------------------------------------------------------

class IncidentSummary(BaseModel):
    """Lightweight model returned in list responses."""

    incident_id: str
    service: str
    severity: SeverityEnum
    status: StatusEnum


class IncidentResponse(BaseModel):
    """Full incident model returned for single-record responses."""

    incident_id: str
    service: str
    severity: SeverityEnum
    message: str
    status: StatusEnum
    created_at: datetime

    model_config = {
        "json_schema_extra": {
            "example": {
                "incident_id": "INC-001",
                "service": "payment-service",
                "severity": "high",
                "message": "Database connection timeout",
                "status": "open",
                "created_at": "2026-06-02T10:00:00Z",
            }
        }
    }


class CreateIncidentResponse(BaseModel):
    """Response returned after successfully creating an incident."""

    message: str = "Incident created successfully"
    incident_id: str


class MessageResponse(BaseModel):
    """Generic message-only response."""

    message: str
