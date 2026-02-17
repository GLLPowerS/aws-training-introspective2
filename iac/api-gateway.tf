resource "aws_apigatewayv2_api" "claims" {
  name          = "${local.name_prefix}-claims-api"
  protocol_type = "HTTP"
}

resource "aws_security_group" "apigw_vpc_link" {
  count = local.enable_backend_integration ? 1 : 0

  name        = "${local.name_prefix}-apigw-vpclink"
  description = "Security group for API Gateway VPC Link"
  vpc_id      = module.vpc.vpc_id

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

resource "aws_apigatewayv2_vpc_link" "backend" {
  count = local.enable_backend_integration ? 1 : 0

  name               = "${local.name_prefix}-backend-vpclink"
  security_group_ids = [aws_security_group.apigw_vpc_link[0].id]
  subnet_ids         = module.vpc.private_subnets
}

resource "aws_apigatewayv2_integration" "get_claim" {
  count = local.enable_backend_integration ? 1 : 0

  api_id                 = aws_apigatewayv2_api.claims.id
  integration_type       = "HTTP_PROXY"
  integration_method     = "GET"
  integration_uri        = local.backend_listener_arn
  connection_type        = "VPC_LINK"
  connection_id          = aws_apigatewayv2_vpc_link.backend[0].id
  payload_format_version = "1.0"
  timeout_milliseconds   = var.backend_integration_timeout_ms
}

resource "aws_apigatewayv2_integration" "post_summarize" {
  count = local.enable_backend_integration ? 1 : 0

  api_id                 = aws_apigatewayv2_api.claims.id
  integration_type       = "HTTP_PROXY"
  integration_method     = "POST"
  integration_uri        = local.backend_listener_arn
  connection_type        = "VPC_LINK"
  connection_id          = aws_apigatewayv2_vpc_link.backend[0].id
  payload_format_version = "1.0"
  timeout_milliseconds   = var.backend_integration_timeout_ms
}

resource "aws_apigatewayv2_integration" "get_notes" {
  count = local.enable_backend_integration ? 1 : 0

  api_id                 = aws_apigatewayv2_api.claims.id
  integration_type       = "HTTP_PROXY"
  integration_method     = "GET"
  integration_uri        = local.backend_listener_arn
  connection_type        = "VPC_LINK"
  connection_id          = aws_apigatewayv2_vpc_link.backend[0].id
  payload_format_version = "1.0"
  timeout_milliseconds   = var.backend_integration_timeout_ms
}

resource "aws_apigatewayv2_integration" "post_notes" {
  count = local.enable_backend_integration ? 1 : 0

  api_id                 = aws_apigatewayv2_api.claims.id
  integration_type       = "HTTP_PROXY"
  integration_method     = "POST"
  integration_uri        = local.backend_listener_arn
  connection_type        = "VPC_LINK"
  connection_id          = aws_apigatewayv2_vpc_link.backend[0].id
  payload_format_version = "1.0"
  timeout_milliseconds   = var.backend_integration_timeout_ms
}

resource "aws_apigatewayv2_integration" "put_note" {
  count = local.enable_backend_integration ? 1 : 0

  api_id                 = aws_apigatewayv2_api.claims.id
  integration_type       = "HTTP_PROXY"
  integration_method     = "PUT"
  integration_uri        = local.backend_listener_arn
  connection_type        = "VPC_LINK"
  connection_id          = aws_apigatewayv2_vpc_link.backend[0].id
  payload_format_version = "1.0"
  timeout_milliseconds   = var.backend_integration_timeout_ms
}

resource "aws_apigatewayv2_integration" "delete_note" {
  count = local.enable_backend_integration ? 1 : 0

  api_id                 = aws_apigatewayv2_api.claims.id
  integration_type       = "HTTP_PROXY"
  integration_method     = "DELETE"
  integration_uri        = local.backend_listener_arn
  connection_type        = "VPC_LINK"
  connection_id          = aws_apigatewayv2_vpc_link.backend[0].id
  payload_format_version = "1.0"
  timeout_milliseconds   = var.backend_integration_timeout_ms
}

resource "aws_apigatewayv2_route" "get_claim" {
  count = local.enable_backend_integration ? 1 : 0

  api_id    = aws_apigatewayv2_api.claims.id
  route_key = "GET /claims/{id}"
  target    = "integrations/${aws_apigatewayv2_integration.get_claim[0].id}"
}

resource "aws_apigatewayv2_route" "post_summarize" {
  count = local.enable_backend_integration ? 1 : 0

  api_id    = aws_apigatewayv2_api.claims.id
  route_key = "POST /claims/{id}/summarize"
  target    = "integrations/${aws_apigatewayv2_integration.post_summarize[0].id}"
}

resource "aws_apigatewayv2_route" "post_claim" {
  count = local.enable_backend_integration ? 1 : 0

  api_id    = aws_apigatewayv2_api.claims.id
  route_key = "POST /claims"
  target    = "integrations/${aws_apigatewayv2_integration.post_summarize[0].id}"
}

resource "aws_apigatewayv2_route" "get_notes" {
  count = local.enable_backend_integration ? 1 : 0

  api_id    = aws_apigatewayv2_api.claims.id
  route_key = "GET /claims/{id}/notes"
  target    = "integrations/${aws_apigatewayv2_integration.get_notes[0].id}"
}

resource "aws_apigatewayv2_route" "post_notes" {
  count = local.enable_backend_integration ? 1 : 0

  api_id    = aws_apigatewayv2_api.claims.id
  route_key = "POST /claims/{id}/notes"
  target    = "integrations/${aws_apigatewayv2_integration.post_notes[0].id}"
}

resource "aws_apigatewayv2_route" "put_note" {
  count = local.enable_backend_integration ? 1 : 0

  api_id    = aws_apigatewayv2_api.claims.id
  route_key = "PUT /claims/{id}/notes/{noteId}"
  target    = "integrations/${aws_apigatewayv2_integration.put_note[0].id}"
}

resource "aws_apigatewayv2_route" "delete_note" {
  count = local.enable_backend_integration ? 1 : 0

  api_id    = aws_apigatewayv2_api.claims.id
  route_key = "DELETE /claims/{id}/notes/{noteId}"
  target    = "integrations/${aws_apigatewayv2_integration.delete_note[0].id}"
}

resource "aws_apigatewayv2_stage" "default" {
  api_id      = aws_apigatewayv2_api.claims.id
  name        = "$default"
  auto_deploy = true
}
