# FYP Blockchain Cloud Architecture for Transparent Academic Assessment Result Verification

Backend for an academic examination and result verification platform built with Django REST Framework. The system supports exam management, student registration, face-based identity verification, computer-based exam attempts, result publishing, reporting, and an audit layer based on DID and blockchain-style verification records.

## Overview
This project is designed to improve the transparency and integrity of academic assessment workflows. It combines traditional examination management features with identity verification and tamper-evident record handling so institutions can manage registrations, publish results, and verify records through a single backend platform.

The repository is structured as a functional backend prototype with deployment-ready Docker support. It is especially suited for research, demonstration, and controlled deployment scenarios where exam integrity, verification, and operational traceability are key concerns.

## Key Features
- JWT-based authentication for administrative users
- Exam creation and management for paper-based and computer-based exams
- Public student registration with ID card and face image uploads
- Registration review and approval workflow
- Face verification for secure exam check-in
- Session/token-based flow for computer-based exam attempts
- Automatic grading for objective computer-based questions
- Manual result handling for paper-based exams
- Result publishing with certificate and hash-based verification data
- DID assignment and blockchain-style audit record generation
- Monitoring, alerts, and IP blocking for suspicious activity
- CSV and PDF reporting exports

## Core Modules
- `accounts` - custom admin/faculty user model and authentication endpoints
- `examination` - exams, registrations, questions, attempts, answers, and results
- `face_recognition` - facial verification and exam-entry session handling
- `blockchain_layer` - DID entries, verification records, and integrity-related utilities
- `monitoring` - activity logs, alerts, anomaly checks, and blocked IP management
- `reports` - export endpoints for operational and verification data
- `core` - project settings, routing, and application configuration

## Technology Stack
- Python 3.11
- Django 5
- Django REST Framework
- Simple JWT
- PostgreSQL
- Docker and Docker Compose
- Nginx and Gunicorn
- DeepFace, TensorFlow, and OpenCV for face verification
- ReportLab for PDF generation

## Project Structure
```text
.
├── app/
│   ├── accounts/
│   ├── blockchain_layer/
│   ├── core/
│   ├── examination/
│   ├── face_recognition/
│   ├── monitoring/
│   ├── reports/
│   ├── Dockerfile
│   ├── Dockerfile.prod
│   ├── manage.py
│   └── requirements.txt
├── nginx/
├── docker-compose.yml
├── docker-compose.prod.yml
└── compose.staging.yml
```

## How It Works
1. Administrators create exams and configure whether they are paper-based or computer-based.
2. Students submit registration data, ID card images, and a face image.
3. Registrations are reviewed and approved by authorized staff.
4. Approved candidates can be verified at exam time through face matching.
5. Computer-based exams can be attempted through the exam attempt workflow, with objective answers graded automatically.
6. Results are published and linked to verification metadata such as hashes, certificates, and DID-related records.
7. Monitoring and reporting modules help track suspicious behavior and generate operational exports.

## API Areas
Main API groups exposed by the backend:

- `/api/auth/`
- `/api/exams/`
- `/api/registrations/`
- `/api/results/`
- `/api/attempt/`
- `/api/face/`
- `/api/public/`
- `/api/monitoring/`
- `/api/blockchain/`
- `/api/reports/`

## Getting Started
### Recommended: Docker
The most reliable way to run the project is with Docker because the face verification flow depends on heavier ML libraries.

```bash
docker compose up --build
```

This starts the Django backend and PostgreSQL database using the development configuration in `docker-compose.yml`.

### Local Development
If you want to run it without Docker:

```bash
cd app
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Note: local non-Docker execution may require additional system and ML dependencies for face verification beyond what is listed in `requirements.txt`.

## Environment Configuration
The project uses environment variables for secrets and runtime configuration. Typical values include:

- `SECRET_KEY`
- `DEBUG`
- `DJANGO_ALLOWED_HOSTS`
- `SQL_ENGINE`
- `SQL_DATABASE`
- `SQL_USER`
- `SQL_PASSWORD`
- `SQL_HOST`
- `SQL_PORT`
- `CORS_ALLOWED_ORIGINS`
- `CSRF_TRUSTED_ORIGINS`
- `EMAIL_HOST`
- `EMAIL_PORT`
- `EMAIL_HOST_USER`
- `EMAIL_HOST_PASSWORD`
- `DEFAULT_FROM_EMAIL`
- `FRONTEND_URL`

Environment-specific files such as `.env.dev` and staging-related env files are already present in the repository structure. Review and replace sensitive values before running the project in any shared or production environment.

## Deployment
The repository includes multiple deployment paths:

- `docker-compose.yml` for development
- `docker-compose.prod.yml` for production-style deployment
- `compose.staging.yml` for staging environments

Production and staging setups use Gunicorn, PostgreSQL, Nginx, shared static/media volumes, and TLS-oriented proxy configuration.

## Important Note on Verification Layer
This backend includes DID records, result hashes, and blockchain-style verification data as part of its integrity workflow. Based on the code in this repository, the verification layer is best described as an application-level or simulated blockchain/DID implementation rather than a confirmed live on-chain smart contract integration.

## Current Scope
- Strong backend coverage for exam, registration, verification, and reporting workflows
- Dockerized deployment support for development and staging-style environments
- Placeholder automated test files are present, so additional testing is recommended before a full production rollout

## License
Add your preferred license information here if this project is intended for public distribution.
