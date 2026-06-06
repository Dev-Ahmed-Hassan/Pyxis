import os
import unittest
import uuid
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from fastapi import HTTPException
from sqlalchemy.exc import SQLAlchemyError

from services.ai.config import ModelRoute, get_embedding_dimensions
from services.ai.providers.gemini_embeddings import (
    GeminiEmbeddingProvider,
    TextEmbedding,
)
from services.ai.schemas import ParsedResume
from services.semantic_embedding_refresh_service import refresh_match_embeddings
from services.semantic_embedding_service import (
    best_effort_refresh_resume_section_embeddings,
    build_internship_requirement_documents,
    build_resume_section_documents,
    invalidate_resume_section_embeddings,
    refresh_resume_section_embeddings,
)
from services.semantic_matching_service import (
    get_llm_retrieval_candidates,
    get_semantic_skill_score,
)
from tests.test_matching_modules import _parsed_internship, _parsed_resume


class SemanticDocumentBuilderTests(unittest.TestCase):
    def test_resume_documents_preserve_explainable_section_items(self) -> None:
        resume = _parsed_resume()
        resume.summary.value = "Security student interested in defensive operations"
        resume_data = resume.model_dump()
        resume_data["projects"] = [
            {
                "name": "Home Lab",
                "description": ["Triaged network alerts"],
                "skills": [],
                "confidence": 0.9,
                "evidence": "Home Lab",
            }
        ]
        resume_data["education"] = [
            {
                "institution": "Example University",
                "degree": "BS",
                "field_of_study": "Cybersecurity",
                "start_date": None,
                "end_date": None,
                "confidence": 0.9,
                "evidence": "Education",
            }
        ]

        documents = build_resume_section_documents(
            ParsedResume.model_validate(resume_data)
        )

        self.assertEqual(
            [(document.section_type, document.section_key) for document in documents],
            [
                ("summary", "summary"),
                ("project", "project:0"),
                ("project", "project:0:bullet:0"),
                ("education", "education:0"),
            ],
        )
        self.assertIn("Triaged network alerts", documents[1].text)
        self.assertIn("Triaged network alerts", documents[2].text)

    def test_internship_documents_keep_importance_category(self) -> None:
        internship = _parsed_internship(
            required_skills=("Python",),
            preferred_skills=("Docker",),
        )

        documents = build_internship_requirement_documents(internship)

        self.assertEqual(
            [
                (document.requirement_category, document.requirement)
                for document in documents
            ],
            [("required_skill", "Python"), ("preferred_skill", "Docker")],
        )

    def test_internship_documents_include_relevant_description_context(self) -> None:
        internship = _parsed_internship(required_skills=("Wordfence",))
        internship.responsibilities = [
            "Test Wordfence plugin behavior after WordPress updates",
            "Write weekly summaries",
        ]

        documents = build_internship_requirement_documents(internship)

        self.assertIn("Test Wordfence plugin behavior", documents[0].text)
        self.assertNotIn("weekly summaries", documents[0].text)

    def test_resume_documents_include_listed_skills_and_certifications(self) -> None:
        documents = build_resume_section_documents(
            _parsed_resume("Nessus", certifications=("Security+",))
        )

        self.assertEqual(documents[0].section_type, "skills_list")
        self.assertIn("Nessus", documents[0].text)
        self.assertEqual(documents[1].section_type, "certification")
        self.assertIn("Security+", documents[1].text)


