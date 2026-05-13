#!/bin/bash
#
# ClubOS Test Runner
#
# Runs all executable tests:
# 1. Gold snapshot validation
# 2. API contract tests
# 3. UI smoke tests
#
# Usage:
#   ./scripts/run_all_tests.sh

set -e  # Exit on first failure

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

echo "🧪 ClubOS Test Suite"
echo "===================="
echo ""

# 1. Data validation
echo "📊 Running Gold snapshot validation..."
python3 tests/data/validate_gold_snapshots.py
echo ""

# 2. API tests
echo "🔌 Running API contract tests..."
cd backend/api
python -m pytest tests/test_api_contracts.py -v --tb=short
cd "$PROJECT_ROOT"
echo ""

# 3. UI smoke tests
echo "🌐 Running UI smoke tests..."
./tests/ui/smoke_test.sh
echo ""

echo "===================="
echo "✅ ALL TESTS PASSED"
echo ""
