import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from schemas.matching import ResumeSkillEvidence
from services.neo4j_related_skill_service import Neo4jRelatedSkillEvidenceProvider
from services.skill_graph_dataset_service import (
    SkillGraphDatasetError,
    load_skill_graph_dataset,
)


class SkillGraphDatasetTests(unittest.TestCase):
    def tearDown(self) -> None:
        load_skill_graph_dataset.cache_clear()

    def test_rejects_alias_mapped_to_two_canonical_skills(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "one.json").write_text(
                json.dumps(
                    {
                        "schema_version": 1,
                        "domain": "one",
                        "skills": [
                            {
                                "canonical_name": "Burp Suite",
                                "aliases": ["Burp"],
                            }
                        ],
                        "relationships": [],
                    }
                ),
                encoding="utf-8",
            )
            (root / "two.json").write_text(
                json.dumps(
                    {
                        "schema_version": 1,
                        "domain": "two",
                        "skills": [
                            {
                                "canonical_name": "Burp Collaborator",
                                "aliases": ["Burp"],
                            }
                        ],
                        "relationships": [],
                    }
                ),
                encoding="utf-8",
            )

            with patch(
                "services.skill_graph_dataset_service.DATA_DIRECTORY",
                root,
            ):
                load_skill_graph_dataset.cache_clear()
                with self.assertRaisesRegex(
                    SkillGraphDatasetError,
                    "alias 'Burp'",
                ):
                    load_skill_graph_dataset()


class Neo4jRelatedSkillProviderTests(unittest.TestCase):
    @patch(
        "services.neo4j_related_skill_service.find_skill_support_paths_batch"
    )
    def test_uses_one_batch_lookup_for_all_pairs(self, find_paths) -> None:
        find_paths.return_value = [
            {
                "resume_skill": "Nessus",
                "requirement": "Vulnerability Research",
                "nodes": [
                    "Nessus",
                    "Vulnerability Assessment",
                    "Vulnerability Research",
                ],
                "relationships": [
                    {
                        "relationship_type": "evidence_for",
                        "confidence": 0.95,
                    },
                    {
                        "relationship_type": "related_to",
                        "confidence": 0.8,
                    },
                ],
            }
        ]
        resume_evidence = [
            ResumeSkillEvidence(
                skill="Nessus",
                section="skills_list",
                extraction_source="explicit",
                confidence=1,
                provenance_weight=0.75,
                context=None,
            ),
            ResumeSkillEvidence(
                skill="Nmap",
                section="skills_list",
                extraction_source="explicit",
                confidence=1,
                provenance_weight=0.75,
                context=None,
            ),
        ]

        evidence = Neo4jRelatedSkillEvidenceProvider().find_evidence(
            resume_evidence=resume_evidence,
            required_skills=["Vulnerability Research"],
            preferred_skills=["Network Scanning"],
            required_domain_concepts=[],
            preferred_domain_concepts=[],
        )

        find_paths.assert_called_once_with(
            resume_skills=["Nessus", "Nmap"],
            requirements=["Vulnerability Research", "Network Scanning"],
        )
        self.assertEqual(len(evidence), 1)
        self.assertEqual(evidence[0].source, "neo4j")
        self.assertEqual(evidence[0].path_distance, 2)


if __name__ == "__main__":
    unittest.main()
