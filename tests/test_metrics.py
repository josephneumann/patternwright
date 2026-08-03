import unittest

from patternwright import MetricConfig, measure


class MetricTests(unittest.TestCase):
    def test_empty_text_has_zero_distributions(self):
        metrics = measure("")
        self.assertEqual(metrics.words, 0)
        self.assertEqual(metrics.sentences, 0)
        self.assertEqual(metrics.long_word_share, 0.0)
        self.assertEqual(metrics.to_dict()["rates_per_1000_words"]["negations"], 0.0)

    def test_neutral_counts_and_clock_colon_exclusion(self):
        text = (
            "The first sentence is short. The second sentence is also short.\n\n"
            "The third sentence arrives at 9:14; it is not late, and nobody leaves."
        )
        metrics = measure(text)
        self.assertEqual(metrics.paragraphs, 2)
        self.assertEqual(metrics.sentences, 3)
        self.assertEqual(metrics.semicolons, 1)
        self.assertEqual(metrics.colons, 0)
        self.assertEqual(metrics.comma_and, 1)
        self.assertEqual(metrics.negations, 2)
        self.assertIn(("the", 3), metrics.repeated_openings)

    def test_thresholds_are_explicit_and_configurable(self):
        metrics = measure(
            "One two three. Four five six seven.",
            MetricConfig(
                long_sentence_words=4,
                short_sentence_words=4,
                long_word_letters=5,
                repeated_opening_minimum=1,
            ),
        )
        self.assertEqual(metrics.long_sentences, 1)
        self.assertEqual(metrics.short_sentences, 1)
        self.assertEqual(metrics.long_words, 2)
        self.assertEqual(metrics.thresholds.long_sentence_words, 4)

    def test_unicode_words_and_apostrophes_are_one_token(self):
        metrics = measure("Élodie's naïveté wasn't performative.")
        self.assertEqual(metrics.words, 4)
        self.assertEqual(metrics.negations, 1)
        self.assertEqual(metrics.long_words, 1)

    def test_metrics_never_emit_an_authorship_score(self):
        serialized = metrics = measure("A sentence.").to_dict()
        self.assertNotIn("score", serialized)
        self.assertNotIn("probability", serialized)
        self.assertNotIn("authorship", serialized)


if __name__ == "__main__":
    unittest.main()
