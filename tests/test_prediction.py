import json
import tempfile
import unittest
from pathlib import Path

from spectral_instability_waves import FailureWavePredictor, TelemetryFetcher


class TelemetryAndPredictionTests(unittest.TestCase):
    def test_fetches_telemetry_from_file(self) -> None:
        samples = [
            {"timestamp": 1, "node": "a", "error_rate": 0.2, "latency_ms": 120, "saturation": 0.3},
            {"timestamp": 2, "node": "a", "error_rate": 0.4, "latency_ms": 130, "saturation": 0.4},
        ]
        with tempfile.TemporaryDirectory() as tempdir:
            path = Path(tempdir) / "telemetry.json"
            path.write_text(json.dumps({"samples": samples}), encoding="utf-8")
            fetched = TelemetryFetcher().fetch(str(path))
        self.assertEqual(len(fetched), 2)
        self.assertEqual(fetched[-1].node, "a")
        self.assertAlmostEqual(fetched[-1].error_rate, 0.4)

    def test_predicts_failure_propagation_wave(self) -> None:
        telemetry = TelemetryFetcher()._parse_payload(
            [
                {"timestamp": 1, "node": "core", "error_rate": 0.8, "latency_ms": 900, "saturation": 0.7},
                {"timestamp": 2, "node": "core", "error_rate": 0.9, "latency_ms": 980, "saturation": 0.9},
                {"timestamp": 2, "node": "edge", "error_rate": 0.1, "latency_ms": 100, "saturation": 0.2},
            ]
        )
        predictor = FailureWavePredictor(graph={"core": ["edge"]}, decay=0.6)
        results = predictor.predict(telemetry, propagation_steps=2)
        by_node = {result.node: result for result in results}
        self.assertGreater(by_node["core"].predicted_failure_probability, by_node["edge"].predicted_failure_probability)
        self.assertEqual(by_node["edge"].wave_depth, 1)
        self.assertGreater(by_node["edge"].predicted_failure_probability, 0.0)


if __name__ == "__main__":
    unittest.main()
