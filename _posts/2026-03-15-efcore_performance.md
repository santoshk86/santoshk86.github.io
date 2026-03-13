---
title: 'EF Core Performance: AsNoTracking, Compiled Queries, and Split Queries'
date: 2026-03-13
permalink: /posts/2026/03/efcore_performance/
tags:
  - dotnet
  - dotnet8
  - efcore
  - database
  - performance
  - intermediate
---

This post covers some of the most useful EF Core performance techniques you will apply in read-heavy applications: **disable tracking for read-only queries, project only the data you need, use compiled queries for hot paths, and understand when split queries help avoid large join explosions**. Performance work starts with measurement, but these patterns are worth knowing early.

Start with the query shape
------
Many EF Core performance issues are not caused by EF Core itself. They are caused by:
- loading too many rows
- loading too many columns
- loading too many related entities
- running too many separate queries

The first question is always:

```text
What data do I actually need for this use case?
```

If the answer is "three columns for a list page", do not fetch full tracked entity graphs.

Use `AsNoTracking` for read-only work
------
By default, EF Core tracks entities so it can detect changes later. That is useful for updates, but it adds overhead for read-only queries.

Read-only query:

```csharp
var products = await dbContext.Products
    .AsNoTracking()
    .OrderBy(p => p.Name)
    .ToListAsync(cancellationToken);
```

Why it helps:
- less memory usage
- less change-tracking overhead
- better throughput for list and lookup endpoints

Use tracking when:
- you plan to modify and save the entity
- the unit of work needs tracked graph behavior

Use `AsNoTracking` when:
- the query feeds a response model
- the data is read-only
- you do not need EF Core to watch for changes

Project only what you need
------
Projection is often a bigger win than tracking changes alone.

Instead of:

```csharp
var products = await dbContext.Products
    .AsNoTracking()
    .ToListAsync(cancellationToken);
```

prefer:

```csharp
var products = await dbContext.Products
    .AsNoTracking()
    .OrderBy(p => p.Name)
    .Select(p => new ProductListItemDto(
        p.Id,
        p.Name,
        p.Price))
    .ToListAsync(cancellationToken);
```

This avoids:
- materializing unnecessary columns
- accidentally exposing entire entities
- loading data the client never uses

Projection is one of the safest and most broadly effective EF Core optimizations.

Compiled queries for hot paths
------
If a query shape runs extremely often, you can precompile it.

Example:

```csharp
private static readonly Func<StoreDbContext, int, Task<ProductDto?>> GetProductByIdQuery =
    EF.CompileAsyncQuery((StoreDbContext db, int id) =>
        db.Products
            .AsNoTracking()
            .Where(p => p.Id == id)
            .Select(p => new ProductDto(p.Id, p.Name, p.Price))
            .FirstOrDefault());
```

Usage:

```csharp
var product = await GetProductByIdQuery(dbContext, id);
```

Compiled queries are not required for every endpoint. They are most useful when:
- the query shape is fixed
- the query is called very frequently
- profiling shows query compilation overhead matters

Do not reach for compiled queries before you fix larger problems such as over-fetching or missing indexes.

Split queries for large includes
------
When you `Include` several related collections in one big query, the SQL can create a cartesian explosion where rows multiply dramatically.

Example:

```csharp
var orders = await dbContext.Orders
    .AsNoTracking()
    .Include(o => o.Items)
    .Include(o => o.Events)
    .AsSplitQuery()
    .ToListAsync(cancellationToken);
```

Why `AsSplitQuery()` helps:
- EF Core runs multiple SQL queries instead of one huge join
- it can reduce duplicated result data
- it is often better for large object graphs

Tradeoff:
- multiple round trips instead of one

You should measure both patterns for important endpoints, but `AsSplitQuery()` is an important tool when large includes create very wide or repetitive result sets.

Avoid N+1 query problems
------
The N+1 pattern happens when you load a list and then issue one additional query per item.

Example anti-pattern:

```csharp
var orders = await dbContext.Orders.ToListAsync(cancellationToken);

foreach (var order in orders)
{
    order.Items = await dbContext.OrderItems
        .Where(i => i.OrderId == order.Id)
        .ToListAsync(cancellationToken);
}
```

This becomes expensive quickly.

Better options:
- load related data with a carefully chosen `Include`
- project directly into a DTO
- reshape the query to fetch what the API actually needs in one planned pattern

Pagination still matters
------
Even optimized queries can be too slow if you return unbounded result sets.

Example:

```csharp
var products = await dbContext.Products
    .AsNoTracking()
    .OrderBy(p => p.Id)
    .Skip((page - 1) * pageSize)
    .Take(pageSize)
    .Select(p => new ProductListItemDto(p.Id, p.Name, p.Price))
    .ToListAsync(cancellationToken);
```

The best optimization is often "return less data".

Database indexes are part of performance
------
Application-side tuning will not compensate for missing indexes on important query paths.

If you frequently filter or sort by:
- `Sku`
- `CategoryId`
- `CreatedOn`

then the database may need matching indexes. EF Core performance is tightly connected to database design, not just C# code.

A practical read-model example
------
This is a strong default pattern for list endpoints:

```csharp
var items = await dbContext.Products
    .AsNoTracking()
    .Where(p => p.IsActive)
    .OrderBy(p => p.Name)
    .Skip((page - 1) * pageSize)
    .Take(pageSize)
    .Select(p => new ProductListItemDto(
        p.Id,
        p.Name,
        p.Price))
    .ToListAsync(cancellationToken);
```

Why it performs well:
- no tracking
- filtered
- paged
- projected
- ordered explicitly

This is a much better default than `ToListAsync()` over full entities.

Common mistakes to avoid
------
Watch for these issues:
- using tracked entities for every read endpoint
- returning entire entity graphs by default
- ignoring N+1 query patterns
- adding compiled queries before solving bigger bottlenecks
- assuming EF Core performance is separate from database indexing

EF Core performance work is usually about being intentional. Query only what you need, track only what you plan to change, and measure before optimizing the smallest details.

------------------------------------------------------------------------

**Next Article:** Testing ASP.NET Core Apps: xUnit and Integration Tests with WebApplicationFactory
