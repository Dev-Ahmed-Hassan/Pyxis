from services.ai.config import AIConfigurationError, ModelRoute, get_provider_keys
from services.ai.providers.base import (
    AIPermanentProviderError,
    AIProviderAuthenticationError,
    AITemporaryProviderError,
    StructuredOutput,
    StructuredOutputProvider,
)
from services.ai.providers.gemini import GeminiProvider
from services.ai.providers.groq import GroqProvider


class AIOrchestratorError(Exception):
    pass


def generate_structured_with_fallback(
    routes: list[ModelRoute],
    prompt: str,
    json_schema: dict,
) -> StructuredOutput:
    if not routes:
        raise AIOrchestratorError("No AI model routes are configured")

    configuration_failures: list[str] = []
    temporary_failures: list[str] = []
    for route in routes:
        try:
            provider = _build_provider(route)
            return provider.generate_structured(prompt, json_schema)
        except AIConfigurationError as error:
            configuration_failures.append(f"{route.provider}:{route.model}: {error}")
        except AIProviderAuthenticationError as error:
            configuration_failures.append(f"{route.provider}:{route.model}: {error}")
        except AITemporaryProviderError as error:
            temporary_failures.append(f"{route.provider}:{route.model}: {error}")
        except AIPermanentProviderError as error:
            failures = [*configuration_failures, *temporary_failures, f"{route.provider}:{route.model}: {error}"]
            raise AIOrchestratorError("AI providers could not complete request: " + "; ".join(failures)) from error

    if temporary_failures:
        raise AIOrchestratorError(
            "All configured AI providers failed temporarily: " + "; ".join(temporary_failures)
        )
    raise AIOrchestratorError(
        "No usable AI provider configuration: " + "; ".join(configuration_failures)
    )


def _build_provider(route: ModelRoute) -> StructuredOutputProvider:
    api_keys = get_provider_keys(route.provider)
    if route.provider == "gemini":
        return GeminiProvider(route, api_keys)
    if route.provider == "groq":
        return GroqProvider(route, api_keys)
    raise AIConfigurationError(f"Unsupported AI provider '{route.provider}'")
