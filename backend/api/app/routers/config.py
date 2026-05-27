import json
from fastapi import APIRouter
from pathlib import Path

router = APIRouter()


@router.get("/config/scoring")
def get_scoring_config():
    """
    Get scoring configuration including formula weights.

    Returns the contents of scoring_config.json which defines:
    - formula_weights: Weight for each component (severity, persistence, peer_gap, commercial, evidence)
    - severity_z_score_max: Maximum Z-score for severity normalization
    - persistence_window_months: Window for persistence calculation
    - peer_rank_scores: Score mapping for peer ranks
    - evidence_max_count: Maximum evidence count for full score
    - health_status_thresholds: Thresholds for health status classification
    """
    config_path = Path(__file__).parent.parent / "config" / "scoring_config.json"
    with open(config_path, "r") as f:
        return json.load(f)
