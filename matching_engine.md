# Pyxis Matching Engine

This is the living design record for Pyxis resume-to-internship matching.
Update it whenever a scoring rule, evidence rule, calibration assumption, or
matching roadmap decision changes.

The goal is not to produce a mysterious AI score. The goal is to build an
explainable engine whose remaining limitations increasingly come from the
quality and coverage of its aliases, relationships, embeddings, and evaluation
data rather than avoidable weaknesses in the algorithm.

## 1. Product Question

Given one student resume and one real internship description, help the student
answer:

```text
How suitable is this resume for this internship?
Which requirements are directly satisfied?
Which requirements have related but incomplete evidence?
Which important requirements appear to be missing?
Why did the engine produce this result?
```

The result must remain useful when AI providers, Neo4j, or semantic embeddings
are unavailable.

## 2. Non-Negotiable Principles

1. The LLM may extract structured information, adjudicate cited evidence in
   shadow mode, and later explain a result. It must not invent the final score.
2. Exact evidence, related evidence, semantic evidence, and warnings must remain
   distinguishable in the response.
3. A missing relationship must not be treated as proof that two concepts are
   unrelated.
4. A related tool must not be treated as proof that a student fully satisfies a
   broader requirement.
5. Multiple pieces of evidence may strengthen an explanation, but must not
   repeatedly inflate the same requirement score.
6. Every scoring revision receives a new `score_version`.
7. The matcher must remain deterministic for the same validated input data,
   rule set, and score version.
8. Sparse, broad, or ambiguous input should produce warnings rather than
   artificially confident scores.

## 3. Current Request Flow

```text
POST /matches/preview
-> authenticate student
-> verify owned ready resume and internship records
-> load validated parsed documents from MongoDB
-> canonicalize resume skills and internship requirements
-> reclassify known legacy parser-v1 categories
-> normalize known domain-concept aliases
-> collect resume evidence with section and extraction provenance
-> calculate exact technical overlap
-> find curated related-skill evidence paths
-> weight related technical evidence by relationship and resume provenance
-> load strongest refreshed pgvector evidence per concrete requirement
-> attach domain-concept and soft-skill evidence separately
-> return score breakdown, exact paths, semantic evidence, gaps, and warnings

POST /matches/analyses
-> run the same owned ready-input matching flow
-> persist immutable PostgreSQL history with score version and JSON breakdown
-> return the saved analysis

input-changing mutation
-> mark affected saved analyses stale in PostgreSQL
-> invalidate old vectors
-> enqueue latest semantic refresh generation

semantic embedding worker
-> claim queued PostgreSQL refresh job
-> load latest validated MongoDB profile
-> regenerate one input's vectors
-> retry transient failures independently of parsing
-> discard obsolete output when a newer generation was queued

POST /matches/embeddings/refresh
-> verify owned ready resume and internship records
-> assemble deterministic item-level section and requirement documents
-> generate configured Gemini embeddings
-> replace pgvector evidence transactionally
-> mark affected saved analyses stale

POST /matches/adjudications
-> run the official deterministic preview
-> retrieve the top three resume passages for each missing concrete requirement
-> ask the configured structured-output LLM to classify cited evidence
-> reject unknown requirements, missing judgments, and uncited support
-> calculate a bounded Python shadow comparison without changing official score
-> persist model, prompt version, excerpts, citations, and fairness audit
```

Primary implementation files:

