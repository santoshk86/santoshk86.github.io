---
title: 'EF Core 10 Advanced Data Patterns: Named Query Filters, JSON, Complex Types, and Vector Search'
date: 2026-07-28
permalink: /posts/2026/07/efcore10_advanced_data_patterns/
tags:
  - dotnet
  - dotnet10
  - efcore10
  - database
  - json
  - vector-search
  - advanced
---

EF Core 10 is an LTS data-access release aligned with .NET 10. It extends familiar relational modeling with named query filters, richer complex types and JSON support, and vector operations for AI-assisted search. These capabilities are useful when they make domain and query intent clearer. They do not remove the need to inspect generated SQL, design indexes, and test migrations against production-sized data.

Upgrade as a database change
------
EF Core upgrades affect both application code and database behavior. Before moving to EF Core 10:

- update the SDK and target framework to .NET 10
- align all EF Core provider and tooling package versions
- review provider-specific breaking changes
- generate a migration without applying it
- compare representative SQL before and after the upgrade
- run integration tests against the real database engine

Keep `Microsoft.EntityFrameworkCore.Design`, the runtime provider, and the `dotnet-ef` tool on compatible versions. A mixed set may compile but fail during design-time migration discovery.

Use named query filters
------
Global query filters are common for soft deletion and tenant isolation. Earlier versions encouraged combining concerns into one expression. EF Core 10 allows filters to have names.

```csharp
protected override void OnModelCreating(ModelBuilder modelBuilder)
{
    modelBuilder.Entity<Order>()
        .HasQueryFilter(
            "TenantFilter",
            order => order.TenantId == _tenantContext.TenantId)
        .HasQueryFilter(
            "SoftDeletionFilter",
            order => !order.IsDeleted);
}
```

Names let a query disable one filter while retaining the other:

```csharp
var deletedOrdersForCurrentTenant = await dbContext.Orders
    .IgnoreQueryFilters(["SoftDeletionFilter"])
    .Where(order => order.IsDeleted)
    .ToListAsync(cancellationToken);
```

This is safer than disabling every filter for an administrative workflow. It is still security-sensitive. The application must authorize the operation, and tests must prove that tenant isolation remains active.

Model complex values explicitly
------
Complex types represent values that do not have independent identity. Address and money are common examples.

```csharp
public sealed class Order
{
    public Guid Id { get; set; }
    public required ShippingAddress ShippingAddress { get; set; }
}

public sealed record ShippingAddress(
    string Line1,
    string City,
    string Region,
    string PostalCode,
    string CountryCode);
```

Configuration keeps the ownership visible:

```csharp
modelBuilder.Entity<Order>()
    .ComplexProperty(order => order.ShippingAddress);
```

Use complex types when the value belongs to its containing entity and is replaced as a unit. Use an entity when the data has its own identity, lifecycle, relationships, or independent query needs.

Choose columns or JSON intentionally
------
Relational columns are ideal for values that are filtered, sorted, joined, constrained, or indexed frequently. JSON is useful for nested structures that are usually read and written together and vary less predictably.

A practical decision considers:

- query and indexing requirements
- update frequency
- reporting needs
- schema governance
- provider capabilities
- compatibility with existing tools

Do not use JSON to avoid modeling. Important invariants, required properties, and version evolution still need explicit design.

Inspect JSON query translation
------
Provider support determines which JSON expressions can run on the server. Keep projections narrow and inspect SQL for important paths.

```csharp
var summaries = await dbContext.Orders
    .AsNoTracking()
    .Where(order => order.ShippingAddress.CountryCode == "US")
    .Select(order => new
    {
        order.Id,
        order.ShippingAddress.Region
    })
    .ToListAsync(cancellationToken);
```

Verify that the provider translates the predicate rather than loading documents for client-side evaluation. Add computed columns or provider-specific JSON indexes when a nested property becomes a frequent search dimension.

Use bulk updates for set-based work
------
`ExecuteUpdateAsync` updates rows without loading and tracking every entity.

```csharp
var updated = await dbContext.Orders
    .Where(order => order.Status == OrderStatus.Pending)
    .Where(order => order.CreatedAt < cutoff)
    .ExecuteUpdateAsync(
        setters => setters
            .SetProperty(order => order.Status, OrderStatus.Expired)
            .SetProperty(order => order.UpdatedAt, now),
        cancellationToken);
```

Bulk operations bypass the normal tracked-entity workflow. Domain events, interceptors, in-memory state, and per-entity validation may not run as expected. Use them for operations whose business semantics are truly set-based.

Add vector search where it solves a search problem
------
EF Core 10 supports vector data with SQL Server 2025 and Azure SQL. A vector represents an embedding generated from text, an image, or another input.

```csharp
public sealed class KnowledgeArticle
{
    public int Id { get; set; }
    public required string Content { get; set; }

    [Column(TypeName = "vector(1536)")]
    public required SqlVector<float> Embedding { get; set; }
}
```

A similarity query can order candidates by vector distance:

```csharp
var matches = await dbContext.KnowledgeArticles
    .AsNoTracking()
    .OrderBy(article => EF.Functions.VectorDistance(
        article.Embedding,
        queryEmbedding))
    .Take(10)
    .Select(article => new { article.Id, article.Content })
    .ToListAsync(cancellationToken);
```

Vector search is not a replacement for authorization or relational filtering. Apply tenant, visibility, language, and lifecycle predicates before returning results.

Design the embedding lifecycle
------
Production vector search needs more than a vector column. Track:

- embedding model and version
- vector dimensions
- content hash or source version
- generation timestamp
- retry and failure state

When the source content or embedding model changes, re-embedding should be resumable and observable. Avoid regenerating every vector inside an HTTP request. Use a durable background process and make repeated work idempotent.

Protect query performance
------
For each critical query:

1. capture generated SQL
2. review the execution plan
3. test realistic cardinality and parameter values
4. add or adjust indexes
5. measure database time separately from application time
6. watch for query-count regressions

EF Core makes queries easier to express; it cannot decide whether a scan, join, JSON predicate, or vector operation is affordable for your workload.

Common mistakes to avoid
------
Watch for these issues:

- upgrading EF packages without upgrading provider tooling
- disabling all query filters for one administrative case
- treating a query filter as the only tenant security boundary
- placing heavily queried relational data inside JSON without indexing
- using bulk updates when per-entity domain behavior is required
- returning vector matches before applying authorization filters
- changing embedding models without versioning stored vectors

EF Core 10 adds powerful modeling and search options. Use each feature behind a clear data contract, provider-aware integration tests, and measured database behavior.

------------------------------------------------------------------------

**Next Article:** Modern Caching in .NET: HybridCache, Output Caching, Stampede Protection, and Invalidation
