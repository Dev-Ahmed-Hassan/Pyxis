import type {
  GitHubCompactSnapshotResponse,
  GitHubProfileAnalysis,
  GitHubProfileSnapshot,
} from '../types/github'
import { apiRequest } from './api'

let cachedCompactSnapshot: GitHubCompactSnapshotResponse | null = null
let cachedAnalysis: GitHubProfileAnalysis | null = null

export function getCachedGitHubCompactSnapshot() {
  return cachedCompactSnapshot
}

export function getCachedGitHubAnalysis() {
  return cachedAnalysis
}

export async function createGitHubSnapshot(input: {
  github_username: string
  repository_limit: number
}) {
  const snapshot = await apiRequest<GitHubProfileSnapshot>('/github/snapshots', {
    method: 'POST',
    body: JSON.stringify(input),
  })
  cachedCompactSnapshot = {
    id: snapshot.id,
    github_username: snapshot.github_username,
    compact_snapshot: snapshot.compact_snapshot,
    repository_limit: snapshot.repository_limit,
    fetched_at: snapshot.fetched_at,
    created_at: snapshot.created_at,
  }
  cachedAnalysis = null
  return snapshot
}

export async function getLatestGitHubCompactSnapshot() {
  const snapshot = await apiRequest<GitHubCompactSnapshotResponse>(
    '/github/snapshots/latest/compact',
  )
  cachedCompactSnapshot = snapshot
  return snapshot
}

export async function createGitHubAnalysis(input: {
  snapshot_id?: string | null
  target_field?: string | null
  preferred_roles?: string[]
  force_refresh?: boolean
}) {
  const analysis = await apiRequest<GitHubProfileAnalysis>('/github/analyses', {
    method: 'POST',
    body: JSON.stringify({
      snapshot_id: input.snapshot_id ?? null,
      target_field: input.target_field?.trim() || null,
      preferred_roles: input.preferred_roles ?? [],
      force_refresh: input.force_refresh ?? false,
    }),
  })
  cachedAnalysis = analysis
  return analysis
}

export async function getLatestGitHubAnalysis() {
  const analysis = await apiRequest<GitHubProfileAnalysis>(
    '/github/analyses/latest',
  )
  cachedAnalysis = analysis
  return analysis
}
