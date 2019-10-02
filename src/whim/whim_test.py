import unittest


class WhimTestCase(unittest.TestCase):
    def test_importable(self):
        __import__('whim')
