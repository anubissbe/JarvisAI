import unittest
import os
import sys

# Add the parent directory to sys.path to allow imports from the project root
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import all test modules
from test_utils import TestUtils
from test_llm_service import TestLLMService
from test_database import TestDatabase
from test_api_endpoints import TestAPIEndpoints

if __name__ == '__main__':
    # Create a test suite
    test_suite = unittest.TestSuite()
    
    # Add tests to the suite
    test_suite.addTest(unittest.makeSuite(TestUtils))
    test_suite.addTest(unittest.makeSuite(TestLLMService))
    test_suite.addTest(unittest.makeSuite(TestDatabase))
    test_suite.addTest(unittest.makeSuite(TestAPIEndpoints))
    
    # Run the tests
    runner = unittest.TextTestRunner(verbosity=2)
    runner.run(test_suite)