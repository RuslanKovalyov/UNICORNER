"""
Interactive Web Page Text Extractor
Test parser + sanitizer with manual URL input
Run with: python interactive_test.py
"""

import sys
import os

# Add the parent directory to the path so we can import modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from parser import fetch_web_page
from sanitizer import sanitize_web_content


def display_separator(title=""):
    """Display a nice separator line"""
    if title:
        print(f"\n{'='*20} {title} {'='*20}")
    else:
        print("="*60)


def display_results(url, raw_data, clean_data):
    """Display comprehensive results"""
    
    display_separator("PARSING RESULTS")
    print(f"🔍 URL: {url}")
    print(f"📊 Status: {raw_data.get('status_code', 'Unknown')}")
    print(f"🌐 Final URL: {raw_data.get('final_url', 'Unknown')}")
    print(f"📏 Raw size: {raw_data.get('content_size', 0):,} bytes")
    print(f"🔤 Encoding: {raw_data.get('encoding', 'Unknown')}")
    print(f"📄 Content type: {raw_data.get('headers', {}).get('content-type', 'Unknown')}")
    
    display_separator("SANITIZATION RESULTS")
    print(f"🧹 Title: '{clean_data.get('title', 'No title')}'")
    print(f"📝 Description: '{clean_data.get('description', 'No description')}'")
    print(f"📊 Clean size: {clean_data.get('char_count', 0):,} characters")
    print(f"📖 Word count: {clean_data.get('word_count', 0):,} words")
    print(f"✅ Sanitized: {clean_data.get('sanitized', False)}")
    
    # Calculate reduction percentage
    original_size = raw_data.get('content_size', 0)
    final_size = clean_data.get('char_count', 0)
    if original_size > 0:
        reduction = (1 - final_size / original_size) * 100
        print(f"📉 Size reduction: {reduction:.1f}%")
    
    # Display links analysis if available
    if clean_data.get('links'):
        display_links_analysis(clean_data)
    
    display_separator("CLEAN TEXT CONTENT")
    content = clean_data.get('content', '')
    if content:
        print(content)
    else:
        print("❌ No clean content extracted")


def display_links_analysis(clean_data):
    """Display link analysis results"""
    links_data = clean_data.get('links')
    if not links_data:
        return
    
    display_separator("LINKS ANALYSIS")
    
    stats = links_data.get('stats', {})
    print(f"🔗 Total Links: {stats.get('total', 0)}")
    print(f"🏠 Internal: {stats.get('internal', 0)}")
    print(f"🌐 External: {stats.get('external', 0)}")
    print(f"🧭 Navigation: {stats.get('navigation', 0)}")
    print(f"📄 Content: {stats.get('content', 0)}")
    print(f"📱 Social: {stats.get('social', 0)}")
    print(f"📧 Email: {stats.get('email', 0)}")
    print(f"📁 File: {stats.get('file', 0)}")
    
    # Show some example links
    all_links = links_data.get('all_links', [])
    if all_links:
        print(f"\n📋 Sample Links (showing up to 10):")
        for i, link in enumerate(all_links[:10]):
            link_type = link.get('type', 'unknown')
            url = link.get('url', '')
            text = link.get('text', '')
            if len(text) > 50:
                text = text[:47] + '...'
            print(f"  {i+1}. [{link_type}] {url}")
            if text:
                print(f"     Text: '{text}'")
    
    # Show social media links if any
    social_links = links_data.get('social_links', [])
    if social_links:
        print(f"\n📱 Social Media Links:")
        for link in social_links:
            print(f"  • {link.get('url', '')}")
    
    # Show external domains
    external_links = links_data.get('external_links', [])
    if external_links:
        domains = set()
        for link in external_links:
            url = link.get('url', '')
            if url.startswith(('http://', 'https://')):
                try:
                    from urllib.parse import urlparse
                    domain = urlparse(url).netloc
                    domains.add(domain)
                except:
                    pass
        
        if domains:
            print(f"\n🌍 External Domains ({len(domains)}):")
            for domain in sorted(list(domains)[:10]):  # Show up to 10 domains
                print(f"  • {domain}")
            if len(domains) > 10:
                print(f"  ... and {len(domains) - 10} more")
    
    display_separator()


