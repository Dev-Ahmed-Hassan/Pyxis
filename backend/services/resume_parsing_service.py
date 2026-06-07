from datetime import UTC, datetime

from pymongo.database import Database
from pydantic import ValidationError

from services.ai.config import get_resume_parser_routes
from services.ai.orchestrator import AIOrchestratorError, generate_structured_with_fallback
from services.ai.prompt_security import (
    build_resume_extraction_prompt,
    inspect_untrusted_resume_text,
)
from services.ai.schemas import ParsedResume
from services.skill_canonicalizer import canonicalize_parsed_resume

PARSER_VERSION = "resume-parser-v2"
PARSED_RESUME_FIELDS = (
    "full_name",
    "email",
    "phone",
    "location",
    "summary",
    "skills",
    "experience",
    "projects",
    "education",
    "certifications",
)


class ResumeParsingError(Exception):
    pass


class TemporaryResumeParsingError(ResumeParsingError):
    pass


def parse_and_store_resume(resume_id: str, mongodb: Database) -> ParsedResume:
    resume_document = mongodb.resumes.find_one({"postgres_resume_id": resume_id})
    if not resume_document or not resume_document.get("raw_text"):
        raise ResumeParsingError("Extracted resume text is missing")

    raw_text = resume_document["raw_text"]
    security_report = inspect_untrusted_resume_text(raw_text)
    prompt = build_resume_extraction_prompt(raw_text)

    try:
        output = generate_structured_with_fallback(
            routes=get_resume_parser_routes(),
            prompt=prompt,
            json_schema=ParsedResume.model_json_schema(),
        )
    except AIOrchestratorError as error:
        if str(error).startswith("All configured AI providers failed temporarily:"):
            raise TemporaryResumeParsingError(str(error)) from error
        raise ResumeParsingError(str(error)) from error

    try:
        parsed_resume = canonicalize_parsed_resume(ParsedResume.model_validate(output.data))
    except ValidationError as error:
        raise ResumeParsingError("AI resume output failed schema validation") from error

    mongodb.resumes.update_one(
        {"postgres_resume_id": resume_id},
        {
            "$set": {
                "parsed_resume": parsed_resume.model_dump(mode="json"),
                "field_provenance": {
                    field: "extracted" for field in PARSED_RESUME_FIELDS
                },
                "parser": {
                    "version": PARSER_VERSION,
                    "provider": output.route.provider,
                    "model": output.route.model,
                    "validated": True,
                },
                "prompt_security": security_report.to_document(),
                "processing": {
                    "status": "ready",
                    "error": None,
                },
                "updated_at": datetime.now(UTC),
            }
        },
    )
    return parsed_resume
