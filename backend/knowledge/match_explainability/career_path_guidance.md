# Career Path Guidance

This document supports future career suggestions after the core matching
workflow. It is included now so the RAG knowledge base can grow in the same
structure as match explainability.

Career suggestions should be based on repeated evidence across a student's
resume and match history, not one isolated internship result.

## Cybersecurity Career Tracks

### SOC Analyst

Good fit signals:

```text
SIEM
log analysis
alert triage
incident response
network traffic analysis
threat detection
clear written reporting
```

Useful projects:

```text
Wazuh or Elastic SIEM lab
failed-login detection rule
phishing investigation writeup
Windows Event Log analysis
network alert triage report
```

Resume positioning:

```text
Emphasize detection, logs, alert handling, investigation steps, and written
incident reports.
```

### Penetration Tester

Good fit signals:

```text
Nmap
Burp Suite
Metasploit
OWASP Top 10
reconnaissance
web application security
vulnerability assessment
clear remediation reporting
```

Useful projects:

```text
OWASP Juice Shop testing report
lab network enumeration report
Burp Suite request manipulation walkthrough
CTF writeups with methodology and remediation
```

Resume positioning:

```text
Emphasize methodology: recon, enumeration, exploitation validation, impact,
and remediation.
```

### Security Engineer Intern

Good fit signals:

```text
secure coding
web application security
cloud or Linux basics
automation
vulnerability management
access control
```

Useful projects:

```text
secure API with authentication and authorization
dependency vulnerability scanning workflow
secrets management demo
CI security check
```

Resume positioning:

```text
Connect software engineering projects to security controls and risk reduction.
```

### Network Security Intern

Good fit signals:

```text
TCP/IP
DNS
DHCP
VLANs
firewalls
ACLs
Wireshark
network segmentation
IDS concepts
```

Useful projects:

```text
segmented Packet Tracer network
firewall rule lab
Wireshark PCAP investigation
ARP spoofing detection simulation
```

Resume positioning:

```text
Emphasize protocols, segmentation, packet analysis, and defensive monitoring.
```

### Application Security Intern

Good fit signals:

```text
Burp Suite
OWASP ZAP
OWASP Top 10
SQLi
XSS
secure coding
API testing
authentication and authorization testing
```

Useful projects:

```text
OWASP Juice Shop report
secure login implementation
SQL injection fix with parameterized queries
API authorization testing checklist
```

Resume positioning:

```text
Show both offensive testing and defensive fixes.
```

## Career Suggestion Rules

Use "recommended path" only when the student has multiple signals.

Use "emerging path" when the student has some evidence but needs projects.

Use "not enough evidence yet" when the resume is too sparse.

Do not recommend a path solely because one internship required it.

## Suggested Future Output

```json
{
  "top_paths": [
    {
      "path": "SOC Analyst",
      "fit": "good",
      "why": "The resume shows threat detection, log analysis, alert triage, and incident reporting evidence.",
      "supporting_evidence": ["summary", "skills_list", "project:0"],
      "next_steps": [
        "Build a Wazuh SIEM lab",
        "Add one incident triage writeup",
        "Practice Windows Event Log analysis"
      ]
    }
  ],
  "paths_to_delay": [
    {
      "path": "Java Backend Intern",
      "reason": "Current resume has no Java evidence."
    }
  ]
}
```
