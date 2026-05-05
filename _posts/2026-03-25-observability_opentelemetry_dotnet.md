---
title: 'Observability in .NET: OpenTelemetry Traces, Metrics, and Logs'
date: 2026-03-25
permalink: /posts/2026/03/observability_opentelemetry_dotnet/
tags:
  - dotnet
  - observability
  - opentelemetry
  - tracing
  - metrics
  - advanced
---

This post covers observability in .NET using **traces, metrics, logs, and OpenTelemetry**. Logging tells you what happened. Observability helps you understand how a system behaves across services, dependencies, and time.

The three signals
------
Modern observability usually focuses on three signals:

- logs: discrete events and messages
- metrics: numeric measurements over time
- traces: request flows across services

Each signal answers a different question:
- logs explain specific events
- metrics show trends and alerts
- traces show where time was spent

You need all three for production systems.

OpenTelemetry
------
OpenTelemetry is a vendor-neutral standard for collecting telemetry. Instead of locking your app directly to one monitoring platform, you instrument with OpenTelemetry and export data to a backend.

Common destinations:
- Azure Monitor
- Grafana Tempo and Prometheus
- Jaeger
- Zipkin
- Datadog
- New Relic

Basic setup concept:

```csharp
builder.Services.AddOpenTelemetry()
    .WithTracing(tracing =>
    {
        tracing
            .AddAspNetCoreInstrumentation()
            .AddHttpClientInstrumentation()
            .AddEntityFrameworkCoreInstrumentation();
    })
    .WithMetrics(metrics =>
    {
        metrics
            .AddAspNetCoreInstrumentation()
            .AddHttpClientInstrumentation()
            .AddRuntimeInstrumentation();
    });
```

The exact exporter depends on your observability platform.

Traces
------
A trace follows a request through the system. Each operation is a span.

Example flow:

```text
HTTP GET /api/orders/42
  -> SQL query Orders
  -> HTTP call Inventory API
  -> SQL query OrderItems
```

Traces help answer:
- which dependency is slow
- where an error occurred
- how services are connected
- whether retries increased latency

Custom activity:

```csharp
private static readonly ActivitySource ActivitySource = new("Store.Orders");

using var activity = ActivitySource.StartActivity("SubmitOrder");
activity?.SetTag("order.id", orderId);
```

Use custom spans for important business operations, not every tiny method.

Metrics
------
Metrics are numbers over time.

Useful metrics:
- request duration
- request count by status code
- queue depth
- job failure count
- cache hit ratio
- database query duration

Custom metric:

```csharp
private static readonly Meter Meter = new("Store.Orders");
private static readonly Counter<int> OrdersSubmitted =
    Meter.CreateCounter<int>("orders.submitted");

OrdersSubmitted.Add(1, KeyValuePair.Create<string, object?>("channel", "web"));
```

Metrics should be low-cardinality. Do not tag metrics with values like raw user IDs or order IDs.

Logs
------
Logs still matter. Use structured logging:

```csharp
logger.LogInformation(
    "Order {OrderId} submitted by customer {CustomerId}",
    orderId,
    customerId);
```

Good logs include:
- correlation IDs
- stable business identifiers
- meaningful event names
- exception details when failures happen

Do not log secrets, tokens, or sensitive personal data.

Correlation
------
The value of observability increases when logs, traces, and metrics connect through shared identifiers.

Important identifiers:
- trace ID
- span ID
- request ID
- user or tenant ID where appropriate
- business operation ID

When an alert fires, you should be able to move from a metric spike to traces and then to logs for the same time window.

Common mistakes to avoid
------
Watch for these issues:
- logs with no structured properties
- high-cardinality metric labels
- tracing every small method and creating noise
- missing outbound HTTP and database instrumentation
- telemetry that is only configured locally but absent in production

Observability is operational design. It should be part of how you build the service, not something added after the first outage.

------------------------------------------------------------------------

**Next Article:** Performance Tuning in .NET: Kestrel, GC, Allocations, and BenchmarkDotNet
