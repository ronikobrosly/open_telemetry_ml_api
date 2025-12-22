# Demo Traffic Generator Guide

This directory contains two demo traffic generation scripts for the OpenTelemetry instrumented microservice.

## Scripts

### 1. `generate_demo_traffic.sh` - Interactive Mode

The original interactive script that allows you to manually select and run individual demos.

**Usage:**
```bash
./generate_demo_traffic.sh
```

**Features:**
- Interactive menu to select from 5 different demo scenarios
- Runs selected demo indefinitely until you press Ctrl+C
- Useful for focused testing of a specific scenario

### 2. `generate_demo_traffic_automated.py` - Automated Mode

The new automated script that runs all 5 demos sequentially for a fixed duration.

**Usage:**
```bash
# Using Python directly
python3 generate_demo_traffic_automated.py

# Or if executable
./generate_demo_traffic_automated.py
```

**Features:**
- Runs all 5 demos automatically for 20 minutes each (100 minutes total)
- Random request frequency: 0.3 to 5 seconds between requests
- Smart user ID management:
  - Creates users in format `mock_user_xxxxxxx` where x is a random digit
  - 30% probability of reusing existing users (creates realistic multi-request patterns)
- Real-time progress bar for each demo phase
- Comprehensive statistics at the end of each phase
- Perfect for overnight runs or creating rich datasets for dashboard exploration

**Configuration:**

You can modify these constants at the top of the script:

```python
DEMO_DURATION_MINUTES = 20           # Duration for each demo phase
MIN_SLEEP_SECONDS = 0.3              # Minimum time between requests
MAX_SLEEP_SECONDS = 5.0              # Maximum time between requests
USER_REUSE_PROBABILITY = 0.3         # 30% chance to reuse existing user
```

## Demo Scenarios

Both scripts include these 5 demo scenarios:

1. **Normal Request Flow** (20 min)
   - Low failure rates across all components
   - Demonstrates clean distributed traces
   - Queries: machine learning, neural networks, AI topics

2. **Chaos Engineering - Model Failures** (20 min)
   - 80% model failure rate
   - Shows error tracking and handling
   - Queries: programming languages (Python, JavaScript, etc.)

3. **Slow Search Detection** (20 min)
   - 100% slow search rate
   - Identifies performance bottlenecks
   - Queries: cloud/container topics (Kubernetes, Docker, etc.)

4. **Log-Trace Correlation** (20 min)
   - 50% model failures, 10% external failures
   - Demonstrates log-trace correlation for debugging
   - Queries: observability topics (monitoring, tracing, etc.)

5. **Service Health Monitoring** (20 min)
   - Normal failure rates
   - Steady traffic for SLI/SLO monitoring
   - Queries: reliability topics (metrics, uptime, SLOs, etc.)

## Requirements

- Python 3.6+ (for automated script)
- `requests` library: `pip install requests`
- Running microservice at `http://localhost:8000`
- curl (for bash script)

## Tips

### For the Automated Script

1. **Run it before leaving for the day:**
   ```bash
   # Start in a tmux/screen session
   tmux new -s demo
   ./generate_demo_traffic_automated.py
   # Detach: Ctrl+B then D
   ```

2. **Monitor progress remotely:**
   ```bash
   tmux attach -t demo
   ```

3. **Verify your API is running first:**
   ```bash
   curl http://localhost:8000/health
   ```

4. **Check SigNoz dashboards after completion:**
   - Browse by time range to see each 20-minute demo phase
   - Compare error rates, latencies, and trace patterns across phases
   - Look for users who made multiple requests (due to user ID reuse)

### For the Interactive Script

1. **Quick focused testing:**
   - Select a specific demo to understand its behavior
   - Use Ctrl+C to stop and try another scenario
   - Great for presentations or live demos

2. **Return to menu:**
   - Press Ctrl+C during any demo
   - Select a different scenario
   - Choose option 6 to exit

## Example Workflow

```bash
# 1. Start your microservice
python app/main.py

# 2. In another terminal, run automated demos
./generate_demo_traffic_automated.py

# 3. Come back 100 minutes later and explore SigNoz:
#    - Filter by time ranges for each demo phase
#    - Compare metrics across different chaos configurations
#    - Examine traces for both successful and failed requests
#    - Track specific users who made multiple requests
```

## Troubleshooting

**API Connection Error:**
```
✗ Error: Cannot reach API at http://localhost:8000
```
- Ensure the FastAPI service is running
- Check if port 8000 is in use: `lsof -i :8000`
- Verify your .env configuration

**Script Hangs:**
- Check API logs for errors
- Reduce `MAX_SLEEP_SECONDS` if you want faster traffic
- Ensure network connectivity

**Import Error (Python):**
```bash
pip install requests
```

## Output Example

```
======================================================================
OpenTelemetry Demo Traffic Generator - Automated Mode
======================================================================

Checking API connectivity at http://localhost:8000...
✓ API is accessible

Execution Schedule:
  Each demo will run for 20 minutes
  Total duration: 100 minutes
  Request frequency: 0.3-5.0 seconds
  User ID reuse probability: 30%

Start Time: 2025-12-21 14:30:00
Estimated End Time: 2025-12-21 16:10:00

Press Enter to start the automated demo sequence...

======================================================================
DEMO 1: Normal Request Flow
======================================================================
Chaos Config: Model Failures: 5%, External Timeout: 10%, Slow Search: 20%, External Failures: 5%
Starting traffic generation...

[Demo 1] ████████████████████████████████████████ 100.0% | Elapsed: 0:20:00 | Remaining: 0:00:00 | Requests: 287

Demo 1 Complete!
  Total Requests: 287
  Successful: 274 (95.5%)
  Average Latency: 245ms
  Duration: 20 minutes
```
