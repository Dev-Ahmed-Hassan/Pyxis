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


def get_internship_parser_routes() -> list[ModelRoute]:
    primary = os.getenv("LLM_INTERNSHIP_PARSER_PRIMARY", "")
    fallbacks = os.getenv("LLM_INTERNSHIP_PARSER_FALLBACKS", "")
    if not primary:
        return get_resume_parser_routes()
    return [_parse_route(value) for value in [primary, *_split_csv(fallbacks)] if value]


def get_match_adjudicator_routes() -> list[ModelRoute]:
    primary = os.getenv("LLM_MATCH_ADJUDICATOR_PRIMARY", "")
    fallbacks = os.getenv("LLM_MATCH_ADJUDICATOR_FALLBACKS", "")
    if not primary:
        return get_internship_parser_routes()
    return [_parse_route(value) for value in [primary, *_split_csv(fallbacks)] if value]


def get_match_explainer_routes() -> list[ModelRoute]:
    primary = os.getenv("LLM_MATCH_EXPLAINER_PRIMARY", "")
    fallbacks = os.getenv("LLM_MATCH_EXPLAINER_FALLBACKS", "")
    if not primary:
        return get_match_adjudicator_routes()
    return [_parse_route(value) for value in [primary, *_split_csv(fallbacks)] if value]


def get_career_recommender_routes() -> list[ModelRoute]:
    primary = os.getenv("LLM_CAREER_RECOMMENDER_PRIMARY", "")
    fallbacks = os.getenv("LLM_CAREER_RECOMMENDER_FALLBACKS", "")
    if not primary:
        return get_match_explainer_routes()
    return [_parse_route(value) for value in [primary, *_split_csv(fallbacks)] if value]


def get_github_analyzer_routes() -> list[ModelRoute]:
    primary = os.getenv("LLM_GITHUB_ANALYZER_PRIMARY", "")
    fallbacks = os.getenv("LLM_GITHUB_ANALYZER_FALLBACKS", "")
    if not primary:
        return get_career_recommender_routes()
    return [_parse_route(value) for value in [primary, *_split_csv(fallbacks)] if value]


def get_embedding_route() -> ModelRoute | None:
    value = os.getenv("EMBEDDING_MODEL_ROUTE", "")
    return _parse_route(value) if value else None


def get_embedding_dimensions() -> int:
    value = os.getenv("EMBEDDING_DIMENSIONS", "768")
    try:
        dimensions = int(value)
    except ValueError as error:
        raise AIConfigurationError("EMBEDDING_DIMENSIONS must be an integer") from error
    if dimensions != 768:
        raise AIConfigurationError(
            "EMBEDDING_DIMENSIONS must be 768 for the current pgvector schema"
        )
    return dimensions


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
