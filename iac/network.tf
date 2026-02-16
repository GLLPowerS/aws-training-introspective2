module "vpc" {
  source  = "terraform-aws-modules/vpc/aws"
  version = "~> 5.0"

  name = "${local.name_prefix}-vpc"
  cidr = var.vpc_cidr
  azs  = local.azs

  private_subnets = [
    cidrsubnet(var.vpc_cidr, 4, 1),
    cidrsubnet(var.vpc_cidr, 4, 2)
  ]

  public_subnets = [
    cidrsubnet(var.vpc_cidr, 4, 10),
    cidrsubnet(var.vpc_cidr, 4, 11)
  ]

  enable_nat_gateway = true
  single_nat_gateway = true
}
