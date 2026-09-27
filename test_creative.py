import math
import os
import random
import tempfile
import unittest

import creative


def landing_distribution(board):
    """Exact landing probabilities of a board, by pushing probability mass down the pins."""
    mass = [1.0]
    for l in range(board.rows):
        nxt = [0.0] * (len(mass) + 1)
        for x, m in enumerate(mass):
            if m == 0:
                continue
            right = board.right_chance(l, x) / 100
            nxt[x] += m * (1 - right)
            nxt[x + 1] += m * right
        mass = nxt
    return mass


def probs_from_counts(counts, slots):
    total = sum(counts.values())
    return [counts.get(y, 0) / total for y in range(slots)]


class BoardTest(unittest.TestCase):
    def test_trained_pins_reproduce_counts(self):
        counts = {0: 3, 4: 1, 7: 6, 11: 10}
        probs = probs_from_counts(counts, 12)
        dist = landing_distribution(creative.Board(probs))
        for y in range(12):
            self.assertAlmostEqual(dist[y], probs[y], places=6)

    def test_chaos_spreads_the_balls(self):
        probs = [0.001] * 12
        probs[5] = 1 - 0.011
        calm = landing_distribution(creative.Board(probs, chaos=1.0))
        wild = landing_distribution(creative.Board(probs, chaos=1.5))
        self.assertAlmostEqual(calm[5], probs[5], places=6)
        self.assertLess(wild[5], calm[5])
        self.assertAlmostEqual(sum(wild), 1.0, places=9)

    def test_drop_lands_on_a_slot(self):
        board = creative.Board(probs_from_counts({2: 1, 9: 1}, 10))
        random.seed(0)
        landed = {board.drop() for _ in range(300)}
        self.assertEqual(landed, {2, 9})


class CreativeModelTest(unittest.TestCase):
    TEXT = "the cat sat on the mat. the rat sat on the hat.\n" * 5

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.old_dir = creative.MODELS_DIR
        creative.MODELS_DIR = self.tmp.name

    def tearDown(self):
        creative.MODELS_DIR = self.old_dir
        self.tmp.cleanup()

    def test_charset_groups_similar_characters(self):
        charset = creative.order_charset("bca. eo")
        self.assertEqual(charset, " .aeobc")

    def test_distribution_blends_shorter_contexts(self):
        model = creative.CreativeModel.train("tiny", self.TEXT, order=3, min_count=1)
        probs = model.distribution("the")
        self.assertAlmostEqual(sum(probs), 1.0, places=9)
        # " " always followed "the", but blending leaves room for everything else
        self.assertGreater(probs[model.slot_of[" "]], 0.5)
        self.assertGreater(min(probs), 0)
        # Never-seen contexts fall back to the shorter one
        self.assertEqual(model.distribution("zzthe"), model.distribution("the"))

    def test_rare_long_contexts_are_pruned(self):
        text = "abcdefgh" + "the cat. " * 5
        model = creative.CreativeModel.train("tiny", text, order=5, min_count=2)
        self.assertNotIn("abcde", model.counts)   # seen once
        self.assertIn("abc", model.counts)        # short contexts are always kept
        self.assertIn("the c", model.counts)      # seen five times

    def test_evaluate_prefers_familiar_text(self):
        model = creative.CreativeModel.train("tiny", self.TEXT, order=3)
        familiar = model.evaluate("the cat sat on the mat.")
        strange = model.evaluate("tan ohm eat cot sham.")
        self.assertLess(familiar, strange)
        self.assertLess(familiar, math.log2(len(model.charset)))

    def test_save_and_load_roundtrip(self):
        model = creative.CreativeModel.train("tiny", self.TEXT, order=3)
        model.save()
        self.assertTrue(os.path.exists(os.path.join(self.tmp.name, "tiny.mdl")))
        loaded = creative.CreativeModel.load("tiny")
        self.assertEqual(loaded.charset, model.charset)
        self.assertEqual(loaded.order, 3)
        self.assertEqual(loaded.counts, model.counts)
        with self.assertRaises(Exception):
            model.save()

    def test_zero_creativity_only_uses_seen_characters(self):
        model = creative.CreativeModel.train("tiny", self.TEXT, order=3)
        random.seed(1)
        text = model.write("the ", 200, creativity=0.0)
        self.assertEqual(len(text), 204)
        self.assertTrue(set(text) <= set(self.TEXT))

    def test_write_is_reproducible_with_rng_seed(self):
        model = creative.CreativeModel.train("tiny", self.TEXT, order=3)
        random.seed(7)
        first = model.write("the ", 100, creativity=0.8)
        random.seed(7)
        self.assertEqual(model.write("the ", 100, creativity=0.8), first)

    def test_unknown_seed_characters_are_rejected(self):
        model = creative.CreativeModel.train("tiny", self.TEXT, order=3)
        with self.assertRaises(ValueError):
            model.write("zebra", 10)

    def test_originality_counts_new_words(self):
        model = creative.CreativeModel.train("tiny", self.TEXT, order=3)
        score, invented = model.originality("the cat flew")
        self.assertAlmostEqual(score, 1 / 3)
        self.assertEqual(invented, ["flew"])


if __name__ == "__main__":
    unittest.main()
