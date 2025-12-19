#!/bin/bash

# OpenTelemetry Demo Traffic Generator
# Generates API calls to demonstrate SigNoz observability features

# Configuration
API_BASE_URL="http://localhost:8000"

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Function to generate random sleep time between 1-3 seconds
random_sleep() {
    local sleep_time=$(shuf -i 1-3 -n 1)
    sleep ${sleep_time}
}

# Function to make API call and display result
make_search_call() {
    local query="$1"
    local user_id="$2"
    local limit="$3"

    echo -e "${GREEN}[$(date '+%H:%M:%S')]${NC} ${CYAN}API Call:${NC} q=${query}, user_id=${user_id}, limit=${limit}"

    response=$(curl -s "${API_BASE_URL}/search?q=${query}&user_id=${user_id}&limit=${limit}")

    # Extract latency and status from response
    latency=$(echo "$response" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data.get('meta', {}).get('latency_ms', 'N/A'))" 2>/dev/null)

    if [ -n "$latency" ] && [ "$latency" != "N/A" ]; then
        echo -e "${YELLOW}  ↳ Response received (latency: ${latency}ms)${NC}"
    else
        echo -e "${RED}  ↳ Error or invalid response${NC}"
    fi
}

# Function to set chaos config
set_chaos_config() {
    local model_failure="$1"
    local external_timeout="$2"
    local slow_search="$3"
    local external_failure="$4"

    echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${YELLOW}Setting chaos configuration...${NC}"

    curl -s -X POST "${API_BASE_URL}/chaos/config" \
        -H "Content-Type: application/json" \
        -d "{\"model_failure_rate\": ${model_failure}, \"external_api_timeout_rate\": ${external_timeout}, \"slow_search_rate\": ${slow_search}, \"external_api_failure_rate\": ${external_failure}}" > /dev/null

    echo -e "${GREEN}✓ Chaos config updated${NC}"
    echo -e "  Model Failure Rate: ${model_failure}"
    echo -e "  External Timeout Rate: ${external_timeout}"
    echo -e "  Slow Search Rate: ${slow_search}"
    echo -e "  External Failure Rate: ${external_failure}"
    echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}\n"
}

