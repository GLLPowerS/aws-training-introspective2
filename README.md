# GenAI-Enabled Claim Status API (AWS EKS + API Gateway + Bedrock)

This repository implements a claim-status API on AWS using EKS (EC2 worker nodes), API Gateway, DynamoDB, S3, and Amazon Bedrock.

## Task Description
- See `docs/copilot/task-description.md`.

## Repository Structure
- `src/` — FastAPI source code and Dockerfile.
- `mocks/` — sample claims and notes data.
- `iac/` — Terraform infrastructure definitions.
- `apigw/` — API Gateway OpenAPI and route exports.
- `pipelines/` — AWS CodeBuild/CodePipeline definitions and parameters.
- `scans/` — security scan evidence (Inspector / Security Hub / Defender screenshots).
- `observability/` — CloudWatch Logs Insights queries, dashboard template, and screenshot checklist.

## Setup and Run Instructions

### Prerequisites
- AWS account permissions for EKS, API Gateway, ECR, DynamoDB, S3, IAM, CloudWatch.
- Installed tools: Terraform, AWS CLI, kubectl, Docker, Python 3.12+.
- AWS credentials configured (example profile: `org-demo`).

### 1) Provision infrastructure (Terraform)
```powershell
$env:AWS_PROFILE='org-demo'
terraform -chdir=iac init
terraform -chdir=iac apply -auto-approve
```

Useful outputs:
```powershell
terraform -chdir=iac output
terraform -chdir=iac output -raw api_gateway_url
terraform -chdir=iac output -raw ecr_repository_url
```

### 2) Build and push backend image to ECR
```powershell
$env:AWS_PROFILE='org-demo'
$awsRegion = 'us-east-1'
$ecrRepo = terraform -chdir=iac output -raw ecr_repository_url
$imageTag = 'latest'

aws ecr get-login-password --region $awsRegion | docker login --username AWS --password-stdin $ecrRepo.Split('/')[0]
docker build -f src/Dockerfile -t claim-status-api:$imageTag .
docker tag claim-status-api:$imageTag "$ecrRepo`:$imageTag"
docker push "$ecrRepo`:$imageTag"
```

### 3) Deploy image to EKS workload
```powershell
aws eks update-kubeconfig --name cl-01 --region us-east-1
kubectl -n claims set image deployment/claim-status-api claim-status-api="$ecrRepo`:$imageTag"
kubectl -n claims rollout status deployment/claim-status-api --timeout=300s
```

### 4) Run service locally (optional)
```powershell
pip install -r src/requirements.txt
uvicorn src.main:app --host 0.0.0.0 --port 8080 --reload
```

## API Endpoints
- `POST /claims`
- `GET /claims/{id}`
- `GET /claims/{id}/notes`
- `POST /claims/{id}/notes`
- `PUT /claims/{id}/notes/{noteId}`
- `DELETE /claims/{id}/notes/{noteId}`
- `POST /claims/{id}/summarize`

## Tests and Validation

### Manual endpoint tests via API Gateway
Use requests from `local/claims.http` against the deployed API URL.

Quick PowerShell smoke test:
```powershell
$env:AWS_PROFILE='org-demo'
$api = (terraform -chdir=iac output -raw api_gateway_url).TrimEnd('/')
$id = 'CLM-TEST-' + (Get-Date -Format 'yyyyMMddHHmmss')

Invoke-RestMethod -Method Post -Uri "$api/claims" -ContentType 'application/json' -Body (@{ id=$id; status='OPEN'; policyNumber='POL-1'; customer='Smoke Test' } | ConvertTo-Json)
Invoke-RestMethod -Method Post -Uri "$api/claims/$id/notes" -ContentType 'application/json' -Body (@{ content='Repair estimate received and under review.' } | ConvertTo-Json)
Invoke-RestMethod -Method Post -Uri "$api/claims/$id/summarize" -ContentType 'application/json' -Body '{}'
Invoke-RestMethod -Method Get -Uri "$api/claims/$id"
```

Expected result:
- Claim record is returned with notes and summary object fields:
  - `summary`
  - `customer-facing-summary`
  - `adjuster-focused-summary`
  - `recommended-next-step`

## GenAI Prompts Used

The summarize flow makes separate Bedrock calls per field. Prompt template and instructions are implemented in `src/services/claims_service.py`.

### Base prompt template
```text
You are an insurance claim assistant.
Generate ONLY the '<field_key>' value.
Return plain text only, unless asked for JSON explicitly.
Do not include markdown fences.
Instruction: <field_instruction>
Claim: <claim_json>. Notes: <notes_text>
```

### Field-specific instructions
1. `summary`
	- Provide an overall one-to-three sentence claim summary for internal reference.
2. `customer-facing-summary`
	- Provide a customer-facing one-to-three sentence update in empathetic and plain language.
3. `adjuster-focused-summary`
	- Provide an adjuster-focused one-to-three sentence operational summary highlighting important claim handling details.
4. `recommended-next-step`
	- Provide exactly one concise recommended next action for the adjuster.

If Bedrock invocation or parsing fails, the service falls back to deterministic local summary generation.

## Additional Evidence Artifacts
- API Gateway exports: `apigw/`
- Pipeline definitions: `pipelines/`
- Scan evidence checklist: `scans/`
- Observability queries/screenshots: `observability/`
