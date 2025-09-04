from django.core.management.base import BaseCommand
from search.modules.simplified_pagerank import start_simplified_pagerank


class Command(BaseCommand):
    """
    Django management command to run the simplified PageRank crawler
    
    Usage:
        python manage.py run_pagerank
        python manage.py run_pagerank --domain=example.com --depth=3
    """
    
    help = 'Run the simplified PageRank crawler with separate database'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--domain',
            type=str,
            default='unicorner.coffee',
            help='Starting domain to crawl (default: unicorner.coffee)'
        )
        parser.add_argument(
            '--depth',
            type=int,
            default=3,
            help='Maximum crawling depth within each domain (default: 3)'
        )
        parser.add_argument(
            '--delay',
            type=float,
            default=0.1,
            help='Delay between requests in seconds (default: 0.1 = 100ms)'
        )
        parser.add_argument(
            '--parallel',
            action='store_true',
            default=True,
            help='Enable parallel processing (default: True)'
        )
        parser.add_argument(
            '--sequential',
            action='store_true',
            default=False,
            help='Use sequential processing instead of parallel'
        )
        parser.add_argument(
            '--workers',
            type=int,
            default=4,
            help='Number of parallel workers (default: 4)'
        )
    
    def handle(self, *args, **options):
        domain = options['domain']
        depth = options['depth']
        delay = options['delay']
        parallel = not options['sequential']  # Default to parallel unless --sequential is specified
        workers = options['workers']
        
        self.stdout.write(
            self.style.SUCCESS(f'🚀 Starting simplified PageRank crawler')
        )
        self.stdout.write(f'🌐 Seed domain: {domain}')
        self.stdout.write(f'📏 Max depth: {depth}')
        self.stdout.write(f'⏱️ Request delay: {delay}s')
        self.stdout.write(f'� Mode: {"Parallel" if parallel else "Sequential"}')
        if parallel:
            self.stdout.write(f'👥 Workers: {workers}')
        self.stdout.write(f'�💾 Database: search/database/search.sqlite3')
        self.stdout.write('🛑 Press Ctrl+C to stop\n')
        
        try:
            start_simplified_pagerank(
                seed_domain=domain, 
                max_depth=depth, 
                delay=delay, 
                parallel=parallel, 
                max_workers=workers
            )
        except KeyboardInterrupt:
            self.stdout.write(
                self.style.WARNING('\n🛑 Crawler stopped by user')
            )
