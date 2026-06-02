"""
Incident CRUD routes.

All database operations are delegated to FirestoreService via
FastAPI dependency injection, keeping routes thin and testable.
"""

import logging

from fastapi import APIRouter, Depends, status

from app.models.incident import (
    CreateIncidentResponse,
    IncidentCreate,
    IncidentResponse,
    IncidentSummary,
    IncidentUpdate,
    MessageResponse,
)
from app.services.firestore_service import FirestoreService, get_firestore_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/incidents", tags=["Incidents"])


@router.post(
    "",
    response_model=CreateIncidentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new incident",
    description=(
        "Creates a new operational incident record in Firestore. "
        "The `incident_id`, `status`, and `created_at` fields are generated automatically."
    ),
)
async def create_incident(
    payload: IncidentCreate,
    svc: FirestoreService = Depends(get_firestore_service),
) -> CreateIncidentResponse:
    incident_id = await svc.create_incident(payload)
    logger.info("POST /incidents → created %s", incident_id)
    return CreateIncidentResponse(
        message="Incident created successfully",
        incident_id=incident_id,
    )


@router.get(
    "",
    response_model=list[IncidentSummary],
    summary="List all incidents",
    description="Returns a summary list of all incidents ordered by creation time (newest first).",
)
async def list_incidents(
    svc: FirestoreService = Depends(get_firestore_service),
) -> list[IncidentSummary]:
    incidents = await svc.get_all_incidents()
    logger.info("GET /incidents → returned %d records", len(incidents))
    return incidents


@router.get(
    "/{incident_id}",
    response_model=IncidentResponse,
    summary="Get incident by ID",
    description="Retrieves the full detail of a single incident by its ID (e.g. `INC-001`).",
    responses={
        404: {"description": "Incident not found"},
    },
)
async def get_incident(
    incident_id: str,
    svc: FirestoreService = Depends(get_firestore_service),
) -> IncidentResponse:
    incident = await svc.get_incident(incident_id)
    logger.info("GET /incidents/%s → found", incident_id)
    return incident


@router.patch(
    "/{incident_id}",
    response_model=MessageResponse,
    summary="Update incident status",
    description=(
        "Updates the status of an existing incident. "
        "Allowed values: `open`, `investigating`, `resolved`."
    ),
    responses={
        404: {"description": "Incident not found"},
    },
)
async def update_incident(
    incident_id: str,
    payload: IncidentUpdate,
    svc: FirestoreService = Depends(get_firestore_service),
) -> MessageResponse:
    await svc.update_incident(incident_id, payload.status.value)
    logger.info("PATCH /incidents/%s → status=%s", incident_id, payload.status)
    return MessageResponse(message="Incident updated successfully")


@router.delete(
    "/{incident_id}",
    response_model=MessageResponse,
    summary="Delete an incident",
    description="Permanently removes an incident record from Firestore.",
    responses={
        404: {"description": "Incident not found"},
    },
)
async def delete_incident(
    incident_id: str,
    svc: FirestoreService = Depends(get_firestore_service),
) -> MessageResponse:
    await svc.delete_incident(incident_id)
    logger.info("DELETE /incidents/%s → deleted", incident_id)
    return MessageResponse(message="Incident deleted successfully")
