# CI/CD Pipelines

This folder contains CI/CD setup assets.

## Available

- GitHub Actions workflow to build and push container images to Amazon ECR:
	- `.github/workflows/ecr-push.yml`
- Setup guide for AWS IAM OIDC trust and ECR push permissions:
	- `pipelines/github-actions-setup.md`

## Notes

- Current workflow handles image build + ECR push.
- You can add deployment stages (EKS rollout, smoke tests, scans) as next pipeline steps.
