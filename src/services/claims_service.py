import json
import os
from pathlib import Path
from typing import Any

import boto3
from botocore.exceptions import BotoCoreError, ClientError
from fastapi import HTTPException


class ClaimsService:
    def __init__(self, project_root: Path) -> None:
        self.mocks_dir = project_root / "mocks"
        self.claims_file = self.mocks_dir / "claims.json"
        self.notes_file = self.mocks_dir / "notes.json"

    def get_claim_or_404(self, claim_id: str) -> dict[str, Any]:
        claims = self._load_json(self.claims_file)
        claim = next((item for item in claims if item.get("id") == claim_id), None)
        if claim is None:
            raise HTTPException(status_code=404, detail=f"Claim not found: {claim_id}")
        return claim

    def summarize_claim_or_404(self, claim_id: str) -> dict[str, str]:
        claim = self.get_claim_or_404(claim_id)
        notes = self._get_notes_for_claim(claim_id)

        if not notes:
            raise HTTPException(
                status_code=404, detail=f"No notes found for claim: {claim_id}"
            )

        notes_text = " ".join(note.get("content", "") for note in notes)
        return self._summarize_with_bedrock_or_fallback(claim, notes_text)

    def _load_json(self, path: Path) -> list[dict[str, Any]]:
        if not path.exists():
            raise HTTPException(
                status_code=500, detail=f"Data file not found: {path.name}"
            )
        with path.open("r", encoding="utf-8") as file:
            return json.load(file)

    def _get_notes_for_claim(self, claim_id: str) -> list[dict[str, Any]]:
        notes = self._load_json(self.notes_file)
        return [item for item in notes if item.get("claimId") == claim_id]

    def _build_fallback_summary(
        self, claim: dict[str, Any], notes_text: str
    ) -> dict[str, str]:
        status = claim.get("status", "UNKNOWN")
        customer = claim.get("customer", "Customer")
        policy_number = claim.get("policyNumber", "N/A")

        overall = (
            f"Claim {claim['id']} for policy {policy_number} is currently {status}. "
            f"Notes indicate: {notes_text}"
        )
        customer_facing = (
            f"Hi {customer}, your claim ({claim['id']}) is currently marked as {status}. "
            "We are reviewing the latest documentation and will share the next update shortly."
        )
        adjuster_focused = (
            f"Claim {claim['id']} ({policy_number}) status={status}. "
            f"Latest notes summary: {notes_text}"
        )
        recommended_next_step = "Validate outstanding documents and update the claim timeline with the next adjudication checkpoint."

        return {
            "overallSummary": overall,
            "customerFacingSummary": customer_facing,
            "adjusterFocusedSummary": adjuster_focused,
            "recommendedNextStep": recommended_next_step,
            "source": "local-fallback",
        }

    def _summarize_with_bedrock_or_fallback(
        self, claim: dict[str, Any], notes_text: str
    ) -> dict[str, str]:
        model_id = os.getenv("BEDROCK_MODEL_ID")
        region = os.getenv("AWS_REGION", "us-east-1")

        if not model_id:
            return self._build_fallback_summary(claim, notes_text)

        prompt = (
            "You are an insurance claim assistant. Return strict JSON with keys: "
            "overallSummary, customerFacingSummary, adjusterFocusedSummary, recommendedNextStep. "
            f"Claim: {json.dumps(claim)}. Notes: {notes_text}"
        )

        try:
            client = boto3.client("bedrock-runtime", region_name=region)
            response = client.converse(
                modelId=model_id,
                messages=[{"role": "user", "content": [{"text": prompt}]}],
                inferenceConfig={"maxTokens": 400, "temperature": 0.2},
            )

            text_blocks = (
                response.get("output", {}).get("message", {}).get("content", [])
            )
            text = "".join(block.get("text", "") for block in text_blocks)
            parsed = json.loads(text)

            return {
                "overallSummary": parsed["overallSummary"],
                "customerFacingSummary": parsed["customerFacingSummary"],
                "adjusterFocusedSummary": parsed["adjusterFocusedSummary"],
                "recommendedNextStep": parsed["recommendedNextStep"],
                "source": "bedrock",
            }
        except (ClientError, BotoCoreError, ValueError, KeyError, json.JSONDecodeError):
            return self._build_fallback_summary(claim, notes_text)
