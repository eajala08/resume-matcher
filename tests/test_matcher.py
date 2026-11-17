import json
import unittest

from resume_matcher.matcher import compare, find_skills, split_sections

JOB = """\
Backend Engineer

Requirements:
- Python and SQL
- Experience with Docker

Nice to have:
- Kubernetes
- Rust

Benefits:
- Free lunch and a Java-themed coffee bar
"""


class SplitSectionsTests(unittest.TestCase):
    def test_nice_to_have_section_is_preferred(self):
        required, preferred = split_sections(JOB)
        self.assertIn("Python", required)
        self.assertIn("Kubernetes", preferred)
        self.assertNotIn("Kubernetes", required)

    def test_a_later_heading_ends_the_preferred_section(self):
        required, preferred = split_sections(JOB)
        self.assertIn("coffee bar", required)
        self.assertNotIn("coffee bar", preferred)

    def test_single_line_marked_as_a_plus_is_preferred(self):
        required, preferred = split_sections("We use Python.\nExperience with Terraform is a plus.\nWe use Git.")
        self.assertIn("Terraform", preferred)
        self.assertIn("Git", required)

    def test_skills_on_a_heading_line_are_not_lost(self):
        required, preferred = split_sections("Required: Python, SQL\nPreferred: Rust")
        self.assertIn("Python", required)
        self.assertIn("Rust", preferred)


class FindSkillsTests(unittest.TestCase):
    def test_aliases_map_to_one_canonical_name(self):
        found = find_skills("Worked with Postgres, k8s and ReactJS")
        self.assertEqual(set(found), {"PostgreSQL", "Kubernetes", "React"})

    def test_everyday_words_are_not_skills(self):
        found = find_skills("We react quickly, express ideas clearly, and rest on weekends in spring.")
        self.assertEqual(found, {})


class CompareTests(unittest.TestCase):
    def test_full_match_scores_100(self):
        report = compare("Python, SQL, Docker, Kubernetes, Rust, Java", JOB)
        self.assertEqual(report.score, 100)
        self.assertEqual(report.missing, [])

    def test_no_match_scores_0(self):
        report = compare("I enjoy hiking and baking bread.", JOB)
        self.assertEqual(report.score, 0)
        self.assertEqual(report.matched, [])

    def test_preferred_skills_count_half(self):
        # Required: Python (1.0). Preferred: Docker (0.5). Resume has only Python.
        report = compare("Python developer", "Requirements:\n- Python\nNice to have:\n- Docker")
        self.assertEqual(report.score, 67)

    def test_repeated_skills_count_more(self):
        job = "Requirements:\n- Python\n- More Python\n- Python again\n- Java"
        # Python weight 1.5 (3 mentions), Java weight 1.0.
        self.assertEqual(compare("Python", job).score, 60)
        self.assertEqual(compare("Java", job).score, 40)

    def test_missing_lists_required_before_preferred(self):
        report = compare("Python", JOB)
        self.assertEqual([s.name for s in report.missing_required], ["Docker", "Java", "SQL"])
        self.assertEqual([s.name for s in report.missing_preferred], ["Kubernetes", "Rust"])
        self.assertEqual(report.missing, report.missing_required + report.missing_preferred)

    def test_skill_listed_as_both_required_and_preferred_is_required(self):
        report = compare("", "Requirements:\n- Python\nNice to have:\n- Advanced Python")
        self.assertEqual(len(report.missing), 1)
        self.assertFalse(report.missing[0].preferred)
        self.assertEqual(report.missing[0].mentions, 2)

    def test_missing_keywords_are_repeated_words_absent_from_resume(self):
        job = "Robotics team. We love robotics. Payments experience. Payments matter. Python."
        report = compare("I know Python and payments.", job)
        self.assertEqual(report.missing_keywords, ["robotics"])

    def test_skills_never_appear_in_missing_keywords(self):
        job = "Kubernetes and Kubernetes. Machine learning, machine learning."
        self.assertEqual(compare("nothing relevant", job).missing_keywords, [])

    def test_posting_with_no_known_skills(self):
        report = compare("Python", "Come and bake bread with us.")
        self.assertEqual(report.score, 0)
        self.assertEqual(report.skills_in_posting, 0)

    def test_report_converts_to_json(self):
        data = json.loads(json.dumps(compare("Python", JOB).to_dict()))
        self.assertEqual(data["matched"][0]["skill"], "Python")
        self.assertIn("missing_keywords", data)


if __name__ == "__main__":
    unittest.main()
