# Cyber Web Security Guidance

This document supports web security match explanations, projects, career
recommendations, and interview preparation.

## Application Security Role Signals

chunk_type: career
field: cybersecurity
role: Application Security Intern
skills: OWASP Top 10, authentication, authorization, API testing, secure coding
purpose: role-fit

Application security internships value evidence that the student can test or
build safer web applications. Strong signals include OWASP Top 10 testing,
secure login implementation, authorization checks, API security, input
validation, parameterized queries, secrets handling, and clear remediation
advice.

Good evidence is specific:

```text
tested IDOR in a lab API
fixed SQL injection with parameterized queries
implemented role-based authorization
used Burp Suite to inspect requests
documented XSS impact and remediation
```

## Secure Coding Evidence Standards

chunk_type: domain
field: cybersecurity
role: Application Security Intern
skills: secure coding, SQL injection, XSS, authentication, authorization
purpose: evidence-standard

Direct secure coding evidence includes preventing or fixing a named
vulnerability. Examples include parameterized SQL queries, escaping output,
server-side authorization checks, secure password hashing, input validation,
rate limiting, CSRF defenses, and safe file upload handling.

Partial evidence includes general backend or frontend development without a
security control. Explain it as software engineering readiness, not proof of
application security.

## Secure API Project

chunk_type: project
field: cybersecurity
role: Application Security Intern
skills: API security, authentication, authorization, secure coding
purpose: gap-project

Suggested project for application security gaps:

```text
Build a small REST API with login, password hashing, role-based authorization,
input validation, and audit-friendly error handling.
```

Good deliverables:

```text
threat model
security controls list
test cases for unauthorized access
screenshots or curl examples
README explaining risks and mitigations
```

Resume outcome:

```text
Built a secure REST API with password hashing, role-based authorization, input
validation, and tests for unauthorized access paths.
```

## Web Security Interview Guidance

chunk_type: interview
field: cybersecurity
role: Application Security Intern
skills: OWASP Top 10, secure coding, API security
purpose: interview-prep

Common application security interview questions:

```text
How does SQL injection work and how do parameterized queries prevent it?
What is the difference between authentication and authorization?
How would you test for IDOR?
How can XSS be prevented?
What security checks would you add to an API before deployment?
```

Strong answers should define the vulnerability, explain impact, describe a
test method, and recommend a concrete mitigation.

