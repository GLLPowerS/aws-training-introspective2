import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import boto3
from botocore.exceptions import BotoCoreError, ClientError
from fastapi import HTTPException

from src.services.notes_service import NotesService


class ClaimsService:
    def __init__(
        self, project_root: Path, notes_service: NotesService | None = None
    ) -> None:
        self.mocks_dir = project_root / "mocks"
        self.claims_file = self.mocks_dir / "claims.json"
        self.aws_region = os.getenv("AWS_REGION", "us-east-1")
        self.claims_table_name = os.getenv("DYNAMODB_TABLE_NAME", "")
        self.notes_service = notes_service or NotesService(project_root=project_root)

    def create_claim(self, claim: dict[str, Any]) -> dict[str, Any]:
        claim_id = str(claim.get("id", "")).strip()
        if not claim_id:
            raise HTTPException(status_code=400, detail="Claim id is required")

        claim_to_store = {
            "id": claim_id,
            "status": str(claim.get("status", "")).strip(),
            "policyNumber": str(claim.get("policyNumber", "")).strip(),
            "customer": str(claim.get("customer", "")).strip(),
            "updatedAt": str(
                claim.get("updatedAt")
                or datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
            ),
        }

        if self.claims_table_name:
            try:
                self._put_claim_to_dynamodb(claim_to_store)
                return claim_to_store
            except HTTPException:
                raise
            except (ClientError, BotoCoreError) as error:
                raise HTTPException(
                    status_code=500,
                    detail=f"Failed to write claim to DynamoDB: {error}",
                ) from error

        self._put_claim_to_local_file(claim_to_store)
        return claim_to_store

    def get_claim_or_404(self, claim_id: str) -> dict[str, Any]:
        if self.claims_table_name:
            try:
                claim = self._get_claim_from_dynamodb(claim_id)
                if claim is not None:
                    return claim
            except (ClientError, BotoCoreError):
                pass

        claims = self._load_json(self.claims_file)
        claim = next((item for item in claims if item.get("id") == claim_id), None)
        if claim is None:
            raise HTTPException(status_code=404, detail=f"Claim not found: {claim_id}")
        return claim

    def get_claim_with_notes_or_404(self, claim_id: str) -> dict[str, Any]:
        claim = self.get_claim_or_404(claim_id)
        notes = self.notes_service.list_notes_for_claim(claim_id)
        return {**claim, "notes": notes}

    def list_notes_for_claim_or_404(self, claim_id: str) -> list[dict[str, Any]]:
        self.get_claim_or_404(claim_id)
        return self.notes_service.list_notes_for_claim(claim_id)

    def add_note_to_claim_or_404(self, claim_id: str, content: str) -> dict[str, Any]:
        self.get_claim_or_404(claim_id)
        return self.notes_service.add_note_to_claim(claim_id, content)

    def update_note_for_claim_or_404(
        self, claim_id: str, note_id: str, content: str
    ) -> dict[str, Any]:
        self.get_claim_or_404(claim_id)
        return self.notes_service.update_note_for_claim(claim_id, note_id, content)

    def delete_note_for_claim_or_404(
        self, claim_id: str, note_id: str
    ) -> dict[str, Any]:
        self.get_claim_or_404(claim_id)
        return self.notes_service.delete_note_for_claim(claim_id, note_id)

    def summarize_claim_or_404(self, claim_id: str) -> dict[str, str]:
        claim = self.get_claim_or_404(claim_id)
        notes = self.notes_service.list_notes_for_claim(claim_id)

        if not notes:
            raise HTTPException(
                status_code=404, detail=f"No notes found for claim: {claim_id}"
            )

        notes_text = " ".join(note.get("content", "") for note in notes)
        summary = self._summarize_with_bedrock_or_fallback(claim, notes_text)
        self._persist_summary_for_claim(claim_id, summary)
        return summary

    def _load_json(self, path: Path) -> list[dict[str, Any]]:
        if not path.exists():
            raise HTTPException(
                status_code=500, detail=f"Data file not found: {path.name}"
            )
        with path.open("r", encoding="utf-8") as file:
            return json.load(file)

    def _write_json(self, path: Path, data: list[dict[str, Any]]) -> None:
        with path.open("w", encoding="utf-8") as file:
            json.dump(data, file, indent=4)

    def _put_claim_to_local_file(self, claim: dict[str, Any]) -> None:
        claims = self._load_json(self.claims_file)
        exists = any(item.get("id") == claim["id"] for item in claims)
        if exists:
            raise HTTPException(
                status_code=409, detail=f"Claim already exists: {claim['id']}"
            )
        claims.append(claim)
        self._write_json(self.claims_file, claims)

    def _dynamodb_table(self):
        return boto3.resource("dynamodb", region_name=self.aws_region).Table(
            self.claims_table_name
        )

    def _map_dynamodb_item(self, item: dict[str, Any]) -> dict[str, Any]:
        return {
            "id": item.get("claim_id"),
            "status": item.get("status"),
            "policyNumber": item.get("policyNumber"),
            "customer": item.get("customer"),
            "updatedAt": item.get("updatedAt"),
            "summary": item.get("summary"),
        }

    def _get_claim_from_dynamodb(self, claim_id: str) -> dict[str, Any] | None:
        response = self._dynamodb_table().get_item(Key={"claim_id": claim_id})
        item = response.get("Item")
        if not item:
            return None
        return self._map_dynamodb_item(item)

    def _put_claim_to_dynamodb(self, claim: dict[str, Any]) -> None:
        try:
            self._dynamodb_table().put_item(
                Item={
                    "claim_id": claim["id"],
                    "status": claim["status"],
                    "policyNumber": claim["policyNumber"],
                    "customer": claim["customer"],
                    "updatedAt": claim["updatedAt"],
                },
                ConditionExpression="attribute_not_exists(claim_id)",
            )
        except ClientError as error:
            if (
                error.response.get("Error", {}).get("Code")
                == "ConditionalCheckFailedException"
            ):
                raise HTTPException(
                    status_code=409, detail=f"Claim already exists: {claim['id']}"
                ) from error
            raise

    def _persist_summary_for_claim(self, claim_id: str, summary: dict[str, str]) -> None:
        if self.claims_table_name:
            self._persist_summary_for_dynamodb_claim(claim_id, summary)
            return

        self._persist_summary_for_local_claim(claim_id, summary)

    def _persist_summary_for_local_claim(
        self, claim_id: str, summary: dict[str, str]
    ) -> None:
        claims = self._load_json(self.claims_file)
        claim_index = next(
            (index for index, item in enumerate(claims) if item.get("id") == claim_id),
            -1,
        )
        if claim_index == -1:
            raise HTTPException(status_code=404, detail=f"Claim not found: {claim_id}")

        claims[claim_index]["summary"] = summary
        claims[claim_index]["updatedAt"] = datetime.now(timezone.utc).isoformat().replace(
            "+00:00", "Z"
        )
        self._write_json(self.claims_file, claims)

    def _persist_summary_for_dynamodb_claim(
        self, claim_id: str, summary: dict[str, str]
    ) -> None:
        try:
            self._dynamodb_table().update_item(
                Key={"claim_id": claim_id},
                UpdateExpression="SET #summary = :summary, #updatedAt = :updatedAt",
                ExpressionAttributeNames={
                    "#summary": "summary",
                    "#updatedAt": "updatedAt",
                },
                ExpressionAttributeValues={
                    ":summary": summary,
                    ":updatedAt": datetime.now(timezone.utc)
                    .isoformat()
                    .replace("+00:00", "Z"),
                },
                ConditionExpression="attribute_exists(claim_id)",
            )
        except ClientError as error:
            if (
                error.response.get("Error", {}).get("Code")
                == "ConditionalCheckFailedException"
            ):
                raise HTTPException(
                    status_code=404, detail=f"Claim not found: {claim_id}"
                ) from error
            raise HTTPException(
                status_code=500,
                detail=f"Failed to persist claim summary in DynamoDB: {error}",
            ) from error

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
            "summary": overall,
            "customer-facing-summary": customer_facing,
            "adjuster-focused-summary": adjuster_focused,
            "recommended-next-step": recommended_next_step,
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
            "summary, customer-facing-summary, adjuster-focused-summary, recommended-next-step. "
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
                "summary": parsed["summary"],
                "customer-facing-summary": parsed["customer-facing-summary"],
                "adjuster-focused-summary": parsed["adjuster-focused-summary"],
                "recommended-next-step": parsed["recommended-next-step"],
            }
        except (ClientError, BotoCoreError, ValueError, KeyError, json.JSONDecodeError):
            return self._build_fallback_summary(claim, notes_text)