| Path | Responsibility |
| --- | --- |
| `backend/services/matching_service.py` | Deterministic scoring and response assembly |
| `backend/services/related_skill_service.py` | Curated aliases, relationships, and explainable path lookup |
| `backend/services/skill_canonicalizer.py` | Skill-name aliases such as `js -> JavaScript` |
| `backend/services/resume_evidence_service.py` | Provenance-aware resume skill evidence inventory |
| `backend/services/matching_evaluation_service.py` | Fixture loader and deterministic offline evaluation |
| `backend/services/match_analysis_service.py` | Immutable PostgreSQL analysis history |
| `backend/services/analysis_staleness_service.py` | Marks saved analyses stale when inputs change |
| `backend/services/semantic_embedding_service.py` | Builds and persists item-level pgvector documents |
| `backend/services/semantic_matching_service.py` | Loads explainable semantic evidence independently of numeric scoring |
| `backend/services/match_llm_adjudication_service.py` | Validates cited LLM evidence audits and calculates shadow-only bounded comparisons |
| `backend/services/semantic_embedding_queue_service.py` | Enqueues latest semantic refresh generation after input changes |
| `backend/workers/semantic_embedding_worker.py` | Regenerates vectors asynchronously with retries and obsolete-result protection |
| `backend/services/semantic_calibration_service.py` | Reports threshold precision, recall, and F1 over labeled observations |
| `backend/schemas/matching.py` | Public match-preview response contract |
| `backend/tests/test_matching_modules.py` | Focused matcher regression tests |
| `backend/tests/fixtures/matching_engine_cases.json` | Human-reviewed cross-domain evaluation corpus |
| `backend/knowledge/match_explainability/` | RAG source documents for grounded match explanations, resume improvements, and later career guidance |

## 4. Current Score: Version 6

Current score version:

```text
separate-semantic-evidence-reporting-v6
```

### 4.1 Exact Technical Overlap

Concrete required and preferred technical skills are compared after
canonicalization:

```text
required technical skills  = 80%
preferred technical skills = 20%
```

When only one section exists, its unused weight is reassigned:

```text
required only  -> required weight becomes 100%
preferred only -> preferred weight becomes 100%
neither        -> score is 0 with a warning
```

### 4.2 Related Technical Credit

If a concrete technical requirement is not an exact match but has curated
supporting evidence, its strongest reviewed path receives capped partial
credit:

```text
maximum related technical credit = 50% of the requirement's normal value
effective credit factor          = maximum credit
                                   * multiplied edge confidence
                                   * path-distance decay
                                   * resume provenance weight
path-distance decay              = 0.85 ^ (edge count - 1)
```

Example:

```text
Nessus -> Vulnerability Assessment -> Vulnerability Research
```

If `Vulnerability Research` is one of three required technical requirements:

```text
Nessus -> Vulnerability Assessment             confidence = 0.95
Vulnerability Assessment -> Vulnerability Research confidence = 0.80
multiplied edge confidence                     = 0.76
path-distance decay                            = 0.85
effective credit factor                        = 0.50 * 0.76 * 0.85 = 0.323
```

Multiple evidence paths for the same requirement improve the explanation but
do not award duplicate points. The strongest reviewed path determines credit.

### 4.3 Resume Evidence Provenance

Resume skills are collected from multiple sections and remain visible in the
response:

```text
skills-list explicit mention = 0.75
skills-list cautious inference = 0.75 * 0.65 = 0.4875
project evidence             = 0.90
experience evidence          = 1.00
certification name evidence  = 0.85
```

### 4.4 Shadow LLM Evidence Adjudication

`retrieval-assisted-llm-evidence-adjudication-v7` is an audit layer, not a new
official score version. The official score remains
`separate-semantic-evidence-reporting-v6` until reviewed examples justify a
scoring change.

For each concrete requirement still missing after exact and curated
relationship matching:

```text
retrieve top 3 resume passages with pgvector
-> LLM classifies direct, strong_partial, weak_related, or absent
-> every supported classification must cite a retrieved passage
-> Python calculates a shadow-only comparison
```

Initial conservative shadow caps:

```text
direct         = 50% of normal requirement value
strong_partial = 30% of normal requirement value
weak_related   = 0%
absent         = 0%
```

These values are deliberately bounded and are not production scoring weights.
Stored audits must be reviewed against human labels before any LLM-adjudicated
credit can affect the official score.

These are calibration baselines. Provenance adjusts related-evidence credit:

```text
inferred Nessus mention -> Vulnerability Research = 15.75
listed Nessus mention   -> Vulnerability Research = 24.23
project Nessus usage    -> Vulnerability Research = 29.07
experience Nessus usage -> Vulnerability Research = 32.30
```

Exact canonical presence remains a deterministic match. Provenance is exposed
alongside exact matches so the frontend can explain whether the evidence was a
listed skill, project usage, or experience usage without secretly converting a
valid direct match into a heuristic score.

### 4.5 Domain Concepts

Domain concepts remain visible and may receive evidence paths:

