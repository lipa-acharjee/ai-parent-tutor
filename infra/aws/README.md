# AWS deployment plan

Use managed services in production:
- ECS/Fargate for API and Celery workers
- RDS PostgreSQL with pgvector
- ElastiCache Redis
- S3 for private documents/video assets
- CloudFront + WAF for delivery/protection
- Secrets Manager for application secrets
- CloudWatch + OpenTelemetry/Grafana for observability
- ECR for container images

Recommended network: private subnets for ECS/RDS/Redis, public subnets only for the load balancer/NAT path. Do not expose PostgreSQL or Redis to the internet.

The repository intentionally does not hard-code a one-size-fits-all VPC. Create the VPC using your organization's approved baseline (or Terraform modules) and inject subnet/security-group IDs into ECS/RDS/Redis.
