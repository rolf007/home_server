#!/usr/bin/env python3

from argpkarse import ArgpKarse
import unittest
import time

class TestArgpKarse(unittest.TestCase):

    def setUp(self):
        pass

    def test_me(self):
        parser = ArgpKarse()
        parser.add_argument('.a', type=str)
        args = parser.parse_args()
        self.assertEqual(['cmd', ('a', 'hello')], args)

if __name__ == '__main__':
    unittest.main()
