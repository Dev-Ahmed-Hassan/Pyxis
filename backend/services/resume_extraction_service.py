from datetime import UTC, datetime
from pathlib import Path

import pymupdf
from docx import Document
from pymongo.database import Database

from models.resume import Resume


class ResumeExtractionError(Exception):
    pass


def extract_and_store_resume_text(resume: Resume, mongodb: Database) -> str:
    storage_path = _absolute_storage_path(resume)
    extension = storage_path.suffix.lower()

    if extension == ".pdf":
        raw_text = _extract_pdf_text(storage_path)
    elif extension == ".docx":
        raw_text = _extract_docx_text(storage_path)
    else:
        raise ResumeExtractionError("Only PDF and DOCX resume files are supported")

    cleaned_text = _clean_text(raw_text)
    if not cleaned_text:
        raise ResumeExtractionError(
            "No extractable text was found. Image-only resumes are not supported yet."
        )

    now = datetime.now(UTC)
    result = mongodb.resumes.update_one(
        {"postgres_resume_id": str(resume.id)},
        {
            "$set": {
                "postgres_user_id": str(resume.user_id),
                "raw_text": cleaned_text,
                "processing": {
                    "status": "text_extracted",
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
        existing_document = mongodb.resumes.find_one(
            {"postgres_resume_id": str(resume.id)},
            {"_id": 1},
        )
        document_id = existing_document["_id"]
    return str(document_id)


def _absolute_storage_path(resume: Resume) -> Path:
    if not resume.storage_path:
        raise ResumeExtractionError("Stored resume file path is missing")
    return Path(__file__).resolve().parent.parent / resume.storage_path


def _extract_pdf_text(file_path: Path) -> str:
    try:
        with pymupdf.open(file_path) as document:
            return "\n".join(page.get_text() for page in document)
    except Exception as error:
        raise ResumeExtractionError("The uploaded PDF is corrupted or invalid") from error


def _extract_docx_text(file_path: Path) -> str:
    try:
        document = Document(file_path)
        return "\n".join(paragraph.text for paragraph in document.paragraphs)
    except Exception as error:
        raise ResumeExtractionError("The uploaded DOCX file is corrupted or invalid") from error


def _clean_text(raw_text: str) -> str:
    lines = (line.strip() for line in raw_text.splitlines())
    return "\n".join(line for line in lines if line)
