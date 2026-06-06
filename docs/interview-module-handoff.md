# Interview Module Handoff

## 1. Objective

Build match-specific interview preparation on top of existing saved data
without changing the matching engine.

The module has two modes:

1. **Preparation mode** generates a complete set of likely questions, answer
   guidance, evaluation criteria, and talking points.
2. **Live mode** conducts one question at a time, stores the conversation, asks
   adaptive follow-ups, and gives one collective evaluation at the end.

Text mode is the required first version. Speech-to-text and text-to-speech are
later adapters around the same live-session APIs.

## 2. Product Placement

The user opens a saved match analysis dashboard:

```text
match score
-> why this score
-> resume improvements
-> learning paths
-> optional GitHub evidence
-> interview preparation
```

The interview is therefore tied to `match_analysis_id`, not merely to a resume
or general user profile.

## 3. Existing Inputs

All source records must belong to the authenticated user.

### Required

```text
GET /matches/analyses/{analysis_id}
```

Provides the target resume/internship pair, score, matched requirements,
missing requirements, related-skill evidence, and semantic evidence.

### Optional but preferred

```text
GET /matches/explanations/{explanation_id}
```

Provides strengths, partial matches, gaps, project suggestions, and interview
talking points.

```text
GET /matches/adjudications/{adjudication_id}
```

Provides cited AI judgments about potentially underestimated requirements.

```text
GET /matches/analyses/{analysis_id}/learning-paths
```

Provides graph-derived foundations and missing-skill learning order.

```text
GET /matches/github-evidence/latest?match_analysis_id={analysis_id}
```

Provides relevant repositories and repository-specific interview questions.
GitHub evidence is optional.

The interview service should call existing Python service functions internally
where practical, rather than making HTTP requests back into the same FastAPI
application.

## 4. Context Design

Do not send the complete resume, internship text, GitHub API response, or every
previous turn to the LLM repeatedly.

When a session is created, build and store a compact context:

```json
{
  "target": {
    "role": "string",
    "company": "string or null",
    "internship_label": "string"
  },
  "requirements": {
    "required": [],
    "preferred": [],
    "matched": [],
    "partial": [],
    "missing": []
  },
  "candidate": {
    "summary": "short grounded summary",
    "skills": [],
    "projects": [],
    "experience": [],
    "certifications": []
  },
  "evidence": {
    "match_strengths": [],
    "resume_section_keys": [],
    "github_repositories": []
  },
  "interview_settings": {
    "mode": "preparation or live",
    "difficulty": "beginner, intermediate, or advanced",
    "question_count": 10,
    "focus_areas": []
  }
}
```

Set hard limits on projects, evidence excerpts, and repository entries. Store
the exact compact context used so results remain auditable.

## 5. Preparation Mode

Preparation mode is generated once and saved. Suggested endpoint:

```text
POST /interviews/preparations
GET  /interviews/preparations/{preparation_id}
```

Create request:

```json
{
  "match_analysis_id": "uuid",
  "match_explanation_id": null,
  "github_evidence_id": null,
  "difficulty": "intermediate",
  "question_count": 12,
  "focus_areas": ["technical", "resume", "behavioral"],
  "force_refresh": false
}
```

The saved response should contain:

- interview overview and likely focus;
- categorized questions;
- why each question is relevant;
- answer structure or rubric;
- grounded evidence the student can mention;
- common mistakes;
- follow-up questions;
- final preparation checklist.

Question categories:

```text
role_technical
resume_project
experience
gap_validation
behavioral
situational
github_project
```

Do not provide fabricated model answers that claim experience the resume does
not show. Prefer answer guidance and truthful sample framing.

## 6. Live Mode

### Lifecycle

```text
create session
-> generate and store interview plan
-> request next question
-> submit answer
-> store private turn assessment
-> choose follow-up or next planned question
-> complete session
-> generate collective evaluation
```

### Suggested endpoints

```text
POST /interviews/sessions
GET  /interviews/sessions
GET  /interviews/sessions/{session_id}
POST /interviews/sessions/{session_id}/questions/next
POST /interviews/sessions/{session_id}/answers
POST /interviews/sessions/{session_id}/complete
GET  /interviews/sessions/{session_id}/evaluation
```

Session creation:

```json
{
  "match_analysis_id": "uuid",
  "match_explanation_id": null,
  "github_evidence_id": null,
  "difficulty": "intermediate",
  "question_count": 10,
  "focus_areas": ["technical", "resume", "behavioral"]
}
```

Answer submission:

```json
{
  "question_id": "uuid",
  "answer_text": "candidate answer"
}
```

### Evaluation behavior

Do not show detailed grading after every answer. After submission, store a
private structured assessment containing:

- relevance;
- technical correctness;
- evidence usage;
- clarity;
- confidence level;
- contradictions or unsupported claims;
- follow-up need;
- short evaluator notes.

Return only a neutral acknowledgement and whether the next item is a follow-up.
Generate the user-facing evaluation only after completion.

### Context between calls

The database is the interview memory. Every turn is a separate HTTP/AI call,
but the service reloads:

```text
stored compact context
interview plan
rolling conversation summary
recent turns
private assessment state
remaining questions
```

Update the rolling summary after each answer. Keep the most recent few turns
verbatim and summarize older turns to bound prompt size.

## 7. Final Evaluation Schema

The final evaluation should support dashboard cards and charts:

