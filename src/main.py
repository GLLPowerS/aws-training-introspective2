from pathlib import Path
from typing import Any

from fastapi import FastAPI
from pydantic import BaseModel

from src.services.claims_service import ClaimsService

BASE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BASE_DIR.parent


class ClaimSummaryResponse(BaseModel):
    claimId: str
    overallSummary: str
    customerFacingSummary: str
    adjusterFocusedSummary: str
    recommendedNextStep: str
    source: str


app = FastAPI(title="Claim Status API", version="0.1.0")
claims_service = ClaimsService(project_root=PROJECT_ROOT)


@app.get("/claims/{claim_id}")
def get_claim(claim_id: str) -> dict[str, Any]:
    return claims_service.get_claim_or_404(claim_id)


@app.post("/claims/{claim_id}/summarize", response_model=ClaimSummaryResponse)
def summarize_claim(claim_id: str) -> ClaimSummaryResponse:
    summary = claims_service.summarize_claim_or_404(claim_id)

    return ClaimSummaryResponse(claimId=claim_id, **summary)
