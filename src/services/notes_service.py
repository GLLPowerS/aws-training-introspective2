import json
import os
from pathlib import Path
from typing import Any

import boto3
from boto3.dynamodb.conditions import Key
from botocore.exceptions import BotoCoreError, ClientError
from fastapi import HTTPException


class NotesService:
    def __init__(self, project_root: Path) -> None:
        self.mocks_dir = project_root / "mocks"
        self.notes_file = self.mocks_dir / "notes.json"
        self.aws_region = os.getenv("AWS_REGION", "us-east-1")
        self.notes_table_name = os.getenv("DYNAMODB_NOTES_TABLE_NAME", "")

    def list_notes_for_claim(self, claim_id: str) -> list[dict[str, Any]]:
        if self.notes_table_name:
            try:
                response = self._notes_dynamodb_table().query(
                    KeyConditionExpression=Key("claim_id").eq(claim_id),
                )
                items = response.get("Items", [])
                notes = [self._map_dynamodb_note_item(item) for item in items]
                return sorted(notes, key=lambda note: note["noteId"])
            except (ClientError, BotoCoreError):
                pass

        notes = self._load_json(self.notes_file)
        return [item for item in notes if item.get("claimId") == claim_id]

    def add_note_to_claim(self, claim_id: str, content: str) -> dict[str, Any]:
        normalized_content = content.strip()
        if not normalized_content:
            raise HTTPException(status_code=400, detail="Note content is required")

        if self.notes_table_name:
            try:
                note_id = self._next_note_id(self.list_notes_for_claim(claim_id))
                note = {
                    "claimId": claim_id,
                    "noteId": note_id,
                    "content": normalized_content,
                }
                self._put_note_to_dynamodb(note)
                return note
            except HTTPException:
                raise
            except (ClientError, BotoCoreError) as error:
                raise HTTPException(
                    status_code=500,
                    detail=f"Failed to write note to DynamoDB: {error}",
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

        if self.notes_table_name:
            existing_note = self._get_note_from_dynamodb(claim_id, note_id)
            if not existing_note:
                raise HTTPException(
                    status_code=404,
                    detail=f"Note not found: {note_id} for claim {claim_id}",
                )

            note = {
                "claimId": claim_id,
                "noteId": note_id,
                "content": normalized_content,
            }
            try:
                self._put_note_to_dynamodb(note)
                return note
            except (ClientError, BotoCoreError) as error:
                raise HTTPException(
                    status_code=500,
                    detail=f"Failed to update note in DynamoDB: {error}",
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
        if self.notes_table_name:
            existing_note = self._get_note_from_dynamodb(claim_id, note_id)
            if not existing_note:
                raise HTTPException(
                    status_code=404,
                    detail=f"Note not found: {note_id} for claim {claim_id}",
                )

            try:
                self._delete_note_from_dynamodb(claim_id, note_id)
                return {
                    "deleted": True,
                    "claimId": claim_id,
                    "noteId": note_id,
                }
            except (ClientError, BotoCoreError) as error:
                raise HTTPException(
                    status_code=500,
                    detail=f"Failed to delete note from DynamoDB: {error}",
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

    def _notes_dynamodb_table(self):
        return boto3.resource("dynamodb", region_name=self.aws_region).Table(
            self.notes_table_name
        )

    def _map_dynamodb_note_item(self, item: dict[str, Any]) -> dict[str, Any]:
        return {
            "claimId": item.get("claim_id"),
            "noteId": item.get("note_id"),
            "content": item.get("content", ""),
        }

    def _get_note_from_dynamodb(
        self, claim_id: str, note_id: str
    ) -> dict[str, Any] | None:
        response = self._notes_dynamodb_table().get_item(
            Key={"claim_id": claim_id, "note_id": note_id}
        )
        item = response.get("Item")
        if not item:
            return None
        return self._map_dynamodb_note_item(item)

    def _put_note_to_dynamodb(self, note: dict[str, Any]) -> None:
        self._notes_dynamodb_table().put_item(
            Item={
                "claim_id": note["claimId"],
                "note_id": note["noteId"],
                "content": note["content"],
            }
        )

    def _delete_note_from_dynamodb(self, claim_id: str, note_id: str) -> None:
        self._notes_dynamodb_table().delete_item(
            Key={"claim_id": claim_id, "note_id": note_id}
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
