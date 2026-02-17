data "aws_availability_zones" "available" {
  state = "available"
}

locals {
  name_prefix                 = "${var.project_name}-${var.environment}"
  azs                         = slice(data.aws_availability_zones.available.names, 0, 2)
  manage_backend_nlb          = var.enable_backend_nlb && var.backend_nlb_listener_arn == ""
  backend_listener_arn        = var.backend_nlb_listener_arn != "" ? var.backend_nlb_listener_arn : (local.manage_backend_nlb ? aws_lb_listener.backend[0].arn : "")
  enable_backend_integration  = var.backend_nlb_listener_arn != "" || local.manage_backend_nlb
  backend_service_account_sub = "system:serviceaccount:${var.k8s_namespace}:${var.k8s_service_account_name}"
}
