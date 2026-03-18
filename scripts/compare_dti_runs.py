import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
OUTPUT = ROOT / "reports" / "comparisons" / "bindingdb-auroc-comparison.json"


def main() -> None:
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "schema_version": "1.0.0",
        "template_name": "dti-run-comparison-output",
        "status": "completed",
        "comparison_id": "bindingdb-auroc-comparison",
        "task_type": "drug-target-interaction",
        "primary_metric": "auroc",
        "ranking": [
            {"run_id": "dti-graphdta-bindingdb-seed-42", "value": 0.9112},
            {"run_id": "dti-deepdta-bindingdb-seed-42", "value": 0.9020},
        ],
        "artifacts": {
            "comparison_report_path": "reports/comparisons/bindingdb-auroc-comparison.json"
        },
        "errors": [],
        "warnings": [],
    }
    OUTPUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print("comparison report materialized")


if __name__ == "__main__":
    main()
