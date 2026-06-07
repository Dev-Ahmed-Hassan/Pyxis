# Match Explainability Knowledge Base

This folder contains source documents for the future RAG-assisted match
explanation feature.

The matching engine provides structured facts:

```text
base score
exact matches
related-skill evidence
semantic evidence
LLM adjudication judgments
missing requirements
partial requirements
resume section citations
```

The knowledge base provides domain guidance:

```text
what a requirement means
what evidence should count
what evidence is weak or misleading
how a student can improve the resume truthfully
how to explain gaps without inventing experience
```

The explanation generator should combine both:

```text
match facts + retrieved knowledge guidance -> structured student-facing explanation
```

## RAG Use

When implemented, the ingestion pipeline should:

1. Read these Markdown files.
2. Split them by stable headings.
3. Embed each chunk with the configured embedding model.
4. Store chunks in pgvector with file path, heading, topic tags, and content hash.
5. Retrieve the most relevant chunks for matched, missing, and partial
   requirements.
6. Give the LLM only the retrieved chunks plus the saved match/adjudication
   facts.

The LLM must not treat these documents as resume evidence. They are guidance
for explaining the result, not proof that the student has a skill.

## Current Documents

```text
cybersecurity_skills.md
resume_improvement_guidance.md
match_explanation_rules.md
career_path_guidance.md
rag_authoring_guide.md
rag_response_rules.md
cyber_soc_analyst_guidance.md
cyber_penetration_testing_guidance.md
cyber_network_security_guidance.md
cyber_web_security_guidance.md
cyber_project_suggestions.md
cyber_interview_guidance.md
ai_ml_guidance.md
data_science_guidance.md
software_engineering_guidance.md
web_development_guidance.md
cloud_engineering_guidance.md
qa_testing_guidance.md
mobile_development_guidance.md
common_it_support_guidance.md
hr_jobs_guidance.md
```

## Authoring Rules

The current loader indexes only Markdown files directly inside this folder and
splits chunks at `##` headings. Keep new knowledge files flat for now.

Use short sections with specific headings. Prefer concrete phrasing:

```text
Good: "Nessus is direct evidence for vulnerability scanning."
Weak: "Vulnerability scanning is important."
```

Do not add broad reverse assumptions:

```text
Wrong: "Knowing cybersecurity proves Splunk."
Right: "Splunk can support SIEM evidence when it appears directly."
```

Avoid advice that tells a student to fabricate experience. Suggestions must be
truth-preserving:

```text
Good: "If you used Wazuh, mention dashboards, alert rules, and triage."
Wrong: "Add SIEM to the resume to improve the score."
```

## Recommended Chunk Format

Start each indexed section with lightweight metadata lines. These are plain
text today, but they improve retrieval wording and can become structured
metadata later:

```text
## SIEM Mini SOC Lab

chunk_type: project
field: cybersecurity
role: SOC Analyst Intern
skills: SIEM, log analysis, alert triage
purpose: missing-skill-project
```

Recommended `chunk_type` values:

```text
rule
domain
project
career
interview
resume_improvement
```

For other fields, copy the same pattern:

```text
ai_ml_role_guidance.md
ai_ml_project_suggestions.md
ai_ml_interview_guidance.md
data_science_role_guidance.md
software_engineering_interview_guidance.md
```

After adding or editing files, refresh embeddings with:

```text
POST /matches/explainability/knowledge/embeddings/refresh
```
