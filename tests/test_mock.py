from unittest.mock import Mock
import unittest

from apipeline.pipeline.pipeline import Pipeline
from apipeline.processors.frame_processor import FrameProcessor


class TestMock(unittest.TestCase):
    class MockProcessor(FrameProcessor):
        def __init__(self, name):
            self.name = name

        def __str__(self):
            return self.name

    def setUp(self):
        self.processor1 = self.MockProcessor('processor1')
        self.processor2 = self.MockProcessor('processor2')
        self.pipeline = Pipeline([
            self.processor1,
            self.processor2
        ])
        self.pipeline.name = 'MyClass'


class TestMyFunction(unittest.TestCase):
    def test_my_function(self):
        external_service = Mock()
        external_service.get_data.return_value = {"key": "value"}

        result = my_function(external_service)

        self.assertEqual(result, "value")
        external_service.get_data.assert_called_once()


def my_function(service):
    data = service.get_data()
    return data["key"]


if __name__ == '__main__':
    unittest.main()
