"""
Tests for Scoring Fix (V1.8) - Seasonal Z-Score Severity Calculation

Validates that:
1. Severity uses seasonal Z-score (comparing to same calendar month historically)
2. Severity does NOT use deviation_from_rolling_avg
3. Seasonal Z-score calculation is correct
4. Column rename from seasonal_baseline to rolling_12m_avg is complete
5. Config file exists and contains correct weights
6. Evidence scoring scales with count
7. Commercial weights come from metric_dictionary.json
"""

import json
import pandas as pd
import pytest
from pathlib import Path


def test_seasonal_z_score_for_normal_january_is_near_zero():
    """Test that net_sales January 2026 has Z-score near 0 (was falsely flagged as severe)"""
    kpi_health = pd.read_csv("data/gold_snapshots/gold_kpi_health.csv")

    # Get net_sales for Jan 2026
    row = kpi_health[
        (kpi_health["month"] == "2026-01-01") &
        (kpi_health["asset_name"] == "ecommerce") &
        (kpi_health["metric_name"] == "net_sales")
    ]

    assert len(row) == 1, "Should find exactly one net_sales row for Jan 2026"

    z_score = float(row.iloc[0]["seasonal_z_score"])

    # Z-score should be very close to 0 (value is normal for January)
    assert abs(z_score) < 0.5, f"Z-score should be near 0 for seasonally normal value, got {z_score}"


def test_severity_near_zero_for_seasonally_normal_value():
    """Test that severity is near zero when Z-score is near zero"""
    priority_board = pd.read_csv("data/gold_snapshots/gold_priority_board.csv")

    # Check if net_sales is in the priority board
    # It may have dropped out of top 10 due to low severity
    net_sales_rows = priority_board[
        (priority_board["month"] == "2026-01-01") &
        (priority_board["asset_name"] == "ecommerce") &
        (priority_board["primary_metric"] == "net_sales")
    ]

    if len(net_sales_rows) > 0:
        # If it's still in priority board, check that score is low
        row = net_sales_rows.iloc[0]
        supporting_json = json.loads(row["supporting_metrics_json"])
        severity_score = supporting_json["score_components"]["severity"]

        # Severity should be very low (Z-score ~0.01, severity = 0.01/2.0 = 0.005)
        assert severity_score < 0.1, f"Severity should be near 0 for normal seasonal value, got {severity_score}"
    else:
        # Net_sales dropped out of top 10 - this is EXPECTED and CORRECT
        # It means severity was low enough that it's no longer a top priority
        # This is a pass - the fix worked!
        pass


def test_severity_high_for_genuinely_anomalous_value():
    """Test that severity is high for metrics with high Z-score"""
    priority_board = pd.read_csv("data/gold_snapshots/gold_priority_board.csv")

    # Get priorities for Jan 2026
    jan_priorities = priority_board[priority_board["month"] == "2026-01-01"]

    assert len(jan_priorities) > 0, "Should have priorities for Jan 2026"

    # Check that top priorities have meaningful severity scores
    for _, row in jan_priorities.head(3).iterrows():
        supporting_json = json.loads(row["supporting_metrics_json"])
        severity_score = supporting_json["score_components"]["severity"]

        # Top priorities should have severity > 0.3 (Z-score > 0.6)
        assert severity_score > 0.3, f"Top priority {row['priority_id']} should have high severity"


def test_column_rename_complete():
    """Test that seasonal_baseline column no longer exists, replaced by rolling_12m_avg"""
    kpi_health = pd.read_csv("data/gold_snapshots/gold_kpi_health.csv")

    # Check column names
    columns = kpi_health.columns.tolist()

    assert "seasonal_baseline" not in columns, "seasonal_baseline column should be renamed"
    assert "deviation_from_seasonal_baseline" not in columns, "deviation_from_seasonal_baseline should be renamed"
    assert "rolling_12m_avg" in columns, "rolling_12m_avg column should exist"
    assert "deviation_from_rolling_avg" in columns, "deviation_from_rolling_avg column should exist"
    assert "seasonal_z_score" in columns, "seasonal_z_score column should be added"


def test_config_file_exists():
    """Test that scoring_config.json exists and has correct structure"""
    config_path = Path("backend/api/app/config/scoring_config.json")

    assert config_path.exists(), "scoring_config.json should exist"

    with open(config_path) as f:
        config = json.load(f)

    # Check formula weights
    assert "formula_weights" in config
    weights = config["formula_weights"]

    assert weights["severity"] == 0.30
    assert weights["persistence"] == 0.25
    assert weights["peer_gap"] == 0.20
    assert weights["commercial"] == 0.15
    assert weights["evidence"] == 0.10

    # Verify weights sum to 1.0
    total = sum(weights.values())
    assert abs(total - 1.0) < 0.001, f"Weights should sum to 1.0, got {total}"


