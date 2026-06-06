import unittest
import uuid
from types import SimpleNamespace
from unittest.mock import patch

from fastapi import HTTPException

from services.graph_career_service import get_graph_career_recommendations
from services.graph_learning_path_service import get_match_learning_paths
from services.matching_service import calculate_skill_match
from tests.test_matching_modules import _parsed_internship, _parsed_resume


class MatchLearningPathTests(unittest.TestCase):
    @patch(
        "services.graph_learning_path_service.find_skill_support_paths_batch",
        return_value=[],
    )
    @patch(
        "services.graph_learning_path_service.find_prerequisite_paths_batch"
    )
    @patch(
        "services.graph_learning_path_service._get_owned_match_analysis"
    )
    def test_builds_ordered_path_from_saved_match(
        self,
        get_analysis,
        find_paths,
        _find_support_paths,
    ) -> None:
        resume_id = uuid.uuid4()
        internship_id = uuid.uuid4()
        analysis_id = uuid.uuid4()
        match = calculate_skill_match(
            resume_id=resume_id,
            internship_id=internship_id,
            parsed_resume=_parsed_resume("JavaScript"),
            parsed_internship=_parsed_internship(
                required_skills=("React",),
            ),
        )
        get_analysis.return_value = SimpleNamespace(
            id=analysis_id,
            resume_id=resume_id,
            internship_input_id=internship_id,
            analysis_payload=match.model_dump(mode="json"),
        )
        find_paths.return_value = [
            {
                "current_skill": "JavaScript",
                "target_skill": "React",
                "nodes": ["JavaScript", "React"],
                "confidences": [0.9],
            }
        ]

        response = get_match_learning_paths(
            database=object(),
            user=SimpleNamespace(id=uuid.uuid4()),
            analysis_id=analysis_id,
        )

        self.assertEqual(
            response.learning_paths[0].status,
            "prerequisite_path_found",
        )
        self.assertEqual(response.learning_paths[0].current_foundation, "JavaScript")
        self.assertEqual(
            [step.skill for step in response.learning_paths[0].steps],
            ["JavaScript", "React"],
        )
        self.assertEqual(response.learning_paths[0].source, "neo4j")

    @patch(
        "services.graph_learning_path_service.find_skill_support_paths_batch"
    )
    @patch(
        "services.graph_learning_path_service.find_prerequisite_paths_batch",
        return_value=[],
    )
    @patch(
        "services.graph_learning_path_service._get_owned_match_analysis"
    )
    def test_uses_related_evidence_as_detected_foundation(
        self,
        get_analysis,
        _find_prerequisite_paths,
        find_support_paths,
    ) -> None:
        resume_id = uuid.uuid4()
        internship_id = uuid.uuid4()
        match = calculate_skill_match(
            resume_id=resume_id,
            internship_id=internship_id,
            parsed_resume=_parsed_resume("SQL", "Nessus"),
            parsed_internship=_parsed_internship(
                preferred_skills=(
                    "Database Management",
                    "Vulnerability Scanning",
                    "Java",
                ),
            ),
        )
        get_analysis.return_value = SimpleNamespace(
            id=uuid.uuid4(),
            resume_id=resume_id,
            internship_input_id=internship_id,
            analysis_payload=match.model_dump(mode="json"),
        )
        find_support_paths.return_value = [
            {
                "resume_skill": "SQL",
                "requirement": "Database Management",
                "nodes": ["SQL", "Database Management"],
                "relationships": [
                    {
                        "relationship_type": "evidence_for",
                        "confidence": 0.95,
                    }
                ],
            },
            {
                "resume_skill": "Nessus",
                "requirement": "Vulnerability Scanning",
                "nodes": ["Nessus", "Vulnerability Scanning"],
                "relationships": [
                    {
                        "relationship_type": "evidence_for",
                        "confidence": 0.95,
                    }
                ],
            },
        ]

        response = get_match_learning_paths(
            database=object(),
            user=SimpleNamespace(id=uuid.uuid4()),
            analysis_id=get_analysis.return_value.id,
        )

        by_target = {
            item.target_skill: item
            for item in response.learning_paths
        }
        self.assertEqual(
            by_target["Database Management"].status,
            "foundation_detected",
        )
        self.assertEqual(
            by_target["Vulnerability Scanning"].current_foundation,
            "Nessus",
        )
        self.assertEqual(
            by_target["Java"].status,
            "direct_learning_required",
        )


