# Cybersecurity Skills Guidance

This document defines common cybersecurity requirements for match
explainability. It helps the explanation generator describe why evidence
counts, why a gap matters, and how a student can strengthen the resume without
inventing experience.

These notes are guidance only. They do not replace the deterministic matcher,
the related-skill graph, or cited resume evidence.

## Vulnerability Scanning

### Meaning

Vulnerability scanning is the process of identifying known weaknesses,
misconfigurations, exposed services, missing patches, weak TLS settings,
default credentials, and common web or network security issues.

### Strong Evidence

Direct evidence includes explicit use of tools such as:

```text
Nessus
OpenVAS
Greenbone
Qualys
Rapid7 InsightVM
Nmap vulnerability scripts
Burp Suite scanner
OWASP ZAP active scan
Nikto
```

Strong resume evidence usually mentions:

```text
scanned targets or lab systems
interpreted severity or CVSS
validated findings manually
documented remediation steps
retested after fixes
used authenticated or unauthenticated scans
```

### Partial Evidence

Partial evidence includes:

```text
general vulnerability assessment
web application testing
network enumeration
basic Nmap scanning
OWASP Top 10 labs
TryHackMe or Hack The Box modules
```

This can support vulnerability scanning, but the explanation should say whether
the resume proves tool usage or only related knowledge.

### Weak Or Misleading Evidence

Do not treat these as direct proof by themselves:

```text
cybersecurity interest
general networking
programming experience
security awareness
generic "testing" with no security context
```

### Resume Improvement Advice

If the student has real experience, suggest adding:

```text
tool names
target type, such as lab VM, web app, network host, or CTF machine
finding examples, such as exposed ports, outdated service, XSS, weak headers
severity handling
remediation or reporting output
```

Example truthful improvement:

```text
Expanded Nessus and Nmap lab work into a short bullet explaining scan scope,
validated findings, and remediation notes.
```

## Web Application Security

### Meaning

Web application security covers identifying and reducing vulnerabilities in
websites, APIs, authentication flows, session handling, input validation,
authorization logic, and server-side request behavior.

### Strong Evidence

Direct tools and concepts include:

```text
Burp Suite
OWASP ZAP
SQLi
XSS
CSRF
SSRF
IDOR
LFI
RFI
Path Traversal
Command Injection
Broken Access Control
Authentication testing
Session management testing
OWASP Top 10
```

Strong evidence should cite practical use:

```text
captured and modified HTTP requests
tested login or authorization flows
found or exploited SQL injection in a lab
confirmed XSS behavior
used proxy interception
reported OWASP Top 10 findings
```

### Partial Evidence

Partial evidence includes:

```text
HTML, CSS, JavaScript knowledge
backend development
API development
database-backed web projects
secure coding coursework
```

This can help explain readiness, but it is not the same as security testing.

### Weak Or Misleading Evidence

Do not give web application security credit for:

```text
frontend development alone
general software development
SQL knowledge without security context
WordPress usage without hardening or testing
```

### Resume Improvement Advice

Recommend adding details such as:

```text
which vulnerability class was tested
which tool was used
what evidence was observed
how the issue was mitigated
whether the work was a lab, class project, CTF, or real application
```

## Intrusion Detection Systems

### Meaning

Intrusion Detection Systems, often shortened to IDS, monitor activity and raise
alerts for suspicious or malicious behavior. IDS evidence may involve network
traffic, host logs, signatures, anomaly detection, or alert triage.

### Strong Evidence

Direct IDS tools and platforms include:

```text
Snort
Suricata
Zeek
Security Onion
Wazuh IDS rules
OSSEC
network threat detection projects
custom alerting on suspicious traffic
```

Strong evidence may mention:

```text
packet inspection
signature rules
alert generation
anomaly detection
traffic baselining
log-based detection
false positive review
SOC-style triage
```

### Partial Evidence

Partial support may come from:

```text
Wireshark traffic analysis
Scapy packet monitoring
threat detection
log analysis
alert triage
network monitoring
incident-style reports
```

