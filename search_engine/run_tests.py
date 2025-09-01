#!/usr/bin/env python3
"""
UNICORNER Search Engine - Test Launcher
=======================================

Quick launcher for the comprehensive test suite.
Run from the search_engine directory.
"""

import sys
import os

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import and run the test runner
from tests.test_runner import main

if __name__ == "__main__":
    main()