def process_url(url):
    """Process a single URL through parser and sanitizer"""
    
    print(f"\n🚀 Processing: {url}")
    print("⏳ Fetching page...")
    
    # Step 1: Parse the URL
    try:
        raw_data = fetch_web_page(url)
        
        if not raw_data or not raw_data.get('success'):
            print(f"❌ Failed to fetch URL: {url}")
            return False
            
        print(f"✅ Successfully fetched {raw_data.get('content_size', 0):,} bytes")
        
    except Exception as e:
        print(f"❌ Parser error: {e}")
        return False
    
    # Step 2: Sanitize the content and extract links
    print("🧹 Sanitizing content and extracting links...")
    
    try:
        clean_data = sanitize_web_content(raw_data['content'], extract_links=True)
        
        if not clean_data.get('sanitized'):
            print(f"❌ Failed to sanitize content: {clean_data.get('error', 'Unknown error')}")
            return False
            
        char_count = clean_data.get('char_count', 0)
        link_count = clean_data.get('total_links', 0)
        print(f"✅ Successfully sanitized to {char_count:,} characters and found {link_count} links")
        
    except Exception as e:
        print(f"❌ Sanitizer error: {e}")
        return False
    
    # Step 3: Display results
    display_results(url, raw_data, clean_data)
    
    return True


def interactive_mode():
    """Run in interactive mode"""
    
    print("🚀 UNICORNER Search Engine - Interactive Text Extractor")
    print("=" * 60)
    print("📝 Enter URLs to see clean text extraction")
    print("💡 Uses parser.py (fetching) + sanitizer.py (cleaning)")
    print("🚪 Type 'quit' or 'exit' to stop")
    print("📖 Type 'help' for examples")
    
    while True:
        try:
            print("\n" + "-" * 40)
            url = input("🔗 Enter URL: ").strip()
            
            if not url:
                continue
                
            if url.lower() in ['quit', 'exit', 'q']:
                print("👋 Goodbye!")
                break
                
            if url.lower() in ['help', 'h']:
                show_help()
                continue
            
            # Add protocol if missing
            if not url.startswith(('http://', 'https://')):
                url = 'https://' + url
                print(f"🔧 Added HTTPS protocol: {url}")
            
            # Process the URL
            success = process_url(url)
            
            if success:
                print("\n✅ Processing completed successfully!")
            else:
                print("\n❌ Processing failed!")
                
        except KeyboardInterrupt:
            print("\n\n👋 Interrupted by user. Goodbye!")
            break
        except Exception as e:
            print(f"\n❌ Unexpected error: {e}")


def batch_mode(urls):
    """Process multiple URLs in batch"""
    
    print("🚀 UNICORNER Search Engine - Batch Text Extractor")
    print("=" * 60)
    print(f"📝 Processing {len(urls)} URLs")
    
    for i, url in enumerate(urls, 1):
        print(f"\n📍 Processing {i}/{len(urls)}")
        
        # Add protocol if missing
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
        
        success = process_url(url)
        
        if success:
            print(f"✅ URL {i} completed")
        else:
            print(f"❌ URL {i} failed")
        
        # Ask if user wants to continue (except for last URL)
        if i < len(urls):
            try:
                continue_choice = input("\n⏯️  Continue to next URL? (y/n): ").strip().lower()
                if continue_choice in ['n', 'no']:
                    print("🛑 Batch processing stopped by user")
                    break
            except KeyboardInterrupt:
                print("\n🛑 Batch processing interrupted")
                break
    
    print("\n🎉 Batch processing completed!")


def show_help():
    """Show help and examples"""
    
    print("\n📖 HELP - Example URLs to try:")
    print("-" * 40)
    print("🌐 News sites:")
    print("   • bbc.com/news")
    print("   • reuters.com")
    print("   • techcrunch.com")
    print("")
    print("📚 Documentation:")
    print("   • docs.python.org")
    print("   • github.com/microsoft/vscode")
    print("")
    print("🧪 Test sites:")
    print("   • httpbin.org/html")
    print("   • example.com")
    print("")
    print("⚠️  Note: Some sites may block automated requests")
    print("🔒 All content is safely sanitized before display")


def main():
    """Main function"""
    
    # Check command line arguments
    if len(sys.argv) > 1:
        # Batch mode with URLs from command line
        urls = sys.argv[1:]
        batch_mode(urls)
    else:
        # Interactive mode
        interactive_mode()


if __name__ == "__main__":
    main()