# Demo 1: Normal Request Flow
demo_1() {
    clear
    echo -e "${BLUE}╔════════════════════════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║          Demo 1: Normal Request Flow                  ║${NC}"
    echo -e "${BLUE}╚════════════════════════════════════════════════════════╝${NC}"
    echo -e "${YELLOW}Objective:${NC} See complete distributed trace across all components\n"

    # Set normal chaos config
    set_chaos_config 0.05 0.1 0.2 0.05

    local queries=("machine+learning" "neural+networks" "deep+learning" "artificial+intelligence" "data+science" "supervised+learning" "reinforcement+learning" "gradient+descent")
    local counter=1

    echo -e "${GREEN}Generating clean requests...${NC} (Press Ctrl+C to return to menu)\n"

    while true; do
        local query=${queries[$((RANDOM % ${#queries[@]}))]}
        make_search_call "${query}" "demo1_${counter}" 3
        echo ""
        counter=$((counter + 1))
        random_sleep
    done
}

# Demo 2: Chaos Engineering - Model Failures
demo_2() {
    clear
    echo -e "${BLUE}╔════════════════════════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║     Demo 2: Chaos Engineering - Model Failures        ║${NC}"
    echo -e "${BLUE}╚════════════════════════════════════════════════════════╝${NC}"
    echo -e "${YELLOW}Objective:${NC} Show how OTel captures ML model failures\n"

    # Set high model failure rate (80%)
    set_chaos_config 0.8 0.1 0.2 0.05

    local queries=("python" "javascript" "golang" "rust" "typescript" "java" "ruby" "kotlin" "swift" "c++")
    local counter=1

    echo -e "${GREEN}Generating requests with HIGH model failure rate...${NC} (Press Ctrl+C to return to menu)\n"

    while true; do
        local query=${queries[$((RANDOM % ${#queries[@]}))]}
        make_search_call "${query}" "chaos_demo_${counter}" 5
        echo ""
        counter=$((counter + 1))
        random_sleep
    done
}

# Demo 3: Slow Search Detection
demo_3() {
    clear
    echo -e "${BLUE}╔════════════════════════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║          Demo 3: Slow Search Detection                ║${NC}"
    echo -e "${BLUE}╚════════════════════════════════════════════════════════╝${NC}"
    echo -e "${YELLOW}Objective:${NC} Identify performance bottlenecks\n"

    # Set 100% slow search rate
    set_chaos_config 0.05 0.1 1.0 0.05

    local queries=("kubernetes" "docker" "containers" "microservices" "orchestration" "cloud+native" "service+mesh" "istio")
    local counter=1

    echo -e "${GREEN}Generating requests with SLOW search...${NC} (Press Ctrl+C to return to menu)\n"

    while true; do
        local query=${queries[$((RANDOM % ${#queries[@]}))]}
        make_search_call "${query}" "slow_demo_${counter}" 3
        echo ""
        counter=$((counter + 1))
        random_sleep
    done
}

# Demo 4: Log-Trace Correlation
demo_4() {
    clear
    echo -e "${BLUE}╔════════════════════════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║          Demo 4: Log-Trace Correlation                ║${NC}"
    echo -e "${BLUE}╚════════════════════════════════════════════════════════╝${NC}"
    echo -e "${YELLOW}Objective:${NC} Correlate logs with traces for debugging\n"

    # Set moderate failure rates to generate interesting errors
    set_chaos_config 0.5 0.1 0.2 0.1

    local queries=("testing" "debugging" "monitoring" "observability" "tracing" "logging" "instrumentation" "telemetry")
    local counter=1

    echo -e "${GREEN}Generating requests with moderate failure rates...${NC} (Press Ctrl+C to return to menu)\n"

    while true; do
        local query=${queries[$((RANDOM % ${#queries[@]}))]}
        make_search_call "${query}" "log_demo_${counter}" 3
        echo ""
        counter=$((counter + 1))
        random_sleep
    done
}

# Demo 5: Service Health Monitoring
demo_5() {
    clear
    echo -e "${BLUE}╔════════════════════════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║        Demo 5: Service Health Monitoring              ║${NC}"
    echo -e "${BLUE}╚════════════════════════════════════════════════════════╝${NC}"
    echo -e "${YELLOW}Objective:${NC} Monitor overall service health and SLIs\n"

    # Set normal chaos config for realistic traffic
    set_chaos_config 0.05 0.1 0.2 0.05

    local queries=("monitoring" "metrics" "performance" "reliability" "availability" "latency" "throughput" "scalability" "uptime" "slo" "sli" "error+rate")
    local counter=1

    echo -e "${GREEN}Generating steady traffic for health monitoring...${NC} (Press Ctrl+C to return to menu)\n"

    while true; do
        local query=${queries[$((RANDOM % ${#queries[@]}))]}
        make_search_call "${query}" "health_demo_${counter}" 3
        echo ""
        counter=$((counter + 1))
        random_sleep
    done
}

# Main menu
show_menu() {
    clear
    echo -e "${CYAN}╔════════════════════════════════════════════════════════╗${NC}"
    echo -e "${CYAN}║                                                        ║${NC}"
    echo -e "${CYAN}║      ${GREEN}OpenTelemetry Demo Traffic Generator${CYAN}            ║${NC}"
    echo -e "${CYAN}║      ${YELLOW}SigNoz Observability Showcase${CYAN}                  ║${NC}"
    echo -e "${CYAN}║                                                        ║${NC}"
    echo -e "${CYAN}╚════════════════════════════════════════════════════════╝${NC}"
    echo ""
    echo -e "${YELLOW}Select a demo scenario:${NC}"
    echo ""
    echo -e "  ${GREEN}1)${NC} Normal Request Flow"
    echo -e "     ${CYAN}└─${NC} Clean requests showing complete distributed traces"
    echo ""
    echo -e "  ${GREEN}2)${NC} Chaos Engineering - Model Failures"
    echo -e "     ${CYAN}└─${NC} High failure rate to demonstrate error tracking"
    echo ""
    echo -e "  ${GREEN}3)${NC} Slow Search Detection"
    echo -e "     ${CYAN}└─${NC} Performance bottleneck identification"
    echo ""
    echo -e "  ${GREEN}4)${NC} Log-Trace Correlation"
    echo -e "     ${CYAN}└─${NC} Debugging with correlated logs and traces"
    echo ""
    echo -e "  ${GREEN}5)${NC} Service Health Monitoring"
    echo -e "     ${CYAN}└─${NC} Steady traffic for SLI monitoring"
    echo ""
    echo -e "  ${RED}6)${NC} Exit"
    echo ""
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
}

# Trap Ctrl+C to return to menu gracefully
trap_ctrlc() {
    echo -e "\n${YELLOW}⚠ Stopping traffic generation...${NC}\n"
    sleep 1
    return
}

# Main loop
main() {
    # Check if API is accessible
    echo -e "${YELLOW}Checking API connectivity...${NC}"
    if ! curl -s "${API_BASE_URL}/health" > /dev/null 2>&1; then
        echo -e "${RED}✗ Error: Cannot reach API at ${API_BASE_URL}${NC}"
        echo -e "${YELLOW}Please ensure the service is running:${NC}"
        echo -e "  python app/main.py"
        echo ""
        exit 1
    fi

    echo -e "${GREEN}✓ API is accessible at ${API_BASE_URL}${NC}"
    sleep 2

    while true; do
        show_menu
        read -p "Enter your choice (1-6): " choice

        # Set trap for Ctrl+C
        trap trap_ctrlc INT

        case $choice in
            1)
                demo_1
                ;;
            2)
                demo_2
                ;;
            3)
                demo_3
                ;;
            4)
                demo_4
                ;;
            5)
                demo_5
                ;;
            6)
                echo -e "${GREEN}Exiting... Goodbye!${NC}"
                exit 0
                ;;
            *)
                echo -e "${RED}✗ Invalid choice. Please select 1-6.${NC}"
                sleep 2
                ;;
        esac

        # Reset trap after demo completes
        trap - INT
    done
}

# Run main function
main
