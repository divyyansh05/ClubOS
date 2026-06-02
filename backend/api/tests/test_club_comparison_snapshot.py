from pathlib import Path

import pandas as pd


def test_club_comparison_snapshot_contains_full_club_list() -> None:
    csv_path = Path(__file__).resolve().parents[3] / "data" / "gold_snapshots" / "gold_club_comparison.csv"
    assert csv_path.exists(), "gold_club_comparison.csv must exist"

    df = pd.read_csv(csv_path)
    sample = df[
        (df["asset_name"] == "ecommerce")
        & (df["metric_name"] == "conversion_rate")
        & (df["month"] == "2026-01-01")
    ]

    assert len(sample) == 6, "club comparison snapshot should include Real Madrid plus five peer clubs"
    assert (sample["club"] == "Real Madrid").any(), "Real Madrid row missing from club comparison snapshot"