"""
Content Sanitizer for Search Engine
Independent module for cleaning and sterilizing web content
Removes malicious code, scripts, and unsafe content
"""

import re
from bs4 import BeautifulSoup
from typing import Dict, Any, List
import html


class ContentSanitizer:
    """
    Independent content sanitizer for web scraping security
    Removes scripts, styles, and potentially malicious content
    """
    
    def __init__(self):
        """Initialize the sanitizer with security rules"""
        
        # Dangerous HTML tags to completely remove
        self.dangerous_tags = [
            'script', 'noscript', 'style', 'iframe', 'frame', 'frameset',
            'embed', 'object', 'applet', 'form', 'input', 'button',
            'textarea', 'select', 'option', 'meta', 'link', 'base'
        ]
        
        # Additional unwanted content tags (for better content extraction)
        self.unwanted_content_tags = [
            'nav', 'header', 'footer', 'aside', 'sidebar'
        ]
        
        # CSS selectors for unwanted content sections
        self.unwanted_selectors = [
            '.related-articles', '.related-content', '.related-stories',
            '.sidebar', '.footer', '.header', '.navigation', '.nav',
            '.comments', '.comment-section', '.social-sharing',
            '.advertisement', '.ads', '.ad-banner', '.promo',
            '.newsletter', '.signup', '.subscribe',
            '.tags', '.categories', '.breadcrumb',
            '.more-stories', '.trending', '.popular',
            '.recommended', '.you-might-like',
            '[data-module="RelatedTopics"]',
            '[data-module="MoreOnThisStory"]',
            '[data-module="RelatedContent"]',
            '.bbc-19j92fr',  # BBC specific classes that contain related content
            '.bbc-vj40wa',   # BBC specific sidebar classes
            # Wikipedia specific unwanted elements
            '#mw-navigation',  # Wikipedia navigation
            '.navbox',         # Wikipedia navigation boxes
            '.infobox',        # Wikipedia info boxes (keep them for now)
            '.catlinks',       # Wikipedia category links
            '#footer',         # Wikipedia footer
            '.printfooter'     # Wikipedia print footer
        ]
        
        # Dangerous attributes to remove from any tag
        self.dangerous_attributes = [
            'onclick', 'onload', 'onerror', 'onmouseover', 'onmouseout',
            'onfocus', 'onblur', 'onchange', 'onsubmit', 'onreset',
            'onselect', 'onkeydown', 'onkeyup', 'onkeypress',
            'javascript:', 'vbscript:', 'data:', 'file:'
        ]
        
        # Common UI and navigation patterns to remove
        self.ui_patterns = [
            r'\bClick\s+here\b',
            r'\bMore\s+info\b',
            r'\bRead\s+more\b',
            r'\bContinue\s+reading\b',
            r'\bMenu\b',
            r'\bNavigation\b',
            r'\bBreadcrumb\b',
            r'\bFooter\b',
            r'\bSidebar\b',
            r'\bAdvertisement\b',
            r'\bCookie\s+policy\b',
            r'\bPrivacy\s+policy\b',
            r'\bTerms\s+of\s+service\b',
            r'\bSign\s+in\b',
            r'\bLog\s+in\b',
            r'\bRegister\b',
            r'\bSubscribe\b',
            r'\bNewsletter\b',
            r'\bShare\s+this\b',
            r'\bFollow\s+us\b',
            r'\bLike\s+us\b',
            r'\bComments?\b',
            r'\bRelated\s+articles?\b'
        ]
    
    def sanitize_html(self, html_content: str, extract_links: bool = False) -> Dict[str, Any]:
        """
        Sanitize HTML content by removing dangerous elements
        
        Args:
            html_content: Raw HTML content to sanitize
            extract_links: Whether to extract all links from the page
            
        Returns:
            Dictionary with sanitized content and metadata
        """
        if not html_content or not html_content.strip():
            return self._empty_result("Empty or None content")

        try:
            # Parse HTML with BeautifulSoup
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Extract links before removing dangerous tags (if requested)
            links_data = self._extract_links(soup) if extract_links else None
            
            # Remove dangerous tags completely
            for tag_name in self.dangerous_tags:
                for tag in soup.find_all(tag_name):
                    tag.decompose()
            
            # Remove unwanted content sections
            self._remove_unwanted_content(soup)
            
            # Remove dangerous attributes
            self._remove_dangerous_attributes(soup)
            
            # Extract clean content
            result = self._extract_clean_content(soup)
            
            # Add links data if extracted
            if links_data:
                result['links'] = links_data
                result['total_links'] = len(links_data.get('all_links', []))
            else:
                result['links'] = None
                result['total_links'] = 0
            
            return result
            
        except Exception as e:
            return self._empty_result(f"HTML sanitization error: {str(e)}")
    
    def sanitize_text(self, text_content: str) -> Dict[str, Any]:
        """
        Sanitize plain text content
        
        Args:
            text_content: Plain text to sanitize
            
        Returns:
            Dictionary with sanitized text and metadata
        """
        if not text_content or not text_content.strip():
            return self._empty_result("Empty or None text")
        
        try:
            # HTML decode any entities
            decoded = html.unescape(text_content)
            
            # Remove UI patterns
            cleaned = self._remove_ui_patterns(decoded)
            
            # Normalize whitespace
            normalized = self._normalize_whitespace(cleaned)
            
            # Remove suspicious patterns
            safe_text = self._remove_suspicious_patterns(normalized)
            
            return {
                'content': safe_text,
                'word_count': len(safe_text.split()),
                'char_count': len(safe_text),
                'original_size': len(text_content),
                'reduction_percent': round((1 - len(safe_text) / len(text_content)) * 100, 1),
                'sanitized': True,
                'error': None
            }
            
        except Exception as e:
            return self._empty_result(f"Text sanitization error: {str(e)}")
    
    def _remove_unwanted_content(self, soup: BeautifulSoup):
        """Remove unwanted content sections like ads, related articles, navigation"""
        
        # First, check if this is a Wikipedia page
        is_wikipedia = 'wikipedia.org' in str(soup) or soup.find('body', class_=re.compile(r'mediawiki', re.I))
        
        # For Wikipedia, be more conservative - only remove specific navigation elements
        if is_wikipedia:
            # Remove Wikipedia-specific navigation and UI elements
            wikipedia_unwanted = [
                '#mw-navigation', '.navbox', '.catlinks', '#footer', 
                '.printfooter', '#mw-head', '#mw-panel', '#p-logo',
                '.mw-editsection', '.mw-cite-backlink', '#mw-head-base',
                '#mw-page-base', '.mw-body-header', '.mw-indicators',
                '#siteSub', '#contentSub', '#jump-to-nav', 
                '.language-list', '#p-lang', '.vector-menu',
                '.mw-empty-elt', '.navbox-inner', '.hatnote'
            ]
            
            for selector in wikipedia_unwanted:
                try:
                    for element in soup.select(selector):
                        element.decompose()
                except Exception:
                    continue
            
            # Remove specific Wikipedia elements by tag and attribute
            # Remove language links sections
            for element in soup.find_all('div', class_=re.compile(r'lang|language', re.I)):
                if 'language' in element.get_text().lower():
                    element.decompose()
            
            # Remove "Toggle" elements
            for element in soup.find_all(text=re.compile(r'Toggle|Edit links', re.I)):
                parent = element.parent
                if parent:
                    parent.decompose()
            
            # Don't apply aggressive filtering to Wikipedia
            return
        
        # For non-Wikipedia sites, apply selective filtering
        
        # Remove unwanted content tags (but be selective)
        selective_unwanted_tags = ['nav', 'footer', 'aside']  # Don't remove header as it may contain article content
        for tag_name in selective_unwanted_tags:
            for tag in soup.find_all(tag_name):
                tag.decompose()
        
        # Remove elements by CSS selectors (only the most obvious ones)
        obvious_unwanted_selectors = [
            '.footer', '.navigation', '.nav', '.sidebar',
            '.comments', '.comment-section', '.social-sharing',
            '.advertisement', '.ads', '.ad-banner', 
            '.newsletter', '.signup', '.subscribe',
            '.breadcrumb', '.catlinks', '.printfooter'
        ]
        
        for selector in obvious_unwanted_selectors:
            try:
                for element in soup.select(selector):
                    element.decompose()
            except Exception:
                continue
        
        # Only remove elements with very obvious unwanted patterns
        obvious_unwanted_patterns = [r'footer', r'sidebar', r'nav-', r'comment', r'social-share']
        
        for pattern in obvious_unwanted_patterns:
            for element in soup.find_all(class_=re.compile(pattern, re.I)):
                element.decompose()
            for element in soup.find_all(id=re.compile(pattern, re.I)):
                element.decompose()

    def _remove_dangerous_attributes(self, soup: BeautifulSoup):
        """Remove dangerous attributes from all tags"""
        for tag in soup.find_all():
            if tag.attrs:
                # Get list of attributes to remove
                attrs_to_remove = []
                for attr_name, attr_value in tag.attrs.items():
                    # Check attribute name
                    if any(dangerous in attr_name.lower() for dangerous in self.dangerous_attributes):
                        attrs_to_remove.append(attr_name)
                    # Check attribute value
                    elif isinstance(attr_value, str) and any(dangerous in attr_value.lower() for dangerous in self.dangerous_attributes):
                        attrs_to_remove.append(attr_name)
                
                # Remove dangerous attributes
                for attr in attrs_to_remove:
                    del tag.attrs[attr]
    
    def _extract_clean_content(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Extract clean content from sanitized soup with better structure preservation"""
        
        # Extract title
        title_tag = soup.find('title')
        title = title_tag.get_text().strip() if title_tag else ""
        
        # Extract meta description
        meta_desc = soup.find('meta', attrs={'name': 'description'})
        description = meta_desc.get('content', '').strip() if meta_desc else ""
        
        # Try to find main content area
        main_content = self._find_main_content(soup)
        
        # Extract structured text from main content
        if main_content:
            content_text = self._extract_structured_text(main_content)
        else:
            # Fallback to body or entire document
            body = soup.find('body') or soup
            content_text = self._extract_structured_text(body)
        
        # Clean the extracted text while preserving structure
        cleaned_content = self._clean_structured_text(content_text)
        
        return {
            'title': self._sanitize_text_field(title),
            'description': self._sanitize_text_field(description),
            'content': cleaned_content,
            'word_count': len(cleaned_content.split()),
            'char_count': len(cleaned_content),
            'sanitized': True,
            'error': None
        }
    
    def _find_main_content(self, soup: BeautifulSoup):
        """Find the main content area of the page"""
        # Priority list of selectors for main content
        content_selectors = [
            'main',
            'article', 
            '[role="main"]',
            '.content',
            '#content',
            '.post',
            '.entry',
            '.article-body',
            '.post-content',
            '.entry-content',
            '#mw-content-text',  # Wikipedia main content
            '.mw-parser-output',  # Wikipedia article content
            '#bodyContent'       # Wikipedia body content
        ]
        
        for selector in content_selectors:
            main_content = soup.select_one(selector)
            if main_content:
                return main_content
        
        return None
    
    def _remove_ui_patterns(self, text: str) -> str:
        """Remove common UI and navigation patterns"""
        for pattern in self.ui_patterns:
            text = re.sub(pattern, '', text, flags=re.IGNORECASE)
        return text
    
    def _normalize_whitespace(self, text: str) -> str:
        """Normalize whitespace while preserving some structure"""
        if not text:
            return ""
        
        # Replace multiple spaces with single space
        text = re.sub(r' +', ' ', text)
        
        # Normalize line breaks (preserve up to 2 consecutive line breaks)
        text = re.sub(r'\n\s*\n\s*\n+', '\n\n', text)
        
        # Remove leading/trailing whitespace from each line
        lines = text.split('\n')
        lines = [line.strip() for line in lines]
        
        # Remove empty lines but preserve double line breaks for paragraphs
        result_lines = []
        prev_empty = False
        
        for line in lines:
            if line:
                result_lines.append(line)
                prev_empty = False
            elif not prev_empty and result_lines:
                result_lines.append('')
                prev_empty = True
        
        return '\n'.join(result_lines).strip()

    def _extract_structured_text(self, element) -> str:
        """Extract text while preserving structure and hierarchy"""
        if not element:
            return ""
        
        def get_text_with_spacing(elem):
            """Get text from element with proper spacing between inline elements"""
            text_parts = []
            for item in elem.children:
                if item.name is None:  # Text node
                    text = str(item).strip()
                    if text:
                        text_parts.append(text)
                else:  # HTML element
                    # Add space before inline elements
                    if item.name in ['a', 'span', 'button', 'strong', 'em', 'b', 'i']:
                        item_text = item.get_text(strip=True)
                        if item_text:
                            text_parts.append(f" {item_text} ")
                    else:
                        item_text = item.get_text(strip=True)
                        if item_text:
                            text_parts.append(item_text)
            
            # Join and clean up extra spaces
            result = ''.join(text_parts)
            result = ' '.join(result.split())  # Normalize whitespace
            return result
        
        text_parts = []
        processed_elements = set()
        
        # Process elements in document order, avoiding duplicates
        for child in element.find_all(True):
            if child in processed_elements:
                continue
                
            if child.name in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
                # Headers - add extra spacing and structure
                header_text = get_text_with_spacing(child)
                if header_text:
                    text_parts.append(f"\n\n## {header_text} ##\n")
                processed_elements.add(child)
            
            elif child.name == 'p':
                # Paragraphs - ensure proper spacing
                para_text = get_text_with_spacing(child)
                if para_text:
                    text_parts.append(f"\n{para_text}\n")
                processed_elements.add(child)
            
            elif child.name in ['ul', 'ol']:
                # Lists - preserve structure
                list_items = child.find_all('li', recursive=False)
                if list_items:
                    text_parts.append("\n")
                    for i, li in enumerate(list_items):
                        item_text = get_text_with_spacing(li)
                        if item_text:
                            prefix = f"{i+1}. " if child.name == 'ol' else "• "
                            text_parts.append(f"{prefix}{item_text}\n")
                        processed_elements.add(li)
                    text_parts.append("\n")
                processed_elements.add(child)
            
            elif child.name in ['nav', 'header', 'footer']:
                # Navigation and structural elements - preserve with labels and proper spacing
                nav_links = []
                seen_texts = set()  # Avoid duplicates
                
                for link in child.find_all(['a', 'button', 'span']):
                    link_text = link.get_text(strip=True)
                    # Clean up common UI text
                    if link_text and len(link_text) > 0:
                        # Remove common noise like "(opens in a new tab)"
                        clean_text = link_text.replace('(opens in a new tab)', '').strip()
                        if clean_text and clean_text not in seen_texts and len(clean_text) > 1:
                            nav_links.append(clean_text)
                            seen_texts.add(clean_text)
                            processed_elements.add(link)
                
                if nav_links:
                    section_name = child.name.upper()
                    nav_text = ' | '.join(nav_links)  # Separate nav items with |
                    text_parts.append(f"\n[{section_name}]\n{nav_text}\n[/{section_name}]\n")
                processed_elements.add(child)
            
            elif child.name == 'div' and child.get('class'):
                # Div with classes might indicate content sections
                classes = ' '.join(child.get('class', []))
                if any(keyword in classes.lower() for keyword in ['content', 'main', 'article', 'post']):
                    div_text = get_text_with_spacing(child)
                    if div_text and len(div_text) > 50:  # Only significant content
                        text_parts.append(f"\n{div_text}\n")
                    processed_elements.add(child)
            
            elif child.name in ['section', 'article']:
                # Content sections
                section_text = get_text_with_spacing(child)
                if section_text and len(section_text) > 30:
                    text_parts.append(f"\n{section_text}\n")
                processed_elements.add(child)
        
        return ''.join(text_parts)

    def _clean_structured_text(self, text: str) -> str:
        """Clean text while preserving structure"""
        if not text:
            return ""
        
        # Remove UI patterns but preserve structure
        cleaned = self._remove_ui_patterns(text)
        
        # Normalize whitespace while preserving structure
        normalized = self._normalize_whitespace(cleaned)
        
        # Remove suspicious patterns
        safe_text = self._remove_suspicious_patterns(normalized)
        
        # Final cleanup - remove excessive empty lines
        lines = safe_text.split('\n')
        result_lines = []
        empty_count = 0
        
        for line in lines:
            if line.strip():
                result_lines.append(line)
                empty_count = 0
            else:
                empty_count += 1
                if empty_count <= 2:  # Allow max 2 consecutive empty lines
                    result_lines.append(line)
        
        return '\n'.join(result_lines).strip()
    
    def _remove_suspicious_patterns(self, text: str) -> str:
        """Remove potentially suspicious or malicious text patterns while preserving structure"""
        
        # Remove common suspicious patterns but be more conservative
        suspicious_patterns = [
            r'javascript:\s*[\w\(\)]+',  # JavaScript protocols
            r'data:[\w/]+;base64,[\w+/=]+',  # Base64 data URLs
            r'<script[^>]*>.*?</script>',  # Any remaining script tags
            r'<style[^>]*>.*?</style>',  # Any remaining style tags
            r'&[a-zA-Z0-9]+;',  # HTML entities (most should be decoded already)
        ]
        
        for pattern in suspicious_patterns:
            text = re.sub(pattern, ' ', text, flags=re.IGNORECASE | re.DOTALL)
        
        # Remove excessive repeated characters (potential spam/malicious content)
        text = re.sub(r'(.)\1{10,}', r'\1\1\1', text)  # Limit repeated chars to 3
        
        # Final light cleanup - preserve structure
        text = re.sub(r'[ \t]+', ' ', text)  # Multiple spaces/tabs to single space
        
        return text.strip()
    
    def _extract_links(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Extract all links from the page for PageRank analysis"""
        links_data = {
            'all_links': [],
            'internal_links': [],
            'external_links': [],
            'navigation_links': [],
            'content_links': [],
            'social_links': [],
            'email_links': [],
            'file_links': []
        }
        
        try:
            # Find all anchor tags with href attributes
            all_anchors = soup.find_all('a', href=True)
            
            for anchor in all_anchors:
                href = anchor.get('href', '').strip()
                text = anchor.get_text(strip=True)
                title = anchor.get('title', '').strip()
                
                if not href or href.startswith('#'):  # Skip empty links and fragments
                    continue
                
                # Create link object
                link_obj = {
                    'url': href,
                    'text': text,
                    'title': title,
                    'type': self._classify_link(href, anchor)
                }
                
                # Add to all links
                links_data['all_links'].append(link_obj)
                
                # Classify and categorize links
                link_type = link_obj['type']
                
                if link_type == 'internal':
                    links_data['internal_links'].append(link_obj)
                elif link_type == 'external':
                    links_data['external_links'].append(link_obj)
                elif link_type == 'email':
                    links_data['email_links'].append(link_obj)
                elif link_type == 'file':
                    links_data['file_links'].append(link_obj)
                elif link_type == 'social':
                    links_data['social_links'].append(link_obj)
                
                # Check if it's in navigation area
                if anchor.find_parent(['nav', 'header', 'footer']):
                    links_data['navigation_links'].append(link_obj)
                else:
                    links_data['content_links'].append(link_obj)
            
            # Add summary statistics
            links_data['stats'] = {
                'total': len(links_data['all_links']),
                'internal': len(links_data['internal_links']),
                'external': len(links_data['external_links']),
                'navigation': len(links_data['navigation_links']),
                'content': len(links_data['content_links']),
                'social': len(links_data['social_links']),
                'email': len(links_data['email_links']),
                'file': len(links_data['file_links'])
            }
            
        except Exception as e:
            links_data['error'] = f"Link extraction error: {str(e)}"
        
        return links_data
    
    def _classify_link(self, href: str, anchor_tag) -> str:
        """Classify a link by its type"""
        href_lower = href.lower()
        
        # Email links
        if href_lower.startswith('mailto:'):
            return 'email'
        
        # File links
        file_extensions = ['.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx', 
                          '.zip', '.rar', '.mp3', '.mp4', '.avi', '.jpg', '.png', '.gif']
        if any(href_lower.endswith(ext) for ext in file_extensions):
            return 'file'
        
        # Social media links
        social_domains = ['facebook.com', 'twitter.com', 'instagram.com', 'linkedin.com', 
                         'youtube.com', 'tiktok.com', 'pinterest.com', 'snapchat.com',
                         'whatsapp.com', 'telegram.org']
        if any(domain in href_lower for domain in social_domains):
            return 'social'
        
        # Protocol-based classification
        if href_lower.startswith(('http://', 'https://')):
            return 'external'
        elif href_lower.startswith('/') or not any(char in href for char in [':', '//']):
            return 'internal'
        else:
            return 'unknown'

    def _sanitize_text_field(self, text: str) -> str:
        """Sanitize individual text fields like title, description"""
        if not text:
            return ""
        
        # HTML decode
        decoded = html.unescape(text)
        # Remove any HTML tags
        no_html = re.sub(r'<[^>]*>', '', decoded)
        # Normalize whitespace
        normalized = re.sub(r'\s+', ' ', no_html).strip()
        # Remove suspicious characters
        safe = re.sub(r'[^\w\s\.,!?;:\(\)\-\'\"]+', '', normalized)
        
        return safe
    
    def _empty_result(self, error_msg: str) -> Dict[str, Any]:
        """Return empty result with error message"""
        return {
            'title': "",
            'description': "",
            'content': "",
            'word_count': 0,
            'char_count': 0,
            'original_size': 0,
            'reduction_percent': 0,
            'sanitized': False,
            'error': error_msg
        }
    
    def get_security_report(self, original_content: str, sanitized_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate a security report of what was sanitized
        
        Args:
            original_content: Original content before sanitization
            sanitized_result: Result from sanitization
            
        Returns:
            Security report with statistics
        """
        if not sanitized_result.get('sanitized'):
            return {'error': 'Content was not successfully sanitized'}
        
        original_size = len(original_content)
        final_size = sanitized_result.get('char_count', 0)
        
        # Count dangerous elements removed
        dangerous_count = 0
        for tag in self.dangerous_tags:
            dangerous_count += original_content.lower().count(f'<{tag}')
        
        return {
            'original_size_bytes': original_size,
            'final_size_bytes': final_size,
            'size_reduction_percent': round((1 - final_size / original_size) * 100, 1) if original_size > 0 else 0,
            'dangerous_tags_removed': dangerous_count,
            'security_threats_found': dangerous_count > 0,
            'sanitization_successful': True
        }


# Convenience function for simple usage
def sanitize_web_content(html_content: str, extract_links: bool = False) -> Dict[str, Any]:
    """
    Simple function to sanitize HTML content
    
    Args:
        html_content: HTML content to sanitize
        extract_links: Whether to extract links for PageRank analysis
        
    Returns:
        Sanitized content dictionary
    """
    sanitizer = ContentSanitizer()
    return sanitizer.sanitize_html(html_content, extract_links=extract_links)


def sanitize_text_content(text_content: str) -> Dict[str, Any]:
    """
    Simple function to sanitize text content
    
    Args:
        text_content: Text content to sanitize
        
    Returns:
        Sanitized text dictionary
    """
    sanitizer = ContentSanitizer()
    return sanitizer.sanitize_text(text_content)


if __name__ == "__main__":
    # Test the sanitizer
    test_html = """
    <html>
    <head>
        <title>Test Page</title>
        <script>alert('malicious');</script>
    </head>
    <body>
        <h1 onclick="hack()">Safe Title</h1>
        <p>This is safe content.</p>
        <script>steal_data();</script>
        <iframe src="malicious.com"></iframe>
    </body>
    </html>
    """
    
    result = sanitize_web_content(test_html)
    
    print("🧹 Content Sanitizer Test")
    print("=" * 40)
    print(f"Title: '{result['title']}'")
    print(f"Content: '{result['content']}'")
    print(f"Sanitized: {result['sanitized']}")
    print(f"Original size: {result['original_size']} bytes")
    print(f"Final size: {result['char_count']} bytes")
    if result['original_size'] > 0:
        reduction = (1 - result['char_count'] / result['original_size']) * 100
        print(f"Size reduction: {reduction:.1f}%")
