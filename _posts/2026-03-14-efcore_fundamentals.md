---
title: 'EF Core Fundamentals: DbContext, Migrations, Tracking, and Relationships'
date: 2026-03-14
permalink: /posts/2026/03/efcore_fundamentals/
tags:
  - dotnet
  - dotnet8
  - efcore
  - database
  - intermediate
  - fundamentals
---

This post covers the pieces of Entity Framework Core you need before building real data-backed applications. The essential model is: **your entities represent data, `DbContext` coordinates access to that data, migrations evolve the schema, and change tracking decides what EF Core will insert, update, or delete**.

What `DbContext` does
------
`DbContext` is the central EF Core type. It:
- exposes entity sets through `DbSet<T>`
- tracks changes to loaded entities
- translates LINQ into database queries
- saves inserts, updates, and deletes

Example:

```csharp
public sealed class StoreDbContext(DbContextOptions<StoreDbContext> options)
    : DbContext(options)
{
    public DbSet<Product> Products => Set<Product>();
    public DbSet<Category> Categories => Set<Category>();
}
```

You usually register it in DI as a scoped service:

```csharp
builder.Services.AddDbContext<StoreDbContext>(options =>
    options.UseSqlServer(builder.Configuration.GetConnectionString("Default")));
```

Scoped lifetime is important because a `DbContext` is designed to represent a unit of work for a request or operation.

Defining entities
------
Entities are plain C# classes that EF Core maps to tables.

Example:

```csharp
public sealed class Product
{
    public int Id { get; set; }
    public string Name { get; set; } = string.Empty;
    public decimal Price { get; set; }

    public int CategoryId { get; set; }
    public Category Category { get; set; } = null!;
}

public sealed class Category
{
    public int Id { get; set; }
    public string Name { get; set; } = string.Empty;

    public ICollection<Product> Products { get; set; } = new List<Product>();
}
```

This example shows a one-to-many relationship:
- one category
- many products

EF Core can infer many relationships from conventions, but you can also configure them explicitly.

Configuring relationships
------
Fluent configuration in `OnModelCreating` gives you more control:

```csharp
protected override void OnModelCreating(ModelBuilder modelBuilder)
{
    modelBuilder.Entity<Product>()
        .HasOne(p => p.Category)
        .WithMany(c => c.Products)
        .HasForeignKey(p => p.CategoryId);
}
```

Why this matters:
- your intent becomes explicit
- foreign key behavior is clearer
- more complex mappings stay maintainable

Creating and applying migrations
------
Migrations track schema changes over time. They are one of the most important workflow pieces in EF Core.

Typical commands:

```bash
dotnet ef migrations add InitialCreate
dotnet ef database update
```

What happens:
- EF Core compares your current model to the last migration snapshot
- it generates migration files
- `database update` applies those changes to the database

When you later add a property:

```csharp
public string Sku { get; set; } = string.Empty;
```

you create a new migration:

```bash
dotnet ef migrations add AddProductSku
dotnet ef database update
```

That migration history becomes part of your application lifecycle.

Basic CRUD with `DbContext`
------
Create:

```csharp
var product = new Product
{
    Name = "Mechanical Keyboard",
    Price = 129.00m,
    CategoryId = 1
};

dbContext.Products.Add(product);
await dbContext.SaveChangesAsync(cancellationToken);
```

Read:

```csharp
var products = await dbContext.Products
    .OrderBy(p => p.Name)
    .ToListAsync(cancellationToken);
```

Update:

```csharp
var product = await dbContext.Products.FindAsync([id], cancellationToken);
if (product is null)
    return Results.NotFound();

product.Price = 139.00m;
await dbContext.SaveChangesAsync(cancellationToken);
```

Delete:

```csharp
var product = await dbContext.Products.FindAsync([id], cancellationToken);
if (product is null)
    return Results.NotFound();

dbContext.Products.Remove(product);
await dbContext.SaveChangesAsync(cancellationToken);
```

The important part is `SaveChangesAsync`. Until you call it, EF Core has tracked changes in memory but has not committed them to the database.

Change tracking
------
Tracking is one of the most important EF Core behaviors.

When you load an entity normally:

```csharp
var product = await dbContext.Products.FirstAsync(cancellationToken);
```

EF Core tracks that entity. If you modify one of its properties and call `SaveChangesAsync`, EF Core knows what changed and generates an update statement.

This is convenient for write workflows, but tracking also has a cost. For read-only queries, you often want to disable it. That is a performance topic we will cover next.

Loading related data
------
Relationships are often loaded with `Include`:

```csharp
var categories = await dbContext.Categories
    .Include(c => c.Products)
    .ToListAsync(cancellationToken);
```

This tells EF Core to bring the related products along with each category.

Use `Include` deliberately:
- it is useful when the response truly needs the related data
- it can become expensive if you pull large graphs by default

Choosing the database provider
------
EF Core supports multiple providers such as:
- SQL Server
- PostgreSQL
- SQLite
- MySQL
- in-memory providers for testing scenarios

The provider changes the database connection and some capabilities, but the main EF Core concepts remain the same.

A practical API example
------
Minimal API using `StoreDbContext`:

```csharp
app.MapGet("/api/products/{id:int}", async (
    int id,
    StoreDbContext dbContext,
    CancellationToken cancellationToken) =>
{
    var product = await dbContext.Products
        .Include(p => p.Category)
        .FirstOrDefaultAsync(p => p.Id == id, cancellationToken);

    return product is null
        ? Results.NotFound()
        : Results.Ok(new
        {
            product.Id,
            product.Name,
            product.Price,
            Category = product.Category.Name
        });
});
```

This ties together several fundamentals:
- DI-managed `DbContext`
- LINQ translation to SQL
- related data loading
- mapping entities into response shapes

Common mistakes to avoid
------
Watch for these issues:
- keeping one `DbContext` alive too long
- forgetting `SaveChangesAsync`
- exposing entities directly when an API DTO would be safer
- loading huge related graphs by default
- treating migrations as optional instead of part of the development workflow

If you understand `DbContext`, migrations, tracking, and relationships, you have the foundation needed to build real EF Core-backed applications.

------------------------------------------------------------------------

**Next Article:** EF Core Performance: AsNoTracking, Compiled Queries, and Split Queries
