import unittest

from resume_matcher.text import count_mentions, keyword_table, normalize_word, tokenize


class TokenizeTests(unittest.TestCase):
    def test_keeps_tech_spellings_together(self):
        self.assertEqual(tokenize("C++, Node.js and C#."), ["c++", "node.js", "and", "c#"])

    def test_plurals_are_merged(self):
        self.assertEqual(normalize_word("apis"), "api")
        self.assertEqual(normalize_word("libraries"), "library")

    def test_words_that_only_look_plural_are_left_alone(self):
        for word in ("class", "analysis", "status"):
            self.assertEqual(normalize_word(word), word)

    def test_keyword_table_drops_filler_and_remembers_spellings(self):
        table = keyword_table("The robots and the robot need strong experience")
        self.assertEqual(set(table), {"robot"})
        self.assertEqual(table["robot"]["robots"], 1)
        self.assertEqual(table["robot"]["robot"], 1)


class CountMentionsTests(unittest.TestCase):
    def test_java_is_not_found_inside_javascript(self):
        self.assertEqual(count_mentions("I write JavaScript daily", ["java"]), 0)
        self.assertEqual(count_mentions("I write Java and JavaScript", ["java"]), 1)

    def test_js_is_not_found_inside_node_js(self):
        self.assertEqual(count_mentions("Built with Node.js", ["js"]), 0)

    def test_symbols_are_part_of_the_term(self):
        self.assertEqual(count_mentions("Python, C++, and C#.", ["c++"]), 1)
        self.assertEqual(count_mentions("Python, C++, and C#.", ["c#"]), 1)

    def test_term_at_end_of_sentence_still_counts(self):
        self.assertEqual(count_mentions("We deploy with Docker.", ["docker"]), 1)

    def test_multi_word_alias_matches_across_a_line_break(self):
        self.assertEqual(count_mentions("machine\nlearning", ["machine learning"]), 1)

    def test_overlapping_aliases_count_once(self):
        aliases = ["cs:REST", "rest api", "rest apis"]
        self.assertEqual(count_mentions("Built a REST API", aliases), 1)
        self.assertEqual(count_mentions("REST APIs and more REST", aliases), 2)

    def test_case_sensitive_aliases(self):
        self.assertEqual(count_mentions("Take a rest after lunch", ["cs:REST"]), 0)
        self.assertEqual(count_mentions("Wired an LED driver", ["cs:Led", "cs:led"]), 0)
        self.assertEqual(count_mentions("Led a team of five", ["cs:Led", "cs:led"]), 1)


if __name__ == "__main__":
    unittest.main()
