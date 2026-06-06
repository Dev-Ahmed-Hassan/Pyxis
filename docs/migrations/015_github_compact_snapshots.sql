-- Phase 15: compact GitHub snapshots for UI and future LLM analysis.
-- Raw GitHub API payloads remain stored for audit/debugging, while this
-- compact JSON removes noisy fields and decodes README excerpts.

ALTER TABLE public.github_profile_snapshots
    ADD COLUMN compact_snapshot JSONB NOT NULL DEFAULT '{}'::jsonb;
