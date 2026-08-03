---
title: 'Modern Resilience in .NET: Resilience Pipelines, Standard HTTP Handlers, Hedging, and Telemetry'
date: 2026-07-30
permalink: /posts/2026/07/resilience_pipelines_dotnet/
tags:
  - dotnet
  - dotnet10
  - resilience
  - httpclient
  - polly
  - distributed-systems
  - advanced
---

The modern .NET resilience stack is built around `Microsoft.Extensions.Resilience` and `Microsoft.Extensions.Http.Resilience`, both powered by Polly. These packages replace older integrations that attached individual Polly policies to `HttpClient`. The newer model composes strategies into observable pipelines with safer defaults for timeouts, retries, circuit breakers, and hedging.

Start with a time budget
------
Resilience begins with the caller's deadline. If an API must respond within two seconds, its downstream calls, retries, serialization, and local work must fit inside that budget.

Define:

- total request timeout
- timeout for each individual attempt
- maximum retry count
- delay and jitter between attempts
- circuit-breaker sampling window
- the final failure returned to the caller

Cancellation from the incoming request should flow through every dependency call. A timeout policy is not a substitute for passing `CancellationToken`.

Add the standard HTTP resilience handler
------
For many HTTP clients, the standard handler is a strong baseline:

```csharp
builder.Services
    .AddHttpClient<InventoryClient>(client =>
    {
        client.BaseAddress = new Uri("https://inventory.internal/");
    })
    .AddStandardResilienceHandler(options =>
    {
        options.TotalRequestTimeout.Timeout = TimeSpan.FromSeconds(3);
        options.AttemptTimeout.Timeout = TimeSpan.FromSeconds(1);
        options.Retry.MaxRetryAttempts = 2;
        options.CircuitBreaker.SamplingDuration = TimeSpan.FromSeconds(30);
    });
```

The standard pipeline combines multiple strategies in a tested order. Do not add several standard handlers to the same client. If the defaults do not fit the workload, configure one pipeline intentionally.

Retry only transient and repeatable work
------
Retries are appropriate when failure is temporary and repeating the operation is safe.

Good candidates include:

- connection failures
- selected gateway failures
- `408 Request Timeout`
- `429 Too Many Requests` when retry guidance is honored
- selected `5xx` responses

Do not retry authentication failures, validation failures, ordinary `404` responses, or writes that can create duplicates.

For a write, use an idempotency key or operation identifier recognized by the receiving service:

```csharp
request.Headers.Add("Idempotency-Key", command.OperationId.ToString());
```

The server must persist and enforce that key. Adding a header alone does not make the operation idempotent.

Use backoff and jitter
------
Immediate retries can synchronize many callers and amplify an outage. Exponential backoff spaces attempts, while jitter prevents callers from retrying at exactly the same time.

Keep retry counts small. The total number of calls multiplies quickly across service chains. Three layers each making three attempts can produce far more downstream traffic than the original request volume suggests.

Fail fast with circuit breakers
------
A circuit breaker temporarily blocks calls when recent failures cross a threshold. This protects the caller, reduces load on the dependency, and returns failure without waiting for repeated timeouts.

Circuit-breaker events should be visible in telemetry. Operators need to know:

- which dependency opened the circuit
- failure ratio and throughput
- how long the circuit remained open
- whether probe calls succeeded
- which user operations were affected

Do not use a circuit breaker to hide a dependency problem. It limits damage while the system reports the problem clearly.

Use hedging selectively
------
Hedging sends an additional request when the first attempt is slow rather than waiting for it to fail. It can reduce tail latency for safe reads across equivalent endpoints.

Use hedging only when:

- operations are idempotent
- multiple endpoints or replicas can serve the request
- the latency benefit justifies extra traffic
- cancellation stops losing attempts
- the dependency can absorb the increased load

Do not hedge payment creation, inventory reservation, email sending, or any write without strong deduplication.

Build custom pipelines for non-HTTP operations
------
`Microsoft.Extensions.Resilience` can protect database-independent operations, SDK calls, and internal work.

```csharp
builder.Services.AddResiliencePipeline("report-generation", pipeline =>
{
    pipeline
        .AddTimeout(TimeSpan.FromSeconds(10))
        .AddRetry(new RetryStrategyOptions
        {
            MaxRetryAttempts = 2,
            Delay = TimeSpan.FromMilliseconds(200),
            BackoffType = DelayBackoffType.Exponential,
            UseJitter = true
        });
});
```

Resolve the registered pipeline through `ResiliencePipelineProvider<string>` and execute the bounded operation. Keep business fallback decisions outside low-level infrastructure configuration.

Design honest fallbacks
------
A fallback may return cached data, a partial result, a queued acknowledgement, or a clear degraded response. It should never present stale or incomplete information as current and complete.

Include freshness metadata when returning cached data:

```json
{
  "status": "degraded",
  "asOf": "2026-07-30T18:42:00Z",
  "items": []
}
```

Some operations have no safe fallback. Failing clearly is better than inventing a success state.

Instrument every strategy
------
Measure resilience by dependency and operation:

- request attempts
- retries and retry outcomes
- timeout count
- circuit state transitions
- hedged attempts and winners
- end-to-end latency
- final success or failure

Attach trace context to outbound calls and log structured events at appropriate levels. Avoid one warning for every expected retry during a known incident; aggregate metrics and sample logs where volume is high.

Test failure behavior
------
Integration tests should simulate:

- connection refusal
- slow responses
- transient `5xx` followed by success
- persistent failure that opens the circuit
- cancellation from the caller
- duplicate delivery of a retried write

Assertions should verify attempt count, total duration, final response, telemetry, and side effects. A resilience pipeline that eventually succeeds but violates the caller's time budget is still incorrect.

Common mistakes to avoid
------
Watch for these issues:

- using deprecated `Microsoft.Extensions.Http.Polly` patterns in new code
- stacking multiple standard handlers on one client
- retrying non-idempotent writes
- using large retry counts without an end-to-end deadline
- enabling hedging without measuring additional load
- swallowing final failure behind misleading fallback data
- adding policies without testing their timing and telemetry

Resilience is controlled failure behavior. Modern pipelines make strategies easier to compose, but the service still needs explicit time budgets, idempotency, observable outcomes, and honest degradation.

------------------------------------------------------------------------

**Next Article:** Native AOT for ASP.NET Core APIs: Trimming, Source Generation, Containers, and Trade-offs
