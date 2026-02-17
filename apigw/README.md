# API Gateway Artifacts

This folder contains API Gateway export artifacts required by the lab deliverable.

## Included artifacts
- `openapi-export.yaml` — OpenAPI 3.0 export of the deployed HTTP API stage (`$default`).
- `routes-export.json` — route inventory exported from API Gateway (`get-routes`).

## Regenerate artifacts

```powershell
$env:AWS_PROFILE='org-demo'
$env:AWS_PAGER=''
$invoke=(terraform -chdir=iac output -raw api_gateway_url).TrimEnd('/')
$apiId=([uri]$invoke).Host.Split('.')[0]

aws apigatewayv2 export-api --api-id $apiId --output-type YAML --specification OAS30 --stage-name '$default' --region us-east-1 apigw/openapi-export.yaml
aws apigatewayv2 get-routes --api-id $apiId --region us-east-1 > apigw/routes-export.json
```
