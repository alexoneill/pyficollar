"""Test backwards compatibility shim for 'fi' import."""

import unittest
import warnings


class TestCompatibilityShim(unittest.TestCase):
    def test_import_fi_shim(self):
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            import fi
            from fi import FiClient, Pet

            self.assertIsNotNone(FiClient)
            self.assertIsNotNone(Pet)
            self.assertTrue(any(issubclass(item.category, DeprecationWarning) for item in w))


if __name__ == "__main__":
    unittest.main()
