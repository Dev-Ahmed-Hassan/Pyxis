# Cyber Interview Guidance

This document supports prepared interview sets and future live mock interview
sessions. It focuses on question style, answer expectations, and project
deep-dives.

## Project Deep Dive Pattern

chunk_type: interview
field: cybersecurity
role: any
skills: project explanation, communication, technical depth
purpose: interview-question-style

For project questions, ask the student to explain:

```text
problem
tools used
architecture or workflow
security concept demonstrated
tradeoff or limitation
what they would improve next
```

Strong answer structure:

```text
I built X to solve Y. I used A and B. The core workflow was C. The security
idea was D. A limitation was E, and I would improve it by F.
```

## Gap Challenge Pattern

chunk_type: interview
field: cybersecurity
role: any
skills: gap handling, honesty, learning plan
purpose: interview-question-style

When a match has missing skills, the interviewer may ask about them. The
student should not fake experience. A strong answer acknowledges the gap,
connects adjacent experience, and gives a concrete learning plan.

Example:

```text
I have not used PowerShell deeply yet. My scripting experience is stronger in
Bash and Python. To close that gap, I am building a small Windows event-log
triage script in PowerShell.
```

## SOC Interview Answer Expectations

chunk_type: interview
field: cybersecurity
role: SOC Analyst Intern
skills: SIEM, alert triage, incident response
purpose: answer-guide

Good SOC answers should mention:

```text
alert context
affected asset
log source
timeline
severity
false-positive check
containment or escalation
documentation
```

Weak SOC answers only name tools without explaining investigation steps.

## Pentest Interview Answer Expectations

chunk_type: interview
field: cybersecurity
role: Penetration Testing Intern
skills: reconnaissance, exploitation validation, reporting
purpose: answer-guide

Good penetration testing answers should mention:

```text
scope
authorization
reconnaissance
enumeration
vulnerability validation
impact
remediation
reporting
```

Weak answers focus only on exploiting without explaining ethics, scope, or
remediation.

## Network Security Interview Answer Expectations

chunk_type: interview
field: cybersecurity
role: Network Security Intern
skills: firewalls, segmentation, packet analysis
purpose: answer-guide

Good network security answers should connect technical configuration to risk
reduction. When discussing firewalls or ACLs, explain what traffic is allowed,
what is denied, why the rule exists, and how it was tested.

When discussing packet analysis, explain normal traffic first, then suspicious
signals such as unusual ARP behavior, repeated failed connections, strange DNS
queries, or unexpected ports.

