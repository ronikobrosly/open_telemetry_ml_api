#!/usr/bin/env python3
"""
OpenTelemetry Demo Traffic Generator - Automated
Runs all 5 demo scenarios sequentially for 20 minutes each
"""

import requests
import random
import time
import sys
from datetime import datetime, timedelta
from typing import List, Dict, Tuple
import json

# Configuration
API_BASE_URL = "http://localhost:8000"
DEMO_DURATION_MINUTES = 20
MIN_SLEEP_SECONDS = 0.3
MAX_SLEEP_SECONDS = 5.0
USER_REUSE_PROBABILITY = 0.01  # 1% chance to reuse an existing user

# ANSI Color codes
class Colors:
    GREEN = '\033[0;32m'
    YELLOW = '\033[1;33m'
    BLUE = '\033[0;34m'
    RED = '\033[0;31m'
    CYAN = '\033[0;36m'
    MAGENTA = '\033[0;35m'
    BOLD = '\033[1m'
    NC = '\033[0m'  # No Color


class UserIDManager:
    """Manages user IDs with occasional reuse"""

    def __init__(self):
        self.used_users = []

    def get_user_id(self) -> str:
        """Get a user ID - either new or reused"""
        if self.used_users and random.random() < USER_REUSE_PROBABILITY:
            # Reuse an existing user
            user_id = random.choice(self.used_users)
        else:
            # Create a new user
            user_id = f"mock_user_{random.randint(1000000, 9999999)}"
            self.used_users.append(user_id)

        return user_id


class ProgressBar:
    """Simple progress bar for terminal"""

    def __init__(self, total_seconds: int, demo_name: str):
        self.total_seconds = total_seconds
        self.demo_name = demo_name
        self.start_time = time.time()

    def update(self, requests_made: int):
        """Update progress bar"""
        elapsed = time.time() - self.start_time
        remaining = max(0, self.total_seconds - elapsed)
        progress = min(1.0, elapsed / self.total_seconds)

        # Create progress bar
        bar_length = 40
        filled_length = int(bar_length * progress)
        bar = '█' * filled_length + '░' * (bar_length - filled_length)

        # Format time
        elapsed_str = str(timedelta(seconds=int(elapsed)))
        remaining_str = str(timedelta(seconds=int(remaining)))

        # Print progress (overwrite previous line)
        sys.stdout.write('\r')
        sys.stdout.write(
            f"{Colors.CYAN}[{self.demo_name}]{Colors.NC} "
            f"{Colors.YELLOW}{bar}{Colors.NC} "
            f"{Colors.GREEN}{progress*100:.1f}%{Colors.NC} | "
            f"Elapsed: {elapsed_str} | Remaining: {remaining_str} | "
            f"Requests: {requests_made}"
        )
        sys.stdout.flush()

    def finish(self):
        """Complete the progress bar"""
        sys.stdout.write('\n')
        sys.stdout.flush()


def set_chaos_config(model_failure_rate: float, external_timeout_rate: float,
                     slow_search_rate: float, external_failure_rate: float):
    """Set chaos configuration"""
    try:
        response = requests.post(
            f"{API_BASE_URL}/chaos/config",
            json={
                "model_failure_rate": model_failure_rate,
                "external_api_timeout_rate": external_timeout_rate,
                "slow_search_rate": slow_search_rate,
                "external_api_failure_rate": external_failure_rate
            },
            timeout=10
        )
        return response.status_code == 200
    except Exception as e:
        print(f"{Colors.RED}Error setting chaos config: {e}{Colors.NC}")
        return False


def make_search_call(query: str, user_id: str, limit: int) -> Tuple[bool, int]:
    """
    Make a search API call
    Returns: (success, latency_ms)
    """
    try:
        response = requests.get(
            f"{API_BASE_URL}/search",
            params={
                "q": query,
                "user_id": user_id,
                "limit": limit
            },
            timeout=15
        )

        if response.status_code == 200:
            data = response.json()
            latency = data.get('meta', {}).get('latency_ms', 0)
            return True, latency
        else:
            return False, 0

    except Exception as e:
        return False, 0


