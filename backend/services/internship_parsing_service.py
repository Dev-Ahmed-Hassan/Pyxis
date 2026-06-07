from datetime import UTC, datetime

from pymongo.database import Database
from pydantic import ValidationError

from models.internship import InternshipInput
from services.ai.config import get_internship_parser_routes
from services.ai.internship_schemas import ParsedInternship
from services.ai.orchestrator import AIOrchestratorError, generate_structured_with_fallback
from services.ai.prompt_security import (
    build_internship_extraction_prompt,
    inspect_untrusted_resume_text,
)
from services.skill_canonicalizer import canonicalize_parsed_internship

INTERNSHIP_PARSER_VERSION = "internship-parser-v2"


class InternshipParsingError(Exception):
    pass


class TemporaryInternshipParsingError(InternshipParsingError):
    pass


def parse_and_store_internship(
    internship: InternshipInput,
    mongodb: Database,
) -> tuple[str, ParsedInternship]:
    security_report = inspect_untrusted_resume_text(internship.original_description)
    prompt = build_internship_extraction_prompt(internship.original_description)

    try:
        output = generate_structured_with_fallback(
            routes=get_internship_parser_routes(),
            prompt=prompt,
            json_schema=ParsedInternship.model_json_schema(),
        )
    except AIOrchestratorError as error:
        if str(error).startswith("All configured AI providers failed temporarily:"):
            raise TemporaryInternshipParsingError(str(error)) from error
        raise InternshipParsingError(str(error)) from error

    try:
        parsed_internship = canonicalize_parsed_internship(
            ParsedInternship.model_validate(output.data)
        )
    except ValidationError as error:
        raise InternshipParsingError("AI internship output failed schema validation") from error

    now = datetime.now(UTC)
    result = mongodb.internship_inputs.update_one(
        {"postgres_internship_id": str(internship.id)},
        {
            "$set": {
                "postgres_user_id": str(internship.user_id),
                "original_description": internship.original_description,
                "application_url": internship.application_url,
                "parsed_internship": parsed_internship.model_dump(mode="json"),
                "parser": {
                    "version": INTERNSHIP_PARSER_VERSION,
                    "provider": output.route.provider,
                    "model": output.route.model,
                    "validated": True,
                },
                "prompt_security": security_report.to_document(),
                "processing": {
                    "status": "ready",
                    "error": None,
                },
                "updated_at": now,
            },
            "$setOnInsert": {
                "created_at": now,
            },
        },
        upsert=True,
    )
    document_id = result.upserted_id
    if document_id is None:
        document = mongodb.internship_inputs.find_one(
            {"postgres_internship_id": str(internship.id)},
            {"_id": 1},
        )
        document_id = document["_id"]
    return str(document_id), parsed_internship
