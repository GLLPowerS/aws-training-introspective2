# Infrastructure as Code (Terraform)

This folder contains initial Terraform scripts to provision core AWS infrastructure for the lab:

- VPC with public/private subnets and NAT gateway
- Amazon EKS cluster with EC2 managed node group
- Amazon ECR repository with scan-on-push enabled
- Amazon DynamoDB table for claim status data
- Amazon S3 bucket for claim notes with encryption and versioning
- Amazon CloudWatch Log Group for application logs
- Amazon API Gateway HTTP API (with optional private backend routes/integrations)
- IAM role + least-privilege policy for backend workload via IRSA
- Kubernetes namespace, service account (IRSA annotation), and backend deployment bootstrap in EKS

## Files

- `providers.tf` — Terraform and provider configuration
- `locals.tf` — Shared locals and discovery data
- `variables.tf` — Input variables
- `network.tf` — VPC and subnet resources
- `eks.tf` — EKS cluster and node groups
- `data-platform.tf` — ECR, DynamoDB, S3, CloudWatch log group
- `api-gateway.tf` — HTTP API, VPC Link, integrations, routes, stage
- `iam.tf` — Backend IRSA role and least-privilege permissions
- `k8s.tf` — Terraform-managed Kubernetes namespace, service account, and deployment
- `main.tf` — Root entrypoint note
- `outputs.tf` — Useful output values
- `terraform.tfvars.example` — Example variable values

## Usage

1. Ensure AWS credentials are configured in your shell/profile.
2. Copy `terraform.tfvars.example` to `terraform.tfvars` and adjust values.
3. Run:

	- `terraform init`
	- `terraform plan`
	- `terraform apply`

## Notes

- Set `backend_nlb_listener_arn` in `terraform.tfvars` to enable private API Gateway routes:
	- `GET /claims/{id}`
	- `POST /claims/{id}/summarize`
- Backend integration uses API Gateway VPC Link to an internal NLB listener ARN.
- The IRSA role output (`backend_irsa_role_arn`) should be annotated on the backend Kubernetes service account:
	- `eks.amazonaws.com/role-arn: <backend_irsa_role_arn>`
- Fine-tune `bedrock_model_arn` from `*` to a specific model ARN for stricter least privilege.