```text
Nmap -> Network Security
Kali Linux -> Cybersecurity Fundamentals
```

They do not add numeric credit yet. A broad concept needs a calibrated scoring
policy before it can influence the result safely.

### 4.6 Soft Skills

Soft skills remain visible but do not affect the technical score:

```text
Teamwork
Communication Skills
Attention to Detail
```

A resume parser cannot reliably prove these qualities from keyword presence
alone.

### 4.7 Semantic Evidence Reporting

Version 6 stores and reports section-level pgvector evidence without adding
semantic points yet:

```text
resume documents:
summary
project:0, project:1, ...
experience:0, experience:1, ...
education:0, education:1, ...

internship documents:
required_skill
preferred_skill
```

Each reported semantic item includes:

```text
requirement
requirement category
supporting resume section and stable key
resume text excerpt
embedding model
cosine similarity
reporting threshold
```

The initial reporting threshold is `0.72`. This is an explicit calibration
baseline, not a final truth boundary. For each requirement, only the strongest
resume section above the threshold is returned so repeated similar bullets do
not create a misleading volume effect.

Semantic evidence currently has:

```text
contributes_to_score = false
```

This is intentional. Similarity needs reviewed positive, borderline, and
negative examples before it can affect numeric scoring safely.

## 5. Current Alias And Relationship Data

Current domain aliases:

```text
Network Security Principles -> Network Security
Security Concepts           -> Cybersecurity Fundamentals
```

Current curated relationships include a type and confidence value:

```text
Nmap                     -[evidence_for 0.90]-> Network Security
DNS                      -[evidence_for 0.80]-> Network Security
Firewalls                -[evidence_for 0.90]-> Network Security
TCP/IP                   -[evidence_for 0.85]-> Network Security
Nessus                   -[evidence_for 0.95]-> Vulnerability Assessment
Burp Suite               -[evidence_for 0.90]-> Vulnerability Assessment
OWASP ZAP                 -[evidence_for 0.90]-> Vulnerability Assessment
Vulnerability Assessment -[related_to   0.80]-> Vulnerability Research
Burp Suite               -[evidence_for 0.90]-> Web Security
SQLi                     -[evidence_for 0.95]-> Web Security
XSS                      -[evidence_for 0.95]-> Web Security
OWASP ZAP                 -[evidence_for 0.90]-> Web Security
Kali Linux               -[evidence_for 0.75]-> Cybersecurity Fundamentals
Metasploit               -[evidence_for 0.80]-> Cybersecurity Fundamentals
```

The current provider follows paths up to three nodes long. This permits a
direct relationship or one intermediate concept while keeping explanations
short enough to review manually.

## 6. Decisions Made So Far

### Decision 001: Start With Exact Canonical Matching

Exact overlap is the deterministic fallback. It remains useful even when richer
services are unavailable.

### Decision 002: Keep Requirement Categories Separate

Internship requirements are separated into:

```text
technical skills
domain concepts
soft skills
```

This avoids inflating scores with vague concepts or unverifiable personality
claims.

### Decision 003: Introduce Related Skills Behind An Interface

The related-skill provider began as dictionary-backed. Live matching now uses a
Neo4j provider first and preserves the dictionary-backed provider as a
deterministic fallback, without changing the matching response shape.

Neo4j evidence is identified by `source: "neo4j"`. Fallback evidence remains
identified by `source: "curated_rule"`.

### Decision 004: Normalize Domain Aliases Before Path Lookup

Real parser output exposed terminology variations such as:

```text
Network Security Principles
Network Security
```

They now normalize to one concept before relationship lookup.

### Decision 005: Allow Short Explainable Paths

A direct lookup was insufficient for:

```text
Nessus -> Vulnerability Assessment -> Vulnerability Research
```

The provider now follows short curated paths. Long or opaque chains remain
disallowed.

### Decision 006: Award Conservative Partial Credit

Version 3 introduced a flat `35%` partial-credit baseline for related concrete
technical evidence. Version 4 supersedes that flat factor with typed,
confidence-weighted paths and distance decay as recorded in Decision 011.

### Decision 007: Deduplicate Credit Per Requirement

`Nessus`, `Burp Suite`, and `OWASP ZAP` can all support
`Vulnerability Research`, but that requirement contributes partial credit only
once. All paths remain visible as evidence.

