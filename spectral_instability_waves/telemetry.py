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

    def fetch(
        self,
        source: str,
        *,
        field_map: dict[str, str] | None = None,
        samples_path: str | None = None,
    ) -> list[TelemetryPoint]:
        payload = self._load_json(source)
        return self._parse_payload(payload, field_map=field_map, samples_path=samples_path)

    def _load_json(self, source: str) -> Any:
        if source.startswith(("http://", "https://")):
            with urlopen(source) as response:  # nosec B310
                return json.loads(response.read().decode("utf-8"))
        return json.loads(Path(source).read_text(encoding="utf-8"))

    def _parse_payload(
        self,
        payload: Any,
        *,
        field_map: dict[str, str] | None = None,
        samples_path: str | None = None,
    ) -> list[TelemetryPoint]:
        if isinstance(payload, dict):
            if samples_path:
                samples = self._get_value(payload, samples_path)
            elif "samples" in payload:
                samples = payload["samples"]
            else:
                samples = self._detect_samples_list(payload)
        elif isinstance(payload, list):
            samples = payload
        else:
            raise ValueError("Telemetry payload must be a list or object with 'samples'.")

        if not isinstance(samples, list):
            raise ValueError("Telemetry samples must be a JSON array.")

        fields = {
            "timestamp": "timestamp",
            "node": "node",
            "error_rate": "error_rate",
            "latency_ms": "latency_ms",
            "saturation": "saturation",
        }
        if field_map:
            fields.update(field_map)

        points: list[TelemetryPoint] = []
        for sample in samples:
            timestamp = self._get_value(sample, fields["timestamp"])
            node = self._get_value(sample, fields["node"])
            points.append(
                TelemetryPoint(
                    timestamp=float(timestamp),
                    node=str(node),
                    error_rate=float(self._get_value(sample, fields["error_rate"], default=0.0)),
                    latency_ms=float(self._get_value(sample, fields["latency_ms"], default=0.0)),
                    saturation=float(self._get_value(sample, fields["saturation"], default=0.0)),
                )
            )
        return points

    def _detect_samples_list(self, payload: dict[str, Any]) -> list[Any]:
        candidates = [value for value in payload.values() if isinstance(value, list)]
        if len(candidates) == 1:
            return candidates[0]
        raise ValueError(
            "Telemetry payload object must contain 'samples', a provided samples_path, or a single list field."
        )

    def _get_value(self, item: Any, path: str, default: Any = ... ) -> Any:
        current: Any = item
        for key in path.split("."):
            if isinstance(current, dict) and key in current:
                current = current[key]
                continue
            if default is ...:
                raise ValueError(f"Missing telemetry field: {path}")
            return default
        return current
