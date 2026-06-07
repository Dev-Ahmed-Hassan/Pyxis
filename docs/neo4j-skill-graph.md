# Skill Graph Data Authoring Guide

## 1. Purpose

The files in `backend/data/skill_graph/` are the source of truth for:

- canonical skill names;
- aliases and alternate spellings;
- explicit relationships between skills;
- the local related-skill matching fallback;
- the data seeded into Neo4j.

Neo4j stores explicit relationships. It does not replace exact canonical
matching, semantic embeddings, PostgreSQL, or `pgvector`.

## 2. Directory Structure

The loader reads every direct `*.json` file in:

```text
backend/data/skill_graph/
```

Current files:

```text
ai_ml.json
cloud_engineering.json
common_skills.json
cybersecurity.json
software_engineering.json
web_development.json
```

You can add files such as:

```text
data_engineering.json
mobile_development.json
penetration_testing.json
soc_analysis.json
```

Subdirectories are not loaded. Use valid JSON, not JSON with comments.

Organize files by subject for maintainability. File boundaries do not create
separate graphs: all files are validated together and seeded into one graph.

## 3. Complete File Structure

Every file should use this structure:

```json
{
  "schema_version": 1,
  "domain": "penetration_testing",
  "description": "Penetration-testing tools, concepts, and relationships.",
  "skills": [
    {
      "canonical_name": "Burp Suite",
      "aliases": [
        "Burp",
        "Burp Suite Professional"
      ]
    },
    {
      "canonical_name": "Web Application Security",
      "aliases": [
        "Web App Security"
      ]
    }
  ],
  "relationships": [
    {
      "source": "Burp Suite",
      "target": "Web Application Security",
      "type": "evidence_for",
      "confidence": 0.95
    }
  ]
}
```

The top-level properties are:

| Property | Required | Meaning |
| --- | --- | --- |
| `schema_version` | Yes | Must currently be the number `1` |
| `domain` | Yes | Non-empty identifier attached to seeded relationships |
| `description` | Recommended | Human explanation; currently not used at runtime |
| `skills` | Yes | Array of canonical skill definitions |
| `relationships` | Yes | Array of relationships; use `[]` when empty |
| `roles` | Optional | Career-role definitions |
| `role_requirements` | Optional | `Role` to `Skill` requirements |

Role datasets may include:

```json
{
  "roles": [
    {
      "name": "Backend Developer",
      "aliases": ["Backend Engineer"],
      "description": "Builds APIs and database-backed services."
    }
  ],
  "role_requirements": [
    {
      "role": "Backend Developer",
      "skill": "REST API",
      "importance": "required",
      "confidence": 0.95
    }
  ]
}
```

These seed:

```text
(:Role)-[:REQUIRES]->(:Skill)
```

`importance` must be `required` or `preferred`.

## 4. Skill Definitions

A skill definition is:

```json
{
  "canonical_name": "PostgreSQL",
  "aliases": [
    "Postgres",
    "Postgre SQL"
  ]
}
```

### `canonical_name`

`canonical_name` is the official name returned by canonicalization and used on
the Neo4j `Skill` node.

Choose one stable, readable form:

```text
PostgreSQL
Burp Suite
Machine Learning
Amazon Web Services
```

Avoid making separate canonical skills for spelling variations:

```text
Postgres
postgresql
Postgre SQL
```

Those should normally be aliases of `PostgreSQL`.

### `aliases`

Aliases are names that should resolve to the canonical skill:

```json
{
  "canonical_name": "Cross-Site Scripting (XSS)",
  "aliases": [
    "XSS",
    "Cross Site Scripting",
    "Cross-Site Scripting"
  ]
}
```

The canonical name itself does not need to be repeated in `aliases`.

Good aliases include:

- common abbreviations;
- old product names;
- spacing variations;
- parser or job-description terminology;
- widely used informal names.

Do not use an alias merely because two skills are related. For example,
`Nessus` is not an alias of `Vulnerability Assessment`; it is evidence for that
concept.

## 5. Normalization And Uniqueness

Names are normalized before duplicate checks:

- converted to lowercase;
- periods become spaces;
- hyphens become spaces;
- underscores become spaces;
- repeated whitespace is collapsed.

Therefore these collide:

```text
Machine-Learning
machine_learning
machine learning
```

Rules enforced across all files:

1. A canonical skill may be defined in only one file.
2. An alias may point to only one canonical skill.
3. A relationship with the same source, target, and type may appear only once.
4. Every relationship endpoint must reference a declared canonical skill.

Neo4j also has uniqueness constraints on:

```text
Skill.normalized_name
SkillTerm.normalized_name
```

The validator catches data problems first; Neo4j constraints provide final
database protection.

## 6. Cross-File References

A relationship may reference a skill declared in another file.

For example, `cloud_engineering.json` may contain:

```json
{
  "source": "AWS Lambda",
  "target": "Python",
  "type": "related_to",
  "confidence": 0.75
}
```

