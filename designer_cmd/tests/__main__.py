import unittest

from .api import TestDesigner, TestConnection
from .utils import TestUtils, TestPlatform

__all__ = [
    'TestDesigner',
    'TestConnection',
    'TestUtils',
    'TestPlatform'
]

if __name__ == '__main__':
    unittest.main()
