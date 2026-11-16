import argparse
import json
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from main import analyse
from settings import MODEL_PATH


def save_result(result, results_dir):
    # Reject unsupported values before creating a run folder.
    content = json.dumps(result, indent=2, allow_nan=False)
    results_dir = Path(results_dir)
    results_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    run_dir = Path(tempfile.mkdtemp(prefix=f"run-{timestamp}-", dir=results_dir))
    output = run_dir / "result.json"
    output.write_text(content + "\n", encoding="utf-8")
    return output


def main():
    parser = argparse.ArgumentParser(description="Run your analysis on a local IFC.")
    parser.add_argument(
        "model", nargs="?", type=Path,
        help="IFC path (defaults to MODEL_PATH in src/settings.py)",
    )
    parser.add_argument(
        "--results-dir",
        type=Path,
        default=Path(__file__).resolve().parents[1] / "results",
        help="Output directory (default: this capability's results folder)",
    )
    args = parser.parse_args()
    if args.model is None:
        if not MODEL_PATH.strip():
            parser.error("Set MODEL_PATH in src/settings.py or pass an IFC path.")
        args.model = Path(MODEL_PATH)
        if not args.model.is_absolute():
            args.model = Path(__file__).resolve().parents[1] / args.model
    if not args.model.is_file():
        parser.error(f"IFC file not found: {args.model}")

    import ifcopenshell

    model = ifcopenshell.open(str(args.model))
    result = analyse(model)
    output = save_result(result, args.results_dir)
    print(f"Result saved to: {output.resolve()}")


if __name__ == "__main__":
    main()
