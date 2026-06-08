# Interview Module Workings

This guide explains the architecture and API flow for the Pyxis Interview Module, which provides candidate interview preparation and live adaptive mock interviews based on a saved internship match.

## 1. Architecture & Context Builder

The interview module runs on top of a saved `MatchAnalysis` and optionally incorporates a `MatchExplanation` and `GitHubEvidence`. 

To prevent sending the user's entire raw resume and the internship description to the LLM on every single interview turn (which would be slow, expensive, and exceed context limits), the backend uses a **Context Builder Service**. 

When an interview session or preparation packet is created, the Context Builder compresses the relevant match data into a tiny, auditable JSON dictionary called `compact_context`. This context serves as the "ground truth" memory for the AI.

## 2. Preparation Mode (Static Setup)

**Endpoint:** `POST /interviews/preparations`

| Field | Purpose |
|---|---|
| `match_analysis_id` | Required. The UUID of the saved match. |
| `difficulty` | Target difficulty (e.g., "intermediate"). |
| `question_count` | Number of questions to generate (default 12). |

This endpoint generates an instant, comprehensive interview study guide. The AI generates targeted questions across categories like `technical`, `behavioral`, and `resume_project`. For each question, it provides:
- Why the question is relevant.
- How to structure a good answer.
- Grounded evidence from the candidate's resume to mention.
- Common mistakes to avoid.

The resulting packet is cached in the PostgreSQL `interview_preparations` table. Use `GET /interviews/preparations/{id}` to fetch it again without incurring AI costs.

## 3. Live Mode (Interactive)

Live Mode conducts an adaptive, turn-by-turn mock interview. It maintains state across multiple API calls using the `interview_sessions`, `interview_questions`, and `interview_answers` tables.

### Step A: Session Creation

**Endpoint:** `POST /interviews/sessions`

When a session starts, the AI secretly writes an **Interview Plan** (a hidden script of primary questions). It stores this script in the database and returns a `session_id` with `status: "created"`. The user does *not* see the planned questions yet.

### Step B: Fetching the Next Question

**Endpoint:** `POST /interviews/sessions/{session_id}/questions/next`

The frontend calls this to act as the "interviewer speaking." 
- The backend pops the next question from the hidden script.
- It saves it to the `interview_questions` table.
- It returns the question text to the frontend.

### Step C: Submitting an Answer

**Endpoint:** `POST /interviews/sessions/{session_id}/answers`

When the candidate submits their answer, the backend does two background AI tasks:
1. **Private Assessment:** Grades the answer for relevance, correctness, and clarity. It determines if a follow-up question is needed (`follow_up_needed: true|false`).
2. **Rolling Summary:** Compresses the conversation so far into a short summary. This keeps the AI prompt size bounded as the interview progresses.

The frontend receives a neutral acknowledgement. If `next_is_follow_up` is true, the next call to `/questions/next` will return a newly generated clarifying question instead of the next primary question from the script.

### Step D: Final Evaluation

**Endpoint:** `POST /interviews/sessions/{session_id}/complete`

Once the candidate has answered all questions (or chooses to end early), this endpoint gathers the complete transcript and all the private turn-by-turn assessments. It feeds everything to a Final Evaluator AI.

It generates an `InterviewEvaluation` report card containing:
- An overall score (0-100).
- Category-level score breakdowns.
- Detailed reviews of every specific answer.
- Knowledge gaps and recommended next actions.

Retrieve a saved evaluation via `GET /interviews/sessions/{session_id}/evaluation`.

## 4. Frontend Integration Workflow

```text
dashboard
-> create preparation packet (study guide)
-> start live session
-> loop:
     -> fetch next question
     -> submit candidate answer
     -> check if session_complete == true
-> complete session
-> display final evaluation scorecard
```
