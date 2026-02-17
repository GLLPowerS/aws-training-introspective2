module "eks" {
  source  = "terraform-aws-modules/eks/aws"
  version = "~> 20.0"

  cluster_name    = var.cluster_name
  cluster_version = var.cluster_version
  cluster_enabled_log_types = var.cluster_enabled_log_types

  cluster_endpoint_public_access           = true
  enable_cluster_creator_admin_permissions = true

  cluster_addons = var.enable_container_insights ? {
    amazon-cloudwatch-observability = {
      most_recent = true
    }
  } : {}

  vpc_id     = module.vpc.vpc_id
  subnet_ids = module.vpc.private_subnets

  eks_managed_node_group_defaults = {
    iam_role_additional_policies = {
      CloudWatchAgentServerPolicy = "arn:aws:iam::aws:policy/CloudWatchAgentServerPolicy"
    }
  }

  eks_managed_node_groups = {
    default = {
      instance_types = var.node_instance_types
      capacity_type  = "ON_DEMAND"

      desired_size = var.node_desired_size
      min_size     = var.node_min_size
      max_size     = var.node_max_size
    }
  }
}
