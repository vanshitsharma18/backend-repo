"""
AI analysis route — Phase 1 (rule-based) implementation.

The endpoint accepts a free-form incident message and returns a structured
diagnosis including predicted severity, root cause, and remediation advice.

Phase 2 will replace or augment the rule engine with Google Gemini.
"""

import logging

from fastapi import APIRouter, Depends

from app.services.analysis_service import (
    AnalysisRequest,
    AnalysisResponse,
    AnalysisService,
    get_analysis_service,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/analyze", tags=["Analysis"])


@router.post(
    "",
    response_model=AnalysisResponse,
    summary="Analyse an incident message",
    description=(
        "Accepts a free-form incident message and returns a structured analysis "
        "including severity, possible root cause, and a remediation recommendation. "
        "\n\n"
        "**Phase 1** — rule-based keyword matching. "
        "**Phase 2** — Google Gemini LLM integration (coming soon)."
    ),
)
async def analyse_incident(
    payload: AnalysisRequest,
    svc: AnalysisService = Depends(get_analysis_service),
) -> AnalysisResponse:
    result = svc.analyse(payload.message)
    logger.info(
        "POST /analyze → severity=%s cause=%r",
        result.severity,
        result.possible_root_cause[:60],
    )
    return result