### Decision 008: Warn About Broad Requirements

Terms such as `Troubleshooting` are broad and difficult to score from a resume
skill list. They remain visible and trigger a manual-review warning.

### Decision 009: Measure Engine Revisions Against Reviewed Fixtures

Engine tuning must not rely on one resume or one internship. A fixture-backed
evaluation harness now records reviewed score ranges, evidence paths, and
warning expectations across multiple domains. Synthetic UUIDs are deterministic
so reports are reproducible.

Run the baseline report from `backend/`:

```bash
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -B -m scripts.evaluate_matching_engine
```

Print the complete machine-readable report:

```bash
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -B -m scripts.evaluate_matching_engine --json
```

### Decision 010: Type And Weight Relationship Edges

Bare relationships were not expressive enough. Curated edges now carry a type
and confidence value. The provider understands:

```text
alias_of
evidence_for
related_to
prerequisite_for
```

Only `evidence_for` and `related_to` participate in scoring today.
`prerequisite_for` is reserved for future learning-path explanations, and
aliases continue to normalize before path lookup.

### Decision 011: Decay Indirect Evidence And Score The Strongest Path

Direct reviewed evidence should count more than an indirect chain. Path
confidence multiplies edge confidence values and applies a `0.85` decay for
each additional edge after the first. When several paths support one missing
requirement, the strongest path determines numeric credit while all paths stay
visible for explanation.

### Decision 012: Preserve Resume Evidence Provenance

Top-level skills alone were insufficient. Matching now inventories evidence
from the skills list, projects, experience, and certification names. Each item
keeps its section, parser extraction source, confidence, context, and
provenance weight.

Related credit uses the strongest combination of relationship path and resume
provenance. Exact matches remain deterministic but return their strongest
evidence so explanations can distinguish a listed skill from demonstrated
usage.

Certification evidence is intentionally conservative: the certification name
must itself canonicalize to a recognized skill or participate in a curated
relationship. Education does not yet expose nested skills in the parser schema,
so education-based skill evidence remains future work rather than an
unsupported inference.

### Decision 013: Persist Immutable Versioned Analyses

`POST /matches/preview` remains read-only. A separate
`POST /matches/analyses` route calculates the same deterministic result and
stores an immutable PostgreSQL row containing:

```text
resume_id
internship_input_id
analysis_session_id
score_version
overall_score
complete JSON evidence breakdown
created_at
stale_at
```

Clients may reuse an `analysis_session_id` when comparing several resumes for
one internship. Historical payloads retain their original score version even
after the engine evolves.

### Decision 014: Mark History Stale Instead Of Rewriting It

Saved analyses are marked stale when parsed resume content is manually
corrected, a resume is deleted or retried, or an internship input is deleted,
retried, or reparsed. Historical rows remain available for auditing rather than
being silently recalculated or overwritten.

### Decision 015: Store Item-Level Semantic Evidence Before Scoring It

Aggregate vectors such as one vector for all projects are too vague for an
explainable engine. Version 6 stores one `768`-dimension Gemini embedding per
resume summary, project, experience, or education item and one embedding per
concrete internship requirement. Rows retain source text, a SHA-256 content
hash, and model identity.

`POST /matches/embeddings/refresh` regenerates both sides for an owned ready
resume and internship pair. Existing rows are replaced transactionally and
saved analyses are marked stale.

Match previews use pgvector cosine distance to report the strongest source
section above `0.72` for each requirement. Semantic evidence remains a separate
reporting layer until reviewed examples justify both the threshold and any
numeric contribution policy. Missing migration, configuration, or embeddings
does not break deterministic fallback matching; the response reports that
semantic evidence is unavailable.

### Decision 016: Invalidate First And Refresh Asynchronously

Serving old vectors after a profile edit is worse than temporarily serving no
semantic evidence. Successful resume parsing, internship parsing, and relevant
manual resume edits now:

```text
invalidate existing vectors
mark saved analyses stale
enqueue latest semantic refresh generation
```

A dedicated worker regenerates vectors with bounded exponential retries.
Parsing and profile correction remain available if Gemini, pgvector, or the
refresh queue is unavailable during rollout. Deterministic matching continues
to work while semantic evidence is absent.