This is valid if `AWS Lambda` and `Python` are each declared exactly once
somewhere in the complete dataset.

Do not redefine `Python` in every domain file. Give it one owner, usually
`common_skills.json`, and reference it elsewhere.

## 7. Relationship Structure

Every relationship contains:

```json
{
  "source": "Nessus",
  "target": "Vulnerability Assessment",
  "type": "evidence_for",
  "confidence": 0.95
}
```

| Property | Required | Meaning |
| --- | --- | --- |
| `source` | Yes | Starting canonical skill |
| `target` | Yes | Ending canonical skill |
| `type` | Yes | One supported relationship type |
| `confidence` | Yes | Number greater than `0` and at most `1` |

Direction matters:

```text
source -[TYPE]-> target
```

## 8. Relationship Types

### `evidence_for`

Use when possessing or demonstrating the source provides concrete evidence for
the target capability.

```json
{
  "source": "Nessus",
  "target": "Vulnerability Assessment",
  "type": "evidence_for",
  "confidence": 0.95
}
```

Interpretation:

```text
Experience with Nessus is strong evidence for Vulnerability Assessment.
```

Typical uses:

- tool to capability;
- framework to practice;
- concrete technique to broader competency;
- language or platform to a directly demonstrated engineering capability.

This relationship can contribute capped partial credit during matching.

### `related_to`

Use when the concepts are meaningfully connected but one does not directly
prove mastery of the other.

```json
{
  "source": "Vulnerability Assessment",
  "target": "Vulnerability Research",
  "type": "related_to",
  "confidence": 0.8
}
```

This relationship can participate in short matching paths and capped partial
credit.

Although the phrase "related to" sounds symmetric, graph edges are currently
directional. Add the reverse relationship when traversal must work both ways:

```json
{
  "source": "Vulnerability Research",
  "target": "Vulnerability Assessment",
  "type": "related_to",
  "confidence": 0.8
}
```

Do not add reverse edges automatically without considering whether both
directions deserve the same confidence.

### `prerequisite_for`

Use when the source should normally be learned before the target:

```json
{
  "source": "TCP/IP",
  "target": "Network Security",
  "type": "prerequisite_for",
  "confidence": 0.9
}
```

Interpretation:

```text
TCP/IP is a prerequisite for learning Network Security.
```

This relationship is seeded into Neo4j, but the current match score query does
not use it. It is intended for future learning paths, gap prioritization, and
career roadmaps.

Never reverse the meaning:

```text
correct: TCP/IP -> prerequisite_for -> Network Security
wrong:   Network Security -> prerequisite_for -> TCP/IP
```

## 9. Confidence Guidelines

Confidence represents the strength of the declared relationship, not the
student's proficiency.

Suggested scale:

| Value | Guidance |
| --- | --- |
| `0.95` to `1.0` | Direct, nearly universal evidence |
| `0.85` to `0.94` | Strong relationship |
| `0.70` to `0.84` | Useful but contextual relationship |
| `0.50` to `0.69` | Weak relationship; include cautiously |
| Below `0.50` | Usually omit until reviewed |

Examples:

```json
{
  "source": "Nessus",
  "target": "Vulnerability Scanning",
  "type": "evidence_for",
  "confidence": 0.95
}
```

```json
{
  "source": "Python",
  "target": "Machine Learning",
  "type": "related_to",
  "confidence": 0.65
}
```

Do not assign high confidence only because two terms often appear together.
Ask whether the source truthfully supports the target.

## 10. How JSON Becomes Neo4j Data

The seeding flow is:

```text
All direct JSON files
        |
        v
Dataset loader
        |
        v
Cross-file validation
        |
        v
Normalized combined dataset
        |
        v
Neo4j MERGE operations
```

A canonical skill becomes:

```text
(:Skill {
  canonical_name: "Burp Suite",
  normalized_name: "burp suite",
  created_at: ...,
  updated_at: ...
})
```

An alias becomes:

```text
(:SkillTerm {
  display_name: "burp",
  normalized_name: "burp",
  created_at: ...,
  updated_at: ...
})
-[:ALIAS_OF {
  relationship_type: "alias_of",
  confidence: 1.0,
  source: "dataset_json",
  created_at: ...,
  updated_at: ...
}]->
(:Skill {canonical_name: "Burp Suite"})
```

A skill relationship becomes:

```text
(:Skill {canonical_name: "Nessus"})
-[:EVIDENCE_FOR {
  relationship_type: "evidence_for",
  confidence: 0.95,
  domain: "cybersecurity",
  source: "dataset_json",
  created_at: ...,
  updated_at: ...
}]->
(:Skill {canonical_name: "Vulnerability Assessment"})
```

Relationship type mapping:

```text
evidence_for     -> EVIDENCE_FOR
related_to       -> RELATED_TO
prerequisite_for -> PREREQUISITE_FOR
```

A role requirement becomes:

