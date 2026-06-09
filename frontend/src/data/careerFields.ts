export type FieldKey = 'cybersecurity' | 'ai-ml' | 'software'

export type FieldStory = {
  label: string
  role: string
  score: number
  summary: string
  strengths: string[]
  missingSkills: string[]
  improvements: string[]
  roadmap: string[][]
  profileTitle: string
  profileFacts: string[][]
  coverage: [string, number][]
  evidence: { skill: string; detail: string; confidence: string }
  graphNodes: [string, 'known' | 'related' | 'gap', string][]
  relationship: string[]
  project: {
    title: string
    description: string
    tools: string[]
    outcome: string
  }
  learningSequence: string[]
  careers: [string, string, string][]
  nextSkill: string
  repositories: string[][]
  repositoryEvidence: string
  interviewQuestion: string
  interviewAnswer: string
  feedback: [string, string][]
}

export const fieldStories: Record<FieldKey, FieldStory> = {
  cybersecurity: {
    label: 'Cyber Security',
    role: 'Security Analyst Intern',
    score: 88,
    summary: 'Strong practical security and network-analysis foundation.',
    strengths: [
      'Hands-on experience with Kali Linux, Nmap, and Wireshark.',
      'Projects demonstrate vulnerability assessment and traffic analysis.',
      'Relevant understanding of web and network security concepts.',
    ],
    missingSkills: [
      'Production experience with SIEM and alert investigation workflows.',
      'Clear evidence of security reporting for non-technical stakeholders.',
    ],
    improvements: [
      'Add measurable findings and remediation outcomes to security projects.',
      'Connect each listed tool to a specific investigation or assessment.',
    ],
    roadmap: [
      ['Week 1: Detection', 'Build and document a small SIEM alert workflow.'],
      ['Week 2: Reporting', 'Write an executive and technical incident summary.'],
      ['Week 3: Evidence', 'Publish a sanitized investigation portfolio entry.'],
    ],
    profileTitle: 'Security-focused CS student',
    profileFacts: [
      ['Wireshark', 'Network monitor', 'Strong'],
      ['Python', '3 projects', 'Strong'],
      ['Incident response', 'Coursework', 'Emerging'],
      ['Burp Suite', 'Web audit', 'Moderate'],
    ],
    coverage: [
      ['Required technical skills', 92],
      ['Preferred technical skills', 70],
      ['Domain concepts', 84],
    ],
    evidence: {
      skill: 'Vulnerability scanning',
      detail: 'Nessus and assessment evidence in Project 02',
      confidence: '0.89 confidence',
    },
    graphNodes: [
      ['Python', 'known', 'Automation evidence from three projects.'],
      ['Network Security', 'known', 'Explicit resume and coursework evidence.'],
      ['Wireshark', 'known', 'Demonstrated in a packet-analysis project.'],
      ['Threat Detection', 'related', 'Supported by monitoring and traffic analysis.'],
      ['SIEM', 'gap', 'Target skill with a reviewed prerequisite path.'],
    ],
    relationship: ['Wireshark', 'Threat Detection', 'SIEM'],
    project: {
      title: 'Home SOC investigation lab',
      description:
        'Generate suspicious traffic, collect alerts, investigate them, and publish a concise incident report.',
      tools: ['Wazuh', 'Sysmon', 'Python'],
      outcome: 'Evidence for SIEM, alert triage, and security reporting.',
    },
    learningSequence: [
      'Log analysis fundamentals',
      'Detection rule design',
      'Alert investigation',
      'Incident communication',
    ],
    careers: [
      ['SOC Analyst', '92%', 'Strong'],
      ['Security Engineer', '78%', 'Good'],
      ['Penetration Tester', '74%', 'Good'],
    ],
    nextSkill: 'Security Information & Event Management',
    repositories: [
      ['network-monitor', 'Python · Scapy', 'Strong evidence'],
      ['web-security-lab', 'JavaScript · Burp', 'Resume worthy'],
      ['semester-project', 'C# · SQL', 'README needs work'],
    ],
    repositoryEvidence:
      'network-monitor supports packet analysis, automation, and threat-detection requirements.',
    interviewQuestion:
      'Your network-monitor project mentions ARP spoofing detection. Walk me through how you established a baseline and decided that an event was suspicious.',
    interviewAnswer:
      'I first recorded normal IP-to-MAC mappings, then compared new ARP replies against that baseline...',
    feedback: [
      ['Technical accuracy', '86'],
      ['Evidence usage', '91'],
      ['Communication', '75'],
    ],
  },
  'ai-ml': {
    label: 'AI / ML',
    role: 'Machine Learning Intern',
    score: 72,
    summary: 'Good programming base with room for stronger model evidence.',
    strengths: [
      'Python and data-structure fundamentals support model development.',
      'Academic projects show analytical and problem-solving ability.',
      'Existing SQL knowledge supports practical data preparation.',
    ],
    missingSkills: [
      'No clear model evaluation, experiment tracking, or deployment evidence.',
      'Limited proof of work with a modern ML framework.',
    ],
    improvements: [
      'Describe datasets, evaluation metrics, and model outcomes in projects.',
      'Add one end-to-end project using scikit-learn or PyTorch.',
    ],
    roadmap: [
      ['Week 1: Modeling', 'Train and evaluate a baseline classification model.'],
      ['Week 2: Experimentation', 'Compare models and document tradeoffs.'],
      ['Week 3: Delivery', 'Expose the model through a small FastAPI service.'],
    ],
    profileTitle: 'Data-minded software student',
    profileFacts: [
      ['Python', '3 projects', 'Strong'],
      ['SQL', 'Database project', 'Strong'],
      ['Data analysis', 'Coursework', 'Moderate'],
      ['Statistics', 'Academic record', 'Emerging'],
    ],
    coverage: [
      ['Programming foundations', 88],
      ['ML frameworks and tools', 54],
      ['Model evaluation concepts', 66],
    ],
    evidence: {
      skill: 'Data preparation',
      detail: 'SQL and Python transformations in Project 03',
      confidence: '0.84 confidence',
    },
    graphNodes: [
      ['Python', 'known', 'Strong evidence across multiple projects.'],
      ['Statistics', 'known', 'Supported by academic coursework.'],
      ['SQL', 'known', 'Explicit database and data-query evidence.'],
      ['Model Evaluation', 'related', 'Built on statistics and analytical work.'],
      ['MLOps', 'gap', 'Target gap requiring deployment foundations.'],
    ],
    relationship: ['Statistics', 'Model Evaluation', 'MLOps'],
    project: {
      title: 'Explainable internship recommender',
      description:
        'Train a role recommendation model, compare baselines, expose predictions, and explain the important features.',
      tools: ['scikit-learn', 'MLflow', 'FastAPI'],
      outcome: 'Evidence for evaluation, experiment tracking, and deployment.',
    },
    learningSequence: [
      'Data validation',
      'Baseline modeling',
      'Evaluation and tuning',
      'Model deployment',
    ],
    careers: [
      ['Data Analyst', '86%', 'Strong'],
      ['ML Engineer', '72%', 'Good'],
      ['Data Scientist', '68%', 'Emerging'],
    ],
    nextSkill: 'Model evaluation and experiment tracking',
    repositories: [
      ['student-performance-ml', 'Python · pandas', 'Strong evidence'],
      ['data-dashboard', 'Python · SQL', 'Resume worthy'],
      ['notebook-practice', 'Jupyter', 'Needs narrative'],
    ],
    repositoryEvidence:
      'student-performance-ml supports preprocessing, feature engineering, and baseline-model requirements.',
    interviewQuestion:
      'Your classification project reports accuracy. How did you choose that metric, and what would make it misleading for this dataset?',
    interviewAnswer:
      'I started with accuracy, but then checked the class balance and compared precision, recall, and the confusion matrix...',
    feedback: [
      ['Model reasoning', '80'],
      ['Evidence usage', '84'],
      ['Communication', '78'],
    ],
  },
  software: {
    label: 'Software Engineering',
    role: 'Software Engineering Intern',
    score: 81,
    summary: 'Solid programming breadth with useful project foundations.',
    strengths: [
      'Experience across Python, C/C++, C#, SQL, and JavaScript.',
      'Projects demonstrate API, database, and software-design exposure.',
      'Technical documentation and problem solving are visible strengths.',
    ],
    missingSkills: [
      'Limited evidence of automated testing and continuous integration.',
      'Project descriptions do not clearly explain architecture decisions.',
    ],
    improvements: [
      'Add test coverage, architecture notes, and measurable project outcomes.',
      'Describe individual ownership inside collaborative projects.',
    ],
    roadmap: [
      ['Week 1: Quality', 'Add unit and integration tests to one existing API.'],
      ['Week 2: Delivery', 'Configure a CI workflow for linting and tests.'],
      ['Week 3: Architecture', 'Document system boundaries and design choices.'],
    ],
    profileTitle: 'Full-stack software student',
    profileFacts: [
      ['FastAPI', 'Backend project', 'Strong'],
      ['SQL', '2 applications', 'Strong'],
      ['JavaScript', 'Web projects', 'Moderate'],
      ['Testing', 'Limited evidence', 'Emerging'],
    ],
    coverage: [
      ['Programming and OOP', 94],
      ['Web and API development', 82],
      ['Testing and delivery', 58],
    ],
    evidence: {
      skill: 'API development',
      detail: 'FastAPI services and PostgreSQL integration in Project 01',
      confidence: '0.92 confidence',
    },
    graphNodes: [
      ['Python', 'known', 'Strong programming and backend evidence.'],
      ['OOP', 'known', 'Explicit coursework and project usage.'],
      ['SQL', 'known', 'Used in multiple application projects.'],
      ['Automated Testing', 'related', 'Supported by software-quality foundations.'],
      ['CI/CD', 'gap', 'Target gap connected to testing and delivery.'],
    ],
    relationship: ['Python', 'Automated Testing', 'CI/CD'],
    project: {
      title: 'Production-ready task platform',
      description:
        'Build a typed API and frontend, add test coverage, containerize it, and automate checks on every pull request.',
      tools: ['React', 'FastAPI', 'GitHub Actions'],
      outcome: 'Evidence for architecture, testing, CI, and team workflow.',
    },
    learningSequence: [
      'Unit and integration testing',
      'API contract design',
      'Containerization',
      'Continuous integration',
    ],
    careers: [
      ['Backend Engineer', '89%', 'Strong'],
      ['Full-stack Engineer', '82%', 'Strong'],
      ['Platform Engineer', '65%', 'Emerging'],
    ],
    nextSkill: 'Automated testing and continuous integration',
    repositories: [
      ['career-platform-api', 'Python · FastAPI', 'Strong evidence'],
      ['inventory-system', 'C# · SQL', 'Resume worthy'],
      ['frontend-practice', 'JavaScript · CSS', 'Needs testing'],
    ],
    repositoryEvidence:
      'career-platform-api supports API design, database integration, and documentation requirements.',
    interviewQuestion:
      'Your career-platform API uses several services and databases. How did you decide the module boundaries, and what would you change at larger scale?',
    interviewAnswer:
      'I separated ownership, processing, and analysis responsibilities so each service had one clear reason to change...',
    feedback: [
      ['System design', '88'],
      ['Evidence usage', '87'],
      ['Communication', '80'],
    ],
  },
}
