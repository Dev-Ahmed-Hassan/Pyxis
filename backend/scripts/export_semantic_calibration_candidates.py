"""Export stored pgvector comparisons as review-ready calibration observations."""

import argparse
import json
import sys
import uuid

from database.postgres import SessionLocal
from services.semantic_calibration_candidate_service import (
    collect_semantic_calibration_candidates,
)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Export pending semantic calibration observations."
    )
    parser.add_argument("--resume-id", type=uuid.UUID, required=True)
    parser.add_argument("--internship-id", type=uuid.UUID, required=True)
    arguments = parser.parse_args()
    try:
        with SessionLocal() as database:
            candidates = collect_semantic_calibration_candidates(
                database,
                arguments.resume_id,
                arguments.internship_id,
            )
    except Exception as error:
        print(f"Unable to export semantic calibration candidates: {error}")
        return 1
    print(
        json.dumps(
            {"cases": [candidate.model_dump(mode="json") for candidate in candidates]},
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
