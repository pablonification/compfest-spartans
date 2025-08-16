#!/usr/bin/env python3
"""Test runner script for SmartBin backend."""

import subprocess
import sys
import os
from pathlib import Path


def run_command(command, description):
    """Run a command and handle errors."""
    print(f"\n🔄 {description}...")
    print(f"Running: {command}")
    
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed successfully")
        if result.stdout:
            print("Output:", result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed with exit code {e.returncode}")
        if e.stdout:
            print("Stdout:", e.stdout)
        if e.stderr:
            print("Stderr:", e.stderr)
        return False


def main():
    """Main test runner function."""
    print("🧪 SmartBin Backend Test Runner")
    print("=" * 50)
    
    # Change to backend directory
    backend_dir = Path(__file__).parent
    os.chdir(backend_dir)
    
    # Check if we're in the right directory
    if not (backend_dir / "pyproject.toml").exists():
        print("❌ Error: pyproject.toml not found. Please run this script from the backend directory.")
        sys.exit(1)
    
    # Install test dependencies if needed
    print("\n📦 Checking dependencies...")
    if not run_command("uv pip list | grep pytest", "Checking pytest installation"):
        print("Installing test dependencies...")
        if not run_command("uv add --dev pytest pytest-asyncio pytest-cov pytest-mock", "Installing test dependencies"):
            print("❌ Failed to install test dependencies")
            sys.exit(1)
    
    # Run different types of tests
    test_results = []
    
    # Unit tests
    print("\n" + "=" * 50)
    print("🔬 UNIT TESTS")
    print("=" * 50)
    
    test_results.append(run_command(
        "uv run pytest tests/unit/ -v --tb=short --cov=src/backend --cov-report=term-missing",
        "Running unit tests with coverage"
    ))
    
    # Integration tests
    print("\n" + "=" * 50)
    print("🔗 INTEGRATION TESTS")
    print("=" * 50)
    
    test_results.append(run_command(
        "uv run pytest tests/integration/ -v --tb=short -m integration",
        "Running integration tests"
    ))
    
    # Security tests
    print("\n" + "=" * 50)
    print("🔒 SECURITY TESTS")
    print("=" * 50)
    
    test_results.append(run_command(
        "uv run pytest tests/unit/test_security.py -v --tb=short -m security",
        "Running security tests"
    ))
    
    # Generate coverage report
    print("\n" + "=" * 50)
    print("📊 COVERAGE REPORT")
    print("=" * 50)
    
    test_results.append(run_command(
        "uv run pytest --cov=src/backend --cov-report=html:htmlcov --cov-report=xml:coverage.xml",
        "Generating coverage reports"
    ))
    
    # Summary
    print("\n" + "=" * 50)
    print("📋 TEST SUMMARY")
    print("=" * 50)
    
    passed = sum(test_results)
    total = len(test_results)
    
    print(f"Tests passed: {passed}/{total}")
    
    if passed == total:
        print("🎉 All test categories passed!")
        print("\n📁 Coverage reports generated:")
        print("  - HTML: htmlcov/index.html")
        print("  - XML: coverage.xml")
        return 0
    else:
        print("❌ Some test categories failed. Check the output above for details.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
