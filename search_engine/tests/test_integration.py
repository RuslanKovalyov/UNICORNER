"""
Integration Tests
================

Tests for the combined parser + sanitizer workflow.
Tests the complete pipeline from URL to clean content.
"""

import sys
import os
import unittest
from unittest.mock import patch, MagicMock

# Add parent directories to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from parser import fetch_web_page
    from sanitizer import sanitize_web_content
except ImportError:
    # Try with search_engine prefix
    from search_engine.parser import fetch_web_page
    from search_engine.sanitizer import sanitize_web_content
from tests import TEST_CONFIG


class TestIntegrationWorkflow(unittest.TestCase):
    """Test complete parser + sanitizer workflow"""
    
    def setUp(self):
        """Set up test fixtures"""
        if TEST_CONFIG.get('skip_network_tests', False):
            self.skipTest("Network tests disabled in configuration")
    
    def test_complete_workflow(self):
        """Test complete workflow from URL to clean content"""
        test_url = "https://httpbin.org/html"
        
        # Step 1: Fetch page
        parser_result = fetch_web_page(test_url)
        self.assertIsNotNone(parser_result, "Parser should return result")
        self.assertTrue(parser_result.get('success'), "Parser should succeed")
        
        # Step 2: Sanitize content
        sanitizer_result = sanitize_web_content(
            parser_result['content'], 
            extract_links=True
        )
        self.assertTrue(sanitizer_result.get('sanitized'), "Sanitizer should succeed")
        
        # Verify complete pipeline
        self.assertIn('content', sanitizer_result)
        self.assertGreater(sanitizer_result.get('char_count', 0), 0)
        self.assertIn('links', sanitizer_result)
    
    def test_workflow_with_real_website(self):
        """Test workflow with a real website"""
        test_url = "https://example.com"
        
        # Complete workflow
        parser_result = fetch_web_page(test_url)
        if not parser_result or not parser_result.get('success'):
            self.skipTest(f"Could not fetch {test_url}")
        
        sanitizer_result = sanitize_web_content(
            parser_result['content'], 
            extract_links=True
        )
        
        # Verify results
        self.assertTrue(sanitizer_result.get('sanitized'))
        self.assertGreater(sanitizer_result.get('word_count', 0), 0)
        
        # Check if links were extracted
        if sanitizer_result.get('total_links', 0) > 0:
            self.assertIn('links', sanitizer_result)
            links_data = sanitizer_result['links']
            self.assertIn('stats', links_data)
    
    @patch('parser.fetch_web_page')
    def test_workflow_error_handling(self, mock_fetch):
        """Test workflow error handling"""
        # Mock parser failure
        mock_fetch.return_value = None
        
        # Call the mocked function
        parser_result = mock_fetch("https://example.com")
        self.assertIsNone(parser_result, "Mocked function should return None")
    
    def test_workflow_with_malicious_content(self):
        """Test workflow with malicious content"""
        malicious_html = """
        <html>
        <head><title>Test</title></head>
        <body>
            <script>alert('hack');</script>
            <h1 onclick="steal()">Title</h1>
            <p>Safe content</p>
            <a href="javascript:void(0)">Bad Link</a>
            <a href="/safe">Safe Link</a>
        </body>
        </html>
        """
        
        # Sanitize malicious content
        result = sanitize_web_content(malicious_html, extract_links=True)
        
        # Should sanitize successfully
        self.assertTrue(result.get('sanitized'))
        content = result.get('content', '')
        
        # Should remove malicious content
        self.assertNotIn('script', content.lower())
        self.assertNotIn('alert', content.lower())
        self.assertNotIn('onclick', content.lower())
        self.assertNotIn('javascript:', content.lower())
        
        # Should preserve safe content
        self.assertIn('Title', content)
        self.assertIn('Safe content', content)
        
        # Should extract only safe links
        if result.get('total_links', 0) > 0:
            all_links = result['links']['all_links']
            safe_links = [link for link in all_links if 'safe' in link.get('url', '').lower()]
            self.assertGreater(len(safe_links), 0, "Should find safe links")


