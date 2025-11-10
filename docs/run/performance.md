# Performance

Performance tests live in `tests/test_performance.py` and should be opt-in via the `performance` marker.

## Load Testing Checklist

- [ ] Capture baseline throughput (messages/minute)
- [ ] Measure 95th percentile handler duration
- [ ] Record memory usage and GC pauses

## Running Soak Tests

```bash
pytest tests/test_performance.py -m performance --duration=900
```

Document findings in this page so regressions are easy to spot.