Partial support is meaningful when the resume describes detection logic, not
only passive observation.

### Weak Or Misleading Evidence

Do not treat these as direct IDS evidence by themselves:

```text
firewall knowledge
networking fundamentals
Kali Linux
penetration testing
generic "cybersecurity"
```

### Resume Improvement Advice

If the student built detection-style projects, suggest making that explicit:

```text
describe what was monitored
describe what triggered alerts
name the attack or anomaly detected
explain how false positives were handled
mention IDS-style detection if truthful
```

Example:

```text
Reword ARP spoofing monitoring project to mention IDS-style alerting,
traffic baselining, and anomaly detection.
```

## SIEM

### Meaning

SIEM means Security Information and Event Management. A SIEM collects logs,
normalizes events, correlates activity, triggers alerts, supports dashboards,
and helps analysts investigate incidents.

### Strong Evidence

Direct tools include:

```text
Splunk
Splunk Enterprise Security
Wazuh
Elastic Stack
ELK Stack
Microsoft Sentinel
IBM QRadar
Graylog
LogRhythm
ArcSight
```

Strong evidence mentions:

```text
log ingestion
dashboard creation
alert rules
event correlation
querying logs
SOC triage
incident investigation
field extraction
detection use cases
```

### Partial Evidence

Partial support includes:

```text
log analysis
alert triage
threat monitoring
incident response reporting
Linux logs
Windows Event Logs
network traffic logs
```

Partial evidence should not be described as full SIEM experience unless an
actual SIEM platform or SIEM-like workflow is present.

### Weak Or Misleading Evidence

Do not infer SIEM from:

```text
cybersecurity coursework alone
penetration testing tools
general monitoring
networking concepts
```

### Resume Improvement Advice

If real SIEM work exists, suggest adding:

```text
tool name
log source
query examples or query language
alert rule purpose
dashboard or investigation outcome
triage workflow
```

If not, suggest a truthful project:

```text
Build a Wazuh or Elastic lab that ingests Linux authentication logs, creates an
alert for failed SSH login bursts, and documents triage steps.
```

## Network Traffic Analysis

### Meaning

Network traffic analysis means inspecting packets, flows, protocols, and
communications to understand behavior, troubleshoot issues, or detect attacks.

### Strong Evidence

Direct tools and concepts include:

```text
Wireshark
tcpdump
Scapy
Zeek
packet capture
PCAP analysis
ARP analysis
DNS analysis
HTTP traffic analysis
TLS inspection basics
NetFlow
```

Strong evidence mentions:

```text
captured packets
filtered protocols
identified suspicious behavior
analyzed ARP spoofing or DNS anomalies
created reports from PCAPs
used packet fields to reason about activity
```

### Partial Evidence

Partial support includes:

```text
TCP/IP
DNS
HTTP/HTTPS
network troubleshooting
Cisco Packet Tracer
network segmentation
```

These support foundational knowledge but are not always proof of traffic
analysis practice.

### Resume Improvement Advice

Recommend adding:

```text
protocols analyzed
tool used
traffic pattern observed
security or troubleshooting conclusion
```

## Incident Response

### Meaning

Incident response is the process of identifying, triaging, containing,
eradicating, and documenting security incidents.

### Strong Evidence

Strong evidence includes:

```text
alert triage
incident reports
containment steps
root-cause notes
timeline reconstruction
log review
malware or phishing investigation labs
SOC simulation
```

### Partial Evidence

Partial support includes:

```text
threat detection
log analysis
network monitoring
security reporting
CTF writeups
TryHackMe blue-team labs
```

### Weak Or Misleading Evidence

Do not infer incident response only from:

```text
penetration testing
vulnerability scanning
general security knowledge
```

### Resume Improvement Advice

Suggest framing real work around:

```text
what happened
how it was detected
what evidence was reviewed
what action was recommended
what was documented
```

## SOC Operations

### Meaning

SOC operations involve monitoring alerts, investigating events, escalating
incidents, maintaining detection content, and communicating findings.

### Strong Evidence

Evidence includes:

