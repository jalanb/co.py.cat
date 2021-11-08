import unittest

from copycat.codelet import Codelet


class TestCodelet(unittest.TestCase):
    def test_string(self):
        """A codelet should use it's name as string"""
        expected = "fred"
        codelet = Codelet("fred", None, None)
        actual = str(codelet)
        self.assertEqual(actual, expected)
