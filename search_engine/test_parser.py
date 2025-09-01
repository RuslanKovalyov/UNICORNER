"""
Test file for the Web Page Parser (Pure Parsing Only)
Run with: python test_parser.py
"""

import sys
import os

# Add the parent directory to the path so we can import the parser
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from parser import WebPageParser, fetch_web_page


def test_url_validation():
    """Test URL validation"""
    print("🔒 Testing URL Validation")
    print("=" * 50)
    
    parser = WebPageParser()
    
    test_urls = [
        ("https://example.com", True, "Valid HTTPS URL"),
        ("http://example.com", True, "Valid HTTP URL"),
        ("ftp://example.com", False, "Invalid FTP protocol"),
        ("https://localhost", False, "Localhost blocked"),
        ("https://127.0.0.1", False, "Local IP blocked"),
        ("not-a-url", False, "Invalid URL format"),
        ("", False, "Empty URL"),
    ]
    
    for url, expected, description in test_urls:
        result = parser._is_valid_url(url)
        status = "✅" if result == expected else "❌"
        print(f"{status} {description}: {url} -> {result}")
    
    parser.close()
    print()


def test_rate_limiting():
    """Test rate limiting functionality"""
    print("⏱️  Testing Rate Limiting")
    print("=" * 50)
    
    parser = WebPageParser()
    
    # Test rate limiting with same domain
    domain = "example.com"
    
    print(f"Testing rate limiting for domain: {domain}")
    
    import time
    start_time = time.time()
    
    # Should apply delay on second request
    parser._apply_rate_limit(domain)
    first_request_time = time.time()
    
    parser._apply_rate_limit(domain)
    second_request_time = time.time()
    
    delay = second_request_time - first_request_time
    print(f"Delay between requests: {delay:.2f} seconds")
    
    if delay >= 0.9:  # Should be close to 1 second delay
        print("✅ Rate limiting working correctly")
    else:
        print("❌ Rate limiting may not be working")
    
    parser.close()
    print()


def test_fetch_page():
    """Test page fetching functionality"""
    print("🌐 Testing Page Fetching")
    print("=" * 50)
    
    try:
        # Test with httpbin.org - a simple testing service
        test_url = "https://httpbin.org/html"
        result = fetch_web_page(test_url)
        
        if result and result.get('success'):
            print(f"✅ Successfully fetched: {test_url}")
            print(f"✅ Status code: {result['status_code']}")
            print(f"✅ Final URL: {result['final_url']}")
            print(f"✅ Content size: {result['content_size']} bytes")
            print(f"✅ Content type: {result['headers'].get('content-type', 'unknown')}")
            print(f"✅ Encoding: {result['encoding']}")
            
            # Check if we got HTML content
            content = result.get('content', '')
            if '<html' in content.lower() or '<body' in content.lower():
                print("✅ HTML content detected")
            else:
                print("⚠️  HTML content not detected")
            
            # Show first 100 characters of content
            content_preview = content[:100].replace('\n', ' ')
            print(f"✅ Content preview: '{content_preview}...'")
            
        else:
            print("❌ Failed to fetch live URL")
            
    except Exception as e:
        print(f"⚠️  Live URL test failed (this is okay if no internet): {e}")
    
    print()


def test_security_features():
    """Test security features"""
    print("🛡️  Testing Security Features")
    print("=" * 50)
    
    parser = WebPageParser()
    
    # Test dangerous TLD blocking
    dangerous_urls = [
        "https://malicious.tk",
        "https://spam.ml", 
        "https://bad.ga",
        "https://evil.cf"
    ]
    
    for url in dangerous_urls:
        is_valid = parser._is_valid_url(url)
        if not is_valid:
            print(f"✅ Blocked dangerous TLD: {url}")
        else:
            print(f"⚠️  Allowed potentially dangerous URL: {url}")
    
    # Test internal IP blocking
    internal_urls = [
        "https://192.168.1.1",
        "https://10.0.0.1", 
        "https://172.16.0.1"
    ]
    
    for url in internal_urls:
        is_valid = parser._is_valid_url(url)
        if not is_valid:
            print(f"✅ Blocked internal IP: {url}")
        else:
            print(f"❌ Failed to block internal IP: {url}")
    
    parser.close()
    print()


def test_error_handling():
    """Test error handling"""
    print("� Testing Error Handling")
    print("=" * 50)
    
    # Test with invalid URLs
    invalid_urls = [
        "https://thisdefinitelydoesnotexist12345.com",
        "https://httpbin.org/status/404",
        "https://httpbin.org/status/500"
    ]
    
    for url in invalid_urls:
        try:
            result = fetch_web_page(url)
            if result is None:
                print(f"✅ Properly handled invalid URL: {url}")
            else:
                print(f"⚠️  Got result for potentially invalid URL: {url} (status: {result.get('status_code')})")
        except Exception as e:
            print(f"✅ Exception properly caught for {url}: {e}")
    
    print()


def run_parser_tests():
    """Run all parser tests"""
    print("🚀 UNICORNER Search Engine - Parser Tests")
    print("=" * 50)
    print("Testing PURE PARSING functionality only")
    print("Content sanitization tested separately in test_sanitizer.py")
    print()
    
    test_url_validation()
    test_rate_limiting()
    test_fetch_page()
    test_security_features()
    test_error_handling()
    
    print("🎉 All parser tests completed!")
    print("=" * 50)


if __name__ == "__main__":
    run_parser_tests()
