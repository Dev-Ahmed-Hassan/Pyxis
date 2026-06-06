# RAG Authoring Guide

This guide defines the format for adding new knowledge documents. The current
loader indexes Markdown files directly inside this folder and splits chunks at
level-two headings (`##`). Keep files flat for now; do not place documents in
nested folders unless the loader is changed to read recursively.

## Field Document Template

chunk_type: rule
field: any
purpose: authoring-format

Use one Markdown file per focused role, domain, project family, or interview
topic. Prefer specific files such as `cyber_soc_analyst_guidance.md` or
`ai_ml_project_suggestions.md` over one giant mixed document.

Recommended chunk header format:

```text
## Clear Chunk Title

chunk_type: domain | project | career | interview | resume_improvement | rule
field: cybersecurity | ai_ml | data_science | software_engineering
role: SOC Analyst Intern | Penetration Testing Intern | Any
skills: SIEM, log analysis, alert triage
purpose: short reason this chunk exists
```

The metadata is plain text today. It helps embeddings and future metadata
parsing. Later, the retrieval service can parse these lines into structured
filters.

## Good Chunk Shape

chunk_type: rule
field: any
purpose: quality-control

A good chunk should contain one idea. It should name the role, skill, evidence
standard, project suggestion, or interview pattern clearly.

Good chunk:

```text
SOC analysts use SIEM tools to collect logs, triage alerts, reduce false
positives, and escalate incidents. A student project can demonstrate this by
building a Wazuh lab that detects repeated failed SSH logins and documents the
triage process.
```

Weak chunk:

```text
Cybersecurity is important and students should learn tools.
```

Avoid broad, vague, duplicated chunks. Retrieval works by similarity, so noisy
chunks can crowd out useful guidance.

## Adding A New Field

chunk_type: rule
field: any
purpose: expansion-format

To add another field, create focused files using the same pattern.

Examples:

```text
ai_ml_role_guidance.md
ai_ml_project_suggestions.md
ai_ml_interview_guidance.md
data_science_role_guidance.md
data_science_project_suggestions.md
software_engineering_role_guidance.md
software_engineering_interview_guidance.md
```

Each file should include chunks for:

```text
domain expectations
role signals
strong evidence
partial evidence
missing-skill project suggestions
resume improvement advice
interview questions
```

After adding or editing knowledge files, refresh embeddings:

```text
POST /matches/explainability/knowledge/embeddings/refresh
```

