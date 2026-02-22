import unittest

from coverage_guardrail import classify_word, is_valid_word, normalize_word


class CoverageGuardrailTests(unittest.TestCase):
    def test_normalize_word(self):
        self.assertEqual(normalize_word('  Hello  '), 'hello')
        self.assertEqual(normalize_word(None), '')

    def test_is_valid_word(self):
        self.assertTrue(is_valid_word('alpha'))
        self.assertTrue(is_valid_word('re-do'))
        self.assertFalse(is_valid_word(''))
        self.assertFalse(is_valid_word('toolong-token-name-here', max_len=10))
        self.assertFalse(is_valid_word('bad123'))

    def test_classify_word(self):
        self.assertEqual(classify_word(''), 'empty')
        self.assertEqual(classify_word('re-do'), 'hyphenated')
        self.assertEqual(classify_word('word'), 'alpha')
        self.assertEqual(classify_word('w0rd'), 'other')


if __name__ == '__main__':
    unittest.main()
