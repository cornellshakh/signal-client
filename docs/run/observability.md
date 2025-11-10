# Observability Runbook

| Signal | Where to look |
| --- | --- |
| Increased latency | Command timer dashboards (Prometheus/Grafana). |
| Message drops | Dead-letter queues or retry logs. |
| API drift | Compatibility checker output vs [`cli_rest_api_swagger.json`](https://bbernhard.github.io/signal-cli-rest-api/src/docs/swagger.json). |

## Dashboards

- Event throughput
- Command success/error ratio
- Retry + backoff histograms

Embed ECharts as metrics mature:

```echarts
{
  "tooltip": {},
  "xAxis": {"type": "category", "data": ["00:00","06:00","12:00","18:00"]},
  "yAxis": {"type": "value"},
  "series": [{"data": [120, 600, 450, 700], "type": "line"}]
}
```

## Alerting

- 5xx rate > 2% for 5 minutes
- Command queue backlog > threshold
- Compatibility checker failure

Associate alerts with runbook steps in this page.
