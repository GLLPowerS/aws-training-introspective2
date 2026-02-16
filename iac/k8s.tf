data "aws_eks_cluster" "this" {
  name = module.eks.cluster_name

  depends_on = [module.eks]
}

data "aws_eks_cluster_auth" "this" {
  name = module.eks.cluster_name

  depends_on = [module.eks]
}

resource "kubernetes_namespace_v1" "backend" {
  metadata {
    name = var.k8s_namespace
  }

  depends_on = [module.eks]
}

resource "kubernetes_service_account_v1" "backend" {
  metadata {
    name      = var.k8s_service_account_name
    namespace = kubernetes_namespace_v1.backend.metadata[0].name

    annotations = {
      "eks.amazonaws.com/role-arn" = aws_iam_role.backend_workload.arn
    }
  }
}

resource "kubernetes_deployment_v1" "backend" {
  metadata {
    name      = var.k8s_deployment_name
    namespace = kubernetes_namespace_v1.backend.metadata[0].name
    labels = {
      app = var.k8s_deployment_name
    }
  }

  spec {
    replicas = var.k8s_deployment_replicas

    selector {
      match_labels = {
        app = var.k8s_deployment_name
      }
    }

    template {
      metadata {
        labels = {
          app = var.k8s_deployment_name
        }
      }

      spec {
        service_account_name = kubernetes_service_account_v1.backend.metadata[0].name

        container {
          name              = var.k8s_container_name
          image             = "${aws_ecr_repository.service.repository_url}:latest"
          image_pull_policy = "Always"

          port {
            container_port = 8080
          }
        }
      }
    }
  }

  lifecycle {
    ignore_changes = [
      spec[0].template[0].spec[0].container[0].image
    ]
  }
}
