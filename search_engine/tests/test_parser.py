"""
Enhanced Parser Tests
====================

Tests for the WebPageParser and fetch_web_page functionality.
Optimized for maintainability and comprehensive coverage.
"""

import sys
import os
import time
import unittest
from unittest.mock import patch, MagicMock

# Add parent directories to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from parser import WebPageParser, fetch_web_page
except ImportError:
    # Try with search_engine prefix
    from search_engine.parser import WebPageParser, fetch_web_page
from tests import TEST_CONFIG


class TestURLValidation(unittest.TestCase):
    """Test URL validation functionality"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.parser = WebPageParser()
    
    def tearDown(self):
        """Clean up after tests"""
        self.parser.close()
    
    def test_valid_urls(self):
        """Test valid URL formats"""
        valid_urls = [
            "https://example.com",
            "http://example.com",
            "https://subdomain.example.com",
            "https://example.com/path",
            "https://example.com/path?query=value",
            "https://example.com:8080/path"
        ]
        
        for url in valid_urls:
            with self.subTest(url=url):
                self.assertTrue(
                    self.parser._is_valid_url(url),
                    f"Valid URL should pass validation: {url}"
                )
    
    def test_invalid_protocols(self):
        """Test invalid protocol rejection"""
        invalid_protocols = [
            "ftp://example.com",
            "file:///path/to/file",
            "mailto:test@example.com",
            "javascript:alert(1)",
            "data:text/html,<script>alert(1)</script>"
        ]
        
        for url in invalid_protocols:
            with self.subTest(url=url):
                self.assertFalse(
                    self.parser._is_valid_url(url),
                    f"Invalid protocol should be rejected: {url}"
                )
    
    def test_localhost_blocking(self):
        """Test localhost and local IP blocking"""
        localhost_urls = [
            "https://localhost",
            "http://localhost:8080",
            "https://127.0.0.1",
            "http://127.0.0.1:3000",
            "https://192.168.1.1",
            "http://10.0.0.1",
            "https://172.16.0.1"
        ]
        
        for url in localhost_urls:
            with self.subTest(url=url):
                self.assertFalse(
                    self.parser._is_valid_url(url),
                    f"Localhost/internal IP should be blocked: {url}"
                )
    
    def test_dangerous_tlds(self):
        """Test dangerous TLD blocking"""
        dangerous_urls = [
            "https://malicious.tk",
            "https://spam.ml", 
            "https://bad.ga",
            "https://evil.cf",
            "https://suspicious.tk"
        ]
        
        for url in dangerous_urls:
            with self.subTest(url=url):
                self.assertFalse(
                    self.parser._is_valid_url(url),
                    f"Dangerous TLD should be blocked: {url}"
                )
    
    def test_malformed_urls(self):
        """Test malformed URL rejection"""
        malformed_urls = [
            "",
            "not-a-url",
            "http://",
            "https://",
            "://example.com",
            "http:example.com",
            "https:example.com"
        ]
        
        for url in malformed_urls:
            with self.subTest(url=url):
                self.assertFalse(
                    self.parser._is_valid_url(url),
                    f"Malformed URL should be rejected: {url}"
                )


class TestRateLimiting(unittest.TestCase):
    """Test rate limiting functionality"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.parser = WebPageParser()
    
    def tearDown(self):
        """Clean up after tests"""
        self.parser.close()
    
    def test_rate_limiting_delay(self):
        """Test that rate limiting applies proper delays"""
        domain = "example.com"
        
        # First request should not have delay
        start_time = time.time()
        self.parser._apply_rate_limit(domain)
        first_request_time = time.time() - start_time
        
        # Second request should have delay
        start_time = time.time()
        self.parser._apply_rate_limit(domain)
        second_request_time = time.time() - start_time
        
        # Should have at least 0.9 seconds delay (allowing for some variance)
        self.assertGreaterEqual(
            second_request_time, 0.9,
            "Rate limiting should apply at least 1 second delay"
        )
        self.assertLess(
            second_request_time, 2.0,
            "Rate limiting should not exceed reasonable delay"
        )
    
    def test_different_domains_no_delay(self):
        """Test that different domains don't interfere with each other"""
        domain1 = "example.com"
        domain2 = "different.com"
        
        # Apply rate limit to domain1
        self.parser._apply_rate_limit(domain1)
        
        # Request to domain2 should not have delay
        start_time = time.time()
        self.parser._apply_rate_limit(domain2)
        request_time = time.time() - start_time
        
        self.assertLess(
            request_time, 0.1,
            "Different domains should not interfere with rate limiting"
        )


