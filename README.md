# spectral-instability-waves

Fetch telemetry streams and predict instability-wave propagation of failures across service nodes.

## Telemetry format

Provide telemetry as JSON array or an object with a `samples` array:

```json
{
  "samples": [
    {
      "timestamp": 1720000000,
      "node": "core-api",
      "error_rate": 0.41,
      "latency_ms": 530,
      "saturation": 0.72
    }
  ]
}
```

## Run predictions

```bash
python -m spectral_instability_waves --source /absolute/path/to/telemetry.json
```

Optional graph file:

```json
{
  "core-api": ["payments", "search"],
  "payments": ["checkout"]
}
```

Run with graph and propagation steps:

```bash
python -m spectral_instability_waves \
  --source /absolute/path/to/telemetry.json \
  --graph /absolute/path/to/graph.json \
  --steps 3
```

The command returns JSON results ranked by predicted failure probability.

## Plug in any observability tool

If your telemetry uses different field names or nests samples, provide a field-map file and samples path.

`field-map.json`:

```json
{
  "timestamp": "ts",
  "node": "service",
  "error_rate": "metrics.errors",
  "latency_ms": "metrics.latency",
  "saturation": "metrics.sat"
}
```

Then run:

```bash
python -m spectral_instability_waves \
  --source /absolute/path/to/obs-output.json \
  --field-map /absolute/path/to/field-map.json \
  --samples-path result.events
```