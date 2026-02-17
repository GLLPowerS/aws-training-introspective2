import json
import os
from pathlib import Path
from typing import Any

import boto3
from botocore.exceptions import BotoCoreError, ClientError
from fastapi import HTTPException


class NotesService:
    def __init__(self, project_root: Path) -> None:
        self.mocks_dir = project_root / "mocks"
        self.notes_file = self.mocks_dir / "notes.json"
        self.aws_region = os.getenv("AWS_REGION", "us-east-1")
        self.notes_bucket_name = os.getenv("NOTES_S3_BUCKET_NAME", "")
        self.notes_s3_key = os.getenv("NOTES_S3_OBJECT_KEY", "notes.json")

    def list_notes_for_claim(self, claim_id: str) -> list[dict[str, Any]]:
        if self.notes_bucket_name:
            try:
                notes = self._load_notes_from_s3()
                return [item for item in notes if item.get("claimId") == claim_id]
            except (ClientError, BotoCoreError):
                pass

        notes = self._load_json(self.notes_file)
        return [item for item in notes if item.get("claimId") == claim_id]

    def add_note_to_claim(self, claim_id: str, content: str) -> dict[str, Any]:
        normalized_content = content.strip()
        if not normalized_content:
            raise HTTPException(status_code=400, detail="Note content is required")

        if self.notes_bucket_name:
            try:
                note_id = self._next_note_id(self.list_notes_for_claim(claim_id))
                note = {
                    "claimId": claim_id,
                    "noteId": note_id,
                    "content": normalized_content,
                }
                notes = self._load_notes_from_s3()
                notes.append(note)
                self._write_notes_to_s3(notes)
                return note
            except HTTPException:
                raise
            except (ClientError, BotoCoreError) as error:
                raise HTTPException(
                    status_code=500,
                    detail=f"Failed to write note to S3: {error}",
                ) from error

        notes = self._load_json(self.notes_file)
        note = {
            "claimId": claim_id,
            "noteId": self._next_note_id(notes),
            "content": normalized_content,
        }
        notes.append(note)
        self._write_json(self.notes_file, notes)
        return note

    def update_note_for_claim(
        self, claim_id: str, note_id: str, content: str
    ) -> dict[str, Any]:
        normalized_content = content.strip()
        if not normalized_content:
            raise HTTPException(status_code=400, detail="Note content is required")

        if self.notes_bucket_name:
            notes = self._load_notes_from_s3()
            note_index = next(
                (
                    index
                    for index, item in enumerate(notes)
                    if item.get("claimId") == claim_id and item.get("noteId") == note_id
                ),
                -1,
            )
            if note_index == -1:
                raise HTTPException(
                    status_code=404,
                    detail=f"Note not found: {note_id} for claim {claim_id}",
                )

            try:
                notes[note_index]["content"] = normalized_content
                self._write_notes_to_s3(notes)
                return notes[note_index]
            except (ClientError, BotoCoreError) as error:
                raise HTTPException(
                    status_code=500,
                    detail=f"Failed to update note in S3: {error}",
                ) from error

        notes = self._load_json(self.notes_file)
        note_index = next(
            (
                index
                for index, item in enumerate(notes)
                if item.get("claimId") == claim_id and item.get("noteId") == note_id
            ),
            -1,
        )
        if note_index == -1:
            raise HTTPException(
                status_code=404,
                detail=f"Note not found: {note_id} for claim {claim_id}",
            )

        notes[note_index]["content"] = normalized_content
        self._write_json(self.notes_file, notes)
        return notes[note_index]

    def delete_note_for_claim(self, claim_id: str, note_id: str) -> dict[str, Any]:
        if self.notes_bucket_name:
            notes = self._load_notes_from_s3()
            note_index = next(
                (
                    index
                    for index, item in enumerate(notes)
                    if item.get("claimId") == claim_id and item.get("noteId") == note_id
                ),
                -1,
            )
            if note_index == -1:
                raise HTTPException(
                    status_code=404,
                    detail=f"Note not found: {note_id} for claim {claim_id}",
                )

            try:
                deleted_note = notes.pop(note_index)
                self._write_notes_to_s3(notes)
                return {
                    "deleted": True,
                    "claimId": claim_id,
                    "noteId": deleted_note.get("noteId"),
                }
            except (ClientError, BotoCoreError) as error:
                raise HTTPException(
                    status_code=500,
                    detail=f"Failed to delete note from S3: {error}",
                ) from error

        notes = self._load_json(self.notes_file)
        note_index = next(
            (
                index
                for index, item in enumerate(notes)
                if item.get("claimId") == claim_id and item.get("noteId") == note_id
            ),
            -1,
        )
        if note_index == -1:
            raise HTTPException(
                status_code=404,
                detail=f"Note not found: {note_id} for claim {claim_id}",
            )

        deleted_note = notes.pop(note_index)
        self._write_json(self.notes_file, notes)
        return {
            "deleted": True,
            "claimId": claim_id,
            "noteId": deleted_note.get("noteId"),
        }

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

    def _s3_client(self):
        return boto3.client("s3", region_name=self.aws_region)

    def _load_notes_from_s3(self) -> list[dict[str, Any]]:
        try:
            response = self._s3_client().get_object(
                Bucket=self.notes_bucket_name,
                Key=self.notes_s3_key,
            )
            raw = response["Body"].read().decode("utf-8")
            data = json.loads(raw)
            if isinstance(data, list):
                return data
            return []
        except ClientError as error:
            code = error.response.get("Error", {}).get("Code", "")
            if code in {"NoSuchKey", "NoSuchBucket"}:
                return []
            raise

    def _write_notes_to_s3(self, notes: list[dict[str, Any]]) -> None:
        payload = json.dumps(notes, indent=4).encode("utf-8")
        self._s3_client().put_object(
            Bucket=self.notes_bucket_name,
            Key=self.notes_s3_key,
            Body=payload,
            ContentType="application/json",
        )

    def _next_note_id(self, notes: list[dict[str, Any]]) -> str:
        max_numeric_id = 0
        for note in notes:
            note_id = str(note.get("noteId", ""))
            if not note_id.startswith("N-"):
                continue

            numeric_part = note_id[2:]
            if numeric_part.isdigit():
                max_numeric_id = max(max_numeric_id, int(numeric_part))

        return f"N-{max_numeric_id + 1:03d}"
