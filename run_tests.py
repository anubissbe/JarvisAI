#!/usr/bin/env python3
"""
JarvisAI Test Runner
Run all tests for the JarvisAI system
"""

import os
import sys
import unittest
import argparse
import time
import subprocess
import logging
from typing import List, Dict, Any, Optional
import json

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('test_runner')

# Color codes for terminal output
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


def run_test_module(module_name: str, pattern: Optional[str] = None, verbose: bool = False) -> bool:
    """Run tests from a specific module"""
    print(f"\n{Colors.HEADER}Running tests for: {Colors.BOLD}{module_name}{Colors.ENDC}")
    
    # Build the command
    cmd = [sys.executable, '-m', 'unittest', module_name]
    
    if pattern:
        cmd.extend(['-k', pattern])
    
    if verbose:
        cmd.append('-v')
    
    # Run the tests
    start_time = time.time()
    process = subprocess.run(cmd, capture_output=True, text=True)
    duration = time.time() - start_time
    
    # Print output
    if process.stdout:
        print(process.stdout)
    
    if process.stderr:
        print(f"{Colors.RED}{process.stderr}{Colors.ENDC}")
    
    # Print summary
    if process.returncode == 0:
        print(f"{Colors.GREEN}✓ Tests passed{Colors.ENDC} in {duration:.2f} seconds")
        return True
    else:
        print(f"{Colors.RED}✗ Tests failed{Colors.ENDC} in {duration:.2f} seconds")
        return False


def check_service_status() -> Dict[str, bool]:
    """Check if required services are running"""
    services = {
        'ollama': False,
        'ollama_proxy': False,
        'speech_service': False,
        'neo4j': False
    }
    
    # Check Ollama
    try:
        import requests
        response = requests.get('http://localhost:11434/api/version', timeout=2)
        services['ollama'] = response.status_code == 200
    except:
        pass
    
    # Check Ollama Proxy
    try:
        response = requests.get('http://localhost:11435/health', timeout=2)
        services['ollama_proxy'] = response.status_code == 200
    except:
        pass
    
    # Check Speech Service
    try:
        response = requests.get('http://localhost:5000/health', timeout=2)
        services['speech_service'] = response.status_code == 200
    except:
        pass
    
    # Check Neo4j
    try:
        from neo4j import GraphDatabase
        driver = GraphDatabase.driver(
            'bolt://localhost:7687', 
            auth=('neo4j', os.environ.get('NEO4J_PASSWORD', 'password'))
        )
        with driver.session() as session:
            result = session.run("RETURN 1 as num")
            services['neo4j'] = result.single()["num"] == 1
        driver.close()
    except:
        pass
    
    return services


def print_service_status(services: Dict[str, bool]):
    """Print the status of required services"""
    print(f"\n{Colors.HEADER}Service Status:{Colors.ENDC}")
    
    for service, status in services.items():
        status_text = f"{Colors.GREEN}Running{Colors.ENDC}" if status else f"{Colors.RED}Not Running{Colors.ENDC}"
        print(f"  {service.ljust(15)}: {status_text}")


def run_all_tests(args: argparse.Namespace) -> int:
    """Run all test modules"""
    # Get service status
    if not args.skip_service_check:
        services = check_service_status()
        print_service_status(services)
        
        # Check if we should continue
        if args.require_services and not all(services.values()):
            print(f"{Colors.RED}Error: Not all required services are running.{Colors.ENDC}")
            print(f"Run with --skip-service-check to bypass this check or start all services first.")
            return 1
    
    # Define test modules
    test_modules = [
        'tests.test_ollama_proxy',
        'tests.test_document_processor',
        'tests.test_speech_service'
    ]
    
    if args.module:
        # Run only specified module
        if args.module in test_modules:
            success = run_test_module(args.module, args.pattern, args.verbose)
            return 0 if success else 1
        else:
            print(f"{Colors.RED}Error: Unknown test module '{args.module}'.{Colors.ENDC}")
            print(f"Available modules: {', '.join(test_modules)}")
            return 1
    
    # Run all modules
    results = {}
    for module in test_modules:
        results[module] = run_test_module(module, args.pattern, args.verbose)
    
    # Print summary
    print(f"\n{Colors.HEADER}Test Summary:{Colors.ENDC}")
    all_passed = True
    
    for module, success in results.items():
        status = f"{Colors.GREEN}PASSED{Colors.ENDC}" if success else f"{Colors.RED}FAILED{Colors.ENDC}"
        print(f"  {module.ljust(30)}: {status}")
        all_passed = all_passed and success
    
    # Final result
    if all_passed:
        print(f"\n{Colors.GREEN}All tests passed!{Colors.ENDC}")
        return 0
    else:
        print(f"\n{Colors.RED}Some tests failed.{Colors.ENDC}")
        return 1


def run_integration_test(args: argparse.Namespace) -> int:
    """Run an integration test by sending a message through the system"""
    print(f"\n{Colors.HEADER}Running Integration Test{Colors.ENDC}")
    
    try:
        import requests
        
        # Check if Ollama is running
        try:
            response = requests.get('http://localhost:11434/api/version', timeout=2)
            if response.status_code != 200:
                print(f"{Colors.RED}Ollama is not running. Start the service and try again.{Colors.ENDC}")
                return 1
        except:
            print(f"{Colors.RED}Ollama is not running. Start the service and try again.{Colors.ENDC}")
            return 1
        
        # Send a test message to the Ollama API
        test_message = "Hello, I'm running an integration test. Please respond with a simple greeting."
        
        print(f"{Colors.BLUE}Sending test message to Ollama:{Colors.ENDC} {test_message}")
        
        response = requests.post(
            'http://localhost:11434/api/chat',
            json={
                "model": "jarvis",  # Use the jarvis model if available
                "messages": [{"role": "user", "content": test_message}],
                "stream": False
            }
        )
        
        if response.status_code == 200:
            assistant_response = response.json().get('message', {}).get('content', '')
            print(f"{Colors.GREEN}Received response:{Colors.ENDC} {assistant_response}")
            print(f"\n{Colors.GREEN}Integration test passed!{Colors.ENDC}")
            return 0
        else:
            print(f"{Colors.RED}Error: Received status code {response.status_code}{Colors.ENDC}")
            print(f"Response: {response.text}")
            return 1
    
    except Exception as e:
        print(f"{Colors.RED}Error during integration test: {str(e)}{Colors.ENDC}")
        return 1


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='JarvisAI Test Runner')
    parser.add_argument('--module', help='Run tests from a specific module')
    parser.add_argument('--pattern', help='Only run tests matching the pattern')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    parser.add_argument('--skip-service-check', action='store_true', help='Skip checking if services are running')
    parser.add_argument('--require-services', action='store_true', help='Require all services to be running')
    parser.add_argument('--integration', action='store_true', help='Run integration test')
    
    args = parser.parse_args()
    
    if args.integration:
        return run_integration_test(args)
    else:
        return run_all_tests(args)


if __name__ == '__main__':
    sys.exit(main())