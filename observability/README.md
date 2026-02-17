# Observability Evidence

## Enabled Components
- EKS control plane logs to CloudWatch (`api`, `audit`, `authenticator`, `controllerManager`, `scheduler`).
- EKS workload logs and metrics via `amazon-cloudwatch-observability` add-on (Container Insights).
- API Gateway HTTP API access logs in CloudWatch.

## Apply Infrastructure
```powershell
$env:AWS_PROFILE='org-demo'
terraform -chdir=iac plan -out tfplan-observability
terraform -chdir=iac apply tfplan-observability
```

## Import Dashboard (Template)
Template file: `observability/cloudwatch-dashboard.json`

```powershell
$env:AWS_PROFILE='org-demo'
aws cloudwatch put-dashboard --region us-east-1 --dashboard-name claim-status-api-observability --dashboard-body file://observability/cloudwatch-dashboard.json
```

If your API ID or cluster name differs, update these values in the JSON first:
- `ApiId` (currently `7hnpccv7ai`)
- `ClusterName` in SEARCH expressions (currently `cl-01`)

## CloudWatch Log Groups To Validate
- `/aws/eks/<cluster-name>/cluster`
- `/aws/containerinsights/<cluster-name>/application`
- `/aws/containerinsights/<cluster-name>/host`
- `/aws/apigateway/<project>-<env>-claims-api-access`

## Logs Insights Queries

### 1) API Gateway Errors and Latency Signals
```sql
fields @timestamp, status, routeKey, path, requestId, integrationErr
| filter ispresent(status)
| sort @timestamp desc
| limit 100
```

### 2) Summarize Endpoint Traffic
```sql
fields @timestamp, routeKey, status, requestId
| filter routeKey = "POST /claims/{id}/summarize"
| stats count(*) as requests, countif(status like /5.*/) as errors by bin(5m)
| sort bin(5m) desc
```

### 3) Application Errors in Pods
```sql
fields @timestamp, kubernetes.namespace_name, kubernetes.pod_name, @message
| filter kubernetes.namespace_name = "claims"
| filter @message like /ERROR|Exception|Traceback/
| sort @timestamp desc
| limit 100
```

## Metrics To Screenshot (Evidence)
- `ContainerInsights` namespace:
	- `pod_cpu_utilization`
	- `pod_memory_utilization`
	- `pod_number_of_container_restarts`
- API Gateway:
	- `4XXError`, `5XXError`, `Latency`, `IntegrationLatency`

## Artifacts to Commit
- Saved Logs Insights query screenshots.
- Metric dashboard screenshots.
- Short note on any observed error pattern and mitigation.
