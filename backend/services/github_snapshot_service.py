import base64
import os
import re
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime

import httpx
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from models.github_profile_snapshot import GitHubProfileSnapshot
from models.user import User
from schemas.github import (
    GitHubCompactSnapshotResponse,
    GitHubProfileSnapshotResponse,
    GitHubSnapshotCreate,
)

GITHUB_API_ROOT = "https://api.github.com"
GITHUB_USERNAME_PATTERN = re.compile(r"^[A-Za-z0-9](?:[A-Za-z0-9-]{0,38}[A-Za-z0-9])?$")
REQUEST_TIMEOUT_SECONDS = 15
README_EXCERPT_LIMIT = 1600


@dataclass(frozen=True)
class GitHubRawSnapshot:
    username: str
    profile_payload: dict
    repositories_payload: list[dict]
    languages_payload: dict[str, dict]
    readmes_payload: dict[str, dict | None]
    repository_limit: int
    fetched_at: datetime


def create_github_profile_snapshot(
    database: Session,
    user: User,
    snapshot_create: GitHubSnapshotCreate,
) -> GitHubProfileSnapshotResponse:
    username = _normalize_username(snapshot_create.github_username)
    raw = fetch_github_profile_snapshot(username, snapshot_create.repository_limit)
    stored = GitHubProfileSnapshot(
        user_id=user.id,
        github_username=raw.username,
        profile_payload=raw.profile_payload,
        repositories_payload=raw.repositories_payload,
        languages_payload=raw.languages_payload,
        readmes_payload=raw.readmes_payload,
        compact_snapshot=build_compact_github_snapshot(
            raw.profile_payload,
            raw.repositories_payload,
            raw.languages_payload,
            raw.readmes_payload,
        ),
        repository_limit=raw.repository_limit,
        fetched_at=raw.fetched_at,
    )
    database.add(stored)
    database.commit()
    database.refresh(stored)
    return _to_response(stored)


def get_latest_github_profile_snapshot(
    database: Session,
    user: User,
) -> GitHubProfileSnapshotResponse:
    snapshot = database.scalar(
        select(GitHubProfileSnapshot)
        .where(GitHubProfileSnapshot.user_id == user.id)
        .order_by(GitHubProfileSnapshot.created_at.desc())
        .limit(1)
    )
    if not snapshot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="GitHub profile snapshot not found",
        )
    return _to_response(snapshot)


def get_latest_github_compact_snapshot(
    database: Session,
    user: User,
) -> GitHubCompactSnapshotResponse:
    snapshot = database.scalar(
        select(GitHubProfileSnapshot)
        .where(GitHubProfileSnapshot.user_id == user.id)
        .order_by(GitHubProfileSnapshot.created_at.desc())
        .limit(1)
    )
    if not snapshot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="GitHub profile snapshot not found",
        )
    return _to_compact_response(snapshot)


def get_github_profile_snapshot(
    database: Session,
    user: User,
    snapshot_id: uuid.UUID,
) -> GitHubProfileSnapshotResponse:
    snapshot = database.scalar(
        select(GitHubProfileSnapshot).where(
            GitHubProfileSnapshot.id == snapshot_id,
            GitHubProfileSnapshot.user_id == user.id,
        )
    )
    if not snapshot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="GitHub profile snapshot not found",
        )
    return _to_response(snapshot)


def get_github_compact_snapshot(
    database: Session,
    user: User,
    snapshot_id: uuid.UUID,
) -> GitHubCompactSnapshotResponse:
    snapshot = database.scalar(
        select(GitHubProfileSnapshot).where(
            GitHubProfileSnapshot.id == snapshot_id,
            GitHubProfileSnapshot.user_id == user.id,
        )
    )
    if not snapshot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="GitHub profile snapshot not found",
        )
    return _to_compact_response(snapshot)


