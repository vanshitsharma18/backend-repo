"""
Firestore service — data access layer for the incidents collection.

All Firestore interactions are encapsulated here so that routes
remain thin and unit-testable via dependency injection.
"""

import logging
import os
from datetime import datetime, timezone
from typing import Any

from fastapi import HTTPException, status
from google.api_core.exceptions import NotFound
from google.cloud import firestore

from app.config.settings import get_settings
from app.models.incident import IncidentCreate, IncidentResponse, IncidentSummary

logger = logging.getLogger(__name__)

settings = get_settings()


class FirestoreService:
    """Wrapper around the Google Cloud Firestore client."""

    def __init__(self) -> None:
        # Allow the Firestore emulator for local development.
        emulator_host = settings.firestore_emulator_host or os.getenv(
            "FIRESTORE_EMULATOR_HOST", ""
        )
        if emulator_host:
            os.environ["FIRESTORE_EMULATOR_HOST"] = emulator_host
            logger.info("Using Firestore emulator at %s", emulator_host)

        self._client: firestore.AsyncClient = firestore.AsyncClient(
            project=settings.project_id
        )
        self._collection: str = settings.firestore_collection

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _incidents_ref(self) -> firestore.AsyncCollectionReference:
        return self._client.collection(self._collection)

    def _counter_ref(self) -> firestore.AsyncDocumentReference:
        """Reference to the metadata document that tracks the auto-increment ID."""
        return self._client.collection("_meta").document("incident_counter")

    async def _next_incident_id(self) -> str:
        """
        Atomically increment the global counter and return 'INC-{n:03d}'.

        Uses a Firestore transaction to prevent race conditions under
        concurrent writes.
        """
        counter_ref = self._counter_ref()

        @firestore.async_transactional
        async def _txn(transaction: firestore.AsyncTransaction) -> int:
            snapshot = await counter_ref.get(transaction=transaction)
            current = snapshot.get("count") if snapshot.exists else 0
            next_count = current + 1
            transaction.set(counter_ref, {"count": next_count})
            return next_count

        transaction = self._client.transaction()
        next_val = await _txn(transaction)
        return f"INC-{next_val:03d}"

    @staticmethod
    def _doc_to_response(data: dict[str, Any]) -> IncidentResponse:
        return IncidentResponse(**data)

    @staticmethod
    def _doc_to_summary(data: dict[str, Any]) -> IncidentSummary:
        return IncidentSummary(
            incident_id=data["incident_id"],
            service=data["service"],
            severity=data["severity"],
            status=data["status"],
        )

    # ------------------------------------------------------------------
    # CRUD operations
    # ------------------------------------------------------------------

    async def create_incident(self, payload: IncidentCreate) -> str:
        """
        Persist a new incident and return its generated ID.

        Args:
            payload: Validated incident creation payload.

        Returns:
            The newly assigned incident_id (e.g. 'INC-001').
        """
        incident_id = await self._next_incident_id()
        doc: dict[str, Any] = {
            "incident_id": incident_id,
            "service": payload.service,
            "severity": payload.severity.value,
            "message": payload.message,
            "status": "open",
            "created_at": datetime.now(tz=timezone.utc),
        }

        await self._incidents_ref().document(incident_id).set(doc)
        logger.info("Created incident %s", incident_id)
        return incident_id

    async def get_all_incidents(self) -> list[IncidentSummary]:
        """Return a summary list of all incidents, newest first."""
        docs = (
            await self._incidents_ref()
            .order_by("created_at", direction=firestore.Query.DESCENDING)
            .get()
        )
        return [self._doc_to_summary(d.to_dict()) for d in docs]  # type: ignore[arg-type]

    async def get_incident(self, incident_id: str) -> IncidentResponse:
        """
        Retrieve a single incident by ID.

        Raises:
            HTTPException 404: If the document does not exist.
        """
        doc = await self._incidents_ref().document(incident_id).get()
        if not doc.exists:
            logger.warning("Incident %s not found", incident_id)
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Incident '{incident_id}' not found.",
            )
        return self._doc_to_response(doc.to_dict())  # type: ignore[arg-type]

    async def update_incident(self, incident_id: str, new_status: str) -> None:
        """
        Update the status of an existing incident.

        Raises:
            HTTPException 404: If the document does not exist.
        """
        doc_ref = self._incidents_ref().document(incident_id)
        doc = await doc_ref.get()
        if not doc.exists:
            logger.warning("Update failed — incident %s not found", incident_id)
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Incident '{incident_id}' not found.",
            )
        await doc_ref.update({"status": new_status})
        logger.info("Updated incident %s → status=%s", incident_id, new_status)

    async def delete_incident(self, incident_id: str) -> None:
        """
        Delete an incident document.

        Raises:
            HTTPException 404: If the document does not exist.
        """
        doc_ref = self._incidents_ref().document(incident_id)
        doc = await doc_ref.get()
        if not doc.exists:
            logger.warning("Delete failed — incident %s not found", incident_id)
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Incident '{incident_id}' not found.",
            )
        await doc_ref.delete()
        logger.info("Deleted incident %s", incident_id)


# ---------------------------------------------------------------------------
# FastAPI dependency
# ---------------------------------------------------------------------------

_firestore_service: FirestoreService | None = None


def get_firestore_service() -> FirestoreService:
    """
    Dependency factory that returns a singleton FirestoreService.

    Using a module-level singleton keeps connection setup costs at startup
    rather than per-request.
    """
    global _firestore_service
    if _firestore_service is None:
        _firestore_service = FirestoreService()
    return _firestore_service
