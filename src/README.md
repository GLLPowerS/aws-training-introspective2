# Service Source

Place API source code here.

Required endpoints:
- `POST /claims`
- `GET /claims/{id}` (returns claim with `notes`)
- `GET /claims/{id}/notes`
- `POST /claims/{id}/notes`
- `PUT /claims/{id}/notes/{noteId}`
- `DELETE /claims/{id}/notes/{noteId}`
- `POST /claims/{id}/summarize`

## Run Locally

1. Install dependencies:
	- `pip install -r src/requirements.txt`
2. Start the API:
	- `uvicorn src.main:app --host 0.0.0.0 --port 8080 --reload`

## Optional Bedrock Integration

- `BEDROCK_MODEL_ID` — model ID to call through Bedrock Runtime.
- `AWS_REGION` — AWS region (default: `us-east-1`).
- `NOTES_S3_BUCKET_NAME` — S3 bucket used to persist notes.
- `NOTES_S3_OBJECT_KEY` — S3 object key for notes JSON (default: `notes.json`).

If `BEDROCK_MODEL_ID` is not set, summarization uses a local fallback response.
