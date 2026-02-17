resource "aws_security_group_rule" "backend_nodeport_from_vpc" {
  count = local.manage_backend_nlb ? 1 : 0

  type              = "ingress"
  from_port         = var.backend_node_port
  to_port           = var.backend_node_port
  protocol          = "tcp"
  cidr_blocks       = [module.vpc.vpc_cidr_block]
  security_group_id = module.eks.node_security_group_id
}

resource "aws_lb" "backend" {
  count = local.manage_backend_nlb ? 1 : 0

  name               = "${local.name_prefix}-backend-nlb"
  load_balancer_type = "network"
  internal           = true
  subnets            = module.vpc.private_subnets
}

resource "aws_lb_target_group" "backend" {
  count = local.manage_backend_nlb ? 1 : 0

  name        = "${local.name_prefix}-backend-tg"
  port        = var.backend_node_port
  protocol    = "TCP"
  target_type = "instance"
  vpc_id      = module.vpc.vpc_id

  health_check {
    protocol = "TCP"
    port     = tostring(var.backend_node_port)
  }
}

resource "aws_lb_listener" "backend" {
  count = local.manage_backend_nlb ? 1 : 0

  load_balancer_arn = aws_lb.backend[0].arn
  port              = 80
  protocol          = "TCP"

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.backend[0].arn
  }
}

locals {
  backend_nodegroup_asg_names = local.manage_backend_nlb ? flatten([
    for node_group in values(module.eks.eks_managed_node_groups) : node_group.node_group_autoscaling_group_names
  ]) : []
}

resource "aws_autoscaling_attachment" "backend_tg" {
  for_each = { for asg_name in local.backend_nodegroup_asg_names : asg_name => asg_name }

  autoscaling_group_name = each.value
  lb_target_group_arn    = aws_lb_target_group.backend[0].arn
}
