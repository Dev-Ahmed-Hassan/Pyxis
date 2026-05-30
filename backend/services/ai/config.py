import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()


class AIConfigurationError(Exception):
    pass


@dataclass(frozen=True)
class ModelRoute:
    provider: str
    model: str


def get_resume_parser_routes() -> list[ModelRoute]:
    primary = os.getenv("LLM_RESUME_PARSER_PRIMARY", "")
    fallbacks = os.getenv("LLM_RESUME_PARSER_FALLBACKS", "")
    return [_parse_route(value) for value in [primary, *_split_csv(fallbacks)] if value]


def get_provider_keys(provider: str) -> list[str]:
    variable_name = f"{provider.upper()}_API_KEYS"
    keys = _split_csv(os.getenv(variable_name, ""))
    if not keys:
        raise AIConfigurationError(f"{variable_name} is not configured")
    return keys


def _parse_route(value: str) -> ModelRoute:
    provider, separator, model = value.strip().partition(":")
    if not separator or not provider or not model:
        raise AIConfigurationError(
            f"Invalid LLM route '{value}'. Expected provider:model."
        )
    return ModelRoute(provider=provider.lower(), model=model)


def _split_csv(value: str) -> list[str]:
    return [item.strip() for item in value.split(",") if item.strip()]
