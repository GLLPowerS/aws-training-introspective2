# Service Source

Place API source code here.

Required endpoints:
- `POST /claims`
- `GET /claims/{id}`
- `POST /claims/{id}/summarize`

## Run Locally

1. Install dependencies:
	- `pip install -r src/requirements.txt`
2. Start the API:
	- `uvicorn src.main:app --host 0.0.0.0 --port 8080 --reload`

## Optional Bedrock Integration

- `BEDROCK_MODEL_ID` — model ID to call through Bedrock Runtime.
- `AWS_REGION` — AWS region (default: `us-east-1`).

If `BEDROCK_MODEL_ID` is not set, summarization uses a local fallback response.