def run_demo(demo_num: int, demo_name: str, chaos_config: Dict[str, float],
             queries: List[str], duration_minutes: int, user_manager: UserIDManager):
    """Run a single demo scenario"""

    # Print demo header
    print(f"\n{Colors.BLUE}{'='*70}{Colors.NC}")
    print(f"{Colors.BLUE}{Colors.BOLD}DEMO {demo_num}: {demo_name}{Colors.NC}")
    print(f"{Colors.BLUE}{'='*70}{Colors.NC}")
    print(f"{Colors.YELLOW}Chaos Config:{Colors.NC} "
          f"Model Failures: {chaos_config['model_failure_rate']:.0%}, "
          f"External Timeout: {chaos_config['external_timeout_rate']:.0%}, "
          f"Slow Search: {chaos_config['slow_search_rate']:.0%}, "
          f"External Failures: {chaos_config['external_failure_rate']:.0%}")

    # Set chaos configuration
    if not set_chaos_config(**chaos_config):
        print(f"{Colors.RED}Failed to set chaos config, continuing anyway...{Colors.NC}")

    # Initialize tracking
    duration_seconds = duration_minutes * 60
    end_time = time.time() + duration_seconds
    requests_made = 0
    successful_requests = 0
    total_latency = 0

    # Create progress bar
    progress = ProgressBar(duration_seconds, f"Demo {demo_num}")

    print(f"{Colors.GREEN}Starting traffic generation...{Colors.NC}\n")

    # Generate traffic
    while time.time() < end_time:
        # Select random query and user
        query = random.choice(queries)
        user_id = user_manager.get_user_id()
        limit = random.randint(3, 10)

        # Make API call
        success, latency = make_search_call(query, user_id, limit)

        requests_made += 1
        if success:
            successful_requests += 1
            total_latency += latency

        # Update progress bar
        progress.update(requests_made)

        # Random sleep between requests
        sleep_time = random.uniform(MIN_SLEEP_SECONDS, MAX_SLEEP_SECONDS)
        time.sleep(sleep_time)

    # Finish progress bar
    progress.finish()

    # Print summary
    success_rate = (successful_requests / requests_made * 100) if requests_made > 0 else 0
    avg_latency = (total_latency / successful_requests) if successful_requests > 0 else 0

    print(f"\n{Colors.GREEN}Demo {demo_num} Complete!{Colors.NC}")
    print(f"  Total Requests: {requests_made}")
    print(f"  Successful: {successful_requests} ({success_rate:.1f}%)")
    print(f"  Average Latency: {avg_latency:.0f}ms")
    print(f"  Duration: {duration_minutes} minutes")
    print()


def check_api_health() -> bool:
    """Check if API is accessible"""
    try:
        response = requests.get(f"{API_BASE_URL}/health", timeout=5)
        return response.status_code == 200
    except:
        return False