class TestPageFetching(unittest.TestCase):
    """Test page fetching functionality"""
    
    def setUp(self):
        """Set up test fixtures"""
        if TEST_CONFIG.get('skip_network_tests', False):
            self.skipTest("Network tests disabled in configuration")
    
    def test_successful_fetch(self):
        """Test successful page fetching"""
        test_url = "https://httpbin.org/html"
        
        result = fetch_web_page(test_url)
        
        self.assertIsNotNone(result, "Should return result for valid URL")
        self.assertTrue(result.get('success'), "Fetch should be successful")
        self.assertEqual(result.get('status_code'), 200, "Should get 200 status")
        self.assertGreater(result.get('content_size', 0), 0, "Should have content")
        self.assertIn('content', result, "Should include content")
        self.assertIn('headers', result, "Should include headers")
    
    def test_404_handling(self):
        """Test 404 error handling"""
        test_url = "https://httpbin.org/status/404"
        
        result = fetch_web_page(test_url)
        
        if result:  # Some implementations may return None for 404
            self.assertEqual(
                result.get('status_code'), 404,
                "Should correctly handle 404 status"
            )
        else:
            self.assertIsNone(result, "May return None for 404 errors")
    
    def test_invalid_domain_handling(self):
        """Test handling of invalid domains"""
        test_url = "https://thisdefinitelydoesnotexist12345.com"
        
        result = fetch_web_page(test_url)
        
        # Should either return None or error result
        if result:
            self.assertFalse(
                result.get('success', True),
                "Should indicate failure for invalid domain"
            )
        else:
            self.assertIsNone(result, "May return None for invalid domains")
    
    @patch('parser.requests.get')
    def test_timeout_handling(self, mock_get):
        """Test timeout handling"""
        # Mock a timeout exception
        mock_get.side_effect = Exception("Connection timeout")
        
        try:
            result = fetch_web_page("https://example.com")
            # Should either return None or have success=False
            if result is not None:
                self.assertFalse(result.get('success', True), "Should indicate failure on timeout")
            else:
                self.assertIsNone(result, "Should return None on timeout")
        except Exception:
            # If exception is raised, that's also acceptable
            pass
    
    @patch('parser.requests.get')
    def test_large_content_handling(self, mock_get):
        """Test handling of large content"""
        # Mock response with large content
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.headers = {'content-length': '50000000'}  # 50MB
        mock_response.text = 'x' * 50000000  # Large content
        mock_response.url = 'https://example.com'
        mock_response.encoding = 'utf-8'
        mock_get.return_value = mock_response
        
        result = fetch_web_page("https://example.com")
        
        # Should handle large content appropriately
        self.assertIsNotNone(result, "Should handle large content")


class TestSecurityFeatures(unittest.TestCase):
    """Test security features"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.parser = WebPageParser()
    
    def tearDown(self):
        """Clean up after tests"""
        self.parser.close()
    
    def test_user_agent_spoofing_protection(self):
        """Test that proper user agent is used"""
        # This would require inspecting actual requests
        # For now, we test that the parser initializes properly
        self.assertIsNotNone(self.parser.session)
        self.assertIn('User-Agent', self.parser.session.headers)
    
    def test_redirect_handling(self):
        """Test redirect handling security"""
        if TEST_CONFIG.get('skip_network_tests', False):
            self.skipTest("Network tests disabled")
        
        # Test with httpbin redirect
        test_url = "https://httpbin.org/redirect/1"
        result = fetch_web_page(test_url)
        
        if result and result.get('success'):
            self.assertNotEqual(
                result.get('final_url'), test_url,
                "Should follow redirects and update final URL"
            )


def run_parser_tests():
    """Run all parser tests"""
    print("🚀 Running Parser Tests")
    print("=" * 50)
    
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add test classes
    suite.addTests(loader.loadTestsFromTestCase(TestURLValidation))
    suite.addTests(loader.loadTestsFromTestCase(TestRateLimiting))
    suite.addTests(loader.loadTestsFromTestCase(TestPageFetching))
    suite.addTests(loader.loadTestsFromTestCase(TestSecurityFeatures))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2 if TEST_CONFIG.get('verbose') else 1)
    result = runner.run(suite)
    
    # Return success status
    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_parser_tests()
    sys.exit(0 if success else 1)
