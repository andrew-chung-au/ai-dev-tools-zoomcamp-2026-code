## Question

How do I find the request metric for a lookup in Grafana, and check that its log and trace also appear?

## Answer

Use Grafana's **Explore** page (compass icon in the left menu). Choose a data source at the top: your metrics store (for example Prometheus), your logs store (for example Loki) or your traces store (for example Tempo). Set the time range to cover when you made the request.

**1. Find the metric**

Select the metrics data source and open the metrics browser. Search for part of the metric name, such as `http_server`, rather than the exact name from your app's console output. OpenTelemetry names are often translated when stored. In Prometheus, for example:

- dots become underscores
- the unit is added as a suffix (`s` becomes `_seconds`)
- a histogram is split into `_bucket`, `_count` and `_sum` series

So `http.server.request.duration` is stored as `http_server_request_duration_seconds_count`. Attribute names change the same way, so `http.response.status_code` becomes `http_response_status_code`. Query the `_count` series and group it by route and status code to see your request.

**2. Check the log**

Select the logs data source, filter by your service name, and search for text from the request (for example part of its URL). Expand the log line. If your app adds trace context to its logs, you'll see a trace ID.

**3. Check the trace**

If the logs data source links to traces, click the link next to the trace ID. Otherwise, copy the trace ID into the traces data source's query, or search by service name. New traces can take a few seconds to become searchable, so re-run the search if it's empty at first.

If one of the three doesn't appear, check that your app exports that signal and that your telemetry pipeline routes it to the matching data source.

References:
- [Grafana Explore](https://grafana.com/docs/grafana/latest/explore/)
- [OpenTelemetry: Prometheus name translation](https://opentelemetry.io/docs/compatibility/prometheus/client-libraries/)