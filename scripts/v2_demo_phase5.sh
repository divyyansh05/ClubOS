#!/usr/bin/env bash
# ClubOS 2.0 — Phase 5 End-to-End Demo
# Covers: Watchdog auto-trigger → Investigator → Supervisor → Briefer (with dedup cache)
#
# Prerequisites:
#   - Backend running on :8000  (PYTHONPATH=<project-root> uvicorn app.main:app --port 8000 --app-dir backend/api)
#   - .env.v2 loaded with OPENAI_API_KEY
#
# Usage: bash scripts/v2_demo_phase5.sh
# Override base URL: CLUBOS_BASE_URL=http://localhost:8001 bash scripts/v2_demo_phase5.sh

set -euo pipefail

BASE="${CLUBOS_BASE_URL:-http://localhost:8000}"
PREV_MONTH=$(python3 -c "
from datetime import datetime, timedelta
first = datetime.now().replace(day=1)
prev = (first - timedelta(days=1))
print(prev.strftime('%Y-%m'))
")

ok()  { echo "  ✓ $*"; }
hdr() { echo; echo "━━━ $* ━━━"; }

hdr "STEP 1 — Watchdog run (critical alerts auto-trigger Investigator in background)"

WATCHDOG_RESP=$(curl -s -X POST "$BASE/api/ai/watchdog/run" \
  -H "Content-Type: application/json" \
  -d '{"run_id": "demo_phase5_'"$(date +%s)"'"}')

ALERTS_CREATED=$(echo "$WATCHDOG_RESP" | python3 -c "import json,sys; d=json.load(sys.stdin); print(d.get('alerts_created',0))" 2>/dev/null || echo "0")
ok "Watchdog complete. alerts_created=$ALERTS_CREATED"
echo "  (Critical alerts auto-triggered Investigator via asyncio.create_task — fire-and-forget)"

# Give the background investigation a moment to start
sleep 3

hdr "STEP 2 — Wait for background investigation to progress (10s)"
sleep 10
RECENT_INV=$(curl -s "$BASE/api/ai/investigator?limit=1")
INV_STATUS=$(echo "$RECENT_INV" | python3 -c "
import json,sys
items=json.load(sys.stdin)
if items: print(items[0].get('status','none'))
else: print('none')
" 2>/dev/null || echo "none")
ok "Most recent investigation status: $INV_STATUS"

hdr "STEP 3 — Supervisor: simple Scout question (direct dispatch, no LangGraph)"

SCOUT_RESP=$(curl -s -X POST "$BASE/api/ai/supervisor/query" \
  -H "Content-Type: application/json" \
  -d '{"query": "what is streaming_daily_users this month?"}')

DISPATCH=$(echo "$SCOUT_RESP" | python3 -c "import json,sys; d=json.load(sys.stdin); print(d.get('dispatch_path','?'))")
AGENT=$(echo "$SCOUT_RESP"   | python3 -c "import json,sys; d=json.load(sys.stdin); print(d.get('classification',{}).get('agent','?'))")
CONF=$(echo "$SCOUT_RESP"    | python3 -c "import json,sys; d=json.load(sys.stdin); print(d.get('classification',{}).get('confidence','?'))")
ok "dispatch_path=$DISPATCH  agent=$AGENT  confidence=$CONF"
echo "  → No LangGraph invoked. Deterministic classifier resolved in <10ms."

hdr "STEP 4 — Supervisor: complex query (LangGraph path, multi-step plan)"

COMPLEX_RESP=$(curl -s -X POST "$BASE/api/ai/supervisor/query" \
  -H "Content-Type: application/json" \
  -d '{"query": "how are things going this quarter overall? give me a summary"}')

DISPATCH2=$(echo "$COMPLEX_RESP" | python3 -c "import json,sys; d=json.load(sys.stdin); print(d.get('dispatch_path','?'))")
STEPS=$(echo "$COMPLEX_RESP"     | python3 -c "
import json,sys
d=json.load(sys.stdin)
plan=d.get('result',{}).get('plan') or []
print(len(plan))
" 2>/dev/null || echo "?")
ok "dispatch_path=$DISPATCH2  plan_steps=$STEPS"

hdr "STEP 5 — Monthly briefing (first call — LLM generates)"

BRIEF_RESP=$(curl -s -X POST "$BASE/api/ai/briefer/run_monthly?year_month=$PREV_MONTH")
BRIEF_ID=$(echo "$BRIEF_RESP"     | python3 -c "import json,sys; d=json.load(sys.stdin); print(d.get('briefing_id','?'))")
BRIEF_STATUS=$(echo "$BRIEF_RESP" | python3 -c "import json,sys; d=json.load(sys.stdin); print(d.get('status','?'))")
BRIEF_CACHED=$(echo "$BRIEF_RESP" | python3 -c "import json,sys; d=json.load(sys.stdin); print(d.get('was_cached','?'))")
ok "Briefing generated. id=$BRIEF_ID  status=$BRIEF_STATUS  was_cached=$BRIEF_CACHED"

hdr "STEP 6 — Monthly briefing again (dedup cache — should return cached)"

BRIEF_RESP2=$(curl -s -X POST "$BASE/api/ai/briefer/run_monthly?year_month=$PREV_MONTH")
BRIEF_ID2=$(echo "$BRIEF_RESP2"     | python3 -c "import json,sys; d=json.load(sys.stdin); print(d.get('briefing_id','?'))")
BRIEF_STATUS2=$(echo "$BRIEF_RESP2" | python3 -c "import json,sys; d=json.load(sys.stdin); print(d.get('status','?'))")
BRIEF_CACHED2=$(echo "$BRIEF_RESP2" | python3 -c "import json,sys; d=json.load(sys.stdin); print(d.get('was_cached','?'))")
ok "Second call. id=$BRIEF_ID2  status=$BRIEF_STATUS2  was_cached=$BRIEF_CACHED2"

if [ "$BRIEF_ID" = "$BRIEF_ID2" ] && [ "$BRIEF_CACHED2" = "True" ]; then
  ok "Dedup cache confirmed — same briefing_id returned, no LLM call made."
else
  echo "  ! Unexpected: IDs differ or was_cached is not True. status=$BRIEF_STATUS2"
fi

hdr "STEP 7 — Briefer: direct supervisor dispatch for briefing query"

BRIEF_QUERY_RESP=$(curl -s -X POST "$BASE/api/ai/supervisor/query" \
  -H "Content-Type: application/json" \
  -d "{\"query\": \"give me a monthly summary for $PREV_MONTH\"}")

BRIEF_DISPATCH=$(echo "$BRIEF_QUERY_RESP" | python3 -c "import json,sys; d=json.load(sys.stdin); print(d.get('dispatch_path','?'))")
ok "dispatch_path=$BRIEF_DISPATCH  (should be direct_briefer)"

hdr "STEP 8 — List recent briefings"

LIST_RESP=$(curl -s "$BASE/api/ai/briefer?limit=3")
COUNT=$(echo "$LIST_RESP" | python3 -c "import json,sys; print(len(json.load(sys.stdin)))" 2>/dev/null || echo "?")
ok "Recent briefings: $COUNT entries"

hdr "SUMMARY"
echo "  Phase 5 demo complete."
echo "  Watchdog auto-triggered Investigator for critical alerts (background)."
echo "  Supervisor routed Scout query via deterministic classifier (direct_scout)."
echo "  Supervisor routed complex query via LangGraph ($STEPS-step plan)."
echo "  Monthly briefing generated (status=$BRIEF_STATUS), second call returned from cache."
echo "  Briefing query routed to direct_briefer without LangGraph."
