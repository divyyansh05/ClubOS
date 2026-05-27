import pandas as pd
from pathlib import Path



def test_social_metrics_in_gold_peer_benchmark():
    """
    Test that gold_peer_benchmark.csv contains social_media assets.
    """
    csv_path = Path(__file__).resolve().parents[3] / "data" / "gold_snapshots" / "gold_peer_benchmark.csv"
    assert csv_path.exists(), "gold_peer_benchmark.csv must exist"
    
    df = pd.read_csv(csv_path)
    social_df = df[df["asset_name"] == "social_media"]
    
    assert not social_df.empty, "gold_peer_benchmark.csv should contain social_media rows"
    
    # Check that it has the expected metrics
    metrics = social_df["metric_name"].unique()
    assert "avg_engagement_per_post" in metrics
    assert "total_engagement" in metrics
