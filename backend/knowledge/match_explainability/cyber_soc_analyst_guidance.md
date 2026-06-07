# Cyber SOC Analyst Guidance

This document supports SOC analyst match explanations, career suggestions,
project recommendations, and interview preparation.

## SOC Analyst Role Signals

chunk_type: career
field: cybersecurity
role: SOC Analyst Intern
skills: SIEM, log analysis, alert triage, incident response, threat detection
purpose: role-fit

A SOC analyst internship usually values evidence of monitoring, log review,
alert triage, incident documentation, and basic escalation judgment. Strong
student evidence can come from SIEM labs, Windows or Linux log analysis,
network traffic analysis, phishing investigation writeups, Wazuh or Splunk
dashboards, and detection rules.

Resume evidence is stronger when it names:

```text
log source
alert condition
triage steps
false-positive handling
escalation or incident report
```

## SIEM Evidence Standards

chunk_type: domain
field: cybersecurity
role: SOC Analyst Intern
skills: SIEM, Wazuh, Splunk, Elastic, alert triage
purpose: evidence-standard

Direct SIEM evidence includes using tools such as Wazuh, Splunk, Elastic,
Microsoft Sentinel, QRadar, or Graylog to collect logs, write detections,
triage alerts, or build dashboards.

Partial evidence includes log analysis, threat detection, alert generation, or
network monitoring projects without a named SIEM. Explain partial support
carefully:

```text
This supports SIEM-adjacent monitoring, but it does not prove experience with a
SIEM platform, correlation rules, dashboards, or production alert workflows.
```

## SOC Project Suggestion Wazuh Lab

chunk_type: project
field: cybersecurity
role: SOC Analyst Intern
skills: SIEM, log analysis, alert triage, incident response
purpose: gap-project

Suggested project for SIEM or SOC gaps:

```text
Build a Wazuh mini SOC lab that collects Linux auth logs, detects repeated SSH
login failures, raises an alert, and documents triage steps.
```

Good deliverables:

```text
architecture diagram
log source list
detection rule or alert screenshot
triage notes
false-positive discussion
short incident report
```

Resume outcome:

```text
Built a Wazuh mini SOC lab to ingest Linux authentication logs, detect repeated
failed SSH attempts, triage alerts, and document incident response steps.
```

## SOC Interview Guidance

chunk_type: interview
field: cybersecurity
role: SOC Analyst Intern
skills: alert triage, log analysis, incident response
purpose: interview-prep

Common SOC interview questions:

```text
How would you triage a brute-force alert?
What logs would you check first?
How do you distinguish a false positive from a real incident?
How would you document and escalate an alert?
```

Strong answers should mention evidence, severity, affected assets, timeline,
containment, escalation, and written notes. If the student only has lab
experience, they should say it was a lab and explain the process clearly.

