#!/usr/bin/env python3

from fuzzy_substring import Levenshtein
import unittest

class TestMusicServer(unittest.TestCase):

    def setUp(self):
        pass

    def test_text_book_examples(self):
        levenshtein = Levenshtein(1,1,1)
        self.assertEqual(levenshtein.distance("me", "my", 100), 1)
        self.assertEqual(levenshtein.distance("Sunday", "Saturday", 100), 3)
        self.assertEqual(levenshtein.distance("sitting", "kitten", 100), 3)

    def test_simple(self):
        levenshtein = Levenshtein(1,10,10)
        self.assertEqual(levenshtein.distance("summer of 69", "summer of 69", 100), 0)
        self.assertEqual(levenshtein.distance("summer 69", "summer of 69", 100), 3)
        self.assertEqual(levenshtein.distance("summer 69", "summer sun", 100), 21)
        self.assertEqual(levenshtein.distance("summer", "s", 100), 50)
        self.assertEqual(levenshtein.distance("s", "summer", 100), 5)
        self.assertEqual(levenshtein.distance("summer", "", 100), 60)
        self.assertEqual(levenshtein.distance("", "summer", 100), 6)
        self.assertEqual(levenshtein.distance("", "", 100), 0)

    def test_each_part(self):
        levenshtein = Levenshtein(5,10,12)
        self.assertEqual(levenshtein.distance("sommer", "summer", 100), 12)
        self.assertEqual(levenshtein.distance("sumer", "summer", 100), 5)
        self.assertEqual(levenshtein.distance("suummer", "summer", 100), 10)

    def test_limit(self):
        levenshtein = Levenshtein(5,10,12)
        self.assertEqual(levenshtein.distance("a", "aaaaaa", 17), None)
        self.assertEqual(levenshtein.distance("aa", "aaaaaa", 17), None)
        self.assertEqual(levenshtein.distance("aaa", "aaaaaa", 17), 15)
        self.assertEqual(levenshtein.distance("aaaa", "aaaaaa", 17), 10)
        self.assertEqual(levenshtein.distance("aaaaa", "aaaaaa", 17), 5)
        self.assertEqual(levenshtein.distance("aaaaaa", "aaaaaa", 17), 0)
        self.assertEqual(levenshtein.distance("aaaaaaa", "aaaaaa", 17), 10)
        self.assertEqual(levenshtein.distance("aaaaaaaa", "aaaaaa", 17), None)
        self.assertEqual(levenshtein.distance("aaaaaaaaa", "aaaaaa", 17), None)

        self.assertEqual(levenshtein.distance("a", "aaaaa", 17), None)
        self.assertEqual(levenshtein.distance("aa", "aaaaa", 17), 15)
        self.assertEqual(levenshtein.distance("aaa", "aaaaa", 17), 10)
        self.assertEqual(levenshtein.distance("aaaa", "aaaaa", 17), 5)
        self.assertEqual(levenshtein.distance("aaaaa", "aaaaa", 17), 0)
        self.assertEqual(levenshtein.distance("aaaaaa", "aaaaa", 17), 10)
        self.assertEqual(levenshtein.distance("aaaaaaa", "aaaaa", 17), None)

    def test_print(self):
        levenshtein = Levenshtein(5,10,18)
        self.assertEqual(levenshtein.distance("defg", "defghij", 100), 15)

if __name__ == '__main__':
    unittest.main()