class GraphCareerRecommendationTests(unittest.TestCase):
    @patch("services.graph_career_service.get_user_profile_facts")
    def test_rejects_empty_profile_facts(self, get_profile) -> None:
        get_profile.return_value = SimpleNamespace(skill_inventory=[])

        with self.assertRaises(HTTPException) as context:
            get_graph_career_recommendations(
                database=object(),
                user=SimpleNamespace(id=uuid.uuid4()),
            )

        self.assertEqual(context.exception.status_code, 409)

    @patch(
        "services.graph_career_service.find_prerequisite_paths_batch"
    )
    @patch(
        "services.graph_career_service.find_skill_support_paths_batch"
    )
    @patch("services.graph_career_service.get_role_fit_from_graph")
    @patch("services.graph_career_service.get_user_profile_facts")
    def test_ranks_roles_and_returns_missing_skill_paths(
        self,
        get_profile,
        get_roles,
        find_related_paths,
        find_paths,
    ) -> None:
        user = SimpleNamespace(id=uuid.uuid4())
        get_profile.return_value = SimpleNamespace(
            skill_inventory=[
                SimpleNamespace(canonical_name="JavaScript"),
                SimpleNamespace(canonical_name="HTML5"),
            ]
        )
        get_roles.return_value = [
            {
                "role": "Frontend Developer",
                "description": "Builds browser interfaces.",
                "domain": "career_roles",
                "requirements": [
                    {
                        "skill": "JavaScript",
                        "normalized_name": "javascript",
                        "importance": "required",
                        "confidence": 0.95,
                    },
                    {
                        "skill": "HTML5",
                        "normalized_name": "html5",
                        "importance": "required",
                        "confidence": 0.95,
                    },
                    {
                        "skill": "React",
                        "normalized_name": "react",
                        "importance": "preferred",
                        "confidence": 0.85,
                    },
                ],
                "matched_skills": ["JavaScript", "HTML5"],
            }
        ]
        find_paths.return_value = [
            {
                "current_skill": "JavaScript",
                "target_skill": "React",
                "nodes": ["JavaScript", "React"],
                "confidences": [0.9],
            }
        ]
        find_related_paths.return_value = []

        response = get_graph_career_recommendations(
            database=object(),
            user=user,
            limit=8,
        )

        recommendation = response.recommendations[0]
        self.assertEqual(recommendation.role, "Frontend Developer")
        self.assertEqual(recommendation.fit_level, "strong")
        self.assertEqual(recommendation.exact_required_coverage, 100)
        self.assertEqual(recommendation.missing_preferred_skills, ["React"])
        self.assertEqual(
            [step.skill for step in recommendation.learning_gaps[0].learning_steps],
            ["JavaScript", "React"],
        )

    @patch(
        "services.graph_career_service.find_prerequisite_paths_batch",
        return_value=[],
    )
    @patch(
        "services.graph_career_service.find_skill_support_paths_batch"
    )
    @patch("services.graph_career_service.get_role_fit_from_graph")
    @patch("services.graph_career_service.get_user_profile_facts")
    def test_related_support_is_partial_and_required_coverage_limits_label(
        self,
        get_profile,
        get_roles,
        find_related_paths,
        _find_prerequisite_paths,
    ) -> None:
        get_profile.return_value = SimpleNamespace(
            skill_inventory=[
                SimpleNamespace(canonical_name="Python"),
                SimpleNamespace(canonical_name="SQL"),
            ]
        )
        get_roles.return_value = [
            {
                "role": "Data Engineer",
                "description": "Builds data platforms.",
                "domain": "career_roles",
                "requirements": [
                    {
                        "skill": "Python",
                        "normalized_name": "python",
                        "importance": "required",
                        "confidence": 0.9,
                    },
                    {
                        "skill": "SQL",
                        "normalized_name": "sql",
                        "importance": "required",
                        "confidence": 0.95,
                    },
                    {
                        "skill": "Database Management",
                        "normalized_name": "database management",
                        "importance": "required",
                        "confidence": 0.9,
                    },
                    {
                        "skill": "Docker",
                        "normalized_name": "docker",
                        "importance": "preferred",
                        "confidence": 0.75,
                    },
                ],
                "matched_skills": ["Python", "SQL"],
            }
        ]
        find_related_paths.return_value = [
            {
                "resume_skill": "SQL",
                "requirement": "Database Management",
                "nodes": ["SQL", "Database Management"],
                "relationships": [
                    {
                        "relationship_type": "evidence_for",
                        "confidence": 0.95,
                    }
                ],
            }
        ]

        response = get_graph_career_recommendations(
            database=object(),
            user=SimpleNamespace(id=uuid.uuid4()),
        )

        recommendation = response.recommendations[0]
        self.assertEqual(recommendation.fit_level, "emerging")
        self.assertEqual(recommendation.exact_required_coverage, 66.67)
        self.assertEqual(
            recommendation.related_skill_support[0].requirement,
            "Database Management",
        )
        self.assertEqual(
            recommendation.related_skill_support[0].credit_factor,
            0.475,
        )


if __name__ == "__main__":
    unittest.main()
