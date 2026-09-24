# Future Architecture

## Planned Direction

The local MVP establishes this pipeline:

```text
URL -> validation and feature extraction -> transparent baseline model -> factors and score -> dashboard
```

The API now persists history through SQLAlchemy. Local development uses SQLite; the same repository selects PostgreSQL when `DATABASE_URL` is configured for Docker or future RDS. The next cloud step is to place datasets and model artifacts in S3 and deploy the FastAPI API on EC2 behind controlled IAM access. CloudWatch can then collect API and model metrics. SNS remains optional until the team defines a notification use case.

## Current Contracts

- Scores are integers from 0 to 100.
- Labels are `low` (0-49), `moderate` (50-74), or `high` (75-100).
- Every response includes `model_version`, extracted features, and signed feature contributions.
- Invalid or unsupported URLs return HTTP 400 rather than being scored.



## Status

This document will be updated as the architecture becomes more concrete during the semester.