Each queued source has a generation UUID. If a newer edit arrives while an
older job is in flight, the worker invalidates the obsolete output and leaves
the newer queued generation intact. This prevents a race from restoring stale
semantic evidence.

### Decision 017: Measure Semantic Thresholds Separately

`scripts.evaluate_semantic_calibration` reports precision, recall, F1, and
confusion counts across candidate thresholds. The first corpus contains eight
cross-domain synthetic baseline observations and is intentionally labeled
`synthetic_baseline`.

`scripts.export_semantic_calibration_candidates` exports all stored section to
requirement similarities for one embedded resume and internship pair. Exported
rows remain `pending_review` with no label until a reviewer decides whether the
evidence should be reported, records a note, and changes the source to
`reviewed_live`. Pending rows are excluded from metrics by construction.

The synthetic corpus is executable scaffolding, not calibration proof. Add
reviewed live similarities before enabling semantic numeric credit or treating
`0.72` as a final threshold.

### Decision 018: Use RAG For Student-Facing Match Explanations

The next student-facing layer should not ask an LLM to freely explain a raw
match payload. It should be RAG-assisted:

```text
saved match facts
+ saved LLM adjudication facts
+ retrieved knowledge-base guidance
-> structured explanation and improvement plan
```

The matching engine remains the source of truth for evidence:

```text
exact matches
related-skill paths
semantic snippets
adjudication judgments
resume section citations
```

The RAG knowledge base provides domain and coaching guidance:

```text
what a skill means
what evidence should count
what weak evidence looks like
how to improve the resume truthfully
what project could close a real gap
how to prepare interview talking points
```

Initial source documents live in:

```text
backend/knowledge/match_explainability/README.md
backend/knowledge/match_explainability/cybersecurity_skills.md
backend/knowledge/match_explainability/resume_improvement_guidance.md
backend/knowledge/match_explainability/match_explanation_rules.md
backend/knowledge/match_explainability/career_path_guidance.md
```

These documents must not be treated as resume evidence. They are explanation
guidance only. For example, a RAG chunk saying "Splunk supports SIEM" does not
prove the student knows Splunk. It only helps the LLM explain a SIEM gap or
interpret already-cited resume evidence.

The future ingestion pipeline should read these Markdown files, split them by
stable headings, embed each chunk, store the chunks in pgvector with path and
heading metadata, and retrieve only relevant chunks for the explanation
request.

Initial indexing support has been added:

```text
docs/migrations/010_match_explainability_knowledge.sql
backend/services/match_explainability_knowledge_service.py
POST /matches/explainability/knowledge/embeddings/refresh
POST /matches/explainability/knowledge/search
POST /matches/explanations
GET /matches/explanations/{explanation_id}
```

The refresh endpoint reads the Markdown files, creates heading-based chunks,
embeds each chunk with the configured embedding provider, and replaces the
global `match_explainability` chunk index transactionally.

The search endpoint embeds a compact query and retrieves only the top relevant
knowledge chunks. This endpoint is a backend validation tool and future
building block for the gap analyzer. It is not a chatbot surface; the real
student-facing explanation endpoint will build its retrieval query from saved
match and adjudication facts.

Saved explanation storage has also been designed:

```text
docs/migrations/011_match_explanations.sql
```

The table links one generated explanation to a saved match analysis and
optionally to a saved LLM adjudication. It stores provider metadata, prompt and
explanation versions, base and AI-reviewed scores, retrieved knowledge chunks,
and the structured explanation payload so the frontend can reuse explanations
without repeatedly spending AI credits.

The first UI-aligned explanation schema has been added:

```text
backend/services/ai/match_explanation_schemas.py
backend/schemas/matching.py
```

The AI output is bucketed for the planned frontend instead of returning a
free-form essay:

```text
score_card
strengths
partial_matches
gaps
resume_improvements
learning_projects
interview_talking_points
fairness_notes
```

This schema is expected to evolve with the UI, so generated rows retain an
`explanation_version`.

The first endpoint implementation has been added:

```text
backend/models/match_explanation.py
backend/services/match_explanation_service.py
POST /matches/explanations
GET /matches/explanations/{explanation_id}
```

