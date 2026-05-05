---
title: 'Resilience in .NET: HttpClientFactory, Polly Policies, Retries, and Timeouts'
date: 2026-03-20
permalink: /posts/2026/03/resilience_httpclientfactory_polly/
tags:
  - dotnet
  - dotnet8
  - aspnetcore
  - resilience
  - httpclient
  - intermediate
---

This post covers how .NET applications should call external services safely using **`HttpClientFactory`, timeouts, retries, and resilience policies**. Distributed systems fail in ordinary ways: networks pause, DNS changes, services restart, and dependencies return temporary errors. Resilience design assumes those failures will happen.

Why `HttpClientFactory` matters
------
Creating `HttpClient` manually in random services can lead to connection management problems and inconsistent configuration.

Use typed clients instead:

```csharp
builder.Services.AddHttpClient<ProductCatalogClient>(client =>
{
    client.BaseAddress = new Uri("https://catalog.example.com/");
    client.Timeout = TimeSpan.FromSeconds(10);
});
```

Typed client:

```csharp
public sealed class ProductCatalogClient(HttpClient httpClient)
{
    public async Task<string> GetProductAsync(int id, CancellationToken cancellationToken)
    {
        return await httpClient.GetStringAsync(
            $"/api/products/{id}",
            cancellationToken);
    }
}
```

Benefits:
- central configuration
- DI-friendly clients
- better handler lifetime management
- consistent logging and resilience policies

Timeouts
------
Every outbound call should have a timeout. Without one, a dependency can hold resources longer than the user or system can tolerate.

```csharp
builder.Services.AddHttpClient<InventoryClient>(client =>
{
    client.BaseAddress = new Uri("https://inventory.example.com/");
    client.Timeout = TimeSpan.FromSeconds(5);
});
```

Choose timeouts based on the caller's real budget. If the API endpoint should respond in two seconds, a 30-second downstream timeout does not make sense.

Retries
------
Retries help with transient failures, but they can also make outages worse if used carelessly.

Retry only when:
- the operation is safe to retry
- the failure is likely transient
- the retry count is small
- there is delay or backoff between attempts

Do not blindly retry:
- non-idempotent writes
- validation failures
- authentication failures
- permanent `404 Not Found` responses

Polly policy concept
------
Polly is a common .NET resilience library. Policies can express retries, timeouts, circuit breakers, and fallback behavior.

Conceptual retry policy:

```csharp
var retryPolicy = Policy
    .Handle<HttpRequestException>()
    .OrResult<HttpResponseMessage>(r => (int)r.StatusCode >= 500)
    .WaitAndRetryAsync(
        retryCount: 3,
        sleepDurationProvider: attempt => TimeSpan.FromMilliseconds(200 * attempt));
```

Attach a policy to an HTTP client:

```csharp
builder.Services.AddHttpClient<InventoryClient>()
    .AddPolicyHandler(retryPolicy);
```

The exact package and APIs may vary by .NET version and resilience stack, but the design principle stays the same: policies should be centralized and intentional.

Circuit breakers
------
A circuit breaker stops sending traffic to a failing dependency for a period of time. This protects your app and the dependency from repeated failing calls.

Use circuit breakers when:
- a dependency can become unhealthy for minutes
- repeated calls amplify the problem
- callers can fail fast or use fallback behavior

Avoid circuit breakers when a failure should always be attempted immediately and there is no useful fallback.

Fallbacks
------
Fallback behavior can include:
- returning cached data
- returning a partial response
- queuing work for later
- showing a degraded feature state

Fallbacks must be honest. Returning stale data as if it is fresh can be worse than returning an error.

Logging and metrics
------
Resilience policies should be observable. You need to know:
- how many retries happened
- which dependency is failing
- whether timeouts increased
- whether circuit breakers opened

Without visibility, retries can hide a dependency problem until latency and cost become unacceptable.

Common mistakes to avoid
------
Watch for these issues:
- creating new `HttpClient` instances manually everywhere
- setting no timeout
- retrying every failure type
- retrying writes without idempotency
- using resilience policies with no logging or metrics

Resilience is not about pretending failures do not happen. It is about limiting blast radius, preserving user experience where possible, and making dependency failures visible.

------------------------------------------------------------------------

**Next Article:** Clean Architecture vs Vertical Slice in .NET: Pragmatic Guidance