class SemanticPersistenceTests(unittest.TestCase):
    def test_resume_refresh_replaces_rows_and_stores_hash_and_model(self) -> None:
        database = MagicMock()
        resume = _parsed_resume()
        resume.summary.value = "Built FastAPI services"
        provider = MagicMock()
        provider.embed.return_value = TextEmbedding(
            values=[0.1, 0.2],
            model_name="test-embedding-model",
        )

        count = refresh_resume_section_embeddings(
            database,
            uuid.uuid4(),
            resume,
            provider=provider,
        )

        self.assertEqual(count, 1)
        self.assertIn("DELETE FROM public.resume_section_embeddings", str(database.execute.call_args_list[0].args[0]))
        inserted = database.execute.call_args_list[1].args[1]
        self.assertEqual(inserted["model_name"], "test-embedding-model")
        self.assertEqual(inserted["embedding"], "[0.1,0.2]")
        self.assertEqual(len(inserted["content_hash"]), 64)

    def test_invalidation_failure_rolls_back_without_breaking_profile_flow(self) -> None:
        database = MagicMock()
        database.execute.side_effect = SQLAlchemyError("missing migration")

        invalidated = invalidate_resume_section_embeddings(database, uuid.uuid4())

        self.assertFalse(invalidated)
        database.rollback.assert_called_once_with()

    @patch("services.semantic_embedding_service.build_embedding_provider")
    def test_best_effort_refresh_reports_provider_failure_without_raising(
        self,
        build_provider,
    ) -> None:
        provider = MagicMock()
        provider.embed.side_effect = SQLAlchemyError("storage unavailable")
        build_provider.return_value = provider
        database = MagicMock()
        resume = _parsed_resume()
        resume.summary.value = "Built APIs"

        result = best_effort_refresh_resume_section_embeddings(
            database,
            uuid.uuid4(),
            resume,
        )

        self.assertFalse(result.refreshed)
        self.assertEqual(result.document_count, 0)
        self.assertIn("storage unavailable", result.warning)
        database.rollback.assert_called_once_with()


class SemanticMatchingTests(unittest.TestCase):
    @patch("services.semantic_matching_service.get_embedding_route")
    def test_llm_retrieval_returns_below_threshold_top_k_candidates(self, route) -> None:
        route.return_value = ModelRoute("gemini", "gemini-embedding-001")
        database = MagicMock()
        database.execute.return_value.mappings.return_value = [
            {
                "requirement": "Vulnerability Research",
                "requirement_category": "required_skill",
                "section_type": "project",
                "section_key": f"project:{index}",
                "section_text": f"Evidence {index}",
                "cosine_similarity": similarity,
            }
            for index, similarity in enumerate([0.69, 0.68, 0.67, 0.66])
        ]

        candidates = get_llm_retrieval_candidates(
            database,
            uuid.uuid4(),
            uuid.uuid4(),
            {("required_skill", "vulnerability research")},
        )

        self.assertEqual(len(candidates), 3)
        self.assertEqual(candidates[0].cosine_similarity, 0.69)

    @patch("services.semantic_matching_service.get_embedding_route")
    def test_semantic_evidence_reports_strongest_section_without_scoring(self, route) -> None:
        route.return_value = ModelRoute("gemini", "gemini-embedding-001")
        database = MagicMock()
        database.scalar.return_value = True
        database.execute.return_value.mappings.return_value = [
            {
                "requirement": "Vulnerability Research",
                "requirement_category": "required_skill",
                "section_type": "project",
                "section_key": "project:0",
                "section_text": "Built a vulnerability scanning lab",
                "cosine_similarity": 0.84,
            },
            {
                "requirement": "Vulnerability Research",
                "requirement_category": "required_skill",
                "section_type": "summary",
                "section_key": "summary",
                "section_text": "Security student",
                "cosine_similarity": 0.75,
            },
        ]

        score = get_semantic_skill_score(database, uuid.uuid4(), uuid.uuid4())

        self.assertTrue(score.available)
        self.assertFalse(score.contributes_to_score)
        self.assertEqual(len(score.evidence), 1)
        self.assertEqual(score.evidence[0].resume_section_key, "project:0")
        self.assertEqual(score.evidence[0].cosine_similarity, 0.84)

    @patch("services.semantic_matching_service.get_embedding_route")
    def test_missing_storage_is_reported_without_running_vector_query(self, route) -> None:
        route.return_value = ModelRoute("gemini", "gemini-embedding-001")
        database = MagicMock()
        database.scalar.return_value = False

        score = get_semantic_skill_score(database, uuid.uuid4(), uuid.uuid4())

        self.assertFalse(score.available)
        database.execute.assert_not_called()
        self.assertIn("Apply the pgvector migration", score.warnings[0])