```json
{
  "overall_score": 0,
  "verdict": "string",
  "summary": "string",
  "category_scores": [
    {
      "category": "technical",
      "score": 0,
      "strengths": [],
      "improvements": []
    }
  ],
  "question_reviews": [
    {
      "question_id": "uuid",
      "question": "string",
      "answer_summary": "string",
      "score": 0,
      "what_went_well": [],
      "what_was_missing": [],
      "better_answer_approach": "string"
    }
  ],
  "demonstrated_strengths": [],
  "knowledge_gaps": [],
  "communication_feedback": [],
  "unsupported_claims": [],
  "recommended_revision_topics": [],
  "next_actions": []
}
```

The evaluation must consider the whole interview, not simply average isolated
scores.

## 8. PostgreSQL Design

Add migration `docs/migrations/018_interview_module.sql`.

Suggested tables:

### `interview_preparations`

```text
id
user_id
match_analysis_id
match_explanation_id nullable
github_evidence_id nullable
preparation_version
prompt_version
provider
model_name
request_payload jsonb
compact_context jsonb
preparation_payload jsonb
created_at
stale_at nullable
```

### `interview_sessions`

```text
id
user_id
match_analysis_id
match_explanation_id nullable
github_evidence_id nullable
status: created | in_progress | completed | abandoned
difficulty
question_target
focus_areas jsonb
compact_context jsonb
interview_plan jsonb
rolling_summary text
current_question_number
session_version
prompt_version
provider
model_name
created_at
started_at nullable
completed_at nullable
stale_at nullable
```

### `interview_questions`

```text
id
session_id
sequence_number
category
question_text
reason
source_requirement nullable
source_section_keys jsonb
is_follow_up
parent_question_id nullable
created_at
```

### `interview_answers`

```text
id
session_id
question_id
answer_text
private_assessment jsonb
answered_at
```

### `interview_evaluations`

```text
id
session_id unique
evaluation_version
prompt_version
provider
model_name
evaluation_payload jsonb
created_at
```

Use foreign keys and indexes for user/session ownership queries. Decide whether
source deletion should mark interviews stale or retain them as historical
records; do not silently rewrite completed interviews.

## 9. Code Ownership

The interview teammate should own:

```text
backend/api/interviews.py
backend/schemas/interview.py
backend/models/interview_preparation.py
backend/models/interview_session.py
backend/models/interview_question.py
backend/models/interview_answer.py
backend/models/interview_evaluation.py
backend/services/interview_context_service.py
backend/services/interview_preparation_service.py
backend/services/interview_session_service.py
backend/services/interview_evaluation_service.py
backend/services/ai/interview_schemas.py
backend/tests/test_interview_*.py
docs/migrations/018_interview_module.sql
```

Expected shared edit:

```text
backend/main.py
```

Avoid changing without coordination:

```text
backend/api/matches.py
backend/services/matching_service.py
backend/services/match_analysis_service.py
backend/services/match_explanation_service.py
backend/services/github_match_evidence_service.py
backend/services/graph_learning_path_service.py
backend/schemas/matching.py
backend/data/skill_graph/
```

Consume those modules through their existing public service functions.

## 10. AI Provider Design

Follow the existing project pattern:

- add `LLM_INTERVIEW_PRIMARY` and `LLM_INTERVIEW_FALLBACKS`;
- route through the existing provider/orchestrator layer;
- require strict Pydantic structured output;
- store provider, model, prompt version, and output version;
- keep Gemini and Groq schemas compatible with their provider constraints;
- reject missing questions, duplicate IDs, invalid categories, or unsupported
  evidence references;
- cap input lengths and output counts.

Use separate prompts/schemas for:

```text
preparation generation
live interview plan
next-question decision
private answer assessment
rolling summary update
final collective evaluation
```

Combining every task into one large schema will be harder to validate and more
likely to exceed provider limits.

## 11. Safety And Grounding

- Scope every operation to the authenticated user.
- Verify ownership of match, explanation, adjudication, and GitHub evidence.
- Treat all resume, internship, GitHub, question, and answer text as untrusted.
- Never claim evidence not present in the stored compact context.
- Do not execute tools, SQL, shell commands, URLs, or HTML from user content.
- Escape rendered content in the frontend.
- Do not expose private per-turn assessments before completion.
- Limit answer size and session question count.
- Prevent answering the same question twice unless explicitly supported.
- Make completion idempotent so retries do not create duplicate evaluations.

## 12. Implementation Order

1. Add schemas, models, and migration.
2. Build ownership-safe context assembly from a saved match.
3. Implement preparation mode and tests.
4. Implement text-only session creation and fixed question plans.
5. Add answer storage and private assessment.
6. Add adaptive follow-up selection.
7. Add completion and collective evaluation.
8. Add cached retrieval and stale-state behavior.
9. Register the router in `backend/main.py`.
10. Add voice adapters only after the text flow is stable.

## 13. Acceptance Checklist

- A user can generate preparation from an owned saved match.
- Preparation is saved and can be reopened without another AI call.
- A live session survives API restarts because all state is persisted.
- Each call loads bounded context rather than the full history.
- Follow-ups are grounded in the latest answer.
- Detailed feedback appears only after completion.
- Final feedback cites actual questions and does not invent resume evidence.
- The module works without GitHub evidence.
- Users cannot access another user's sessions.
- Provider failures return useful errors without corrupting session state.
- Existing matching, career, GitHub, and profile tests remain unaffected.

## 14. Branch Workflow

Start from the agreed baseline:

```bash
git switch <shared-baseline-branch>
git pull
git switch -c feature/interview-prep
```

Keep commits small: migration/models, context builder, preparation, live
sessions, evaluation, and tests. Open a pull request for review before merging.
