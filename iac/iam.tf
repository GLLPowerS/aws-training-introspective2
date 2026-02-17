data "aws_iam_policy_document" "backend_irsa_assume_role" {
  statement {
    actions = ["sts:AssumeRoleWithWebIdentity"]

    principals {
      type        = "Federated"
      identifiers = [module.eks.oidc_provider_arn]
    }

    condition {
      test     = "StringEquals"
      variable = "${replace(module.eks.oidc_provider, "https://", "")}:aud"
      values   = ["sts.amazonaws.com"]
    }

    condition {
      test     = "StringEquals"
      variable = "${replace(module.eks.oidc_provider, "https://", "")}:sub"
      values   = [local.backend_service_account_sub]
    }
  }
}

resource "aws_iam_role" "backend_workload" {
  name               = "${local.name_prefix}-backend-irsa-role"
  assume_role_policy = data.aws_iam_policy_document.backend_irsa_assume_role.json
}

data "aws_iam_policy_document" "backend_workload_permissions" {
  statement {
    sid = "DynamoDbReadClaims"
    actions = [
      "dynamodb:GetItem",
      "dynamodb:Query",
      "dynamodb:Scan"
    ]
    resources = [aws_dynamodb_table.claims.arn]
  }

  statement {
    sid = "DynamoDbWriteClaims"
    actions = [
      "dynamodb:PutItem"
    ]
    resources = [aws_dynamodb_table.claims.arn]
  }

  statement {
    sid = "S3ReadClaimNotes"
    actions = [
      "s3:GetObject"
    ]
    resources = ["${aws_s3_bucket.claim_notes.arn}/*"]
  }

  statement {
    sid = "S3ListClaimNotesBucket"
    actions = [
      "s3:ListBucket"
    ]
    resources = [aws_s3_bucket.claim_notes.arn]
  }

  statement {
    sid = "BedrockInvoke"
    actions = [
      "bedrock:InvokeModel",
      "bedrock:InvokeModelWithResponseStream"
    ]
    resources = [var.bedrock_model_arn]
  }

  statement {
    sid = "CloudWatchWriteLogs"
    actions = [
      "logs:CreateLogStream",
      "logs:PutLogEvents",
      "logs:DescribeLogStreams"
    ]
    resources = ["${aws_cloudwatch_log_group.application.arn}:*"]
  }
}

resource "aws_iam_policy" "backend_workload" {
  name   = "${local.name_prefix}-backend-policy"
  policy = data.aws_iam_policy_document.backend_workload_permissions.json
}

resource "aws_iam_role_policy_attachment" "backend_workload" {
  role       = aws_iam_role.backend_workload.name
  policy_arn = aws_iam_policy.backend_workload.arn
}

data "aws_caller_identity" "current" {}

data "aws_partition" "current" {}

locals {
  github_oidc_provider_host = "token.actions.githubusercontent.com"
  github_oidc_provider_arn = var.create_github_oidc_provider ? aws_iam_openid_connect_provider.github_actions[0].arn : (
    var.github_oidc_provider_arn != "" ? var.github_oidc_provider_arn : "arn:${data.aws_partition.current.partition}:iam::${data.aws_caller_identity.current.account_id}:oidc-provider/${local.github_oidc_provider_host}"
  )
  github_repo_sub              = "repo:${var.github_org}/${var.github_repo}:ref:refs/heads/${var.github_branch}"
  github_actions_role_name_eff = var.github_actions_role_name != "" ? var.github_actions_role_name : "${local.name_prefix}-github-actions-ecr-push"

  computed_cluster_access_entries = concat(
    var.cluster_access_entries,
    var.add_current_caller_access ? [{
      principal_arn = data.aws_caller_identity.current.arn
      policy_arns   = var.current_caller_policy_arns
    }] : []
  )

  cluster_access_entries_by_key = {
    for idx, entry in local.computed_cluster_access_entries :
    format("entry-%02d", idx) => entry
  }

  cluster_access_policy_associations = {
    for item in flatten([
      for entry_key, entry in local.cluster_access_entries_by_key : [
        for policy_idx, policy_arn in entry.policy_arns : {
          key           = "${entry_key}-policy-${policy_idx}"
          principal_arn = entry.principal_arn
          policy_arn    = policy_arn
        }
      ]
    ]) : item.key => item
  }
}