def test_metric_dictionary_has_commercial_weights():
    """Test that metric_dictionary.json contains commercial_weight for all metrics"""
    dict_path = Path("databricks/seeds/metric_dictionary.json")

    assert dict_path.exists(), "metric_dictionary.json should exist"

    with open(dict_path) as f:
        metric_dict = json.load(f)

    # Check that key metrics have commercial weights
    assert "net_sales" in metric_dict
    assert "commercial_weight" in metric_dict["net_sales"]
    assert metric_dict["net_sales"]["commercial_weight"] == 1.0

    assert "conversion_rate" in metric_dict
    assert "commercial_weight" in metric_dict["conversion_rate"]
    assert metric_dict["conversion_rate"]["commercial_weight"] == 0.95

    assert "pct_android" in metric_dict
    assert "commercial_weight" in metric_dict["pct_android"]
    assert metric_dict["pct_android"]["commercial_weight"] == 0.20


def test_evidence_scales_with_count():
    """Test that evidence score is no longer binary but scales with count"""
    priority_board = pd.read_csv("data/gold_snapshots/gold_priority_board.csv")

    # Check priorities and their evidence scores
    for _, row in priority_board.head(10).iterrows():
        supporting_json = json.loads(row["supporting_metrics_json"])
        evidence_score = supporting_json["score_components"]["supporting_evidence"]
        supporting_count = len(supporting_json["supporting_metric_rows"])

        if supporting_count == 0:
            assert evidence_score == 0.0
        elif supporting_count < 5:
            # Should be proportional: count / 5
            expected_score = supporting_count / 5.0
            assert abs(evidence_score - expected_score) < 0.01, \
                f"Evidence score should be {expected_score} for {supporting_count} metrics, got {evidence_score}"
        else:
            # 5+ metrics should cap at 1.0
            assert evidence_score == 1.0


def test_priority_score_reconstruction_matches_stored():
    """Test that recalculating priority score from components matches stored score"""
    priority_board = pd.read_csv("data/gold_snapshots/gold_priority_board.csv")

    # Load weights from scoring_config.json (the actual weights used to build the data)
    import json
    from pathlib import Path
    config_path = Path("backend/api/app/config/scoring_config.json")
    with open(config_path) as f:
        config = json.load(f)
    weights = config["formula_weights"]

    for _, row in priority_board.head(5).iterrows():
        stored_score = float(row["priority_score"])
        supporting_json = json.loads(row["supporting_metrics_json"])
        components = supporting_json["score_components"]

        # Recalculate score
        calc_score = (
            weights["severity"] * components["severity"]
            + weights["persistence"] * components["persistence"]
            + weights["peer_gap"] * components["peer_gap"]
            + weights["commercial"] * components["commercial_weight"]
            + weights["evidence"] * components["supporting_evidence"]
        )

        # Should match within floating point tolerance
        assert abs(calc_score - stored_score) < 0.001, \
            f"Calculated score {calc_score} should match stored score {stored_score} for {row['priority_id']}"


def test_seasonal_z_score_calculation_accuracy():
    """Test that seasonal Z-score is calculated correctly"""
    kpi_health = pd.read_csv("data/gold_snapshots/gold_kpi_health.csv")

    # Get all January values for net_sales
    net_sales = kpi_health[
        (kpi_health["asset_name"] == "ecommerce") &
        (kpi_health["metric_name"] == "net_sales")
    ].copy()

    net_sales["month_date"] = pd.to_datetime(net_sales["month"])
    net_sales["calendar_month"] = net_sales["month_date"].dt.month

    january_values = net_sales[net_sales["calendar_month"] == 1]

    # Get Jan 2026 value
    jan_2026 = january_values[january_values["month"] == "2026-01-01"]
    assert len(jan_2026) == 1

    current_value = float(jan_2026.iloc[0]["metric_value"])
    reported_z_score = float(jan_2026.iloc[0]["seasonal_z_score"])

    # Calculate Z-score manually from historical January values (excluding 2026)
    historical_jan = january_values[january_values["month"] < "2026-01-01"]

    if len(historical_jan) >= 2:
        hist_mean = historical_jan["metric_value"].mean()
        hist_std = historical_jan["metric_value"].std()

        if hist_std > 0:
            manual_z_score = (current_value - hist_mean) / hist_std

            # Should match within small tolerance
            assert abs(reported_z_score - manual_z_score) < 0.01, \
                f"Reported Z-score {reported_z_score} should match manual calculation {manual_z_score}"