`POST /matches/explanations` accepts a saved `analysis_id` and optional
`adjudication_id`. It reuses an active saved explanation when available;
otherwise it builds a compact context, retrieves a small set of relevant RAG
chunks, calls the configured structured-output LLM, stores the result, and
returns the UI-shaped explanation payload.

## 7. Known Algorithm Weaknesses

These are engine limitations, not merely missing data:

1. Relationship types and confidence values are currently hand-curated and need
   a larger reviewed dataset.
2. Alias storage remains separate from relationship-edge storage.
3. All requirements inside the required or preferred section have equal
   importance.
4. Education does not yet expose nested skills in the parser schema.
5. Domain-concept evidence is explanatory only. Its scoring policy is not yet
   calibrated.
6. The `50%` maximum related-credit factor and `0.85` distance decay are
   baseline assumptions, not
   evaluation-backed final value.
7. The semantic `0.72` reporting threshold is an uncalibrated baseline.
8. Semantic evidence does not yet contribute numeric points.
9. The semantic calibration corpus contains synthetic baselines but no reviewed
   live similarities yet.

## 8. Data Coverage Limitations

These should improve by adding or maintaining data without redesigning the
engine:

1. Missing skill aliases.
2. Missing domain aliases.
3. Missing explicit relationships.
4. Missing human-reviewed calibration data for relationship confidence values.
5. Missing semantic examples and embeddings.
6. Missing human-reviewed evaluation cases across career domains.

## 9. Target Engine Architecture

The mature matching engine should combine independent evidence layers:

```text
1. exact canonical overlap
2. typed and weighted curated relationships
3. evidence provenance and confidence
4. section-level pgvector semantic similarity
5. transparent weighted aggregation
6. warnings for sparse, broad, or ambiguous inputs
7. persisted versioned analyses
```

Each scored contribution should eventually be auditable:

```text
requirement:       Vulnerability Research
evidence:          Nessus
evidence source:   resume skills section
relationship path: Nessus -> Vulnerability Assessment -> Vulnerability Research
relationship type: evidence_for
path distance:     2
path confidence:   curated value
credit awarded:    partial
score version:     versioned algorithm
```

## 10. Ordered Implementation Plan

### Phase A: Make The Rule Engine Measurable

- [x] Add a fixture-backed evaluation harness with exact matches, reasonable
  partial matches, and obvious non-matches across several domains.
- [x] Record expected score ranges and expected evidence paths.
- [x] Add the first manual-testing regression case for cybersecurity matching.
- [ ] Continue adding regression cases whenever manual testing exposes a
  weakness.

### Phase B: Make Relationships More Accurate

- [x] Introduce a typed relationship model supporting:
  `alias_of`, `evidence_for`, `related_to`, and `prerequisite_for`.
- [x] Add relationship confidence values.
- [x] Add path-distance decay so indirect evidence contributes less than direct
  evidence.
- [x] Keep a maximum explainable path length.
- [ ] Expand typed relationship data across reviewed domains.
- [ ] Decide whether aliases should move into the same relationship store.

### Phase C: Use Resume Evidence Better

- [x] Preserve whether evidence came from the skills list, a project,
  experience, certification, or cautious parser inference.
- [x] Weight demonstrated project or experience evidence more strongly than a
  bare skill-list mention.
- [x] Keep provenance visible in explanations.
- [ ] Design explicit education-skill extraction before using education as
  scored evidence.

### Phase D: Persist And Audit Results

- [x] Add PostgreSQL match-analysis history.
- [x] Store `score_version`, input IDs, section scores, evidence breakdown,
  creation time, and optional stale time.
- [x] Mark analyses stale when resume or internship profiles change.

### Phase E: Add Semantic Evidence

- [x] Generate section-level embeddings with `pgvector`.
- [x] Compare projects, experience, education, and summary text with internship
  requirements.
- [x] Keep semantic evidence separate from exact and graph evidence.
- [ ] Calibrate semantic thresholds using the evaluation harness.
- [ ] Define a conservative semantic contribution policy after calibration.
- [x] Refresh embeddings automatically after parsing and relevant edits.
- [x] Retry embedding refresh independently and reject obsolete in-flight work.
- [x] Add listed-skill, certification, bullet-level resume embeddings and
  context-enriched requirement embeddings.

