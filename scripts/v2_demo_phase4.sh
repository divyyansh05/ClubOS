#!/usr/bin/env bash
set -euo pipefail
API=http://localhost:8000

echo "=== Phase 4 Demo ==="

echo "1. Triggering Watchdog..."
curl -s -X POST $API/api/ai/watchdog/run -d '{}' | python3 -c "import sys,json; d=json.load(sys.stdin); print(f'Run ID: {d.get(\"run_id\",\"?\")} | Alerts created: {d.get(\"alerts_created\",0)}')"

echo ""
echo "2. Fetching one alert to investigate..."
ALERT_RESP=$(curl -s "$API/api/ai/alerts?limit=1")
ALERT_ID=$(echo $ALERT_RESP | python3 -c "import sys,json; d=json.load(sys.stdin); alerts=d.get('alerts',[]); print(alerts[0]['alert_id'] if alerts else '')")
if [ -z "$ALERT_ID" ]; then
  echo "No alerts found. Run Watchdog first."
  exit 1
fi
echo "Alert: $ALERT_ID"

echo ""
echo "3. Running investigation (may take 20-40s)..."
curl -s -X POST "$API/api/ai/investigator/run/$ALERT_ID" \
  -H "Content-Type: application/json" \
  -d '{"max_steps": 6}' | python3 -c "
import sys, json
d = json.load(sys.stdin)
print(f'Status: {d.get(\"status\")}')
print(f'Latency: {d.get(\"latency_seconds\", 0):.1f}s')
f = d.get('finding') or {}
print(f'Confidence: {f.get(\"confidence\", \"?\")}')
print(f'Hypothesis: {(f.get(\"cause_hypothesis\") or \"\")[:200]}')
print(f'Tools used: {f.get(\"tools_called\", [])}')
print(f'Trace: {d.get(\"trace_url\", \"no trace\")}')
"

echo ""
echo "4. Listing investigations..."
curl -s "$API/api/ai/investigator?limit=3" | python3 -c "
import sys, json
d = json.load(sys.stdin)
print(f'Total investigations: {d.get(\"total\", 0)}')
for inv in d.get('investigations', [])[:3]:
    print(f'  {inv[\"investigation_id\"]} | {inv[\"metric_name\"]} | {inv[\"status\"]} | {inv.get(\"confidence\",\"?\")}')
"

echo ""
echo "5. Asking Scout about the investigated metric..."
METRIC=$(echo $ALERT_RESP | python3 -c "import sys,json; d=json.load(sys.stdin); alerts=d.get('alerts',[]); print(alerts[0]['metric_name'] if alerts else 'streaming_daily_users')")
curl -s -X POST $API/api/ai/query \
  -H "Content-Type: application/json" \
  -d "{\"question\": \"what is happening with $METRIC and why?\"}" | python3 -c "
import sys, json
d = json.load(sys.stdin)
ans = d.get('answer', '')[:300]
cites = [c.get('source','?') for c in d.get('citations', [])]
print(f'Answer: {ans}...')
print(f'Citations: {cites}')
"

echo ""
echo "=== Demo complete ==="
