import unittest

from arg_mine import utils


class TestEnum(unittest.TestCase):
    def test_enum(self):
        my_constants = utils.enum(FOO="foo", BAR="bar")

        self.assertEqual(my_constants.FOO, "foo")
        with self.assertRaises(AttributeError):
            _ = my_constants.BAZ


class TestHash(unittest.TestCase):
    def test_unique_hash(self):
        input_str = "foo_bar"
        hash_str = utils.unique_hash(input_str)
        self.assertIsInstance(hash_str, str)


if __name__ == '__main__':
    unittest.main()
