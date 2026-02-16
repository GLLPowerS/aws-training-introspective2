variable "project_name" {
  description = "Project name used for naming resources"
  type        = string
  default     = "claim-status-api"
}

variable "environment" {
  description = "Deployment environment"
  type        = string
  default     = "dev"
}

variable "aws_region" {
  description = "AWS region for deployment"
  type        = string
  default     = "us-east-1"
}

variable "vpc_cidr" {
  description = "CIDR block for the VPC"
  type        = string
  default     = "10.20.0.0/16"
}

variable "cluster_name" {
  description = "EKS cluster name"
  type        = string
  default     = "claim-status-eks"
}

variable "cluster_version" {
  description = "Kubernetes version for EKS"
  type        = string
  default     = "1.31"
}

variable "node_instance_types" {
  description = "EC2 instance types for EKS managed node group"
  type        = list(string)
  default     = ["t3.large"]
}

variable "node_desired_size" {
  description = "Desired number of worker nodes"
  type        = number
  default     = 2
}

variable "node_min_size" {
  description = "Minimum number of worker nodes"
  type        = number
  default     = 1
}

variable "node_max_size" {
  description = "Maximum number of worker nodes"
  type        = number
  default     = 3
}

variable "log_retention_days" {
  description = "CloudWatch log retention in days"
  type        = number
  default     = 14
}

variable "backend_nlb_listener_arn" {
  description = "NLB listener ARN for private API Gateway integration to backend service"
  type        = string
  default     = ""
}

variable "backend_integration_timeout_ms" {
  description = "HTTP API integration timeout in milliseconds"
  type        = number
  default     = 29000
}

variable "k8s_namespace" {
  description = "Kubernetes namespace for backend service account"
  type        = string
  default     = "claims"
}

variable "k8s_service_account_name" {
  description = "Kubernetes service account name used by backend workload"
  type        = string
  default     = "claim-status-api"
}

variable "k8s_deployment_name" {
  description = "Kubernetes deployment name for backend workload"
  type        = string
  default     = "claim-status-api"
}

variable "k8s_container_name" {
  description = "Container name inside backend Kubernetes deployment"
  type        = string
  default     = "claim-status-api"
}

variable "k8s_deployment_replicas" {
  description = "Replica count for backend Kubernetes deployment"
  type        = number
  default     = 2
}

variable "bedrock_model_arn" {
  description = "Optional Bedrock model ARN to scope invoke permissions. Use '*' for broad access."
  type        = string
  default     = "*"
}

variable "enable_github_actions_role" {
  description = "Create IAM role/policy for GitHub Actions to push images to ECR"
  type        = bool
  default     = false
}

variable "create_github_oidc_provider" {
  description = "Create IAM OIDC provider for token.actions.githubusercontent.com"
  type        = bool
  default     = false
}

variable "github_oidc_provider_arn" {
  description = "Existing GitHub OIDC provider ARN. Used when create_github_oidc_provider is false"
  type        = string
  default     = ""
}

variable "github_org" {
  description = "GitHub organization or user name"
  type        = string
  default     = ""
}

variable "github_repo" {
  description = "GitHub repository name"
  type        = string
  default     = ""
}

variable "github_branch" {
  description = "Git branch allowed to assume the GitHub Actions IAM role"
  type        = string
  default     = "main"
}

variable "github_actions_role_name" {
  description = "IAM role name for GitHub Actions OIDC federation"
  type        = string
  default     = ""
}
