# Cloud Engineering Guidance

This document supports cloud engineering, DevOps, and platform engineering
career suggestions, match explanations, project suggestions, and interviews.

## Cloud Engineering Role Signals

chunk_type: career
field: cloud_engineering
role: Cloud Engineering Intern
skills: AWS, Azure, GCP, Linux, networking, IAM, deployment
purpose: role-fit

Cloud engineering internships usually value evidence of deploying applications
or infrastructure, understanding IAM, networking, compute, storage, monitoring,
and cost or security basics. Student projects can use free tiers or local
cloud-like tools if clearly documented.

Strong evidence names:

```text
cloud provider
service used
deployment architecture
IAM or access control
networking setup
monitoring or logging
cost/security consideration
```

## DevOps Role Signals

chunk_type: career
field: cloud_engineering
role: DevOps Intern
skills: CI/CD, Docker, Linux, GitHub Actions, monitoring, scripting
purpose: role-fit

DevOps roles value automation, containers, CI/CD pipelines, deployment scripts,
Linux administration, monitoring, and reliability thinking. Strong evidence
includes Dockerfiles, compose files, GitHub Actions workflows, deployment docs,
and automated tests.

Partial evidence includes general GitHub usage without automation or
deployment workflow.

## Cloud Security Evidence Standards

chunk_type: domain
field: cloud_engineering
role: Cloud Security Intern
skills: IAM, least privilege, secrets management, logging, network security
purpose: evidence-standard

Cloud security evidence includes IAM policies, least-privilege access, secure
secret handling, logging, monitoring, network security groups, encryption, and
basic threat modeling.

Do not treat cloud deployment alone as cloud security evidence unless security
controls are named and explained.

## Docker Deployment Project

chunk_type: project
field: cloud_engineering
role: DevOps Intern
skills: Docker, deployment, CI/CD, Linux
purpose: missing-skill-project

Use this project when the student lacks deployment or DevOps evidence.

Project:

```text
Containerize a backend API with Docker, add a docker-compose file for the app
and database, and create a GitHub Actions workflow that runs tests.
```

Resume bullet:

```text
Containerized a backend API with Docker Compose and configured GitHub Actions
to run automated tests on each push.
```

## Cloud Resume API Project

chunk_type: project
field: cloud_engineering
role: Cloud Engineering Intern
skills: cloud deployment, API, database, IAM, monitoring
purpose: missing-skill-project

Use this project when the student needs cloud deployment evidence.

Project:

```text
Deploy a small API and database-backed app to a cloud platform. Document the
architecture, environment variables, access controls, and monitoring/logging.
```

Resume bullet:

```text
Deployed a database-backed API to a cloud platform, documenting architecture,
environment configuration, access controls, and monitoring/logging setup.
```

## Cloud Interview Guidance

chunk_type: interview
field: cloud_engineering
role: Cloud Engineering Intern
skills: deployment, IAM, networking, Docker
purpose: interview-prep

Common cloud interview questions:

```text
How would you deploy this application?
What is IAM and why does least privilege matter?
How do containers differ from virtual machines?
How would you store secrets safely?
How would you troubleshoot an app that works locally but fails after deployment?
```

Strong answers should mention reliability, security, observability, and cost
awareness.

