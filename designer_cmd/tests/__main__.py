import unittest

from .test_api import TestDesigner, TestConnection, TestEnterprise, TestClusterMod, TestSessionMod, TestInfobaseMod
from .test_utils import TestUtils, TestPlatform

__all__ = [
    'TestDesigner',
    'TestEnterprise',
    'TestConnection',
    'TestUtils',
    'TestPlatform',
    'TestSessionMod',
    'TestInfobaseMod',
    'TestClusterMod'
]

if __name__ == '__main__':
    unittest.main()
