from pathlib import Path
from typing import Any

from fastapi import FastAPI
from pydantic import BaseModel

from src.services.claims_service import ClaimsService
from src.services.notes_service import NotesService

BASE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BASE_DIR.parent


class ClaimSummaryResponse(BaseModel):
    claimId: str
    overallSummary: str
    customerFacingSummary: str
    adjusterFocusedSummary: str
    recommendedNextStep: str
    source: str


class ClaimCreateRequest(BaseModel):
    id: str
    status: str
    policyNumber: str
    customer: str
    updatedAt: str | None = None


class NoteCreateRequest(BaseModel):
    content: str


class NoteUpdateRequest(BaseModel):
    content: str


app = FastAPI(title="Claim Status API", version="0.1.0")
notes_service = NotesService(project_root=PROJECT_ROOT)
claims_service = ClaimsService(project_root=PROJECT_ROOT, notes_service=notes_service)


@app.get("/claims/{claim_id}")
def get_claim(claim_id: str) -> dict[str, Any]:
    return claims_service.get_claim_with_notes_or_404(claim_id)


@app.post("/claims")
def create_claim(payload: ClaimCreateRequest) -> dict[str, Any]:
    return claims_service.create_claim(payload.model_dump(exclude_none=True))


@app.get("/claims/{claim_id}/notes")
def get_claim_notes(claim_id: str) -> list[dict[str, Any]]:
    claims_service.get_claim_or_404(claim_id)
    return notes_service.list_notes_for_claim(claim_id)


@app.post("/claims/{claim_id}/notes")
def create_claim_note(claim_id: str, payload: NoteCreateRequest) -> dict[str, Any]:
    claims_service.get_claim_or_404(claim_id)
    return notes_service.add_note_to_claim(claim_id, payload.content)


@app.put("/claims/{claim_id}/notes/{note_id}")
def update_claim_note(
    claim_id: str, note_id: str, payload: NoteUpdateRequest
) -> dict[str, Any]:
    claims_service.get_claim_or_404(claim_id)
    return notes_service.update_note_for_claim(claim_id, note_id, payload.content)


@app.delete("/claims/{claim_id}/notes/{note_id}")
def delete_claim_note(claim_id: str, note_id: str) -> dict[str, Any]:
    claims_service.get_claim_or_404(claim_id)
    return notes_service.delete_note_for_claim(claim_id, note_id)


@app.post("/claims/{claim_id}/summarize", response_model=ClaimSummaryResponse)
def summarize_claim(claim_id: str) -> ClaimSummaryResponse:
    summary = claims_service.summarize_claim_or_404(claim_id)

    return ClaimSummaryResponse(claimId=claim_id, **summary)
