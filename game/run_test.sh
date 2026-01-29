#!/bin/bash

# Test runner for multiplayer game
# Starts host and client, takes screenshots, saves logs

cd "/Users/zeratul/Developer/2026-01-28 - test michele"
source game_env/bin/activate

LOG_DIR="game/test_logs"
mkdir -p "$LOG_DIR"

echo "=========================================="
echo "Starting Multiplayer Game Test"
echo "=========================================="
echo ""

# Clean up any previous instances
pkill -f "auto_test.py" 2>/dev/null
sleep 1

# Start host
echo "[1] Starting HOST instance..."
python game/auto_test.py host > "$LOG_DIR/host.log" 2>&1 &
HOST_PID=$!
echo "    Host PID: $HOST_PID"

# Wait for host to start
sleep 4

# Take screenshot of host
echo "[2] Taking screenshot of host..."
screencapture -x "$LOG_DIR/screenshot_host_started.png"

# Start client
echo "[3] Starting CLIENT instance..."
python game/auto_test.py client 127.0.0.1 > "$LOG_DIR/client.log" 2>&1 &
CLIENT_PID=$!
echo "    Client PID: $CLIENT_PID"

# Wait for client to connect
sleep 5

# Take screenshot showing both windows
echo "[4] Taking screenshot of both instances..."
screencapture -x "$LOG_DIR/screenshot_both_running.png"

# Let them run for a bit
echo "[5] Letting game run for 10 seconds..."
sleep 10

# Take final screenshot
echo "[6] Taking final screenshot..."
screencapture -x "$LOG_DIR/screenshot_final.png"

# Show logs
echo ""
echo "=========================================="
echo "HOST LOG:"
echo "=========================================="
cat "$LOG_DIR/host.log"

echo ""
echo "=========================================="
echo "CLIENT LOG:"
echo "=========================================="
cat "$LOG_DIR/client.log"

# Clean up
echo ""
echo "[7] Stopping instances..."
kill $HOST_PID 2>/dev/null
kill $CLIENT_PID 2>/dev/null

echo ""
echo "=========================================="
echo "Test Complete!"
echo "=========================================="
echo "Screenshots saved to: $LOG_DIR/"
echo "  - screenshot_host_started.png"
echo "  - screenshot_both_running.png"
echo "  - screenshot_final.png"
ls -la "$LOG_DIR/"
