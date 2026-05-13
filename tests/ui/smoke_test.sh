#!/bin/bash
#
# UI Smoke Test - Basic health checks for MVP screens
#
# Tests that:
# 1. Frontend dev server is running
# 2. All MVP pages return HTML (not 404)
# 3. Page titles are correct
#
# Usage:
#   ./tests/ui/smoke_test.sh [base_url]
#
# Default base_url: http://localhost:5176

BASE_URL="${1:-http://localhost:5176}"

echo "🧪 UI Smoke Test"
echo "=" 60
echo "Base URL: $BASE_URL"
echo ""

# Track failures
FAILURES=0

# Helper function to test a page
test_page() {
    local path="$1"
    local expected_title="$2"
    local url="$BASE_URL$path"

    echo -n "Testing $path ... "

    # Check if page returns 200
    status=$(curl -s -o /dev/null -w "%{http_code}" "$url")
    if [ "$status" != "200" ]; then
        echo "❌ FAIL (HTTP $status)"
        FAILURES=$((FAILURES + 1))
        return 1
    fi

    # Check if page contains expected title
    content=$(curl -s "$url")
    if echo "$content" | grep -q "<title>$expected_title</title>"; then
        echo "✅ PASS"
        return 0
    else
        echo "❌ FAIL (title mismatch)"
        FAILURES=$((FAILURES + 1))
        return 1
    fi
}

# Test all MVP pages
test_page "/" "ClubOS"
test_page "/priorities" "ClubOS"
test_page "/command-center" "ClubOS"
test_page "/benchmark" "ClubOS"
test_page "/signals" "ClubOS"
test_page "/briefing" "ClubOS"

# Summary
echo ""
echo "=" | head -c 60
echo ""
if [ $FAILURES -eq 0 ]; then
    echo "✅ ALL SMOKE TESTS PASSED"
    exit 0
else
    echo "❌ $FAILURES SMOKE TEST(S) FAILED"
    exit 1
fi
