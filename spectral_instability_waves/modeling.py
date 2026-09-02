from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from typing import Iterable

from .telemetry import TelemetryPoint


@dataclass(frozen=True)
class PredictionResult:
    node: str
    instability_score: float
    predicted_failure_probability: float
    wave_depth: int


class FailureWavePredictor:
    """Predicts failure propagation as an instability wave across a node graph."""

    def __init__(
        self,
        graph: dict[str, list[str]] | None = None,
        *,
        decay: float = 0.55,
        error_weight: float = 0.5,
        latency_weight: float = 0.3,
        saturation_weight: float = 0.2,
    ) -> None:
        self.graph = graph or {}
        self.decay = decay
        self.error_weight = error_weight
        self.latency_weight = latency_weight
        self.saturation_weight = saturation_weight

    def predict(self, telemetry: Iterable[TelemetryPoint], propagation_steps: int = 2) -> list[PredictionResult]:
        by_node: dict[str, list[TelemetryPoint]] = defaultdict(list)
        for point in sorted(telemetry, key=lambda item: item.timestamp):
            by_node[point.node].append(point)

        base_scores = {node: self._node_instability(samples) for node, samples in by_node.items()}
        propagated_scores, depths = self._propagate(base_scores, propagation_steps)

        results = [
            PredictionResult(
                node=node,
                instability_score=score,
                predicted_failure_probability=self._to_probability(score),
                wave_depth=depths.get(node, 0),
            )
            for node, score in propagated_scores.items()
        ]
        return sorted(results, key=lambda result: result.predicted_failure_probability, reverse=True)

    def _node_instability(self, samples: list[TelemetryPoint]) -> float:
        latest = samples[-1]
        recent_error_trend = 0.0
        if len(samples) > 1:
            previous = samples[-2]
            recent_error_trend = max(0.0, latest.error_rate - previous.error_rate)
        weighted_load = (
            self.error_weight * latest.error_rate
            + self.latency_weight * (latest.latency_ms / 1000.0)
            + self.saturation_weight * latest.saturation
        )
        return max(0.0, weighted_load + (recent_error_trend * 0.6))

    def _propagate(self, base_scores: dict[str, float], steps: int) -> tuple[dict[str, float], dict[str, int]]:
        scores = dict(base_scores)
        depths: dict[str, int] = {node: 0 for node in scores}
        frontier = list(base_scores.items())

        for depth in range(1, steps + 1):
            next_frontier: list[tuple[str, float]] = []
            for node, source_score in frontier:
                for neighbor in self.graph.get(node, []):
                    incoming = source_score * self.decay
                    if incoming <= scores.get(neighbor, 0.0):
                        continue
                    scores[neighbor] = incoming
                    depths[neighbor] = depth
                    next_frontier.append((neighbor, incoming))
            if not next_frontier:
                break
            frontier = next_frontier

        return scores, depths

    @staticmethod
    def _to_probability(score: float) -> float:
        return min(1.0, max(0.0, score))