### Phase E2: Audit Missed Evidence With An LLM

- [x] Retrieve top-k semantic passages for still-missing concrete requirements.
- [x] Add strict structured LLM adjudication with resume-passage citations.
- [x] Persist model, prompt version, evidence excerpts, confidence, and fairness audit.
- [x] Keep bounded adjudicated credit shadow-only.
- [ ] Review saved adjudications against human labels before changing the official score.

### Phase F: Move Relationship Storage To Neo4j

- [x] Mirror canonical aliases and curated relationships into Neo4j.
- [x] Query short Neo4j support paths during live match previews.
- [x] Keep the local deterministic fallback available.
- [x] Move graph authoring from Python constants to validated domain JSON files.
- [x] Batch graph evidence retrieval into one Neo4j request per match.
- [x] Add match-specific prerequisite learning-path responses.
- [x] Add role nodes and profile-level graph career recommendations.
- [ ] Add a reviewed graph administration workflow.
- [ ] Connect graph learning gaps to reviewed resources.

### Phase G: Student-Facing Matching Features

- [ ] Compare several resume versions for one internship.
- [x] Create the first RAG knowledge-base source documents for grounded explanations.
- [x] Add migration and refresh endpoint for match-explainability knowledge embeddings.
- [x] Add retrieval endpoint for match-explainability knowledge chunks.
- [x] Add migration for saved RAG-assisted match explanations.
- [x] Add the first UI-aligned structured explanation schema.
- [x] Use saved match and adjudication facts to build compact explanation context.
- [x] Generate grounded explanations from stored evidence and retrieved guidance.
- [ ] Review generated explanation quality against live examples.
- [ ] Produce grouped skill gaps and truthful resume-improvement suggestions.

Interview preparation, career suggestions, application tracking, and RAG
guidance follow after this core matching workflow is dependable.

## 11. Evaluation Rules

Each engine revision should be tested against:

```text
exact match
alias match
partial related match
multiple paths supporting one requirement
indirect path
unsupported requirement
broad ambiguous requirement
soft-skill-only posting
posting with no concrete technical requirements
resume with no extracted skills
legacy parser-v1 internship document
```

Evaluation cases should eventually cover multiple domains:

```text
software engineering
data and AI
cybersecurity
networking
cloud and DevOps
QA and support
```

Do not tune a global scoring rule based on one resume or one internship.

### Current Fixture Baseline

Baseline recorded for `provenance-weighted-related-skill-credit-v5`:

```text
13 reviewed cases
6 represented domains
13 passing cases
0 failing cases
```

Current represented domains:

```text
software engineering
data and AI
cybersecurity
networking
cloud and DevOps
QA and support
```

This baseline verifies current behavior; it does not prove that the weights are
fully calibrated. Expand the corpus as real examples are reviewed.

## 12. Update Protocol

Whenever the matching engine changes:

1. Update this file with the decision, reasoning, and tradeoff.
2. Add or update regression tests.
3. Increment `score_version` when scoring behavior changes.
4. Update `README.md` if the product capability or roadmap changed.
5. Update `docs/workflows.md` if the request path changed.
6. Append a milestone to `docs/dev-log.md`.
7. Run the backend verification checklist from `instructions.md`.

## 13. Stabilization Notes

### 2026-06-03 Deadline Pass

Immediate fixes after the first live cybersecurity match:

1. Added high-confidence aliases for common wording variants:
   `Metasploit Framework -> Metasploit`,
   `Burp Suite Professional -> Burp Suite`,
   `Kali Linux tools -> Kali Linux`,
   `Python scripting -> Python`,
   `HTML -> HTML5`,
   `HTTP/S -> HTTP/HTTPS`,
   `Security+ -> CompTIA Security+`.
2. Kept this as canonicalization-data improvement, not a new score formula.
   Therefore `score_version` remains `separate-semantic-evidence-reporting-v6`.
3. Changed the v7 adjudication prompt to a compact audit context. It now sends
   the official score summary, missing concrete requirements, compact skill
   lists, and retrieved passages instead of the full parsed resume, internship,
   and match payload. This reduces provider token pressure while preserving
   citation validation.