def main():
    """Main execution"""
    print(f"\n{Colors.CYAN}{'='*70}{Colors.NC}")
    print(f"{Colors.CYAN}{Colors.BOLD}OpenTelemetry Demo Traffic Generator - Automated Mode{Colors.NC}")
    print(f"{Colors.CYAN}{'='*70}{Colors.NC}\n")

    # Check API connectivity
    print(f"{Colors.YELLOW}Checking API connectivity at {API_BASE_URL}...{Colors.NC}")
    if not check_api_health():
        print(f"{Colors.RED}✗ Error: Cannot reach API at {API_BASE_URL}{Colors.NC}")
        print(f"{Colors.YELLOW}Please ensure the service is running:{Colors.NC}")
        print(f"  python app/main.py")
        sys.exit(1)

    print(f"{Colors.GREEN}✓ API is accessible{Colors.NC}\n")

    # Initialize user manager
    user_manager = UserIDManager()

    # Configuration for each demo
    demos = [
        {
            "num": 1,
            "name": "Normal Request Flow",
            "chaos_config": {
                "model_failure_rate": 0.005,
                "external_timeout_rate": 0.01,
                "slow_search_rate": 0.01,
                "external_failure_rate": 0.01
            },
            "queries": [
                "machine learning", "neural networks", "deep learning",
                "artificial intelligence", "data science", "supervised learning",
                "reinforcement learning", "gradient descent", "backpropagation",
                "convolutional networks", "transformers", "model training"
            ]
        },
        {
            "num": 2,
            "name": "Chaos Engineering - Model Failures",
            "chaos_config": {
                "model_failure_rate": 0.8,
                "external_timeout_rate": 0.1,
                "slow_search_rate": 0.2,
                "external_failure_rate": 0.05
            },
            "queries": [
                "python", "javascript", "golang", "rust", "typescript",
                "java", "ruby", "kotlin", "swift", "c++", "scala",
                "php", "perl", "haskell", "elixir"
            ]
        },
        {
            "num": 3,
            "name": "Slow Search Detection",
            "chaos_config": {
                "model_failure_rate": 0.05,
                "external_timeout_rate": 0.1,
                "slow_search_rate": 0.9,
                "external_failure_rate": 0.05
            },
            "queries": [
                "kubernetes", "docker", "containers", "microservices",
                "orchestration", "cloud native", "service mesh", "istio",
                "helm", "rancher", "openshift", "deployment"
            ]
        },
        {
            "num": 4,
            "name": "Log-Trace Correlation",
            "chaos_config": {
                "model_failure_rate": 0.5,
                "external_timeout_rate": 0.1,
                "slow_search_rate": 0.2,
                "external_failure_rate": 0.1
            },
            "queries": [
                "testing", "debugging", "monitoring", "observability",
                "tracing", "logging", "instrumentation", "telemetry",
                "metrics", "alerts", "dashboards", "visualization"
            ]
        },
        {
            "num": 5,
            "name": "Service Health Monitoring",
            "chaos_config": {
                "model_failure_rate": 0.01,
                "external_timeout_rate": 0.02,
                "slow_search_rate": 0.01,
                "external_failure_rate": 0.02
            },
            "queries": [
                "monitoring", "metrics", "performance", "reliability",
                "availability", "latency", "throughput", "scalability",
                "uptime", "slo", "sli", "error rate", "apdex", "percentiles"
            ]
        }
    ]

    # Display schedule
    print(f"{Colors.MAGENTA}Execution Schedule:{Colors.NC}")
    print(f"  Each demo will run for {DEMO_DURATION_MINUTES} minutes")
    print(f"  Total duration: {DEMO_DURATION_MINUTES * len(demos)} minutes")
    print(f"  Request frequency: {MIN_SLEEP_SECONDS}-{MAX_SLEEP_SECONDS} seconds")
    print(f"  User ID reuse probability: {USER_REUSE_PROBABILITY:.0%}")

    total_start_time = datetime.now()
    estimated_end_time = total_start_time + timedelta(minutes=DEMO_DURATION_MINUTES * len(demos))
    print(f"\n{Colors.YELLOW}Start Time: {total_start_time.strftime('%Y-%m-%d %H:%M:%S')}{Colors.NC}")
    print(f"{Colors.YELLOW}Estimated End Time: {estimated_end_time.strftime('%Y-%m-%d %H:%M:%S')}{Colors.NC}")

    input(f"\n{Colors.GREEN}Press Enter to start the automated demo sequence...{Colors.NC}")

    # Run all demos
    for demo in demos:
        run_demo(
            demo_num=demo["num"],
            demo_name=demo["name"],
            chaos_config=demo["chaos_config"],
            queries=demo["queries"],
            duration_minutes=DEMO_DURATION_MINUTES,
            user_manager=user_manager
        )

    # Final summary
    total_end_time = datetime.now()
    total_duration = total_end_time - total_start_time

    print(f"\n{Colors.GREEN}{'='*70}{Colors.NC}")
    print(f"{Colors.GREEN}{Colors.BOLD}ALL DEMOS COMPLETED!{Colors.NC}")
    print(f"{Colors.GREEN}{'='*70}{Colors.NC}")
    print(f"  Total Duration: {total_duration}")
    print(f"  Unique Users Created: {len(user_manager.used_users)}")
    print(f"  End Time: {total_end_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"\n{Colors.CYAN}You can now explore the SigNoz dashboard with data from all 5 demo phases!{Colors.NC}\n")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n\n{Colors.YELLOW}⚠ Demo interrupted by user{Colors.NC}")
        print(f"{Colors.GREEN}Exiting gracefully...{Colors.NC}\n")
        sys.exit(0)
    except Exception as e:
        print(f"\n{Colors.RED}✗ Unexpected error: {e}{Colors.NC}\n")
        sys.exit(1)
