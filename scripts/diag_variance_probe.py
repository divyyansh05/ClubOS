"""
Runs 3 sample questions through Scout twice each. Captures full ScoutAnswer.
Diffs outputs to identify WHERE non-determinism enters.

Non-writing to any persistent state. Purely diagnostic.
"""
import asyncio
import json
import sys
from pathlib import Path

# Ensure project root is on path so eval.golden.* resolves
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from clubos2.agents.scout import run_scout
from clubos2.agents.scout_schemas import ScoutInput

QUESTIONS = [
    ("gq_001_style", "What was the streaming_daily_users value in the most recent month?"),
    ("gq_012_style", "What is the current conversion_rate_ecommerce and is it a problem?"),
    ("gq_019_style", "Who is the highest-paid player at Real Madrid this season?"),
]

async def run_probe():
    results = {}
    for label, question in QUESTIONS:
        results[label] = {"question": question, "runs": []}
        for run_idx in [1, 2]:
            print(f"Running {label} pass {run_idx}...")
            answer = await run_scout(ScoutInput(question=question))
            results[label]["runs"].append({
                "run_idx": run_idx,
                "answer_text": answer.answer,
                "confidence": answer.confidence.value if hasattr(answer.confidence, "value") else str(answer.confidence),
                "citations": [c.model_dump() for c in answer.citations],
                "metrics_queried": answer.metrics_queried,
                "assumptions_made": answer.assumptions_made,
                "retrieved_contexts": answer.retrieved_contexts[:3] if answer.retrieved_contexts else [],
            })
    Path("var/diag_variance_probe.json").parent.mkdir(exist_ok=True)
    Path("var/diag_variance_probe.json").write_text(json.dumps(results, indent=2))
    print("Saved to var/diag_variance_probe.json")

    print("\n=== DIFFS ===")
    for label, data in results.items():
        r1, r2 = data["runs"]
        print(f"\n{label}:")
        print(f"  retrieved_contexts match: {r1['retrieved_contexts'] == r2['retrieved_contexts']}")
        print(f"  citations match:          {r1['citations'] == r2['citations']}")
        print(f"  metrics_queried match:    {r1['metrics_queried'] == r2['metrics_queried']}")
        print(f"  confidence match:         {r1['confidence'] == r2['confidence']}")
        print(f"  answer_text match:        {r1['answer_text'] == r2['answer_text']}")
        if r1['answer_text'] != r2['answer_text']:
            print("    → LLM sampling non-determinism above the retrieval layer")

asyncio.run(run_probe())