class SemanticEmbeddingRefreshTests(unittest.TestCase):
    @patch("services.semantic_embedding_refresh_service.mark_internship_analyses_stale")
    @patch("services.semantic_embedding_refresh_service.mark_resume_analyses_stale")
    @patch("services.semantic_embedding_refresh_service.refresh_internship_requirement_embeddings")
    @patch("services.semantic_embedding_refresh_service.refresh_resume_section_embeddings")
    @patch("services.semantic_embedding_refresh_service.get_parsed_internship_requirements")
    @patch("services.semantic_embedding_refresh_service.get_parsed_resume_profile")
    @patch("services.semantic_embedding_refresh_service.get_embedding_route")
    def test_refresh_persists_both_sides_and_marks_history_stale(
        self,
        route,
        get_resume,
        get_internship,
        refresh_resume,
        refresh_internship,
        mark_resume_stale,
        mark_internship_stale,
    ) -> None:
        route.return_value = ModelRoute("gemini", "gemini-embedding-001")
        get_resume.return_value = SimpleNamespace(parsed_resume=_parsed_resume())
        get_internship.return_value = SimpleNamespace(
            parsed_internship=_parsed_internship(required_skills=("Python",))
        )
        refresh_resume.return_value = 3
        refresh_internship.return_value = 1
        database = MagicMock()
        resume_id = uuid.uuid4()
        internship_id = uuid.uuid4()

        response = refresh_match_embeddings(
            database,
            SimpleNamespace(id=uuid.uuid4()),
            resume_id,
            internship_id,
        )

        self.assertEqual(response.resume_section_embedding_count, 3)
        self.assertEqual(response.internship_requirement_embedding_count, 1)
        mark_resume_stale.assert_called_once_with(database, resume_id)
        mark_internship_stale.assert_called_once_with(database, internship_id)
        database.commit.assert_called_once_with()

    @patch("services.semantic_embedding_refresh_service.get_embedding_route")
    def test_refresh_requires_embedding_configuration(self, route) -> None:
        route.return_value = None
        with self.assertRaises(HTTPException) as context:
            refresh_match_embeddings(
                MagicMock(),
                SimpleNamespace(id=uuid.uuid4()),
                uuid.uuid4(),
                uuid.uuid4(),
            )
        self.assertEqual(context.exception.status_code, 409)


class GeminiEmbeddingProviderTests(unittest.TestCase):
    @patch("services.ai.providers.gemini_embeddings.httpx.post")
    def test_embed_content_uses_dimension_contract(self, post) -> None:
        post.return_value = SimpleNamespace(
            status_code=200,
            json=lambda: {"embedding": {"values": [0.1, 0.2]}},
        )
        provider = GeminiEmbeddingProvider(
            ModelRoute("gemini", "gemini-embedding-001"),
            ["test-key"],
            dimensions=2,
        )

        embedding = provider.embed("Built APIs")

        self.assertEqual(embedding.values, [0.1, 0.2])
        self.assertEqual(
            post.call_args.kwargs["json"]["output_dimensionality"],
            2,
        )
        self.assertEqual(
            post.call_args.kwargs["json"]["task_type"],
            "SEMANTIC_SIMILARITY",
        )


class EmbeddingConfigTests(unittest.TestCase):
    def test_database_dimension_contract_is_fixed(self) -> None:
        with patch.dict(os.environ, {"EMBEDDING_DIMENSIONS": "384"}):
            with self.assertRaisesRegex(Exception, "must be 768"):
                get_embedding_dimensions()


if __name__ == "__main__":
    unittest.main()
