"""Run synthetic AI provider checks without reading application data."""

import argparse
import json
import sys
from dataclasses import dataclass

import httpx

from services.ai.config import ModelRoute, get_provider_keys, get_resume_parser_routes
from services.ai.prompt_security import build_resume_extraction_prompt
from services.ai.providers.base import safe_response_error
from services.ai.providers.gemini import GEMINI_API_ROOT, GeminiProvider
from services.ai.providers.groq import GROQ_CHAT_COMPLETIONS_URL, GroqProvider
from services.ai.schemas import ParsedResume

SMOKE_PROMPT = "Reply with the numbers 1 through 10 only, separated by commas."
FAKE_RESUME = "Ada Lovelace\nEmail: ada@example.com\nSkills: Python"


@dataclass(frozen=True)
class CheckResult:
    provider: str
    model: str
    key_number: int | None
    check: str
    passed: bool
    detail: str


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Test configured AI providers using synthetic prompts only."
    )
    parser.add_argument(
        "--structured",
        action="store_true",
        help="Also test the strict resume JSON schema with a fake resume.",
    )
    arguments = parser.parse_args()

    routes = get_resume_parser_routes()
    if not routes:
        print("No resume parser model routes are configured.")
        return 1

    results: list[CheckResult] = []
    for route in routes:
        try:
            keys = get_provider_keys(route.provider)
        except Exception as error:
            results.append(
                CheckResult(route.provider, route.model, None, "configuration", False, str(error))
            )
            continue

        for index, api_key in enumerate(keys, start=1):
            results.append(_run_smoke_check(route, api_key, index))

        if arguments.structured:
            results.append(_run_structured_check(route, keys))

    _print_results(results)
    return 0 if all(result.passed for result in results) else 1


def _run_smoke_check(route: ModelRoute, api_key: str, key_number: int) -> CheckResult:
    if route.provider == "gemini":
        return _run_gemini_smoke_check(route, api_key, key_number)
    if route.provider == "groq":
        return _run_groq_smoke_check(route, api_key, key_number)
    return CheckResult(route.provider, route.model, key_number, "smoke", False, "unsupported provider")


def _run_gemini_smoke_check(route: ModelRoute, api_key: str, key_number: int) -> CheckResult:
    try:
        response = httpx.post(
            f"{GEMINI_API_ROOT}/{route.model}:generateContent",
            headers={"x-goog-api-key": api_key},
            json={"contents": [{"parts": [{"text": SMOKE_PROMPT}]}]},
            timeout=30,
        )
    except httpx.RequestError as error:
        return CheckResult("gemini", route.model, key_number, "smoke", False, type(error).__name__)

    if response.status_code >= 400:
        return CheckResult(
            "gemini", route.model, key_number, "smoke", False, safe_response_error(response)
        )
    return CheckResult("gemini", route.model, key_number, "smoke", True, "request accepted")


def _run_groq_smoke_check(route: ModelRoute, api_key: str, key_number: int) -> CheckResult:
    try:
        response = httpx.post(
            GROQ_CHAT_COMPLETIONS_URL,
            headers={"Authorization": f"Bearer {api_key}"},
            json={
                "model": route.model,
                "messages": [{"role": "user", "content": SMOKE_PROMPT}],
            },
            timeout=30,
        )
    except httpx.RequestError as error:
        return CheckResult("groq", route.model, key_number, "smoke", False, type(error).__name__)

    if response.status_code >= 400:
        return CheckResult(
            "groq", route.model, key_number, "smoke", False, safe_response_error(response)
        )
    return CheckResult("groq", route.model, key_number, "smoke", True, "request accepted")


def _run_structured_check(route: ModelRoute, keys: list[str]) -> CheckResult:
    prompt = build_resume_extraction_prompt(FAKE_RESUME)
    schema = ParsedResume.model_json_schema()
    try:
        if route.provider == "gemini":
            output = GeminiProvider(route, keys).generate_structured(prompt, schema)
        elif route.provider == "groq":
            output = GroqProvider(route, keys).generate_structured(prompt, schema)
        else:
            return CheckResult(
                route.provider, route.model, None, "structured", False, "unsupported provider"
            )
        parsed_resume = ParsedResume.model_validate(output.data)
    except Exception as error:
        return CheckResult(route.provider, route.model, None, "structured", False, str(error))

    detail = json.dumps({"full_name": parsed_resume.full_name.value})
    return CheckResult(route.provider, route.model, None, "structured", True, detail)


def _print_results(results: list[CheckResult]) -> None:
    for result in results:
        key_label = f" key#{result.key_number}" if result.key_number is not None else ""
        status = "PASS" if result.passed else "FAIL"
        print(f"[{status}] {result.provider}:{result.model}{key_label} {result.check}: {result.detail}")


if __name__ == "__main__":
    sys.exit(main())