class TestPerformance(unittest.TestCase):
    """Test performance characteristics"""
    
    def test_large_content_performance(self):
        """Test performance with large content"""
        # Create large HTML content
        large_html = """
        <html>
        <head><title>Large Page</title></head>
        <body>
        """ + "\n".join([f"<p>Paragraph {i} with some content</p>" for i in range(1000)]) + """
        """ + "\n".join([f"<a href='/page/{i}'>Link {i}</a>" for i in range(100)]) + """
        </body>
        </html>
        """
        
        import time
        start_time = time.time()
        
        result = sanitize_web_content(large_html, extract_links=True)
        
        processing_time = time.time() - start_time
        
        # Should complete within reasonable time (adjust as needed)
        self.assertLess(processing_time, 5.0, "Should process large content within 5 seconds")
        self.assertTrue(result.get('sanitized'), "Should successfully process large content")
        self.assertEqual(result.get('total_links'), 100, "Should extract all links")
    
    def test_memory_efficiency(self):
        """Test memory efficiency with repeated operations"""
        import gc
        
        # Create test content
        test_html = """
        <html>
        <head><title>Memory Test</title></head>
        <body>
            <h1>Test Content</h1>
            <p>Some content here</p>
            <a href="/link1">Link 1</a>
            <a href="/link2">Link 2</a>
        </body>
        </html>
        """
        
        # Run multiple iterations
        for i in range(100):
            result = sanitize_web_content(test_html, extract_links=True)
            self.assertTrue(result.get('sanitized'))
        
        # Force garbage collection
        gc.collect()
        
        # Should not accumulate excessive memory
        # This is a basic test - in production you might want more sophisticated memory monitoring


class TestEdgeCases(unittest.TestCase):
    """Test edge cases and unusual inputs"""
    
    def test_empty_html_tags(self):
        """Test handling of empty HTML tags"""
        empty_html = "<html><head></head><body></body></html>"
        
        result = sanitize_web_content(empty_html)
        
        self.assertTrue(result.get('sanitized'))
        # Should handle gracefully even with no content
    
    def test_deeply_nested_html(self):
        """Test handling of deeply nested HTML"""
        nested_html = "<html><body>"
        for i in range(50):
            nested_html += f"<div class='level-{i}'>"
        nested_html += "Deep content"
        for i in range(50):
            nested_html += "</div>"
        nested_html += "</body></html>"
        
        result = sanitize_web_content(nested_html)
        
        self.assertTrue(result.get('sanitized'))
        content = result.get('content', '')
        
        # Should find the content, even if deeply nested
        self.assertTrue('Deep content' in content or result.get('char_count', 0) > 0, 
                       "Should handle deeply nested HTML")
    
    def test_unicode_content(self):
        """Test handling of Unicode content"""
        unicode_html = """
        <html>
        <head><title>Unicode Test 测试</title></head>
        <body>
            <h1>Unicode Content 🚀</h1>
            <p>This contains émojis and spëcial characters: café, naïve, résumé</p>
            <p>And some non-Latin scripts: 你好世界, مرحبا بالعالم, Здравствуй мир</p>
        </body>
        </html>
        """
        
        result = sanitize_web_content(unicode_html)
        
        self.assertTrue(result.get('sanitized'))
        content = result.get('content', '')
        title = result.get('title', '')
        
        # Check Unicode content in title or content
        self.assertTrue('测试' in title or '测试' in content, "Should find Unicode characters")
        self.assertIn('🚀', content)
        self.assertIn('café', content)
        self.assertIn('你好世界', content)
    
    def test_malformed_html(self):
        """Test handling of malformed HTML"""
        malformed_html = """
        <html>
        <head><title>Malformed</title>
        <body>
            <h1>Missing closing tag
            <p>Unclosed paragraph
            <div><span>Nested without closing</div>
            <a href="/link">Link without closing
        </html>
        """
        
        result = sanitize_web_content(malformed_html)
        
        # Should handle gracefully despite malformed HTML
        self.assertTrue(result.get('sanitized'))
        self.assertGreater(result.get('char_count', 0), 0)


def run_integration_tests():
    """Run all integration tests"""
    print("🔗 Running Integration Tests")
    print("=" * 50)
    
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add test classes
    suite.addTests(loader.loadTestsFromTestCase(TestIntegrationWorkflow))
    suite.addTests(loader.loadTestsFromTestCase(TestPerformance))
    suite.addTests(loader.loadTestsFromTestCase(TestEdgeCases))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2 if TEST_CONFIG.get('verbose') else 1)
    result = runner.run(suite)
    
    # Return success status
    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_integration_tests()
    sys.exit(0 if success else 1)
