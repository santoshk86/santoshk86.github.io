---
title: 'Modern Caching in .NET: HybridCache, Output Caching, Stampede Protection, and Invalidation'
date: 2026-07-29
permalink: /posts/2026/07/hybridcache_output_caching_dotnet/
tags:
  - dotnet
  - dotnet10
  - caching
  - hybridcache
  - redis
  - performance
  - advanced
---

Modern .NET applications can use `HybridCache` to coordinate in-process and distributed caching through one API. It adds stampede protection, configurable serialization, and tag-based invalidation while retaining the low latency of a local cache. ASP.NET Core output caching solves a different problem by caching complete HTTP responses. A production design should choose the right layer, define acceptable staleness, and make invalidation observable.

Choose the cache layer by responsibility
------
The common cache layers are:

- `IMemoryCache` for process-local objects
- `IDistributedCache` for shared serialized values
- `HybridCache` for coordinated L1 and L2 application caching
- output caching for complete endpoint responses
- client and proxy caching through HTTP cache headers

Cache data near the layer that understands its validity. A product service can decide when a product read model is stale. HTTP middleware can decide whether a public response is reusable. Mixing those responsibilities makes authorization and invalidation harder to reason about.

Register HybridCache
------
Install the hybrid caching package and register it with the application:

```csharp
builder.Services.AddStackExchangeRedisCache(options =>
{
    options.Configuration = builder.Configuration.GetConnectionString("Redis");
    options.InstanceName = "store:";
});

builder.Services.AddHybridCache(options =>
{
    options.DefaultEntryOptions = new HybridCacheEntryOptions
    {
        Expiration = TimeSpan.FromMinutes(10),
        LocalCacheExpiration = TimeSpan.FromMinutes(1)
    };
});
```

The local L1 cache serves hot values quickly. The distributed L2 cache shares values between application instances. Each application still needs limits and monitoring for both layers.

Use GetOrCreateAsync
------
Keep cache access next to the read operation it protects:

```csharp
public sealed class ProductQueries(
    HybridCache cache,
    StoreDbContext dbContext)
{
    public Task<ProductDto?> GetAsync(
        int productId,
        CancellationToken cancellationToken)
    {
        return cache.GetOrCreateAsync(
            $"products:v1:{productId}",
            async cancel => await dbContext.Products
                .AsNoTracking()
                .Where(product => product.Id == productId)
                .Select(product => new ProductDto(
                    product.Id,
                    product.Name,
                    product.Price))
                .SingleOrDefaultAsync(cancel),
            tags: ["products", $"product:{productId}"],
            cancellationToken: cancellationToken);
    }
}
```

Cache DTOs or immutable read models rather than tracked EF Core entities. Include a key version when the serialized shape or meaning changes.

Understand stampede protection
------
When a popular key expires, many requests can miss simultaneously and repeat the same expensive query. HybridCache coordinates concurrent callers so one caller populates the value while the others await it.

Stampede protection reduces duplicated work, but it does not make the source dependency reliable. The population function still needs cancellation, a sensible timeout, and clear failure behavior. Do not turn a slow database query into a long queue of waiting HTTP requests.

Design expiration from business tolerance
------
Choose expiration based on how long consumers can safely observe old data:

- product descriptions may tolerate minutes
- inventory may tolerate seconds or require no cache
- permissions should usually be checked at request time
- exchange rates may need a timestamp and explicit freshness rule

Use shorter L1 expiration when multiple instances update shared data. The L2 entry may remain valid longer while local copies refresh more frequently.

Invalidate by key and tag
------
After a successful write, remove affected cached views:

```csharp
await cache.RemoveAsync(
    $"products:v1:{productId}",
    cancellationToken);

await cache.RemoveByTagAsync(
    "products",
    cancellationToken);
```

Tags are useful when one change affects list, detail, and search entries. They are not a reason to attach every entry to one global tag. Broad invalidation can erase the performance benefit and create a synchronized reload spike.

Coordinate cache invalidation with data commits
------
Invalidating before a database transaction commits can allow another request to repopulate old data. Invalidating after commit can briefly expose a stale value if the process fails between the commit and removal.

For ordinary data, a short TTL plus post-commit invalidation may be sufficient. For critical projections, publish a durable invalidation event through an outbox and let consumers remove or refresh entries idempotently.

Use output caching for reusable HTTP responses
------
Output caching stores the response produced by an endpoint.

```csharp
builder.Services.AddOutputCache(options =>
{
    options.AddPolicy("PublicCatalog", policy => policy
        .Expire(TimeSpan.FromSeconds(30))
        .Tag("catalog"));
});

var app = builder.Build();
app.UseOutputCache();

app.MapGet("/catalog", GetCatalogAsync)
    .CacheOutput("PublicCatalog");
```

Use it for responses whose cache identity and authorization rules are clear. Be cautious with cookies, user-specific headers, tenant-specific data, localization, and query parameters.

Evict output-cache entries after a relevant change:

```csharp
await outputCacheStore.EvictByTagAsync(
    "catalog",
    cancellationToken);
```

Prevent cache poisoning and data leaks
------
Never let an untrusted value create unbounded key cardinality. Normalize and validate filters before including them in a key. Do not cache a privileged response under a key that an anonymous user can reuse.

For multi-tenant data, include the server-resolved tenant identifier:

```text
tenant:acme:products:v1:42
```

Do not trust a raw tenant header unless authentication and authorization have already bound it to the caller.

Measure cache value
------
Track:

- L1 and L2 hit rates
- population latency and failures
- serialization time and payload size
- evictions and invalidations
- source calls avoided
- stale-data incidents
- Redis latency, memory, and connection health

A high hit rate is not automatically good. A cache that serves incorrect or dangerously stale data is a correctness defect with excellent performance.

Common mistakes to avoid
------
Watch for these issues:

- caching tracked entities or mutable object graphs
- using one key for multiple query shapes
- setting expiration without defining tolerated staleness
- invalidating before a transaction commits
- applying output caching to personalized responses
- creating keys directly from unbounded user input
- adding Redis before measuring the underlying query

Caching is a consistency decision as much as a performance decision. HybridCache and output caching provide stronger tools, but the application must still define identity, freshness, invalidation, and security.

------------------------------------------------------------------------

**Next Article:** Modern Resilience in .NET: Resilience Pipelines, Standard HTTP Handlers, Hedging, and Telemetry
