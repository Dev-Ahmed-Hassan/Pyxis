# Graph Guidance APIs

## Match Learning Paths

```text
GET /matches/analyses/{analysis_id}/learning-paths
```

Use after creating a saved match with:

```text
POST /matches/analyses
```

The endpoint reads the saved match gaps and searches prerequisite paths from
the resume skills to missing internship requirements.

No AI call is made and no new record is stored.

Important response fields:

```text
learning_paths[].target_skill
learning_paths[].priority
learning_paths[].current_foundation
learning_paths[].steps
learning_paths[].path_confidence
learning_paths[].source
```

Learning-path statuses:

```text
prerequisite_path_found = reviewed learning sequence exists
foundation_detected     = existing skill supports the target through related evidence
direct_learning_required = no reviewed connection currently exists
```

Foundation detection uses `EVIDENCE_FOR` and `RELATED_TO`. Ordered learning
sequences use `PREREQUISITE_FOR`.

## Profile Graph Career Recommendations

```text
GET /career/graph-recommendations?limit=8
```

This endpoint reads:

```text
GET /profile/facts
```

It compares the aggregated profile skills with role requirements stored in
Neo4j and returns ranked, deterministic role cards.

No AI call is made and no recommendation record is stored.

Important response fields:

```text
recommendations[].role
recommendations[].fit_score
recommendations[].fit_level
recommendations[].exact_required_coverage
recommendations[].matched_skills
recommendations[].related_skill_support
recommendations[].missing_required_skills
recommendations[].missing_preferred_skills
recommendations[].learning_gaps
```

Exact role requirements receive full credit. `EVIDENCE_FOR` and `RELATED_TO`
paths receive bounded partial credit and are listed separately in
`related_skill_support`. A role cannot receive a `good` or `strong` label from
related evidence alone; the label also requires substantial exact coverage of
required skills.

If profile facts are empty:

```text
POST /profile/facts/refresh
```

Then retry the graph recommendation endpoint.

## Frontend Placement

Match analysis dashboard:

```text
Score
-> Why this score
-> Resume improvements
-> Learning roadmap
-> Interview preparation
```

Profile dashboard:

```text
Profile facts
-> Career matches
-> Role skill gaps
-> Career learning roadmap
```
