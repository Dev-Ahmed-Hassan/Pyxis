import unittest
import uuid

from services.ai.internship_schemas import ParsedInternship
from services.ai.schemas import ParsedResume
from services.matching_service import calculate_skill_match


def _text(value: str | None = None) -> dict:
    return {
        "value": value,
        "confidence": 0.9 if value else 0.0,
        "evidence": value,
    }


def _skill(name: str, source: str = "explicit") -> dict:
    return {
        "name": name,
        "confidence": 0.9,
        "evidence": name,
        "source": source,
    }


def _parsed_resume(
    *skills: str,
    inferred_skills: tuple[str, ...] = (),
    project_skills: tuple[str, ...] = (),
    experience_skills: tuple[str, ...] = (),
    certifications: tuple[str, ...] = (),
) -> ParsedResume:
    return ParsedResume.model_validate(
        {
            "full_name": _text("Ada Lovelace"),
            "email": _text("ada@example.com"),
            "phone": _text(),
            "location": _text(),
            "summary": _text(),
            "skills": [
                *[_skill(skill) for skill in skills],
                *[_skill(skill, source="inferred") for skill in inferred_skills],
            ],
            "experience": [
                {
                    "company": "Example Company",
                    "role": "Security Intern",
                    "start_date": None,
                    "end_date": None,
                    "description": [],
                    "skills": [_skill(skill) for skill in experience_skills],
                    "confidence": 0.9,
                    "evidence": "Used during internship",
                }
            ]
            if experience_skills
            else [],
            "projects": [
                {
                    "name": "Security Lab",
                    "description": [],
                    "skills": [_skill(skill) for skill in project_skills],
                    "confidence": 0.9,
                    "evidence": "Used in project",
                }
            ]
            if project_skills
            else [],
            "education": [],
            "certifications": [
                {
                    "name": certification,
                    "issuer": "Example Issuer",
                    "confidence": 0.9,
                    "evidence": certification,
                }
                for certification in certifications
            ],
        }
    )


def _parsed_internship(
    required_skills: tuple[str, ...] = (),
    preferred_skills: tuple[str, ...] = (),
    required_domain_concepts: tuple[str, ...] = (),
    preferred_domain_concepts: tuple[str, ...] = (),
    required_soft_skills: tuple[str, ...] = (),
    preferred_soft_skills: tuple[str, ...] = (),
) -> ParsedInternship:
    return ParsedInternship.model_validate(
        {
            "title": _text("Backend Intern"),
            "company": _text("Example"),
            "location": _text(),
            "experience_level": _text(),
            "required_skills": [_skill(skill) for skill in required_skills],
            "preferred_skills": [_skill(skill) for skill in preferred_skills],
            "required_domain_concepts": [
                _skill(skill) for skill in required_domain_concepts
            ],
            "preferred_domain_concepts": [
                _skill(skill) for skill in preferred_domain_concepts
            ],
            "required_soft_skills": [_skill(skill) for skill in required_soft_skills],
            "preferred_soft_skills": [_skill(skill) for skill in preferred_soft_skills],
            "responsibilities": [],
            "qualifications": [],
        }
    )


