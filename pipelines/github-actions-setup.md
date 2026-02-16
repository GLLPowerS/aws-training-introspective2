# GitHub Actions -> Amazon ECR Setup

This guide configures GitHub Actions to push your container image to Amazon ECR using OpenID Connect (OIDC).

## 1) Configure Terraform variables

In `iac/terraform.tfvars`, set:

- `enable_github_actions_role = true`
- `github_org`, `github_repo`, `github_branch`
- `create_github_oidc_provider = true` only if your account does not already have the provider

Then apply Terraform:

- `terraform -chdir=iac plan -out tfplan`
- `terraform -chdir=iac apply tfplan`

## 2) Configure repository settings

In GitHub repo settings:

- Add **Repository Variable** `AWS_REGION` (example: `us-east-1`)
- Add **Repository Variable** `ECR_REPOSITORY` (example: `claim-status-api-dev-service`)
- Add **Repository Secret** `AWS_ROLE_TO_ASSUME` from Terraform output:
  - `terraform -chdir=iac output -raw github_actions_role_arn`

## 3) Workflow file

Pipeline is already added at:

- `.github/workflows/ecr-push.yml`

It runs on push to `main` (for source and workflow changes) and on manual dispatch.

## 4) Validate

- Push a commit to `main` or run the workflow manually in GitHub Actions.
- Confirm images are created in ECR with tags:
  - `<git-sha>`
  - `latest` (on `main`)