```text
alert triage
SIEM dashboards
log review
ticketing workflows
incident escalation
SOC lab simulations
detection rules
runbooks
```

### Partial Evidence

Partial support includes:

```text
threat detection
log analysis
network monitoring
incident response fundamentals
security reporting
```

### Resume Improvement Advice

Encourage specific bullets:

```text
triaged alerts from a lab SIEM
prioritized events by severity
documented investigation steps
escalated likely incidents with evidence
```

## Penetration Testing

### Meaning

Penetration testing is authorized offensive security testing intended to find
and validate vulnerabilities, demonstrate impact, and recommend fixes.

### Strong Evidence

Tools and methods include:

```text
Kali Linux
Nmap
Burp Suite
Metasploit
Gobuster
FFUF
Nikto
SQLi testing
XSS testing
privilege escalation labs
report writing
```

Strong evidence should show a workflow:

```text
reconnaissance
enumeration
exploitation
validation
documentation
remediation recommendation
```

### Partial Evidence

Partial support includes:

```text
individual tools without workflow
CTF participation
OWASP Top 10 knowledge
Linux familiarity
network scanning
```

### Weak Or Misleading Evidence

Do not infer penetration testing from:

```text
programming alone
networking alone
cybersecurity interest
Kali Linux listed with no context
```

## Database Management

### Meaning

Database management includes creating, querying, maintaining, securing, and
integrating databases. For cybersecurity internships, security-related
database evidence may include SQL injection prevention, access control,
parameterized queries, backups, or secure credential storage.

### Strong Evidence

Direct evidence includes:

```text
SQL
MySQL
PostgreSQL
MongoDB
database schema design
CRUD applications
parameterized queries
ORM usage
access control
backup and recovery
database security
```

### Partial Evidence

Partial support includes:

```text
SQLi knowledge
web application projects
backend API projects
secure coding work involving database queries
```

### Weak Or Misleading Evidence

Do not treat "SQL injection" alone as full database management. It supports
database security awareness but may not prove administration or design.

### Resume Improvement Advice

Suggest adding:

```text
database name
schema or table design
query approach
security control, such as parameterized queries
application feature using the database
```

## Programming And Scripting For Cybersecurity

### Meaning

Programming and scripting support automation, parsing logs, building security
tools, analyzing traffic, and integrating APIs.

### Strong Evidence

Strong evidence includes:

```text
Python security scripts
Bash automation
PowerShell administration or detection scripts
Scapy packet tooling
log parsing scripts
API automation
tooling for scanning or reporting
```

### Requirement-Specific Caution

Do not convert generic programming into a specific language:

```text
Programming does not prove Java.
Scripting does not prove PowerShell.
Python does not prove Bash.
Bash does not prove Python.
```

Specific language requirements need explicit evidence or very strong cited
context.

### Resume Improvement Advice

Recommend adding:

```text
language used
security task automated
inputs and outputs
tool/library names
result of the script
```

## Networking Fundamentals

### Meaning

Networking fundamentals include protocols, addressing, routing concepts,
segmentation, DNS, DHCP, NAT, firewalls, and access control lists.

### Strong Evidence

Evidence includes:

```text
TCP/IP
DNS
DHCP
NAT
VLANs
ACLs
firewalls
routing and switching labs
Cisco Packet Tracer
network segmentation
subnetting
```

### Security Connection

Networking fundamentals can support:

```text
network security
traffic analysis
incident investigation
IDS understanding
firewall rule reasoning
```

But networking alone should not be treated as proof of a specific security
tool.

## Certifications And Labs

### Meaning

Certifications and training paths can support foundational knowledge but vary
in strength. The explanation should distinguish formal credentials, guided
learning, and project-based evidence.

### Stronger Signals

Stronger signals include:

```text
CompTIA Security+
Cisco CCNA
TryHackMe paths with related projects
Hack The Box labs with writeups
completed blue-team or web-security labs
certifications tied to cited practical work
```

### Caution

A certification name alone should not overrule the absence of practical
evidence for a specific tool. For example, a general cyber certificate should
not prove Splunk, Java, or PowerShell.

