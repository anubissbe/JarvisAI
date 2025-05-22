import unittest
import sys
import os

# Add the parent directory to the path so we can import the modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import all test modules
from test_utils import TestUtils
from test_llm_service import TestLLMService
from test_api_endpoints import TestAPIEndpoints
from test_database import TestDatabase

# Create a test suite
def create_test_suite():
    test_suite = unittest.TestSuite()
    
    # Add test cases
    test_suite.addTest(unittest.makeSuite(TestUtils))
    test_suite.addTest(unittest.makeSuite(TestLLMService))
    test_suite.addTest(unittest.makeSuite(TestAPIEndpoints))
    test_suite.addTest(unittest.makeSuite(TestDatabase))
    
    return test_suite

if __name__ == '__main__':
    # Run the test suite
    runner = unittest.TextTestRunner()
    test_suite = create_test_suite()
    runner.run(test_suite)