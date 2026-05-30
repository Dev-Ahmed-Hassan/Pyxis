import json

import httpx

from services.ai.config import ModelRoute
from services.ai.providers.base import (
    AIPermanentProviderError,
    AIProviderAuthenticationError,
    AITemporaryProviderError,
    StructuredOutput,
    safe_response_error,
)

GEMINI_API_ROOT = "https://generativelanguage.googleapis.com/v1beta/models"


class GeminiProvider:
    def __init__(self, route: ModelRoute, api_keys: list[str]) -> None:
        self.route = route
        self.api_keys = api_keys

    def generate_structured(self, prompt: str, json_schema: dict) -> StructuredOutput:
        url = f"{GEMINI_API_ROOT}/{self.route.model}:generateContent"
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "responseMimeType": "application/json",
                "responseJsonSchema": json_schema,
            },
        }

        for index, api_key in enumerate(self.api_keys):
            try:
                response = httpx.post(
                    url,
                    headers={"x-goog-api-key": api_key},
                    json=payload,
                    timeout=45,
                )
            except httpx.RequestError as error:
                raise AITemporaryProviderError("Gemini is temporarily unreachable") from error

            if response.status_code in {401, 403}:
                if index < len(self.api_keys) - 1:
                    continue
                raise AIProviderAuthenticationError("Gemini API key authentication failed")
            _raise_for_status(response, "Gemini")

            try:
                text = response.json()["candidates"][0]["content"]["parts"][0]["text"]
                return StructuredOutput(data=json.loads(text), route=self.route)
            except (KeyError, IndexError, TypeError, json.JSONDecodeError) as error:
                raise AIPermanentProviderError(
                    "Gemini returned an invalid structured response"
                ) from error

        raise AIProviderAuthenticationError("Gemini API key authentication failed")


def _raise_for_status(response: httpx.Response, provider_name: str) -> None:
    detail = safe_response_error(response)
    if response.status_code == 429 or response.status_code >= 500:
        raise AITemporaryProviderError(f"{provider_name} is temporarily unavailable ({detail})")
    if response.status_code >= 400:
        raise AIPermanentProviderError(f"{provider_name} rejected the AI request ({detail})")
