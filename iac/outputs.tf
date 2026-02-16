output "vpc_id" {
  description = "VPC ID"
  value       = module.vpc.vpc_id
}

output "eks_cluster_name" {
  description = "EKS cluster name"
  value       = module.eks.cluster_name
}

output "eks_cluster_endpoint" {
  description = "EKS API endpoint"
  value       = module.eks.cluster_endpoint
}

output "ecr_repository_url" {
  description = "ECR repository URL"
  value       = aws_ecr_repository.service.repository_url
}

output "dynamodb_table_name" {
  description = "DynamoDB table name"
  value       = aws_dynamodb_table.claims.name
}

output "s3_bucket_name" {
  description = "S3 bucket for claim notes"
  value       = aws_s3_bucket.claim_notes.bucket
}

output "api_gateway_url" {
  description = "HTTP API invoke URL"
  value       = aws_apigatewayv2_stage.default.invoke_url
}

output "api_gateway_vpc_link_id" {
  description = "API Gateway VPC link ID when backend integration is enabled"
  value       = local.enable_backend_integration ? aws_apigatewayv2_vpc_link.backend[0].id : null
}

output "backend_irsa_role_arn" {
  description = "IAM role ARN for backend Kubernetes service account (IRSA)"
  value       = aws_iam_role.backend_workload.arn
}

output "backend_service_account_subject" {
  description = "Kubernetes subject allowed to assume backend IRSA role"
  value       = local.backend_service_account_sub
}

output "k8s_namespace" {
  description = "Kubernetes namespace managed by Terraform for backend workload"
  value       = var.k8s_namespace
}

output "k8s_deployment_name" {
  description = "Kubernetes deployment name managed by Terraform for backend workload"
  value       = var.k8s_deployment_name
}

output "k8s_container_name" {
  description = "Kubernetes container name managed by Terraform for backend workload"
  value       = var.k8s_container_name
}

output "github_actions_role_arn" {
  description = "IAM role ARN for GitHub Actions OIDC ECR push pipeline"
  value       = var.enable_github_actions_role ? aws_iam_role.github_actions_ecr_push[0].arn : null
}

output "github_oidc_provider_arn" {
  description = "OIDC provider ARN used for GitHub Actions trust"
  value       = var.enable_github_actions_role ? local.github_oidc_provider_arn : null
}
