"""
UNICORNER Search Engine Test Runner
==================================

Comprehensive test runner that executes all test suites in order:
1. Parser tests (URL validation, fetching, security)
2. Sanitizer tests (HTML cleaning, link extraction)
3. Integration tests (complete workflow)
4. Interactive test (manual testing interface)

Usage:
    python test_runner.py                    # Run all tests
    python test_runner.py --skip-network     # Skip network-dependent tests
    python test_runner.py --skip-interactive # Skip interactive test
    python test_runner.py --verbose          # Verbose output
"""

import sys
import os
import argparse
import time
from typing import List, Tuple

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import test modules
from tests.test_parser import run_parser_tests
from tests.test_sanitizer import run_sanitizer_tests
from tests.test_integration import run_integration_tests
from tests import TEST_CONFIG


class TestRunner:
    """Main test runner class"""
    
    def __init__(self, args):
        """Initialize test runner with configuration"""
        self.args = args
        self.results = []
        self.start_time = None
        
        # Update test configuration based on arguments
        if args.skip_network:
            TEST_CONFIG['skip_network_tests'] = True
        if args.verbose:
            TEST_CONFIG['verbose'] = True
    
    def print_header(self):
        """Print test runner header"""
        print("🚀 UNICORNER Search Engine - Comprehensive Test Suite")
        print("=" * 60)
        print("🔧 Testing all search engine components")
        print("⚡ Optimized for maintainability and updates")
        print()
        
        if self.args.skip_network:
            print("⚠️  Network tests will be skipped")
        if self.args.skip_interactive:
            print("⚠️  Interactive test will be skipped")
        print()
    
    def run_test_suite(self, name: str, test_function, description: str) -> bool:
        """Run a single test suite and track results"""
        print(f"📋 {name}")
        print("─" * 60)
        print(f"📝 {description}")
        print()
        
        suite_start = time.time()
        
        try:
            success = test_function()
            duration = time.time() - suite_start
            
            if success:
                print(f"✅ {name} completed successfully in {duration:.2f}s")
                self.results.append((name, True, duration, None))
            else:
                print(f"❌ {name} failed after {duration:.2f}s")
                self.results.append((name, False, duration, "Test failures detected"))
            
        except Exception as e:
            duration = time.time() - suite_start
            print(f"💥 {name} crashed after {duration:.2f}s: {str(e)}")
            self.results.append((name, False, duration, str(e)))
            success = False
        
        print()
        return success
    
    def run_interactive_test(self) -> bool:
        """Run interactive test"""
        if self.args.skip_interactive:
            print("⏭️  Skipping interactive test (--skip-interactive flag)")
            print()
            return True
        
        print("🎮 Interactive Test")
        print("─" * 60)
        print("🖱️  Manual testing interface for real-time validation")
        print("💡 Test with your own URLs and see results immediately")
        print()
        
        try:
            # Import and run interactive test
            try:
                from interactive_test import main as interactive_main
            except ImportError:
                # Try with search_engine prefix
                from search_engine.interactive_test import main as interactive_main
            
            print("🚀 Starting interactive test...")
            print("💡 Type 'quit' or 'exit' to finish and return to test results")
            print()
            
            # Run interactive test
            interactive_main()
            
            print()
            print("✅ Interactive test completed")
            self.results.append(("Interactive Test", True, 0, None))
            return True
            
        except KeyboardInterrupt:
            print()
            print("⏹️  Interactive test interrupted by user")
            self.results.append(("Interactive Test", True, 0, "User interrupted"))
            return True
            
        except Exception as e:
            print(f"💥 Interactive test failed: {str(e)}")
            self.results.append(("Interactive Test", False, 0, str(e)))
            return False
    
    def print_summary(self):
        """Print test results summary"""
        total_duration = time.time() - self.start_time
        
        print("📊 TEST RESULTS SUMMARY")
        print("=" * 60)
        
        successful_tests = 0
        failed_tests = 0
        
        for name, success, duration, error in self.results:
            status = "✅ PASS" if success else "❌ FAIL"
            duration_str = f"{duration:.2f}s" if duration > 0 else "N/A"
            
            print(f"{status} {name:<20} ({duration_str})")
            if error and not success:
                print(f"    Error: {error}")
            
            if success:
                successful_tests += 1
            else:
                failed_tests += 1
        
        print("─" * 60)
        print(f"📈 Total: {len(self.results)} test suites")
        print(f"✅ Passed: {successful_tests}")
        print(f"❌ Failed: {failed_tests}")
        print(f"⏱️  Total time: {total_duration:.2f}s")
        
        if failed_tests == 0:
            print()
            print("🎉 ALL TESTS PASSED! 🎉")
            print("🚀 Search engine is ready for production!")
        else:
            print()
            print("⚠️  Some tests failed. Please review and fix issues.")
        
        print("=" * 60)
    
    def run_all_tests(self) -> bool:
        """Run all test suites in order"""
        self.start_time = time.time()
        self.print_header()
        
        # Define test suites in execution order
        test_suites = [
            (
                "Parser Tests",
                run_parser_tests,
                "URL validation, rate limiting, page fetching, and security"
            ),
            (
                "Sanitizer Tests", 
                run_sanitizer_tests,
                "HTML cleaning, content extraction, and link analysis"
            ),
            (
                "Integration Tests",
                run_integration_tests,
                "Complete workflow, performance, and edge cases"
            )
        ]
        
        # Run each test suite
        all_passed = True
        for name, test_function, description in test_suites:
            success = self.run_test_suite(name, test_function, description)
            if not success:
                all_passed = False
        
        # Run interactive test last
        interactive_success = self.run_interactive_test()
        if not interactive_success:
            all_passed = False
        
        # Print summary
        self.print_summary()
        
        return all_passed


def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description="UNICORNER Search Engine Test Runner",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python test_runner.py                    # Run all tests
  python test_runner.py --skip-network     # Skip network tests
  python test_runner.py --skip-interactive # Skip interactive test
  python test_runner.py --verbose          # Verbose output
        """
    )
    
    parser.add_argument(
        '--skip-network',
        action='store_true',
        help='Skip network-dependent tests (useful for offline testing)'
    )
    
    parser.add_argument(
        '--skip-interactive',
        action='store_true',
        help='Skip interactive test (useful for automated testing)'
    )
    
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose output for detailed test information'
    )
    
    parser.add_argument(
        '--version',
        action='version',
        version=f'UNICORNER Search Engine Test Runner v{TEST_CONFIG.get("__version__", "1.0.0")}'
    )
    
    return parser.parse_args()


def main():
    """Main entry point"""
    args = parse_arguments()
    
    # Create and run test runner
    runner = TestRunner(args)
    success = runner.run_all_tests()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
