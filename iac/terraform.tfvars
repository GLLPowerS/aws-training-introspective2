project_name        = "claim-status-api"
environment         = "dev"
aws_region          = "us-east-1"
vpc_cidr            = "10.20.0.0/16"
cluster_name        = "cl-01"
cluster_version     = "1.31"
node_instance_types = ["t3.large"]
node_desired_size   = 2
node_min_size       = 1
node_max_size       = 3
log_retention_days  = 14

# Optional backend integration. Leave empty to skip API routes/integrations until NLB exists.
backend_nlb_listener_arn       = ""
backend_integration_timeout_ms = 29000

# Backend Kubernetes service account (for IRSA)
k8s_namespace            = "claims"
k8s_service_account_name = "claim-status-api"

# Scope Bedrock permission to model ARN, or keep '*' during initial development
bedrock_model_arn = "*"

enable_github_actions_role = true
create_github_oidc_provider = true

# Set to your GitHub owner (organization or username)
github_org = "GLLPowerS"
github_repo = "aws-training-introspective2"
github_branch = "main"

cluster_access_entries = [{
	principal_arn="arn:aws:sts::139592182912:federated-user/c04-vlabuser177@stackroute.in",
    policy_arns=[
        "arn:aws:eks::aws:cluster-access-policy/AmazonEKSAdminPolicy",
        "arn:aws:eks::aws:cluster-access-policy/AmazonEKSClusterAdminPolicy",
        "arn:aws:eks::aws:cluster-access-policy/AmazonEKSViewPolicy"
    ]
}]