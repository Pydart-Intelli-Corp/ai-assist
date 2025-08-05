#!/usr/bin/env python3
"""
Test runner script for POORNASREE AI Platform
Provides convenient commands to run different test suites
"""
import argparse
import subprocess
import sys

def run_command(cmd, description):
    """Run a command and handle the result"""
    print(f"\n{'='*50}")
    print(f"Running: {description}")
    print(f"Command: {' '.join(cmd)}")
    print(f"{'='*50}")
    
    result = subprocess.run(cmd, capture_output=False, check=False)
    if result.returncode != 0:
        print(f"\n❌ {description} failed with exit code {result.returncode}")
        return False
    else:
        print(f"\n✅ {description} completed successfully")
        return True

def main():
    parser = argparse.ArgumentParser(description="Test runner for POORNASREE AI Platform")
    parser.add_argument("--unit", action="store_true", help="Run unit tests only")
    parser.add_argument("--integration", action="store_true", help="Run integration tests only")
    parser.add_argument("--coverage", action="store_true", help="Run tests with coverage report")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    parser.add_argument("--pattern", "-k", help="Run tests matching pattern")
    parser.add_argument("--file", "-f", help="Run specific test file")
    
    args = parser.parse_args()
    
    # Base pytest command
    cmd = ["python", "-m", "pytest"]
    
    # Add verbosity
    if args.verbose:
        cmd.append("-vv")
    
    # Add coverage if requested
    if args.coverage:
        cmd.extend(["--cov=app", "--cov-report=html", "--cov-report=term"])
    
    # Add pattern matching
    if args.pattern:
        cmd.extend(["-k", args.pattern])
    
    # Determine test scope
    if args.unit:
        cmd.append("tests/unit/")
        description = "Unit Tests"
    elif args.integration:
        cmd.append("tests/integration/")
        description = "Integration Tests"
    elif args.file:
        cmd.append(f"tests/{args.file}")
        description = f"Test File: {args.file}"
    else:
        cmd.append("tests/")
        description = "All Tests"
    
    # Run the tests
    success = run_command(cmd, description)
    
    if args.coverage and success:
        print("\n📊 Coverage report generated in htmlcov/index.html")
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
