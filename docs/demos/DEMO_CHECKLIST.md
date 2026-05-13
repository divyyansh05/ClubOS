# ClubOS Demo Checklist

**Pre-demo verification to ensure demo-safe environment.**

---

## Before Demo

### Environment Setup

- [ ] Backend running: `cd backend/api && uvicorn app.main:app --reload`
- [ ] Frontend running: `cd apps/clubos-web && npm run dev`
- [ ] Browser open: `http://localhost:5176`
- [ ] Network stable (no firewall/VPN issues)

### Data Verification

- [ ] Gold snapshots exist: `ls data/gold_snapshots/*.csv`
- [ ] Latest month: **2026-01-01** (verify in Priority Board)
- [ ] Test suite passing: `./scripts/run_all_tests.sh`

### Backend Health

Run these curl commands and verify output:

```bash
# Priority Board (should return 10 priorities)
curl -s http://localhost:8000/priorities/latest | python3 -c "import sys, json; d = json.load(sys.stdin); print(f'Priorities: {len(d[\"items\"])}')"

# Health summary (should return 59 metrics)
curl -s http://localhost:8000/health/summary | python3 -c "import sys, json; d = json.load(sys.stdin); print(f'Metrics: {d[\"metric_count\"]}')"

# Benchmark (should return 103 months)
curl -s http://localhost:8000/benchmark/ecommerce/conversion_rate | python3 -c "import sys, json; d = json.load(sys.stdin); print(f'Months: {len(d[\"points\"])}')"

# Signals (should return 2 signals)
curl -s http://localhost:8000/signals | python3 -c "import sys, json; d = json.load(sys.stdin); print(f'Signals: {len(d[\"items\"])}')"

# Briefing (should return 3 top priorities)
curl -s http://localhost:8000/briefing/latest | python3 -c "import sys, json; d = json.load(sys.stdin); print(f'Briefing priorities: {len(d[\"top_priorities\"])}')"
```

**Expected output:**
```
Priorities: 10
Metrics: 59
Months: 103
Signals: 2
Briefing priorities: 3
```

### Frontend Health

- [ ] Priority Board loads (no blank screen)
- [ ] Summary strip shows: 3 critical, 1 opportunity, 5 benchmark issues
- [ ] Top priority card visible: "#1: Conversion Weakness in Ecommerce"
- [ ] "View evidence" button clickable
- [ ] Evidence modal opens and shows score breakdown bars
- [ ] All sidebar nav links work (no 404s)

### Page-by-Page Verification

**Priority Board:**
- [ ] Loads on `http://localhost:5176/priorities`
- [ ] Shows latest_month: 2026-01-01
- [ ] Shows 10 priority cards
- [ ] Click "View evidence" → modal opens
- [ ] Modal shows 5 score breakdown bars
- [ ] Close modal works

**Command Center:**
- [ ] Loads on `http://localhost:5176/command-center`
- [ ] Shows 4 overview cards
- [ ] Shows health bars (good/review/stable)
- [ ] Shows avg deviation

**Peer Benchmark:**
- [ ] Loads on `http://localhost:5176/benchmark`
- [ ] Metric selector dropdown functional
- [ ] "eCommerce - Conversion Rate" selected
- [ ] Shows rank #4 out of 5
- [ ] Shows current position snapshot
- [ ] Shows 12-month trend table

**Signal Engine:**
- [ ] Loads on `http://localhost:5176/signals`
- [ ] Shows 2 validated signals
- [ ] Signal cards clickable
- [ ] Detail view shows metadata + interpretation

**Monthly Briefing:**
- [ ] Loads on `http://localhost:5176/briefing`
- [ ] Shows top 3 priorities section
- [ ] Shows top 3 anomalies section
- [ ] Shows benchmark summary
- [ ] Shows signals section
- [ ] Shows health summary

---

## Demo Flow Verification

### Critical Path (Must Work)

1. [ ] Open app → auto-routes to `/priorities`
2. [ ] See summary strip at top
3. [ ] See #1 priority card
4. [ ] Click "View evidence" → modal opens
5. [ ] See 5 score breakdown bars
6. [ ] Close modal
7. [ ] Navigate to Peer Benchmark
8. [ ] See conversion_rate data
9. [ ] Navigate to Signal Engine
10. [ ] See 2 signals
11. [ ] Navigate to Monthly Briefing
12. [ ] See top 3 priorities + anomalies

**If all 12 steps ✅ → demo-safe**

### Optional Path (Nice to Have)

- [ ] Try different metric in Peer Benchmark dropdown
- [ ] Click on signal card to see detail
- [ ] Scroll through briefing sections

---

## Fallback Plan (If Something Breaks)

### If Priority Board fails:
1. Open DevTools → Network tab
2. Show `/priorities/latest` response (JSON)
3. Explain: "Frontend rendering issue, but backend data valid"

### If backend fails:
1. Open `data/gold_snapshots/gold_priority_board.csv`
2. Show first few rows
3. Explain: "Data layer valid, API connectivity issue"

### If frontend white screen:
1. Open DevTools → Console
2. Check for React errors
3. Show test suite: `./scripts/run_all_tests.sh`
4. Explain: "Tests pass, proven system works"

### Complete failure:
1. Show demo video/screenshots (if prepared)
2. Walk through `docs/demos/demo_script.md`
3. Show Gold snapshots in CSV
4. Show test results

---

## Post-Demo

### If Demo Successful:
- [ ] Note any questions asked
- [ ] Note any features requested
- [ ] Close browser tabs
- [ ] Stop backend/frontend servers

### If Demo Had Issues:
- [ ] Document exact failure point
- [ ] Check logs for errors
- [ ] Re-run test suite to identify regression
- [ ] Fix before next demo

---

## Quick Reference

**Start backend:**
```bash
cd backend/api
source ../../clubosvenv/bin/activate
uvicorn app.main:app --reload
```

**Start frontend:**
```bash
cd apps/clubos-web
npm run dev
```

**Run tests:**
```bash
./scripts/run_all_tests.sh
```

**Frontend URL:**
```
http://localhost:5176
```

**Backend health:**
```
http://localhost:8000/health
```

---

## Demo Confidence Score

After completing this checklist:

- **10+ items checked** → Proceed with demo
- **<10 items checked** → Fix issues first
- **Critical path working** → Minimum demo-safe
- **All items checked** → Fully demo-ready

---

## Final Check

✅ Backend responding
✅ Frontend loading
✅ Tests passing
✅ Demo flow verified
✅ Fallback plan ready

**→ Demo-safe ✅**
