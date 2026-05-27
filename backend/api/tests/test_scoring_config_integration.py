"""
Tests for Scoring Config Integration (V1.8.1)

Validates that:
1. scoring_config.json file exists and is valid
2. Config endpoint returns correct data
3. Weights sum to 1.0
4. Build scripts read from config (not hardcoded)
5. Score breakdowns match config weights
"""

import json
import os
from pathlib import Path

import pandas as pd
import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_scoring_config_file_exists():
    """Test that scoring_config.json exists and is readable"""
    config_path = Path("backend/api/app/config/scoring_config.json")
    assert config_path.exists(), "scoring_config.json should exist"


def test_scoring_config_weights_sum_to_one():
    """Test that formula weights sum to exactly 1.0"""
    config_path = Path("backend/api/app/config/scoring_config.json")
    with open(config_path) as f:
        config = json.load(f)

    weights = config["formula_weights"]
    total = sum(weights.values())
    assert abs(total - 1.0) < 0.0001, f"Weights should sum to 1.0, got {total}"


def test_scoring_config_endpoint_returns_200():
    """Test GET /config/scoring returns 200 and valid data"""
    response = client.get("/config/scoring")
    assert response.status_code == 200

    data = response.json()
    assert "formula_weights" in data
    assert "severity" in data["formula_weights"]
    assert "persistence" in data["formula_weights"]
    assert "peer_gap" in data["formula_weights"]
    assert "commercial" in data["formula_weights"]
    assert "evidence" in data["formula_weights"]

    # Weights should sum to 1.0
    total = sum(data["formula_weights"].values())
    assert abs(total - 1.0) < 0.0001


def test_score_breakdown_matches_config_weights():
    """Test that scores in priority_board match config weights"""
    config_path = Path("backend/api/app/config/scoring_config.json")
    with open(config_path) as f:
        config = json.load(f)
    weights = config["formula_weights"]

    # Read any row from gold_priority_board.csv
    priority_board = pd.read_csv("data/gold_snapshots/gold_priority_board.csv")

    for _, row in priority_board.head(3).iterrows():
        stored_score = float(row["priority_score"])
        supporting_json = json.loads(row["supporting_metrics_json"])
        components = supporting_json["score_components"]

        # Reconstruct score using config weights
        reconstructed = (
            weights["severity"] * components["severity"] +
            weights["persistence"] * components["persistence"] +
            weights["peer_gap"] * components["peer_gap"] +
            weights["commercial"] * components["commercial_weight"] +
            weights["evidence"] * components["supporting_evidence"]
        )

        assert abs(reconstructed - stored_score) < 0.001, \
            f"Reconstructed score {reconstructed} should match stored {stored_score}"


def test_no_hardcoded_weights_in_build_script():
    """Test that build script uses WEIGHTS variable not hardcoded literals"""
    with open("scripts/build_local_snapshots.py") as f:
        content = f.read()

    # Check that WEIGHTS variable is defined
    assert "WEIGHTS = SCORING_CONFIG" in content, \
        "Build script should load WEIGHTS from SCORING_CONFIG"

    # Check that scoring uses WEIGHTS["severity"] pattern
    assert 'WEIGHTS["severity"]' in content, \
        "Build script should use WEIGHTS['severity'] not hardcoded value"
    assert 'WEIGHTS["persistence"]' in content, \
        "Build script should use WEIGHTS['persistence'] not hardcoded value"


def test_config_contains_all_required_fields():
    """Test that scoring_config.json has all required fields"""
    config_path = Path("backend/api/app/config/scoring_config.json")
    with open(config_path) as f:
        config = json.load(f)

    # Check required top-level fields
    assert "formula_weights" in config
    assert "severity_z_score_max" in config
    assert "persistence_window_months" in config
    assert "peer_rank_scores" in config
    assert "evidence_max_count" in config
    assert "health_status_thresholds" in config

    # Check formula_weights has all 5 components
    weights = config["formula_weights"]
    assert len(weights) == 5
    assert all(k in weights for k in ["severity", "persistence", "peer_gap", "commercial", "evidence"])


def test_config_values_are_in_valid_ranges():
    """Test that config values are reasonable"""
    config_path = Path("backend/api/app/config/scoring_config.json")
    with open(config_path) as f:
        config = json.load(f)

    # All weights should be between 0 and 1
    for component, weight in config["formula_weights"].items():
        assert 0 <= weight <= 1, f"{component} weight should be in [0,1], got {weight}"

    # Z-score max should be positive
    assert config["severity_z_score_max"] > 0

    # Evidence max count should be positive
    assert config["evidence_max_count"] > 0

    # Persistence window should be positive
    assert config["persistence_window_months"] > 0


def test_target_keys_not_in_codebase():
    """Test that TARGET_KEYS hardcoded list has been removed"""
    files_to_check = [
        "databricks/notebooks/analytics/02_compute_priority_inputs.py",
        "scripts/build_local_snapshots.py"
    ]
    for filepath in files_to_check:
        with open(filepath) as f:
            content = f.read()
        assert "TARGET_KEYS" not in content, \
            f"TARGET_KEYS still present in {filepath}"
        assert "target_keys" not in content, \
            f"target_keys still present in {filepath}"
