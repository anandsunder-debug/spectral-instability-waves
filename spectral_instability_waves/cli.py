from __future__ import annotations

import argparse
import json
from pathlib import Path

from .modeling import FailureWavePredictor
from .telemetry import TelemetryFetcher


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Fetch telemetry and predict instability-wave failure propagation."
    )
    parser.add_argument("--source", required=True, help="Telemetry JSON file path or HTTP(S) URL.")
    parser.add_argument("--graph", help="Path to JSON adjacency graph: {'node': ['neighbor']}.")
    parser.add_argument(
        "--field-map",
        help="Path to JSON map of canonical fields to source fields, e.g. {'timestamp':'ts','node':'service'}.",
    )
    parser.add_argument(
        "--samples-path",
        help="Dot path to samples array in payload, e.g. 'data.points'.",
    )
    parser.add_argument("--steps", type=int, default=2, help="Wave propagation steps.")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    graph = {}
    if args.graph:
        graph = json.loads(Path(args.graph).read_text(encoding="utf-8"))

    field_map = None
    if args.field_map:
        field_map = json.loads(Path(args.field_map).read_text(encoding="utf-8"))

    points = TelemetryFetcher().fetch(args.source, field_map=field_map, samples_path=args.samples_path)
    predictor = FailureWavePredictor(graph=graph)
    results = predictor.predict(points, propagation_steps=args.steps)

    print(
        json.dumps(
            [
                {
                    "node": result.node,
                    "instability_score": round(result.instability_score, 4),
                    "predicted_failure_probability": round(result.predicted_failure_probability, 4),
                    "wave_depth": result.wave_depth,
                }
                for result in results
            ],
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
