"""
UNICORNER Search Engine Test Suite
==================================

Comprehensive test suite for the search engine components:
- Parser (URL fetching and validation)
- Sanitizer (Content cleaning and link extraction)
- Interactive testing tools

Run individual tests or the complete suite with test_runner.py
"""

__version__ = "1.0.0"
__author__ = "UNICORNER Team"

# Test configuration
TEST_CONFIG = {
    'timeout': 30,  # seconds
    'max_retries': 3,
    'test_urls': [
        'https://httpbin.org/html',
        'https://example.com',
    ],
    'skip_network_tests': False,  # Set to True to skip network-dependent tests
    'verbose': True
}
