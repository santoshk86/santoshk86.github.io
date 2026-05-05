---
title: 'Caching in .NET: IMemoryCache, Distributed Cache with Redis, and Response Caching'
date: 2026-03-18
permalink: /posts/2026/03/caching_in_dotnet/
tags:
  - dotnet
  - dotnet8
  - aspnetcore
  - caching
  - redis
  - intermediate
---

This post covers the main caching options in .NET applications: **in-memory cache, distributed cache, Redis, and HTTP response caching**. Caching can reduce latency and database load, but it also introduces correctness questions. The hard part is not storing data. The hard part is knowing when cached data is valid.

Why caching matters
------
Caching is useful when:
- data is expensive to compute
- data is read frequently
- data changes less often than it is read
- downstream systems need protection from repeated calls

Bad caching creates stale data and confusing bugs. Good caching has clear expiration, key naming, invalidation rules, and metrics.

`IMemoryCache`
------
`IMemoryCache` stores data inside the current process. It is fast and simple.

Register it:

```csharp
builder.Services.AddMemoryCache();
```

Use it in a service:

```csharp
public sealed class ProductLookupService(
    IMemoryCache cache,
    IProductRepository repository)
{
    public async Task<ProductDto?> GetByIdAsync(int id, CancellationToken cancellationToken)
    {
        var cacheKey = $"products:{id}";

        return await cache.GetOrCreateAsync(cacheKey, async entry =>
        {
            entry.AbsoluteExpirationRelativeToNow = TimeSpan.FromMinutes(5);
            entry.SlidingExpiration = TimeSpan.FromMinutes(1);

            return await repository.GetByIdAsync(id, cancellationToken);
        });
    }
}
```

Use `IMemoryCache` when:
- the app runs as a single instance
- cached data can be different per process
- losing the cache on restart is acceptable

Limitations:
- each app instance has its own cache
- cache entries disappear when the process restarts
- memory pressure matters

Distributed cache
------
`IDistributedCache` stores cache entries outside the process. It is useful when multiple app instances must share cached values.

Register Redis:

```csharp
builder.Services.AddStackExchangeRedisCache(options =>
{
    options.Configuration = builder.Configuration.GetConnectionString("Redis");
    options.InstanceName = "store-api:";
});
```

Use it:

```csharp
public sealed class DistributedProductCache(IDistributedCache cache)
{
    public async Task CacheProductAsync(ProductDto product, CancellationToken cancellationToken)
    {
        var json = JsonSerializer.Serialize(product);

        await cache.SetStringAsync(
            $"products:{product.Id}",
            json,
            new DistributedCacheEntryOptions
            {
                AbsoluteExpirationRelativeToNow = TimeSpan.FromMinutes(10)
            },
            cancellationToken);
    }
}
```

Distributed caching is a better fit for:
- load-balanced APIs
- containerized apps with multiple replicas
- data shared across workers and APIs

Cache key design
------
Cache keys should be predictable and versionable.

Good examples:

```text
products:42
products:list:category:keyboard:page:1:size:25
tenant:acme:settings
```

Avoid vague keys like:

```text
data
result
cache1
```

If the shape of the cached data changes, consider including a version:

```text
products:v2:42
```

Response caching
------
Response caching works at the HTTP response level. It is useful for public or semi-static responses.

Register middleware:

```csharp
builder.Services.AddResponseCaching();

var app = builder.Build();

app.UseResponseCaching();
```

Controller example:

```csharp
[ResponseCache(Duration = 60, Location = ResponseCacheLocation.Any)]
[HttpGet("catalog")]
public IActionResult GetCatalog()
{
    return Ok(catalogService.GetPublicCatalog());
}
```

Response caching is not a replacement for application caching. It is one tool for HTTP-level cache behavior.

Invalidation strategies
------
Expiration is easy. Invalidation is the real design problem.

Common strategies:
- short TTLs for data that can tolerate slight staleness
- explicit removal when data changes
- versioned keys when cache shape changes
- event-based invalidation after writes

Example:

```csharp
cache.Remove($"products:{productId}");
```

For distributed cache:

```csharp
await cache.RemoveAsync($"products:{productId}", cancellationToken);
```

Caching best practices
------
Use these rules:
- cache read models, not tracked EF Core entities
- use DTOs or serialized payloads
- keep TTLs explicit
- avoid caching secrets
- monitor hit rates and latency
- document invalidation behavior for important keys

Common mistakes to avoid
------
Watch for these issues:
- caching data with no expiration
- assuming `IMemoryCache` is shared across servers
- using one cache key for different query shapes
- caching authorization-sensitive responses incorrectly
- adding Redis before fixing inefficient queries

Caching should be a deliberate performance tool. Add it where repeated work is expensive, and make expiration and invalidation part of the design from the beginning.

------------------------------------------------------------------------

**Next Article:** API Documentation in .NET: OpenAPI, Swagger, Examples, and Versioning
