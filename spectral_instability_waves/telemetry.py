from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.request import urlopen


@dataclass(frozen=True)
class TelemetryPoint:
    timestamp: float
    node: str
    error_rate: float
    latency_ms: float
    saturation: float


class TelemetryFetcher:
    """Fetches telemetry samples from file paths or HTTP(S) JSON sources."""

    def fetch(self, source: str) -> list[TelemetryPoint]:
        payload = self._load_json(source)
        return self._parse_payload(payload)

    def _load_json(self, source: str) -> Any:
        if source.startswith(("http://", "https://")):
            with urlopen(source) as response:  # nosec B310
                return json.loads(response.read().decode("utf-8"))
        return json.loads(Path(source).read_text(encoding="utf-8"))

    def _parse_payload(self, payload: Any) -> list[TelemetryPoint]:
        if isinstance(payload, dict):
            samples = payload.get("samples", [])
        elif isinstance(payload, list):
            samples = payload
        else:
            raise ValueError("Telemetry payload must be a list or object with 'samples'.")

        points: list[TelemetryPoint] = []
        for sample in samples:
            points.append(
                TelemetryPoint(
                    timestamp=float(sample["timestamp"]),
                    node=str(sample["node"]),
                    error_rate=float(sample.get("error_rate", 0.0)),
                    latency_ms=float(sample.get("latency_ms", 0.0)),
                    saturation=float(sample.get("saturation", 0.0)),
                )
            )
        return points
