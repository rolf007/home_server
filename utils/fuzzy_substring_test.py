#!/usr/bin/env python3

from fuzzy_substring import Levenshtein
import unittest

class TestMusicServer(unittest.TestCase):

    def setUp(self):
        pass

    def test_text_book_examples(self):
        levenshtein = Levenshtein(1,1,1)
        self.assertEqual(levenshtein.distance("me", "my"), 1)
        self.assertEqual(levenshtein.distance("Sunday", "Saturday"), 3)
        self.assertEqual(levenshtein.distance("sitting", "kitten"), 3)

    def test_simple(self):
        levenshtein = Levenshtein(1,10,10)
        self.assertEqual(levenshtein.distance("summer of 69", "summer of 69"), 0)
        self.assertEqual(levenshtein.distance("summer 69", "summer of 69"), 3)
        self.assertEqual(levenshtein.distance("summer 69", "summer sun"), 21)
        self.assertEqual(levenshtein.distance("summer", "s"), 50)
        self.assertEqual(levenshtein.distance("s", "summer"), 5)
        self.assertEqual(levenshtein.distance("summer", ""), 60)
        self.assertEqual(levenshtein.distance("", "summer"), 6)
        self.assertEqual(levenshtein.distance("", ""), 0)

    def test_each_part(self):
        levenshtein = Levenshtein(5,10,12)
        self.assertEqual(levenshtein.distance("sommer", "summer"), 12)
        self.assertEqual(levenshtein.distance("sumer", "summer"), 5)
        self.assertEqual(levenshtein.distance("suummer", "summer"), 10)

if __name__ == '__main__':
    unittest.main()