```text
(:Role {name: "Backend Developer"})
-[:REQUIRES {
  importance: "required",
  confidence: 0.95,
  source: "dataset_json"
}]->
(:Skill {canonical_name: "REST API"})
```

## 11. Validation And Seeding

Run commands from `backend/`.

Validate after every data edit:

```bash
.venv/bin/python -m scripts.validate_skill_graph_data
```

Validation changes neither Neo4j nor application data.

After validation succeeds, seed Neo4j:

```bash
.venv/bin/python -m scripts.seed_neo4j_skill_graph
```

The seeder uses `MERGE`, so existing nodes and relationships are reused and
updated rather than duplicated.

Restart FastAPI after changing JSON so its cached local canonicalization and
fallback data reload. Neo4j itself does not require a restart.

Recommended workflow:

```text
1. Edit or add JSON files
2. Validate
3. Fix every validation error
4. Seed Neo4j
5. Restart FastAPI
6. Test matching
```

## 12. Important Seeding Limitation

Seeding is currently an upsert, not a full synchronization.

Adding or changing data works:

```text
JSON addition/change -> seed -> Neo4j created or updated
```

Removing an entry from JSON does not delete its old Neo4j node or relationship:

```text
JSON deletion -> seed -> old Neo4j data may remain
```

Do not manually delete large graph sections until a controlled cleanup command
is implemented. Record obsolete entries for deliberate cleanup.

## 13. How Matching Uses The Graph

Matching first performs canonical exact matching. For still-missing
requirements, one batch Neo4j query searches direct and two-edge paths using:

```text
EVIDENCE_FOR
RELATED_TO
```

Example:

```text
Nessus
  -> EVIDENCE_FOR -> Vulnerability Assessment
  -> RELATED_TO   -> Vulnerability Research
```

The result may appear as:

```json
{
  "source": "neo4j",
  "support_path": [
    "Nessus",
    "Vulnerability Assessment",
    "Vulnerability Research"
  ],
  "path_distance": 2,
  "path_confidence": 0.76
}
```

The confidence of a multi-edge path is multiplied:

```text
0.95 x 0.80 = 0.76
```

Longer paths also receive distance decay. Related evidence remains capped and
cannot replace full exact-match credit.

If Neo4j fails or lacks a path, the application uses the same JSON dataset
through the local fallback. The response indicates the source:

```text
neo4j        = graph evidence
curated_rule = local JSON fallback evidence
```

`PREREQUISITE_FOR` is not part of current score calculation.

## 14. Viewing Data In Aura

Open the Aura instance and select **Query**.

Show a small graph sample:

```cypher
MATCH (a)-[r]->(b)
RETURN a, r, b
LIMIT 100
```

Show aliases of Burp Suite:

```cypher
MATCH (alias:SkillTerm)-[r:ALIAS_OF]->(skill:Skill)
WHERE skill.canonical_name = "Burp Suite"
RETURN alias, r, skill
```

Show paths around Nessus:

```cypher
MATCH path = (:Skill {canonical_name: "Nessus"})-[*1..2]-(related)
RETURN path
LIMIT 50
```

Show relationship counts:

```cypher
MATCH (:Skill)-[relationship]->(:Skill)
RETURN type(relationship) AS type, count(*) AS total
ORDER BY total DESC
```

Show data from one domain:

```cypher
MATCH (source:Skill)-[relationship]->(target:Skill)
WHERE relationship.domain = "cybersecurity"
RETURN source, relationship, target
LIMIT 100
```

## 15. Common Errors

### Duplicate canonical skill

```text
duplicate canonical skill 'Python'; already defined in common_skills.json
```

Remove the second definition. Reference the original canonical skill from
relationships instead.

### Conflicting alias

```text
alias 'ML' maps to one canonical skill, but another file maps it differently
```

Choose one canonical meaning or use a more specific alias.

### Unknown relationship endpoint

```text
relationships[3].target references unknown skill 'Network Defense'
```

Declare `Network Defense` as a canonical skill in exactly one file.

### Duplicate relationship

```text
duplicate relationship 'Nessus' -> 'Vulnerability Assessment' (evidence_for)
```

Keep one relationship and choose one reviewed confidence value.

### Invalid confidence

Confidence must be a JSON number above `0` and at most `1`:

```json
"confidence": 0.9
```

Do not use:

```json
"confidence": "high"
```

## 16. Authoring Checklist

Before adding a skill:

- Search all files for the canonical name and likely aliases.
- Decide whether it is a new skill, an alias, or merely a related concept.
- Give the canonical skill one owning file.
- Put shared skills in `common_skills.json`.

Before adding a relationship:

- Confirm both endpoints are canonical skills.
- Confirm the direction expresses the intended meaning.
- Choose the narrowest truthful relationship type.
- Assign a defensible confidence value.
- Avoid relationships based only on keyword co-occurrence.

Before finishing:

- Validate the complete dataset.
- Seed Neo4j.
- Restart FastAPI.
- Inspect representative paths in Aura.
- Run a match containing the new skill or requirement.