class SkillMatchingTests(unittest.TestCase):
    def setUp(self) -> None:
        self.resume_id = uuid.uuid4()
        self.internship_id = uuid.uuid4()

    def test_match_uses_required_and_preferred_weights(self) -> None:
        result = calculate_skill_match(
            resume_id=self.resume_id,
            internship_id=self.internship_id,
            parsed_resume=_parsed_resume("Python", "Git", "FastAPI"),
            parsed_internship=_parsed_internship(
                required_skills=("Python", "Docker"),
                preferred_skills=("Git", "Postgres"),
            ),
        )

        self.assertEqual(result.overall_score, 50.0)
        self.assertEqual(result.technical_skills.required.applied_weight, 0.8)
        self.assertEqual(result.technical_skills.required.matched_skills, ["Python"])
        self.assertEqual(result.technical_skills.required.missing_skills, ["Docker"])
        self.assertEqual(result.technical_skills.preferred.applied_weight, 0.2)
        self.assertEqual(result.technical_skills.preferred.matched_skills, ["Git"])
        self.assertEqual(result.technical_skills.preferred.missing_skills, ["PostgreSQL"])

    def test_match_canonicalizes_aliases_and_deduplicates_skills(self) -> None:
        result = calculate_skill_match(
            resume_id=self.resume_id,
            internship_id=self.internship_id,
            parsed_resume=_parsed_resume("js", "JavaScript", "postgres"),
            parsed_internship=_parsed_internship(
                required_skills=("javascript", "PostgreSQL"),
            ),
        )

        self.assertEqual(result.overall_score, 100.0)
        self.assertEqual(result.resume_skills, ["JavaScript", "PostgreSQL"])
        self.assertEqual(
            result.technical_skills.required.matched_skills,
            ["JavaScript", "PostgreSQL"],
        )

    def test_required_only_match_reassigns_unused_preferred_weight(self) -> None:
        result = calculate_skill_match(
            resume_id=self.resume_id,
            internship_id=self.internship_id,
            parsed_resume=_parsed_resume("Python"),
            parsed_internship=_parsed_internship(
                required_skills=("Python", "Docker"),
            ),
        )

        self.assertEqual(result.overall_score, 50.0)
        self.assertEqual(result.technical_skills.required.applied_weight, 1.0)
        self.assertEqual(result.technical_skills.preferred.applied_weight, 0.0)

    def test_empty_internship_skills_return_zero_with_warnings(self) -> None:
        result = calculate_skill_match(
            resume_id=self.resume_id,
            internship_id=self.internship_id,
            parsed_resume=_parsed_resume("Python"),
            parsed_internship=_parsed_internship(),
        )

        self.assertEqual(result.overall_score, 0.0)
        self.assertIn(
            "The internship description did not identify concrete technical skills.",
            result.warnings,
        )

    def test_soft_skills_are_visible_but_do_not_reduce_technical_score(self) -> None:
        result = calculate_skill_match(
            resume_id=self.resume_id,
            internship_id=self.internship_id,
            parsed_resume=_parsed_resume("Python"),
            parsed_internship=_parsed_internship(
                required_skills=("Python",),
                required_soft_skills=("Teamwork", "Attention to Detail"),
            ),
        )

        self.assertEqual(result.overall_score, 100.0)
        self.assertFalse(result.soft_skills.contributes_to_score)
        self.assertEqual(
            result.soft_skills.required.missing_skills,
            ["Teamwork", "Attention to Detail"],
        )

    def test_curated_related_skill_rule_explains_domain_concept_evidence(self) -> None:
        result = calculate_skill_match(
            resume_id=self.resume_id,
            internship_id=self.internship_id,
            parsed_resume=_parsed_resume("Nmap", "DNS"),
            parsed_internship=_parsed_internship(
                required_domain_concepts=("Network Security",),
            ),
        )

        self.assertEqual(result.overall_score, 0.0)
        self.assertEqual(len(result.related_skill_evidence), 2)
        nmap_evidence = result.related_skill_evidence[0]
        self.assertEqual(nmap_evidence.support_path, ["Nmap", "Network Security"])
        self.assertEqual(nmap_evidence.resume_evidence.section, "skills_list")
        self.assertEqual(nmap_evidence.resume_evidence.provenance_weight, 0.75)
        self.assertEqual(nmap_evidence.relationship_credit_factor, 0.475)
        self.assertEqual(nmap_evidence.effective_credit_factor, 0.3562)

    def test_related_skill_evidence_does_not_inflate_exact_overlap_score(self) -> None:
        result = calculate_skill_match(
            resume_id=self.resume_id,
            internship_id=self.internship_id,
            parsed_resume=_parsed_resume("Burp Suite"),
            parsed_internship=_parsed_internship(
                required_skills=("Python",),
                preferred_domain_concepts=("Web Security",),
            ),
        )

        self.assertEqual(result.overall_score, 0.0)
        self.assertEqual(
            result.related_skill_evidence[0].requirement_category,
            "preferred_domain_concept",
        )
        self.assertEqual(
            result.related_skill_evidence[0].supported_requirement,
            "Web Security",
        )

    def test_security_resume_receives_capped_related_credit_and_normalized_evidence(
        self,
    ) -> None:
        result = calculate_skill_match(
            resume_id=self.resume_id,
            internship_id=self.internship_id,
            parsed_resume=_parsed_resume(
                "Nmap",
                "Burp Suite",
                "OWASP ZAP",
                "Nessus",
                "Kali Linux",
                "Metasploit",
                "TCP/IP",
                "DNS",
                "Firewalls",
                "SQLi",
                "XSS",
                "Vulnerability Assessment",
            ),
            parsed_internship=_parsed_internship(
                required_skills=(
                    "Troubleshooting",
                    "QA Testing",
                    "Vulnerability Research",
                ),
                preferred_skills=("WordPress CMS", "cPanel", "FTP"),
                required_domain_concepts=("Web Technologies", "Security Concepts"),
                preferred_domain_concepts=("Network Security Principles",),
            ),
        )

        self.assertEqual(result.exact_overlap_score, 0.0)
        self.assertEqual(result.related_skill_score.contribution_points, 8.0)
        self.assertEqual(
            result.related_skill_score.supported_required_skills,
            ["Vulnerability Research"],
        )
        self.assertEqual(result.overall_score, 8.0)
        self.assertEqual(
            result.domain_concepts.required.missing_skills,
            ["Web Technologies", "Cybersecurity Fundamentals"],
        )
        self.assertEqual(
            result.domain_concepts.preferred.missing_skills,
            ["Network Security"],
        )
        self.assertTrue(
            any(
                evidence.support_path
                == ["Nessus", "Vulnerability Assessment", "Vulnerability Research"]
                for evidence in result.related_skill_evidence
            )
        )
        self.assertIn(
            "Some technical requirements are broad and may need manual review: "
            "Troubleshooting.",
            result.warnings,
        )

    def test_direct_related_evidence_scores_more_than_indirect_evidence(self) -> None:
        direct_result = calculate_skill_match(
            resume_id=self.resume_id,
            internship_id=self.internship_id,
            parsed_resume=_parsed_resume("Vulnerability Assessment"),
            parsed_internship=_parsed_internship(
                required_skills=("Vulnerability Research",),
            ),
        )
        indirect_result = calculate_skill_match(
            resume_id=self.resume_id,
            internship_id=self.internship_id,
            parsed_resume=_parsed_resume("Nessus"),
            parsed_internship=_parsed_internship(
                required_skills=("Vulnerability Research",),
            ),
        )

        self.assertEqual(direct_result.overall_score, 30.0)
        self.assertEqual(indirect_result.overall_score, 24.23)
        self.assertGreater(direct_result.overall_score, indirect_result.overall_score)
        self.assertEqual(
            indirect_result.related_skill_score.requirement_credits[
                0
            ].strongest_evidence_path,
            ["Nessus", "Vulnerability Assessment", "Vulnerability Research"],
        )

    def test_related_credit_uses_strongest_resume_provenance(self) -> None:
        listed_result = calculate_skill_match(
            resume_id=self.resume_id,
            internship_id=self.internship_id,
            parsed_resume=_parsed_resume("Nessus"),
            parsed_internship=_parsed_internship(
                required_skills=("Vulnerability Research",),
            ),
        )
        project_result = calculate_skill_match(
            resume_id=self.resume_id,
            internship_id=self.internship_id,
            parsed_resume=_parsed_resume(project_skills=("Nessus",)),
            parsed_internship=_parsed_internship(
                required_skills=("Vulnerability Research",),
            ),
        )
        experience_result = calculate_skill_match(
            resume_id=self.resume_id,
            internship_id=self.internship_id,
            parsed_resume=_parsed_resume(experience_skills=("Nessus",)),
            parsed_internship=_parsed_internship(
                required_skills=("Vulnerability Research",),
            ),
        )
        inferred_result = calculate_skill_match(
            resume_id=self.resume_id,
            internship_id=self.internship_id,
            parsed_resume=_parsed_resume(inferred_skills=("Nessus",)),
            parsed_internship=_parsed_internship(
                required_skills=("Vulnerability Research",),
            ),
        )

        self.assertEqual(inferred_result.overall_score, 15.75)
        self.assertEqual(listed_result.overall_score, 24.23)
        self.assertEqual(project_result.overall_score, 29.07)
        self.assertEqual(experience_result.overall_score, 32.3)
        strongest_credit = experience_result.related_skill_score.requirement_credits[0]
        self.assertEqual(strongest_credit.strongest_resume_evidence.section, "experience")

    def test_splunk_supports_siem_without_exact_match(self) -> None:
        result = calculate_skill_match(
            resume_id=self.resume_id,
            internship_id=self.internship_id,
            parsed_resume=_parsed_resume("Splunk"),
            parsed_internship=_parsed_internship(required_skills=("SIEM",)),
        )

        self.assertEqual(result.exact_overlap_score, 0.0)
        self.assertEqual(result.related_skill_score.supported_required_skills, ["SIEM"])
        self.assertEqual(
            result.related_skill_score.requirement_credits[
                0
            ].strongest_evidence_path,
            ["Splunk", "SIEM"],
        )

    def test_kali_linux_supports_linux_without_exact_match(self) -> None:
        result = calculate_skill_match(
            resume_id=self.resume_id,
            internship_id=self.internship_id,
            parsed_resume=_parsed_resume("Kali Linux"),
            parsed_internship=_parsed_internship(required_skills=("Linux",)),
        )

        self.assertEqual(result.exact_overlap_score, 0.0)
        self.assertEqual(result.related_skill_score.supported_required_skills, ["Linux"])
        self.assertEqual(
            result.related_skill_score.requirement_credits[
                0
            ].strongest_evidence_path,
            ["Kali Linux", "Linux"],
        )

    def test_python_alone_does_not_support_penetration_testing(self) -> None:
        result = calculate_skill_match(
            resume_id=self.resume_id,
            internship_id=self.internship_id,
            parsed_resume=_parsed_resume("Python"),
            parsed_internship=_parsed_internship(
                required_skills=("Penetration Testing",),
            ),
        )

        self.assertEqual(result.overall_score, 0.0)
        self.assertEqual(result.related_skill_score.supported_required_skills, [])

    def test_project_skill_participates_in_exact_matching(self) -> None:
        result = calculate_skill_match(
            resume_id=self.resume_id,
            internship_id=self.internship_id,
            parsed_resume=_parsed_resume(project_skills=("Python",)),
            parsed_internship=_parsed_internship(required_skills=("Python",)),
        )

        self.assertEqual(result.overall_score, 100.0)
        self.assertEqual(
            result.technical_skills.required.matched_skill_evidence[
                0
            ].strongest_evidence.section,
            "project",
        )

    def test_legacy_mixed_requirements_are_reclassified(self) -> None:
        result = calculate_skill_match(
            resume_id=self.resume_id,
            internship_id=self.internship_id,
            parsed_resume=_parsed_resume("Nmap", "Burp Suite", "OWASP ZAP"),
            parsed_internship=_parsed_internship(
                required_skills=(
                    "Web Technologies",
                    "Security Concepts",
                    "Teamwork",
                    "Attention to Detail",
                ),
                preferred_skills=(
                    "WordPress CMS",
                    "Network Security Principles",
                    "Customer Support",
                    "QA Processes",
                    "Communication Skills",
                ),
            ),
        )

        self.assertEqual(result.technical_skills.required.missing_skills, [])
        self.assertEqual(
            result.technical_skills.preferred.missing_skills,
            ["WordPress"],
        )
        self.assertEqual(
            result.domain_concepts.required.missing_skills,
            ["Web Technologies", "Cybersecurity Fundamentals"],
        )
        self.assertEqual(
            result.soft_skills.required.missing_skills,
            ["Teamwork", "Attention to Detail"],
        )
        self.assertEqual(
            result.soft_skills.preferred.missing_skills,
            ["Customer Service", "Communication"],
        )


if __name__ == "__main__":
    unittest.main()
