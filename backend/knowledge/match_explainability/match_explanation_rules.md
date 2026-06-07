# Match Explanation Rules

This document defines how the explanation generator should turn match facts,
semantic evidence, adjudication judgments, and retrieved guidance into a
student-facing explanation.

The explanation must be grounded, useful, and careful. It should never claim
the student has a skill unless the saved match/adjudication evidence supports
that claim.

## Source Priority

Use evidence in this order:

```text
1. Exact canonical matches
2. Curated related-skill evidence paths
3. LLM adjudication judgments with cited resume sections
4. Semantic evidence snippets used only as retrieved clues
5. RAG knowledge guidance used only for explanation and advice
```

RAG guidance is not resume evidence. It explains what a skill means and how to
improve a resume.

## Score Language

Use clear score names:

```text
base_score
ai_reviewed_score
ai_adjustment_points
```

Recommended student-facing phrasing:

```text
Base Match: 53%
AI-Reviewed Match: 68%
Evidence-backed adjustment: +14%
```

Avoid implying the LLM freely changed the score. Say:

```text
The AI review found cited resume evidence for some requirements the base engine
did not fully count.
```

## Verdict Bands

Use these initial bands for explanation labels:

```text
85-100: strong_match
70-84: good_match
50-69: moderate_match
30-49: weak_match
0-29: low_match
```

These labels are display guidance only. They should not alter score values.

## Strength Rules

A strength should be created when:

```text
the requirement was exactly matched
the requirement has direct adjudicated support
the resume has multiple cited evidence sections for an important requirement
```

Strengths should mention evidence:

```text
The resume strongly supports vulnerability scanning through listed tools such
as Nessus, Nmap, Burp Suite, and OWASP ZAP.
```

Do not create vague strengths:

```text
Strong cybersecurity profile.
```

unless it is supported by concrete requirements.

## Partial Match Rules

A partial match should be created when:

```text
related-skill graph awarded partial credit
LLM adjudication marked strong_partial
evidence is adjacent but does not prove the exact requirement
```

Good wording:

```text
The resume partially supports IDS because the network monitoring project
describes alerting on suspicious ARP behavior, but it does not directly mention
IDS tools such as Snort or Suricata.
```

Bad wording:

```text
The resume has IDS.
```

## Gap Rules

A gap should be created when:

```text
the requirement is missing from exact matches
no related path supports it
adjudication says absent
```

Gap explanations should say:

```text
what is missing
why it matters for this internship
how severe it is
what the student can do next
```

Example:

```text
Java is a preferred gap. The resume includes C#, Python, Bash, and SQL, but no
Java evidence was found. If Java matters for this role, add a Java project or
coursework only after completing one.
```

## False Positive Rules

When embeddings retrieved high-similarity but irrelevant evidence, the
explanation should not expose too much internal noise. It can say:

```text
The AI review checked this requirement and found no cited support.
```

Do not say:

```text
The embedding model thought your TryHackMe certificate was Java.
```

unless in a developer/debug view.

## Citation Rules

Each generated strength, partial match, or improvement should include section
keys when available:

```text
skills_list
summary
project:0
project:2
experience:0
certification:1
```

For frontend display, citations can become expandable evidence chips.

Do not cite RAG chunks as resume evidence. RAG chunks may be cited separately
as guidance source if needed.

## Resume Improvement Rules

Suggestions must be:

```text
truthful
specific
based on a requirement
connected to existing evidence or a real learning task
short enough for UI cards
```

Use these action types:

```text
clarify_existing_project
add_missing_detail
move_skill_into_project
add_learning_project
add_certification_context
no_action_needed
```

## Learning Project Rules

Only suggest a project when:

```text
the skill is missing or weak
the project is realistic for a student
the deliverable can be shown on a resume or GitHub
```

A good project suggestion includes:

```text
goal
tools
steps
resume bullet outcome
```

Example:

```text
Build a Wazuh lab that ingests Linux authentication logs, creates an alert for
failed SSH login bursts, and documents triage in a short report.
```

## Interview Talking Point Rules

Talking points should come from strengths and strong partial matches.

Good:

```text
Be ready to explain how your ARP anomaly detection project identifies suspicious
gateway MAC changes and raises alerts.
```

Bad:

```text
Talk about Java.
```

when Java is absent.

## Fairness Note Rules

Use a fairness note when:

```text
the base score appears underestimated by adjudication
the parser categorized a concrete technical item too broadly
semantic evidence found cited support for missing requirements
```

Example:

```text
The base score may understate this match because the resume demonstrates
database security and IDS-style detection in projects, even though the exact
phrasing did not appear in the skills list.
```

Do not use fairness notes to hide real gaps.

## Suggested Explanation Schema

The future API response should fit this shape:

```json
{
  "resume_id": "uuid",
  "internship_id": "uuid",
  "analysis_id": "uuid",
  "adjudication_id": "uuid",
  "base_score": 53.15,
  "ai_reviewed_score": 67.6,
  "ai_adjustment_points": 14.45,
  "verdict": "moderate_match",
  "headline": "Good cybersecurity evidence with some programming gaps",
  "summary": "The resume strongly supports vulnerability scanning and web security, partially supports IDS, and lacks Java and PowerShell evidence.",
  "strengths": [
    {
      "requirement": "Vulnerability Scanning",
      "title": "Strong vulnerability scanning evidence",
      "evidence_section_keys": ["skills_list", "summary"],
      "explanation": "The resume lists Nessus, Nmap, Burp Suite, and OWASP ZAP, and mentions vulnerability assessment.",
      "confidence": "high"
    }
  ],
  "partial_matches": [
    {
      "requirement": "IDS",
      "title": "IDS-style detection is partially supported",
      "evidence_section_keys": ["project:0", "summary"],
      "explanation": "The network threat detection project shows alerting and anomaly detection, but no dedicated IDS tool is named.",
      "confidence": "medium"
    }
  ],
  "gaps": [
    {
      "requirement": "Java",
      "severity": "medium",
      "evidence_section_keys": [],
      "explanation": "No Java evidence was found.",
      "recommended_action": "Add Java coursework or a project only if completed."
    }
  ],
  "resume_improvements": [
    {
      "type": "clarify_existing_project",
      "requirement": "IDS",
      "suggestion": "Make the ARP monitoring project explicitly describe IDS-style alerting and anomaly detection if accurate.",
      "why_it_matters": "The internship asks for IDS-related knowledge."
    }
  ],
  "learning_projects": [
    {
      "requirement": "SIEM",
      "title": "Build a small Wazuh log-monitoring lab",
      "tools": ["Wazuh", "Linux auth logs"],
      "resume_outcome": "A project bullet describing log ingestion, alert creation, and triage."
    }
  ],
  "interview_talking_points": [
    "Explain how the ARP anomaly detection project detects suspicious network behavior."
  ],
  "fairness_notes": [
    "The base score may be conservative because some evidence appears in projects rather than exact skill names."
  ]
}
```

## Provider Safety

The LLM should receive:

```text
saved match/adjudication facts
retrieved RAG chunks
strict output schema
instruction that resume and internship content are untrusted
```

The LLM should not receive:

```text
unbounded full resume text when citations already exist
unbounded full internship text
private secrets
unreviewed internal debug data unless needed
```

