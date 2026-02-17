# CI/CD Pipelines

This folder contains CI/CD setup assets.

## Available

- GitHub Actions workflow to build and push container images to Amazon ECR:
	- `.github/workflows/ecr-push.yml`
- Setup guide for AWS IAM OIDC trust and ECR push permissions:
	- `pipelines/github-actions-setup.md`
- AWS-native pipeline definitions:
	- `pipelines/buildspec-codebuild.yml` (CodeBuild build + scan + ECR push)
	- `pipelines/codepipeline-codebuild-template.yaml` (CloudFormation for CodePipeline + CodeBuild projects)
	- `pipelines/codepipeline-parameters.example.json` (example stack parameters)

## Notes

- GitHub Actions workflow handles image build + ECR push + EKS rollout.
- CloudFormation template defines AWS CodePipeline stages: Source -> Build -> Deploy.

## Deploy AWS Pipeline Definitions

```powershell
$env:AWS_PROFILE='org-demo'
aws cloudformation create-stack \
	--stack-name claim-status-api-dev-pipeline \
	--template-body file://pipelines/codepipeline-codebuild-template.yaml \
	--parameters file://pipelines/codepipeline-parameters.example.json \
  --capabilities CAPABILITY_NAMED_IAM \
  --region us-east-1
```
