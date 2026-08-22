#!/usr/bin/env bash
# ClubOS 2.0 — Phase 3 end-to-end demo.
# Requires: backend running on localhost:8000, valid API keys in env.
# Usage: bash scripts/v2_demo_phase3.sh

set -euo pipefail

API=http://localhost:8000

echo "=== ClubOS 2.0 Phase 3 Demo ==="
echo ""

echo "1. Triggering first Watchdog run..."
curl -s -X POST "$API/api/ai/watchdog/run" \
  -H "Content-Type: application/json" \
  -d '{"dedup_window_days": 7, "top_n": 10}' | python3 -m json.tool

echo ""
echo "2. Querying recent alerts (first 3)..."
curl -s "$API/api/ai/watchdog/alerts?limit=3" | python3 -m json.tool

echo ""
echo "3. Asking Scout about streaming_daily_users (should cite watchdog_alerts if alerts exist)..."
curl -s -X POST "$API/api/ai/query" \
  -H "Content-Type: application/json" \
  -d '{"question": "what is happening with streaming_daily_users this month?"}' | python3 -m json.tool

echo ""
echo "4. Triggering second Watchdog run (should show alerts_created=0, dedup > 0)..."
RESULT=$(curl -s -X POST "$API/api/ai/watchdog/run" \
  -H "Content-Type: application/json" \
  -d '{}')
echo "$RESULT" | python3 -m json.tool
echo ""
CREATED=$(echo "$RESULT" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d['alerts_created'])")
DEDUPED=$(echo "$RESULT" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d['alerts_deduped'])")
echo "alerts_created=$CREATED (expect 0)"
echo "alerts_deduped=$DEDUPED (expect > 0)"

echo ""
echo "=== Demo complete ==="
