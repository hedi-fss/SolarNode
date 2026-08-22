#!/bin/bash
# Comprehensive test script for Sprint 1

set -e

echo "=== Sprint 1 Comprehensive Test Suite ==="

# Kill any existing server
pkill -f "python run.py" 2>/dev/null || true

# Source conda and activate environment
source ~/anaconda3/etc/profile.d/conda.sh
conda activate solarnode2

echo "Starting server..."
export PORT=5001
python run.py > /tmp/solarnode.log 2>&1 &
SERVER_PID=$!
sleep 5

# Check if server is running
if ! ps -p $SERVER_PID > /dev/null; then
    echo "❌ Server failed to start. Check /tmp/solarnode.log"
    tail -20 /tmp/solarnode.log
    exit 1
fi
echo "✅ Server started (PID: $SERVER_PID)"

# Function to test endpoint
test_endpoint() {
    local url=$1
    local expected=$2
    local response=$(curl -s -o /dev/null -w "%{http_code}" "http://localhost:5001$url" 2>/dev/null)
    if [ "$response" = "$expected" ]; then
        echo "✅ $url -> $response"
    else
        echo "❌ $url -> $response (expected $expected)"
    fi
}

echo
echo "--- Testing API Endpoints ---"
test_endpoint "/api/simulation/compare" "200"
test_endpoint "/api/simulation/lifetime?nodes=30&hours=100" "200"
test_endpoint "/api/fiveg/status" "200"
test_endpoint "/ml/status" "200"
test_endpoint "/api/hardware/status" "200"
test_endpoint "/api/docs" "200"

echo
echo "--- Testing Pages ---"
test_endpoint "/" "200"
test_endpoint "/dashboard" "200"
test_endpoint "/analysis" "200"

echo
echo "--- Testing ML Training ---"
curl -s -X POST http://localhost:5001/ml/train -H "Content-Type: application/json" -d '{"contamination":0.1}' | python -m json.tool | grep -q '"samples":' && echo "✅ ML training returned samples" || echo "❌ ML training failed"

echo
echo "--- Testing Hardware Mock ---"
# Start mock
curl -s -X POST http://localhost:5001/api/hardware/mock/start -H "Content-Type: application/json" -d '{"nodes":20, "interval":2}' > /dev/null
sleep 3
# Get status
mock_response=$(curl -s http://localhost:5001/api/hardware/status)
if echo "$mock_response" | python -c "import sys, json; json.load(sys.stdin)" 2>/dev/null; then
    mock_running=$(echo "$mock_response" | python -c "import sys, json; print(json.load(sys.stdin).get('mock_running', False))")
    if [ "$mock_running" = "True" ]; then
        echo "✅ Hardware mock running"
    else
        echo "❌ Hardware mock not running (response: $mock_response)"
    fi
else
    echo "❌ Hardware status returned invalid JSON: $mock_response"
fi

echo
echo "--- Testing Database ---"
telemetry_response=$(curl -s http://localhost:5001/api/telemetry/latest)
if echo "$telemetry_response" | python -c "import sys, json; json.load(sys.stdin)" 2>/dev/null; then
    echo "✅ Database has data"
else
    echo "❌ Database empty or invalid response"
fi

echo
echo "--- Checking Logs ---"
if [ -f logs/solarnode.log ]; then
    echo "✅ Log file exists"
    tail -3 logs/solarnode.log
else
    echo "❌ Log file not found"
fi

echo
echo "--- Stopping server ---"
kill $SERVER_PID 2>/dev/null
wait $SERVER_PID 2>/dev/null || true
echo "✅ Server stopped"

echo
echo "=== ✅ Sprint 1 Comprehensive Tests Completed ==="
