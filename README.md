# GenAI Claim Status API Lab

This repository contains the initial structure for the AWS EKS + API Gateway + Bedrock design-and-build lab.

## Task Description
- See [docs/copilot/task-description.md](docs/copilot/task-description.md)

## Repository Structure
- `src/` — service source + Dockerfile
- `mocks/` — sample claim and notes data
- `apigw/` — API Gateway artifacts
- `iac/` — CloudFormation/Terraform templates
- `pipelines/` — CodeBuild/CodePipeline definitions
- `scans/` — security findings evidence
- `observability/` — logs, metrics, and query evidence

## Next Steps
1. Implement service in `src/`
2. Build infrastructure templates in `iac/`
3. Define CI/CD in `pipelines/`
4. Deploy and validate endpoints through API Gateway
5. Add scan and observability evidence
