#!/usr/bin/env python3
import unittest
import os
import sys

def run_tests():
    """Run all tests in the tests directory."""
    # Get the directory containing this script
    root_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Add the root directory to the Python path if not already there
    if root_dir not in sys.path:
        sys.path.insert(0, root_dir)
    
    # Discover and run all tests
    loader = unittest.TestLoader()
    test_dir = os.path.join(root_dir, 'tests')
    suite = loader.discover(test_dir)
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()

if __name__ == '__main__':
    success = run_tests()
    sys.exit(0 if success else 1)