def build_compact_github_snapshot(
    profile_payload: dict,
    repositories_payload: list[dict],
    languages_payload: dict[str, dict],
    readmes_payload: dict[str, dict | None],
) -> dict:
    language_totals: dict[str, int] = {}
    repositories = []
    for repository in repositories_payload:
        name = repository.get("name")
        if not name:
            continue
        repo_languages = languages_payload.get(name) or {}
        if "error" in repo_languages:
            repo_languages = {}
        for language, byte_count in repo_languages.items():
            if isinstance(byte_count, int):
                language_totals[language] = language_totals.get(language, 0) + byte_count

        readme = readmes_payload.get(name)
        readme_excerpt = _decode_readme_excerpt(readme)
        repositories.append(
            {
                "name": name,
                "full_name": repository.get("full_name"),
                "html_url": repository.get("html_url"),
                "description": repository.get("description"),
                "topics": repository.get("topics") or [],
                "primary_language": repository.get("language"),
                "languages": repo_languages,
                "stars": repository.get("stargazers_count", 0),
                "forks": repository.get("forks_count", 0),
                "watchers": repository.get("watchers_count", 0),
                "open_issues": repository.get("open_issues_count", 0),
                "size": repository.get("size", 0),
                "default_branch": repository.get("default_branch"),
                "created_at": repository.get("created_at"),
                "updated_at": repository.get("updated_at"),
                "pushed_at": repository.get("pushed_at"),
                "is_fork": bool(repository.get("fork")),
                "is_archived": bool(repository.get("archived")),
                "has_readme": bool(readme and not readme.get("error")),
                "readme_size": readme.get("size") if isinstance(readme, dict) else None,
                "readme_html_url": readme.get("html_url") if isinstance(readme, dict) else None,
                "readme_excerpt": readme_excerpt,
            }
        )

    sorted_language_totals = dict(
        sorted(language_totals.items(), key=lambda item: item[1], reverse=True)
    )
    return {
        "profile": {
            "login": profile_payload.get("login"),
            "name": profile_payload.get("name"),
            "bio": profile_payload.get("bio"),
            "company": profile_payload.get("company"),
            "blog": profile_payload.get("blog"),
            "location": profile_payload.get("location"),
            "email": profile_payload.get("email"),
            "html_url": profile_payload.get("html_url"),
            "avatar_url": profile_payload.get("avatar_url"),
            "public_repos": profile_payload.get("public_repos"),
            "followers": profile_payload.get("followers"),
            "following": profile_payload.get("following"),
            "created_at": profile_payload.get("created_at"),
            "updated_at": profile_payload.get("updated_at"),
        },
        "summary": {
            "repository_count": len(repositories_payload),
            "analyzed_repository_count": len(repositories),
            "repositories_with_readme_count": sum(
                1 for repository in repositories if repository["has_readme"]
            ),
            "repositories_with_description_count": sum(
                1 for repository in repositories if repository["description"]
            ),
            "total_stars": sum(int(repository["stars"] or 0) for repository in repositories),
            "total_forks": sum(int(repository["forks"] or 0) for repository in repositories),
            "top_languages": list(sorted_language_totals.keys())[:8],
        },
        "language_totals": sorted_language_totals,
        "repositories": repositories,
    }


def fetch_github_profile_snapshot(
    username: str,
    repository_limit: int,
) -> GitHubRawSnapshot:
    headers = {
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "Pyxis-GitHub-Snapshot",
    }
    token = os.getenv("GITHUB_API_TOKEN", "").strip()
    if token:
        headers["Authorization"] = f"Bearer {token}"

    try:
        with httpx.Client(
            base_url=GITHUB_API_ROOT,
            headers=headers,
            timeout=REQUEST_TIMEOUT_SECONDS,
        ) as client:
            profile = _get_json(client, f"/users/{username}")
            repos = _get_json(
                client,
                f"/users/{username}/repos",
                params={
                    "type": "owner",
                    "sort": "updated",
                    "direction": "desc",
                    "per_page": 100,
                },
            )
            selected_repos = _select_repositories(repos, repository_limit)
            languages = {}
            readmes = {}
            for repo in selected_repos:
                repo_name = repo.get("name")
                if not repo_name:
                    continue
                key = str(repo_name)
                languages[key] = _get_optional_json(
                    client,
                    f"/repos/{username}/{key}/languages",
                )
                readmes[key] = _get_optional_json(
                    client,
                    f"/repos/{username}/{key}/readme",
                )
    except httpx.RequestError as error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"GitHub API is temporarily unreachable: {type(error).__name__}",
        ) from error

    return GitHubRawSnapshot(
        username=username,
        profile_payload=profile,
        repositories_payload=selected_repos,
        languages_payload=languages,
        readmes_payload=readmes,
        repository_limit=repository_limit,
        fetched_at=datetime.now(UTC),
    )


