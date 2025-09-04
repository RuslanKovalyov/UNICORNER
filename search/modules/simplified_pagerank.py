"""
Super Simplified PageRank Module
================================

This module implements a domain-level PageRank algorithm that:
1. Scans websites to extract UNIQUE external domains (no duplicates per source domain)
2. Stores only domain names with ranking counts in database
3. Processes domains one by one in infinite loop
4. Prevents duplicate counting: each external domain counted only ONCE per source domain
5. Prevents duplicate crawling: each internal URL visited only ONCE per domain crawl

Database: Only 3 columns - domain, rank, processed
RAM: Temporary storage of internal/external links during processing (with deduplication)
Logic: External domains from any pages boost target domain rank by +1 (not +1 per link occurrence)
Optimization: Uses SETs to prevent duplicates in both external domains and internal URL queue
"""

import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import time
import logging
from typing import Set, List, Tuple
from django.db import transaction
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
from search.models import DomainRank


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Thread-safe lock for database operations
db_lock = threading.Lock()


class SimplifiedPageRank:
    """
    Super simplified PageRank that only tracks domain-level external links
    """
    
    def __init__(self, max_depth: int = 3, delay: float = 0.1, max_pages_per_domain: int = 50, max_workers: int = 4):
        """
        Initialize the simplified PageRank crawler
        
        Args:
            max_depth: How deep to crawl within each domain for finding external links
            delay: Delay between requests in seconds (default: 0.1 = 100ms)
            max_pages_per_domain: Maximum pages to crawl per domain to avoid infinite loops
            max_workers: Number of concurrent threads for parallel processing
        """
        self.max_depth = max_depth
        self.delay = delay
        self.max_pages_per_domain = max_pages_per_domain
        self.max_workers = max_workers
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (compatible; SimplifiedPageRank/1.0; +http://unicorner.coffee/search)'
        })
    
    def extract_domain(self, url: str) -> str:
        """Extract clean domain from URL (no protocol, no path)"""
        try:
            parsed = urlparse(url if url.startswith(('http://', 'https://')) else f'http://{url}')
            domain = parsed.netloc.lower()
            # Remove www. prefix for consistency
            if domain.startswith('www.'):
                domain = domain[4:]
            return domain
        except Exception:
            return ""
    
    def fetch_page_links(self, url: str) -> Set[str]:
        """
        Fetch only meaningful external links from a single page
        Filters out CSS, JS, images, and other non-content links
        Returns set of absolute URLs pointing to OTHER domains only
        """
        try:
            logger.info(f"🔍 Fetching: {url}")
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            links = set()
            current_domain = self.extract_domain(url)
            
            # Extract only meaningful href links from content areas
            for link in soup.find_all('a', href=True):
                href = link.get('href', '').strip()
                
                # Skip empty hrefs
                if not href:
                    continue
                
                # Skip non-HTTP links (mailto, tel, javascript, etc.)
                if href.startswith(('mailto:', 'tel:', 'javascript:', '#', 'data:')):
                    continue
                
                # Convert to absolute URL
                absolute_url = urljoin(url, href)
                
                # Only keep HTTP/HTTPS URLs
                if not absolute_url.startswith(('http://', 'https://')):
                    continue
                
                # Extract domain from this link
                link_domain = self.extract_domain(absolute_url)
                
                # Skip if no domain or same domain (internal link)
                if not link_domain or link_domain == current_domain:
                    continue
                
                # Skip common non-content file extensions
                if any(absolute_url.lower().endswith(ext) for ext in [
                    '.css', '.js', '.png', '.jpg', '.jpeg', '.gif', '.svg', '.ico',
                    '.pdf', '.zip', '.rar', '.exe', '.dmg', '.mp4', '.mp3', '.avi'
                ]):
                    continue
                
                # This is an external content link - add it
                links.add(absolute_url)
            
            logger.info(f"✅ Found {len(links)} external links on {url}")
            return links
            
        except Exception as e:
            logger.warning(f"❌ Failed to fetch {url}: {str(e)[:100]}")
            return set()
    
    def fetch_internal_links(self, url: str, domain: str) -> Set[str]:
        """
        Fetch only internal links from a page for navigation within domain
        Used only to discover more pages within the same domain
        """
        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            internal_links = set()
            
            # Extract only internal navigation links
            for link in soup.find_all('a', href=True):
                href = link.get('href', '').strip()
                
                if not href:
                    continue
                
                # Skip non-HTTP links
                if href.startswith(('mailto:', 'tel:', 'javascript:', 'data:')):
                    continue
                
                # Convert to absolute URL
                absolute_url = urljoin(url, href)
                
                # Only keep HTTP/HTTPS URLs
                if not absolute_url.startswith(('http://', 'https://')):
                    continue
                
                # Check if it's internal to this domain
                link_domain = self.extract_domain(absolute_url)
                if link_domain == domain:
                    # Skip non-content file extensions
                    if not any(absolute_url.lower().endswith(ext) for ext in [
                        '.css', '.js', '.png', '.jpg', '.jpeg', '.gif', '.svg', '.ico',
                        '.pdf', '.zip', '.rar', '.exe', '.dmg', '.mp4', '.mp3', '.avi'
                    ]):
                        internal_links.add(absolute_url)
            
            return internal_links
            
        except Exception as e:
            return set()
    
    def crawl_domain_for_external_links(self, start_domain: str) -> Set[str]:
        """
        Crawl a domain to find UNIQUE external domains (no duplicates)
        
        Each external domain is counted only ONCE per crawled domain,
        regardless of how many times it appears across different pages.
        This prevents rank inflation from repeated links (like Facebook on every page).
        
        Args:
            start_domain: Domain to crawl (e.g., "example.com")
            
        Returns:
            Set of unique external domain names that this domain links to
        """
        logger.info(f"🌐 Starting domain crawl: {start_domain}")
        
        # Initialize with root URL
        start_url = f"https://{start_domain}"
        internal_urls_to_visit = {start_url}  # Queue of URLs to visit within this domain
        visited_urls = set()                  # URLs already processed (prevents revisiting)
        # Use SET to automatically prevent duplicates - each external domain counted only once!
        unique_external_domains = set()
        pages_crawled = 0
        
        # Breadth-first crawl within domain
        for depth in range(self.max_depth):
            if not internal_urls_to_visit or pages_crawled >= self.max_pages_per_domain:
                break
                
            logger.info(f"📏 Depth {depth + 1}/{self.max_depth}: {len(internal_urls_to_visit)} URLs to visit")
            current_level_urls = internal_urls_to_visit.copy()
            internal_urls_to_visit.clear()
            
            for url in current_level_urls:
                if pages_crawled >= self.max_pages_per_domain:
                    break
                    
                if url in visited_urls:
                    continue
                    
                visited_urls.add(url)
                pages_crawled += 1
                
                # Fetch external links from this page
                external_links = self.fetch_page_links(url)
                
                # Track unique external domains (SET automatically prevents duplicates)
                domains_found_on_this_page = set()
                for external_link in external_links:
                    external_domain = self.extract_domain(external_link)
                    if external_domain and external_domain != start_domain:
                        # Add to unique set - duplicates are automatically ignored
                        if external_domain not in unique_external_domains:
                            unique_external_domains.add(external_domain)
                            domains_found_on_this_page.add(external_domain)
                
                # Log only NEW domains found on this page (to reduce noise)
                if domains_found_on_this_page:
                    logger.info(f"🔗 Found {len(domains_found_on_this_page)} new unique domains on {url}")
                
                # For internal navigation, fetch internal links separately
                if depth < self.max_depth - 1:
                    internal_links = self.fetch_internal_links(url, start_domain)
                    new_internal_links_count = 0
                    for internal_link in internal_links:
                        # Avoid duplicates: check both visited URLs and URLs already queued for visiting
                        if internal_link not in visited_urls and internal_link not in internal_urls_to_visit:
                            internal_urls_to_visit.add(internal_link)
                            new_internal_links_count += 1
                    
                    # Log only if we found new internal links (to reduce noise)
                    if new_internal_links_count > 0:
                        logger.info(f"📄 Added {new_internal_links_count} new internal URLs from {url}")
                
                # Rate limiting
                time.sleep(self.delay)
        
        logger.info(f"🎉 Domain crawl complete: {start_domain}")
        logger.info(f"📄 Pages crawled: {pages_crawled}")
        logger.info(f"🌐 UNIQUE external domains found: {len(unique_external_domains)}")
        
        return unique_external_domains
    
    def update_domain_ranks(self, source_domain: str, unique_external_domains: Set[str]):
        """
        Update database with UNIQUE external domains found
        Each external domain gets +1 rank for each DOMAIN that links to it (not per link occurrence)
        
        This prevents rank inflation from repeated links like:
        - Facebook appearing on every page of a website
        - Same external domain linked multiple times
        
        Args:
            source_domain: The domain that was crawled
            unique_external_domains: Set of unique external domains found (no duplicates)
        """
        logger.info(f"💾 Updating ranks for {len(unique_external_domains)} UNIQUE domains")
        
        with transaction.atomic(using='search_db'):
            # Mark source domain as processed
            source_obj, created = DomainRank.objects.using('search_db').get_or_create(
                domain=source_domain,
                defaults={'rank': 0, 'processed': True}
            )
            if not created:
                source_obj.processed = True
                source_obj.save(using='search_db')
            
            # Update ranks for unique external domains (each gets +1 regardless of link count)
            for external_domain in unique_external_domains:
                if external_domain and external_domain != source_domain:
                    domain_obj, created = DomainRank.objects.using('search_db').get_or_create(
                        domain=external_domain,
                        defaults={'rank': 1, 'processed': False}
                    )
                    if not created:
                        # Domain exists, increment rank by 1 (not by number of links)
                        domain_obj.rank += 1
                        domain_obj.save(using='search_db')
                    
                    logger.info(f"📈 {external_domain}: rank = {domain_obj.rank}")
        
        logger.info("✅ Database updated successfully")
    
    def get_next_unprocessed_domain(self) -> str:
        """
        Get the next domain to process from database
        Priority: highest rank unprocessed domains first
        """
        unprocessed = DomainRank.objects.using('search_db').filter(processed=False).order_by('-rank', 'domain').first()
        
        if unprocessed:
            logger.info(f"🎯 Next domain to process: {unprocessed.domain} (rank: {unprocessed.rank})")
            return unprocessed.domain
        else:
            logger.info("🏁 No unprocessed domains found")
            return None
    
    def add_seed_domain(self, domain: str):
        """Add a starting domain to the database"""
        clean_domain = self.extract_domain(domain)
        if clean_domain:
            DomainRank.objects.using('search_db').get_or_create(
                domain=clean_domain,
                defaults={'rank': 1, 'processed': False}
            )
            logger.info(f"🌱 Added seed domain: {clean_domain}")
    
    def process_domain_parallel(self, domain: str) -> Tuple[str, Set[str]]:
        """
        Process a single domain and return results (thread-safe)
        
        Args:
            domain: Domain to process
            
        Returns:
            Tuple of (domain, external_domains_found)
        """
        try:
            logger.info(f"🎯 [Thread] Processing domain: {domain}")
            external_domains = self.crawl_domain_for_external_links(domain)
            logger.info(f"✅ [Thread] Completed {domain}: {len(external_domains)} external domains found")
            return domain, external_domains
        except Exception as e:
            logger.error(f"❌ [Thread] Failed to process {domain}: {e}")
            return domain, set()
    
    def get_multiple_unprocessed_domains(self, count: int = 4) -> List[str]:
        """
        Get multiple unprocessed domains for parallel processing
        
        Args:
            count: Number of domains to fetch
            
        Returns:
            List of domain names to process
        """
        with db_lock:
            domains = list(DomainRank.objects.using('search_db').filter(
                processed=False
            ).order_by('-rank').values_list('domain', flat=True)[:count])
            
            return domains
    
    def run_parallel_crawler(self, seed_domain: str = None):
        """
        Enhanced crawler that processes multiple domains in parallel
        """
        # Add seed domain if provided
        if seed_domain:
            domain_name = self.extract_domain(seed_domain)
            logger.info(f"🌱 Added seed domain: {domain_name}")
            DomainRank.objects.using('search_db').get_or_create(
                domain=domain_name,
                defaults={'rank': 0, 'processed': False}
            )
        
        iteration = 0
        logger.info("🚀 Starting parallel simplified PageRank crawler")
        
        while True:
            iteration += 1
            logger.info(f"\n🔄 Parallel Iteration {iteration}")
            
            # Get multiple domains to process in parallel
            domains_to_process = self.get_multiple_unprocessed_domains(self.max_workers)
            
            if not domains_to_process:
                logger.info("😴 No domains to process. Waiting for new domains...")
                time.sleep(5)
                continue
            
            logger.info(f"🎯 Processing {len(domains_to_process)} domains in parallel: {domains_to_process}")
            
            # Process domains in parallel using ThreadPoolExecutor
            results = []
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                # Submit all domains for processing
                future_to_domain = {
                    executor.submit(self.process_domain_parallel, domain): domain 
                    for domain in domains_to_process
                }
                
                # Collect results as they complete
                for future in as_completed(future_to_domain):
                    domain = future_to_domain[future]
                    try:
                        processed_domain, external_domains = future.result()
                        results.append((processed_domain, external_domains))
                    except Exception as e:
                        logger.error(f"❌ Parallel processing failed for {domain}: {e}")
                        results.append((domain, set()))
            
            # Update database with all results (thread-safe)
            total_new_domains = 0
            for processed_domain, unique_external_domains in results:
                with db_lock:
                    self.update_domain_ranks(processed_domain, unique_external_domains)
                    total_new_domains += len(unique_external_domains)
            
            logger.info(f"🎉 Parallel batch complete: {len(results)} domains processed, {total_new_domains} new domains discovered")
            
            # Show current top domains
            self.show_top_domains()
            
            # Brief pause between parallel batches
            time.sleep(0.5)

    def run_infinite_crawler(self, seed_domain: str = None):
        """
        Run the infinite domain crawler
        Processes domains one by one forever
        """
        logger.info("🚀 Starting infinite simplified PageRank crawler")
        
        # Add seed domain if provided
        if seed_domain:
            self.add_seed_domain(seed_domain)
        
        iteration = 0
        
        while True:
            iteration += 1
            logger.info(f"\n🔄 Iteration {iteration}")
            
            # Get next domain to process
            current_domain = self.get_next_unprocessed_domain()
            
            if not current_domain:
                logger.info("😴 No domains to process. Waiting for new domains...")
                time.sleep(5)  # Wait 5 seconds before checking again
                continue
            
            try:
                # Crawl domain for unique external domains
                unique_external_domains = self.crawl_domain_for_external_links(current_domain)
                
                # Update database with findings
                self.update_domain_ranks(current_domain, unique_external_domains)
                
                # Show current top domains
                self.show_top_domains()
                
            except Exception as e:
                logger.error(f"💥 Error processing {current_domain}: {str(e)}")
                # Mark as processed even if failed to avoid infinite retries
                try:
                    domain_obj = DomainRank.objects.using('search_db').get(domain=current_domain)
                    domain_obj.processed = True
                    domain_obj.save(using='search_db')
                except:
                    pass
            
            # Brief pause between domains
            time.sleep(5)
    
    def show_top_domains(self, limit: int = 10):
        """Show current top ranked domains"""
        logger.info(f"\n🏆 TOP {limit} DOMAINS:")
        top_domains = DomainRank.objects.using('search_db').order_by('-rank')[:limit]
        
        for i, domain in enumerate(top_domains, 1):
            status = "✅" if domain.processed else "⏳"
            logger.info(f"  {i:2d}. {status} {domain.domain:30} (rank: {domain.rank})")
        
        total_domains = DomainRank.objects.using('search_db').count()
        processed_count = DomainRank.objects.using('search_db').filter(processed=True).count()
        logger.info(f"\n📊 Total domains: {total_domains} | Processed: {processed_count} | Pending: {total_domains - processed_count}")


# Convenience function for easy usage
def start_simplified_pagerank(seed_domain: str = "unicorner.coffee", max_depth: int = 3, delay: float = 0.1, parallel: bool = True, max_workers: int = 4):
    """
    Start the simplified PageRank crawler with default settings
    
    Args:
        seed_domain: Starting domain to crawl
        max_depth: How deep to crawl within each domain
        delay: Delay between requests in seconds
        parallel: Use parallel processing (default: True)
        max_workers: Number of parallel threads (default: 4)
    """
    crawler = SimplifiedPageRank(max_depth=max_depth, delay=delay, max_pages_per_domain=20, max_workers=max_workers)
    
    if parallel:
        crawler.run_parallel_crawler(seed_domain)
    else:
        crawler.run_infinite_crawler(seed_domain)


if __name__ == "__main__":
    # For testing the module directly
    start_simplified_pagerank()
