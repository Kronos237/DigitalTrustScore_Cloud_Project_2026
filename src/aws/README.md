# AWS

AWS services planned:

- EC2
- S3
- RDS
- IAM
- CloudWatch
- SNS

AWS architecture will be finalized after implementation planning.

## Deployment target

The intended deployment is AWS Amplify for the frontend, an EC2 instance running the FastAPI adapter, private RDS PostgreSQL, S3 for datasets and model/report artifacts, IAM instance roles, and CloudWatch logs/metrics. The EC2 security group should expose only HTTPS through a reverse proxy; the RDS security group should accept PostgreSQL traffic only from the EC2 security group. RDS must not be internet reachable.

The application is intentionally usable without AWS. Configure the deployment only after local analysis, persistence, and model evaluation are evidenced. Do not put access keys in source or committed `.env` files; use an EC2 IAM role for S3 and CloudWatch access.