def _normalize_username(value: str) -> str:
    username = value.strip()
    if username.startswith("https://github.com/"):
        username = username.removeprefix("https://github.com/").strip("/")
    username = username.split("/")[0].strip()
    if not GITHUB_USERNAME_PATTERN.fullmatch(username):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Invalid GitHub username",
        )
    return username


def _get_json(client: httpx.Client, path: str, params: dict | None = None):
    response = client.get(path, params=params)
    if response.status_code == 404:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="GitHub profile not found",
        )
    if response.status_code == 403:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="GitHub API rate limit or access restriction reached",
        )
    if response.status_code >= 400:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"GitHub API request failed with HTTP {response.status_code}",
        )
    return response.json()


def _get_optional_json(client: httpx.Client, path: str) -> dict | None:
    response = client.get(path)
    if response.status_code == 404:
        return None
    if response.status_code == 403:
        return {"error": "rate_limited_or_forbidden"}
    if response.status_code >= 400:
        return {"error": f"http_{response.status_code}"}
    return response.json()


def _select_repositories(repositories: list[dict], limit: int) -> list[dict]:
    owned = [repo for repo in repositories if not repo.get("fork")]
    candidates = owned or repositories
    return candidates[:limit]


def _to_response(snapshot: GitHubProfileSnapshot) -> GitHubProfileSnapshotResponse:
    compact_snapshot = _stored_or_built_compact_snapshot(snapshot)
    return GitHubProfileSnapshotResponse(
        id=snapshot.id,
        github_username=snapshot.github_username,
        profile_payload=snapshot.profile_payload,
        repositories_payload=snapshot.repositories_payload,
        languages_payload=snapshot.languages_payload,
        readmes_payload=snapshot.readmes_payload,
        compact_snapshot=compact_snapshot,
        repository_limit=snapshot.repository_limit,
        fetched_at=snapshot.fetched_at,
        created_at=snapshot.created_at,
    )


def _to_compact_response(snapshot: GitHubProfileSnapshot) -> GitHubCompactSnapshotResponse:
    return GitHubCompactSnapshotResponse(
        id=snapshot.id,
        github_username=snapshot.github_username,
        compact_snapshot=_stored_or_built_compact_snapshot(snapshot),
        repository_limit=snapshot.repository_limit,
        fetched_at=snapshot.fetched_at,
        created_at=snapshot.created_at,
    )


def _stored_or_built_compact_snapshot(snapshot: GitHubProfileSnapshot) -> dict:
    if snapshot.compact_snapshot:
        return snapshot.compact_snapshot
    return build_compact_github_snapshot(
        snapshot.profile_payload,
        snapshot.repositories_payload,
        snapshot.languages_payload,
        snapshot.readmes_payload,
    )


def _decode_readme_excerpt(readme: dict | None) -> str | None:
    if not readme or readme.get("error"):
        return None
    content = readme.get("content")
    if not content:
        return ""
    if readme.get("encoding") != "base64":
        return None
    try:
        decoded = base64.b64decode(content, validate=False).decode(
            "utf-8",
            errors="replace",
        )
    except (ValueError, TypeError):
        return None
    decoded = re.sub(r"\s+", " ", decoded).strip()
    return decoded[:README_EXCERPT_LIMIT]
