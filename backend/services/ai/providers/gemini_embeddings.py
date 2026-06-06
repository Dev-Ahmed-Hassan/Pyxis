from dataclasses import dataclass

import httpx

from services.ai.config import ModelRoute
from services.ai.providers.base import (
    AIPermanentProviderError,
    AIProviderAuthenticationError,
    AITemporaryProviderError,
    safe_response_error,
)

GEMINI_API_ROOT = "https://generativelanguage.googleapis.com/v1beta/models"


@dataclass(frozen=True)
class TextEmbedding:
    values: list[float]
    model_name: str


class GeminiEmbeddingProvider:
    def __init__(
        self,
        route: ModelRoute,
        api_keys: list[str],
        dimensions: int,
    ) -> None:
        self.route = route
        self.api_keys = api_keys
        self.dimensions = dimensions

    def embed(self, text: str) -> TextEmbedding:
        url = f"{GEMINI_API_ROOT}/{self.route.model}:embedContent"
        payload = {
            "content": {"parts": [{"text": text}]},
            "task_type": "SEMANTIC_SIMILARITY",
            "output_dimensionality": self.dimensions,
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
                raise AITemporaryProviderError(
                    "Gemini embeddings are temporarily unreachable"
                ) from error

            if response.status_code in {401, 403}:
                if index < len(self.api_keys) - 1:
                    continue
                raise AIProviderAuthenticationError(
                    "Gemini embedding API key authentication failed"
                )
            _raise_for_status(response)
            try:
                values = [float(value) for value in response.json()["embedding"]["values"]]
            except (KeyError, TypeError, ValueError) as error:
                raise AIPermanentProviderError(
                    "Gemini returned an invalid embedding response"
                ) from error
            if len(values) != self.dimensions:
                raise AIPermanentProviderError(
                    "Gemini returned an embedding with an unexpected dimension"
                )
            return TextEmbedding(values=values, model_name=self.route.model)

        raise AIProviderAuthenticationError(
            "Gemini embedding API key authentication failed"
        )


def _raise_for_status(response: httpx.Response) -> None:
    detail = safe_response_error(response)
    if response.status_code == 429 or response.status_code >= 500:
        raise AITemporaryProviderError(
            f"Gemini embeddings are temporarily unavailable ({detail})"
        )
    if response.status_code >= 400:
        raise AIPermanentProviderError(
            f"Gemini rejected the embedding request ({detail})"
        )
