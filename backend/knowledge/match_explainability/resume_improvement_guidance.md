# Resume Improvement Guidance

This document guides student-facing improvement suggestions after a match.
Suggestions must be truthful, specific, and tied to match evidence.

The explanation generator should not tell a student to add a skill they do not
have. It should say how to better describe existing experience, or propose a
real project the student can do to close the gap.

## General Improvement Principles

### Preserve Truth

Every suggestion must be compatible with the evidence:

```text
If the resume proves a skill, suggest clearer wording.
If the resume partially supports a skill, suggest adding missing context.
If the resume lacks a skill, suggest a learning project or course.
```

Avoid:

```text
Add Splunk to your resume.
Claim Java experience.
Mention PowerShell even if you have not used it.
```

Prefer:

```text
If you have used Splunk or Wazuh, add the log source, query, alert, and triage outcome.
If not, build a small SIEM lab before listing SIEM experience.
```

### Be Requirement-Aware

Tie advice to the internship's actual requirements:

```text
Requirement: IDS
Resume evidence: ARP anomaly detection project
Advice: Mention IDS-style alerting, baselining, and anomaly detection.
```

Do not give generic career advice when a concrete gap exists.

### Use Evidence Citations

When possible, cite stable resume sections from the match/adjudication result:

```text
skills_list
summary
project:0
project:0:bullet:2
experience:1
certification:0
```

The generated explanation should make it clear whether advice is based on
skills, projects, experience, or certifications.

## Improvement Types

### Clarify Existing Evidence

Use this when the resume has relevant evidence but the wording is not aligned
with the internship requirement.

Example:

```text
The resume describes a network threat detection project, but the internship asks
for IDS knowledge. Reword the project bullet to explicitly mention IDS-style
alerting and anomaly detection if that accurately describes the work.
```

Good for:

```text
IDS partial evidence
SIEM-like log analysis
database security from SQL project
web security from secure coding project
SOC operations from alert triage
```

### Add Missing Technical Detail

Use this when the resume names a tool or concept but lacks practical detail.

Example:

```text
The resume lists Nessus. Add one bullet explaining what was scanned, what type
of finding was validated, and how remediation was documented.
```

Good details:

```text
tool name
task performed
target type
security finding
result or report
```

### Move Evidence To A Stronger Section

Use this when a skill appears only in the skills list but would be stronger in
a project or experience bullet.

Example:

```text
Burp Suite appears in the skills list. If it was used in a project, mention the
specific web vulnerability tested inside that project.
```

The engine treats demonstrated project or experience evidence as stronger than
a bare listed skill. The explanation should make this transparent.

### Add A Small Project

Use this when a gap is real and the student can close it with a realistic
project.

Project advice should include:

```text
project goal
tools
deliverable
resume bullet output
```

Example:

```text
To build SIEM evidence, create a Wazuh lab that ingests Linux auth logs, raises
an alert for repeated failed SSH logins, and documents triage steps in a short
incident report.
```

### Add Coursework Or Certification Context

Use this when a student has learning evidence but limited practical evidence.

Example:

```text
The TryHackMe path supports foundational security knowledge. Add one or two lab
writeups or project bullets to show what skills were practiced.
```

Do not overstate certifications as hands-on experience.

## Gap Severity Guidance

### High Severity Gap

Use high severity when:

```text
the requirement is required, not preferred
the resume has no direct or partial evidence
the missing skill is central to the role
```

Example explanation:

```text
This is a high-priority gap because the internship explicitly requires Java and
the resume has no Java evidence.
```

### Medium Severity Gap

Use medium severity when:

```text
the requirement is preferred
the resume has adjacent experience
the skill could be learned or demonstrated with a small project
```

Example:

```text
PowerShell is a preferred gap. The resume has scripting experience, but not
PowerShell specifically.
```

### Low Severity Gap

Use low severity when:

```text
the requirement is broad or optional
the resume strongly covers more important requirements
the missing item is a nice-to-have
```

## Cybersecurity Resume Patterns

### Strong Project Bullet Pattern

Use:

```text
Built [security tool/workflow] using [tools/languages] to [detect/test/analyze]
[target/problem], producing [result/report/finding].
```

Example:

```text
Built a Python and Scapy ARP monitoring tool to detect gateway MAC mismatch
behavior, raise alerts, and document spoofing indicators in an incident-style
report.
```

### Strong Vulnerability Assessment Bullet Pattern

Use:

```text
Performed [tool]-based vulnerability assessment on [target], validated
[finding type], and documented [remediation/report].
```

Example:

```text
Used Nessus and Nmap against lab hosts to identify exposed services, validate
findings manually, and summarize remediation steps.
```

### Strong Web Security Bullet Pattern

Use:

```text
Tested [application/API] for [vulnerability class] using [tool], then
implemented or recommended [fix].
```

Example:

```text
Tested a database-backed C# web application for SQL injection and used
parameterized queries to prevent unsafe input handling.
```

### Strong SIEM/SOC Bullet Pattern

Use:

```text
Ingested [log source] into [SIEM/tool], created [query/rule/dashboard], and
triaged [alert scenario].
```

Example:

```text
Ingested Linux authentication logs into Wazuh, created an alert for repeated
failed SSH logins, and documented triage steps.
```

## Explaining Strong Matches

When the resume strongly matches the internship, the explanation should still
be precise:

```text
Strong match because the resume directly lists Wireshark, Nmap, Burp Suite, and
Nessus, and also demonstrates traffic monitoring and vulnerability assessment
through projects.
```

Avoid:

```text
You are a perfect fit.
```

Even strong matches should mention remaining gaps.

## Explaining Partial Matches

Partial match wording should be honest:

```text
The resume does not directly list IDS tools such as Snort or Suricata, but the
network threat detection project provides strong partial evidence because it
includes traffic monitoring, anomaly detection, and alerting.
```

This is better than saying:

```text
The resume has IDS experience.
```

unless the resume directly supports that claim.

## Explaining Missing Skills

Missing skills should be stated plainly:

```text
No Java evidence was found.
No PowerShell evidence was found.
No Splunk or SIEM platform evidence was found.
```

Then suggest next action:

```text
If Java is important for this role, add a Java coursework or project bullet
only if you have completed one. Otherwise, build a small Java CLI or web
project before listing Java.
```

## Recommended Output Buckets

The future schema should group advice into:

```text
strengths
partial_matches
gaps
resume_improvements
learning_projects
interview_talking_points
fairness_notes
```

Each item should include:

```text
title
requirement
severity or impact
evidence section keys
student-facing explanation
recommended action
```