resource "aws_eks_access_entry" "cluster_access" {
  for_each = local.cluster_access_entries_by_key

  cluster_name  = module.eks.cluster_name
  principal_arn = each.value.principal_arn
  type          = "STANDARD"
}

resource "aws_eks_access_policy_association" "cluster_access" {
  for_each = local.cluster_access_policy_associations

  cluster_name  = module.eks.cluster_name
  principal_arn = each.value.principal_arn
  policy_arn    = each.value.policy_arn

  access_scope {
    type = "cluster"
  }

  depends_on = [aws_eks_access_entry.cluster_access]
}

data "tls_certificate" "github_actions" {
  count = var.enable_github_actions_role && var.create_github_oidc_provider ? 1 : 0

  url = "https://${local.github_oidc_provider_host}"
}

resource "aws_iam_openid_connect_provider" "github_actions" {
  count = var.enable_github_actions_role && var.create_github_oidc_provider ? 1 : 0

  url             = "https://${local.github_oidc_provider_host}"
  client_id_list  = ["sts.amazonaws.com"]
  thumbprint_list = [data.tls_certificate.github_actions[0].certificates[0].sha1_fingerprint]
}

data "aws_iam_policy_document" "github_actions_assume_role" {
  count = var.enable_github_actions_role ? 1 : 0

  statement {
    actions = ["sts:AssumeRoleWithWebIdentity"]

    principals {
      type        = "Federated"
      identifiers = [local.github_oidc_provider_arn]
    }

    condition {
      test     = "StringEquals"
      variable = "${local.github_oidc_provider_host}:aud"
      values   = ["sts.amazonaws.com"]
    }

    condition {
      test     = "StringLike"
      variable = "${local.github_oidc_provider_host}:sub"
      values   = [local.github_repo_sub]
    }
  }
}

resource "aws_iam_role" "github_actions_ecr_push" {
  count = var.enable_github_actions_role ? 1 : 0

  name               = local.github_actions_role_name_eff
  assume_role_policy = data.aws_iam_policy_document.github_actions_assume_role[0].json
}

data "aws_iam_policy_document" "github_actions_ecr_push_permissions" {
  count = var.enable_github_actions_role ? 1 : 0

  statement {
    sid = "EcrAuthorizationToken"
    actions = [
      "ecr:GetAuthorizationToken"
    ]
    resources = ["*"]
  }

  statement {
    sid = "EcrPushPullRepository"
    actions = [
      "ecr:BatchCheckLayerAvailability",
      "ecr:BatchGetImage",
      "ecr:CompleteLayerUpload",
      "ecr:GetDownloadUrlForLayer",
      "ecr:InitiateLayerUpload",
      "ecr:PutImage",
      "ecr:UploadLayerPart"
    ]
    resources = [aws_ecr_repository.service.arn]
  }

  statement {
    sid = "EksDescribeCluster"
    actions = [
      "eks:DescribeCluster"
    ]
    resources = [module.eks.cluster_arn]
  }
}

resource "aws_iam_policy" "github_actions_ecr_push" {
  count = var.enable_github_actions_role ? 1 : 0

  name   = "${local.name_prefix}-github-actions-ecr-push"
  policy = data.aws_iam_policy_document.github_actions_ecr_push_permissions[0].json
}

resource "aws_iam_role_policy_attachment" "github_actions_ecr_push" {
  count = var.enable_github_actions_role ? 1 : 0

  role       = aws_iam_role.github_actions_ecr_push[0].name
  policy_arn = aws_iam_policy.github_actions_ecr_push[0].arn
}

resource "aws_eks_access_entry" "github_actions" {
  count = var.enable_github_actions_role ? 1 : 0

  cluster_name  = module.eks.cluster_name
  principal_arn = aws_iam_role.github_actions_ecr_push[0].arn
  type          = "STANDARD"
}

resource "aws_eks_access_policy_association" "github_actions" {
  count = var.enable_github_actions_role ? 1 : 0

  cluster_name  = module.eks.cluster_name
  principal_arn = aws_iam_role.github_actions_ecr_push[0].arn
  policy_arn    = "arn:${data.aws_partition.current.partition}:eks::aws:cluster-access-policy/AmazonEKSClusterAdminPolicy"

  access_scope {
    type = "cluster"
  }

  depends_on = [aws_eks_access_entry.github_actions]
}
