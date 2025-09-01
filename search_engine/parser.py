"""
Web Page Parser for Search Engine
Independent module for fetching web pages
Pure parsing - no content sanitization (handled by sanitizer.py)
"""

import requests
import re
import time
from urllib.parse import urljoin, urlparse
from typing import Optional, Dict, Any
from collections import defaultdict


class WebPageParser:
    """
    Web page parser that fetches URLs only
    Pure parsing - content sanitization handled by sanitizer.py
    """
    
    # Class-level rate limiting tracking
    _request_times = defaultdict(list)
    _min_delay = 1.0  # Minimum delay between requests to same domain
    
    def __init__(self, timeout: int = 10, max_retries: int = 3, max_content_size: int = 10485760):
        """
        Initialize the parser with configuration
        
        Args:
            timeout: Request timeout in seconds
            max_retries: Maximum retry attempts for failed requests
            max_content_size: Maximum content size in bytes (default 10MB)
        """
        self.timeout = timeout
        self.max_retries = max_retries
        self.max_content_size = max_content_size
        self.session = requests.Session()
        
        # Set user agent to appear as a regular browser
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        
        # Security: Set maximum redirects
        self.session.max_redirects = 5
    
    def fetch_page(self, url: str) -> Optional[Dict[str, Any]]:
        """
        Fetch a web page and return raw content with metadata
        
        Args:
            url: The URL to fetch
            
        Returns:
            Dictionary with page content and metadata, or None if failed
        """
        if not self._is_valid_url(url):
            return None
        
        # Security: Rate limiting per domain
        domain = urlparse(url).netloc
        self._apply_rate_limit(domain)
        
        for attempt in range(self.max_retries):
            try:
                # Security: Stream the response to check size first
                response = self.session.get(url, timeout=self.timeout, stream=True)
                response.raise_for_status()
                
                # Security: Check content length
                content_length = response.headers.get('content-length')
                if content_length and int(content_length) > self.max_content_size:
                    print(f"Content too large: {content_length} bytes (max: {self.max_content_size})")
                    return None
                
                # Security: Read content with size limit
                content = ""
                downloaded = 0
                for chunk in response.iter_content(chunk_size=8192, decode_unicode=True):
                    if chunk:
                        downloaded += len(chunk.encode('utf-8'))
                        if downloaded > self.max_content_size:
                            print(f"Content size exceeded limit during download: {downloaded} bytes")
                            return None
                        content += chunk
                
                return {
                    'url': url,
                    'status_code': response.status_code,
                    'content': content,
                    'headers': dict(response.headers),
                    'encoding': response.encoding,
                    'final_url': response.url,  # In case of redirects
                    'fetch_time': time.time(),
                    'content_size': len(content.encode('utf-8'))
                }
                
            except requests.exceptions.RequestException as e:
                print(f"Attempt {attempt + 1} failed for {url}: {str(e)}")
                if attempt == self.max_retries - 1:
                    return None
                time.sleep(1)  # Brief delay before retry
        
        return None
    
    def parse_url(self, url: str) -> Optional[Dict[str, Any]]:
        """
        Fetch URL and return raw content (no content processing)
        Content sanitization should be done separately with sanitizer.py
        
        Args:
            url: The URL to parse
            
        Returns:
            Dictionary with raw page data or None if failed
        """
        # Fetch the page
        page_data = self.fetch_page(url)
        if not page_data:
            return None
        
        # Add success flag
        page_data['success'] = True
        
        return page_data
    
    def _is_valid_url(self, url: str) -> bool:
        """
        Validate URL format and security
        
        Args:
            url: URL to validate
            
        Returns:
            True if URL is valid and safe
        """
        try:
            parsed = urlparse(url)
            
            # Must have scheme and netloc
            if not parsed.scheme or not parsed.netloc:
                return False
            
            # Only allow HTTP and HTTPS
            if parsed.scheme not in ['http', 'https']:
                return False
            
            # Block localhost and internal IPs for security
            blocked_hosts = ['localhost', '127.0.0.1', '0.0.0.0', '10.', '192.168.', '172.']
            netloc_lower = parsed.netloc.lower()
            
            # Check for blocked hosts and internal IP ranges
            for blocked in blocked_hosts:
                if netloc_lower.startswith(blocked) or blocked in netloc_lower:
                    return False
            
            # Block common dangerous TLDs (optional - can be removed if too restrictive)
            dangerous_tlds = ['.tk', '.ml', '.ga', '.cf']  # Known for malicious content
            for tld in dangerous_tlds:
                if netloc_lower.endswith(tld):
                    print(f"Blocked potentially dangerous TLD: {tld}")
                    return False
            
            return True
            
        except Exception:
            return False
    
    def _apply_rate_limit(self, domain: str):
        """
        Apply rate limiting per domain to be respectful
        
        Args:
            domain: Domain to apply rate limiting to
        """
        now = time.time()
        domain_requests = self._request_times[domain]
        
        # Clean old requests (older than 60 seconds)
        domain_requests[:] = [req_time for req_time in domain_requests if now - req_time < 60]
        
        # Check if we need to wait
        if domain_requests:
            last_request = max(domain_requests)
            time_since_last = now - last_request
            
            if time_since_last < self._min_delay:
                sleep_time = self._min_delay - time_since_last
                print(f"Rate limiting: waiting {sleep_time:.1f}s for {domain}")
                time.sleep(sleep_time)
        
        # Record this request
        domain_requests.append(time.time())
    
    def close(self):
        """Close the session"""
        self.session.close()


# Convenience function for simple usage
def fetch_web_page(url: str) -> Optional[Dict[str, Any]]:
    """
    Simple function to fetch a web page (no content processing)
    Use with sanitizer.py for content cleaning
    
    Args:
        url: The URL to fetch
        
    Returns:
        Raw page data or None if failed
    """
    parser = WebPageParser()
    try:
        return parser.parse_url(url)
    finally:
        parser.close()


if __name__ == "__main__":
    # Test the parser
    test_url = "https://httpbin.org/html"
    result = fetch_web_page(test_url)
    
    if result:
        print(f"Successfully fetched: {result['final_url']}")
        print(f"Status code: {result['status_code']}")
        print(f"Content size: {result['content_size']} bytes")
        print(f"Content type: {result['headers'].get('content-type', 'unknown')}")
        print("\nFirst 200 characters of raw content:")
        content = result.get('content', '')
        print(content[:200] + "..." if len(content) > 200 else content)
    else:
        print("Failed to fetch the URL")
