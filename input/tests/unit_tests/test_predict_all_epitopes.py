import os
import unittest
from unittest import TestCase

import input
from input.exceptions import INPuTConfigurationException
from input.predict_all_epitopes import Bunchepitopes


class TestPredictAllEpitopes(TestCase):

    def test_reference_environment_variable_is_required(self):
        # del os.environ[input.REFERENCE_FOLDER_ENV]
        with self.assertRaises(INPuTConfigurationException):
            Bunchepitopes()

    def test_empty_reference_folder_fails(self):
        os.environ[input.REFERENCE_FOLDER_ENV] = 'dummy'
        with self.assertRaises(INPuTConfigurationException):
            Bunchepitopes()


if __name__ == "__main__":
    unittest.main()
