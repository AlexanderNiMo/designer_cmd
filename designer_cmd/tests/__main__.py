import unittest

from .test_api import TestDesigner, TestConnection
from .test_utils import TestUtils, TestPlatform

__all__ = [
    'TestDesigner',
    'TestConnection',
    'TestUtils',
    'TestPlatform'
]

if __name__ == '__main__':
    unittest.main()
