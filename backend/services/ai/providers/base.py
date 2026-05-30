from dataclasses import dataclass
from typing import Protocol

import httpx

from services.ai.config import ModelRoute


class AIProviderError(Exception):
    pass


class AITemporaryProviderError(AIProviderError):
    pass


class AIProviderAuthenticationError(AIProviderError):
    pass


class AIPermanentProviderError(AIProviderError):
    pass


@dataclass(frozen=True)
class StructuredOutput:
    data: dict
    route: ModelRoute


class StructuredOutputProvider(Protocol):
    def generate_structured(self, prompt: str, json_schema: dict) -> StructuredOutput:
        ...


def safe_response_error(response: httpx.Response) -> str:
    try:
        body = response.json()
    except ValueError:
        return f"HTTP {response.status_code}"

    error = body.get("error", body) if isinstance(body, dict) else {}
    if isinstance(error, dict):
        message = error.get("message")
        code = error.get("code")
        details = ": ".join(str(value) for value in [code, message] if value)
        if details:
            return f"HTTP {response.status_code}: {details[:300]}"
    return f"HTTP {response.status_code}"
