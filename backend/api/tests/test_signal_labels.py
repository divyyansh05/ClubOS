"""
Tests for V1.5.5 Driver/Outcome Variable Labelling

Validates that signal responses include driver/outcome labels,
causal direction statements, and action statements based on
current signal status.
"""

from app.services.signal_service import get_signal_view


def test_signal_response_includes_driver_label():
    """All signals should have driver_label field"""
    result = get_signal_view()
    assert len(result["items"]) > 0, "No signals found in test data"

    for signal in result["items"]:
        assert "driver_label" in signal
        assert signal["driver_label"] == "Independent Variable (Driver)"


def test_signal_response_includes_outcome_label():
    """All signals should have outcome_label field"""
    result = get_signal_view()

    for signal in result["items"]:
        assert "outcome_label" in signal
        assert signal["outcome_label"] == "Dependent Variable (Outcome)"


def test_causal_direction_statement_is_non_empty():
    """All signals should have non-empty causal_direction_statement"""
    result = get_signal_view()

    for signal in result["items"]:
        assert "causal_direction_statement" in signal
        assert signal["causal_direction_statement"] is not None
        assert len(signal["causal_direction_statement"]) > 0
        assert "precede" in signal["causal_direction_statement"].lower()


def test_action_statement_changes_based_on_signal_status():
    """Action statements should differ based on current_status"""
    result = get_signal_view()

    firing_positive_statements = []
    firing_negative_statements = []
    neutral_statements = []

    for signal in result["items"]:
        assert "action_statement" in signal
        assert signal["action_statement"] is not None

        if signal.get("current_status") == "firing_positive":
            firing_positive_statements.append(signal["action_statement"])
        elif signal.get("current_status") == "firing_negative":
            firing_negative_statements.append(signal["action_statement"])
        else:
            neutral_statements.append(signal["action_statement"])

    # Verify statements are different across statuses
    # (They should contain status-specific language)
    if firing_positive_statements:
        assert any("rising" in s.lower() for s in firing_positive_statements)
    if firing_negative_statements:
        assert any("declining" in s.lower() for s in firing_negative_statements)
    if neutral_statements:
        assert any("stable" in s.lower() or "monitoring" in s.lower() for s in neutral_statements)


def test_firing_positive_action_statement_contains_expected_language():
    """Firing positive signals should have 'rising' and 'upward' language"""
    result = get_signal_view()

    firing_positive_signals = [
        s for s in result["items"]
        if s.get("current_status") == "firing_positive"
    ]

    if len(firing_positive_signals) > 0:
        for signal in firing_positive_signals:
            action = signal["action_statement"].lower()
            assert "rising" in action or "upward" in action
            assert "anticipated" in action or "expected" in action or "anticipate" in action


def test_firing_negative_action_statement_contains_expected_language():
    """Firing negative signals should have 'declining' and 'downward' language"""
    result = get_signal_view()

    firing_negative_signals = [
        s for s in result["items"]
        if s.get("current_status") == "firing_negative"
    ]

    if len(firing_negative_signals) > 0:
        for signal in firing_negative_signals:
            action = signal["action_statement"].lower()
            assert "declining" in action or "downward" in action
            assert "flag" in action or "intervention" in action or "expected" in action


def test_relationship_type_is_leading_indicator():
    """All signals with lag > 0 should be marked as leading_indicator"""
    result = get_signal_view()

    for signal in result["items"]:
        assert "relationship_type" in signal
        if signal["lag_months"] > 0:
            assert signal["relationship_type"] == "leading_indicator"


def test_causal_direction_statement_includes_metric_names():
    """Causal direction statement should reference both source and target metrics"""
    result = get_signal_view()

    for signal in result["items"]:
        statement = signal["causal_direction_statement"]
        assert signal["source_metric"] in statement
        assert signal["target_metric"] in statement


def test_action_statement_includes_lag_months():
    """Action statements should reference the lag time window"""
    result = get_signal_view()

    for signal in result["items"]:
        action = signal["action_statement"]
        # Should mention lag months in some form
        assert str(signal["lag_months"]) in action or "month" in action.lower()
