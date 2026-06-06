# RAG Response Rules

These chunks are instruction-like guidance for LLM outputs. Critical safety
rules still belong in code prompts; these chunks provide reusable explanation
style and quality guidance.

## Do Not Treat Guidance As User Evidence

chunk_type: rule
field: any
purpose: grounding

Knowledge chunks are not resume evidence, internship evidence, or GitHub
evidence. They explain what a skill means and how to improve. A generated
response must distinguish:

```text
user evidence: saved resume, internship, match, adjudication, GitHub snapshot
guidance: retrieved knowledge chunk
```

Do not say the student has a skill because a guidance document mentions it.

## Prefer Truth-Preserving Advice

chunk_type: rule
field: any
purpose: resume-improvement

If evidence is direct, suggest clearer wording and stronger metrics. If
evidence is partial, explain what is present and what is missing. If evidence
is absent, suggest a project, course, lab, or practice plan before listing the
skill on the resume.

Use:

```text
Build a Wazuh lab before claiming SIEM experience.
```

Avoid:

```text
Add SIEM to your resume to increase the match score.
```

## Separate Score From Advice

chunk_type: rule
field: any
purpose: match-explanation

The official match score is calculated by backend logic. Retrieved guidance
can explain gaps and recommend improvements, but it should not invent a new
score. If an AI-reviewed score is present, describe it as an evidence review,
not as a replacement for deterministic scoring.

Use clear wording:

```text
Base match shows exact and related-skill coverage.
AI review found cited evidence that may make the resume look stronger.
```

## Keep UI Output Actionable

chunk_type: rule
field: any
purpose: frontend

Generated output should fit cards, checklists, and dashboards. Prefer short
titles, clear requirements, concrete evidence, next actions, and interview
prompts. Avoid long essays unless the endpoint explicitly asks for a report.

Good UI card content:

```text
Requirement: IDS
Evidence: network threat detection project
Gap: no Snort or Suricata rules
Action: add an IDS lab or document alert rules
```

