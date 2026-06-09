# Interview Module Integration Fixes

## Why this work was needed

The interview backend merged successfully and its database migration was already
applied, but three workflow gaps remained before frontend integration:

1. The compact AI context exposed skills but left projects, experience, and
   certifications empty.
2. Answer assessment could request a follow-up, but the next-question endpoint
   never generated one.
3. Optional match explanations and GitHub evidence were checked for user
   ownership, but not for association with the selected match.

## Changes made

### Resume-specific profile evidence

`interview_context_service.py` now reads the existing profile facts and filters
every item by the `resume_id` stored on the selected match analysis.

The compact candidate context can now include:

- up to 3 projects;
- up to 3 experience evidence groups;
- up to 5 certifications;
- the existing capped skill list.

This filtering is important when a user has uploaded multiple resumes. Evidence
from one resume cannot silently appear in an interview created for another.

### Evidence alignment checks

An optional match explanation or GitHub evidence record is accepted only when:

- it belongs to the authenticated user;
- it belongs to the selected `match_analysis_id`;
- it is not stale.

Invalid combinations fail before an AI request is made.

### Adaptive follow-up questions

After an answer is saved, its private assessment may set
`follow_up_needed=true`. On the next question request, the backend now asks the
AI for a structured decision:

- `follow_up`: generate one concise question tied to the previous answer; or
- `next_planned`: continue with the existing interview plan.

Only one adaptive follow-up is allowed for each planned question. Follow-ups do
not increase the planned-question counter, which keeps session length bounded.

### Context-aware preparation caching

Preparation mode still reuses saved AI output, but only when both the request
settings and the complete compact context match. Updated profile evidence will
therefore produce a fresh preparation instead of returning stale guidance.

## Verification

Targeted tests cover:

- selected-resume filtering;
- prevention of repeated follow-up chains;
- rejection of incomplete follow-up output;
- creation of a persisted adaptive follow-up;
- existing matching, graph, and adjudication behavior.

No database migration change was required because the existing interview tables
already support parent question IDs, private assessments, compact context, and
saved evaluations.

## Frontend integration

The interview page now exposes both backend modes:

- **Question Bank** calls `POST /interviews/preparations`. The normal action
  allows backend cache reuse; **Generate fresh** sends `force_refresh=true`.
- **Live Interview** creates a session with `POST /interviews/sessions`, asks
  questions through `POST /sessions/{id}/questions/next`, and submits answers
  through `POST /sessions/{id}/answers`.
- Per-answer assessments remain private. The page requests and displays the
  collective report only through `POST /sessions/{id}/complete`.

Frontend request and response contracts live in:

- `frontend/src/types/interview.ts`
- `frontend/src/lib/interviews.ts`

The existing `InterviewsPage` remains responsible for selecting saved match
context and presenting both workflows. Match explanation context is included
when its saved frontend reference is available. GitHub match evidence remains
optional until its evidence ID is exposed by the match UI.
