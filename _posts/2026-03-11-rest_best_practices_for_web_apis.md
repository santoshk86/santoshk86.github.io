---
title: 'REST Best Practices for ASP.NET Core APIs: Status Codes, Pagination, Filtering, and Versioning'
date: 2026-03-11
permalink: /posts/2026/03/rest_best_practices_for_web_apis/
tags:
  - dotnet
  - dotnet8
  - aspnetcore
  - webapi
  - rest
  - intermediate
---

This post covers the API design habits that matter once you move beyond "it works on my machine" and start building endpoints other systems will rely on. Good REST design is mostly about **clear resource modeling, predictable status codes, safe query patterns, and a versioning strategy you decide before clients are locked in**.

What REST best practices are really about
------
REST is often explained as a set of abstract constraints, but in day-to-day API design the practical questions are simpler:
- are your URLs resource-oriented
- do status codes match the outcome
- can clients page and filter large datasets safely
- can you evolve the API without breaking consumers

Most API pain comes from inconsistency, not from lack of sophistication.

Use resource-oriented URLs
------
A common beginner mistake is designing endpoints around verbs:

```text
/getProducts
/createOrder
/deleteCustomer
```

Prefer nouns that represent resources:

```text
GET    /api/products
GET    /api/products/42
POST   /api/orders
DELETE /api/customers/10
```

Why this is better:
- the HTTP verb already expresses the action
- the URL describes the resource, not the operation name
- the API becomes easier to reason about consistently

Nested resources can be useful when the relationship is real:

```text
GET /api/orders/42/items
```

But do not over-nest everything. Deep URLs often signal that the data model is leaking into the API surface too aggressively.

Status codes should match the outcome
------
Status codes are part of the contract. Clients use them to decide what to do next.

Common choices:
- `200 OK` for successful reads
- `201 Created` when a new resource is created
- `204 No Content` for successful updates or deletes without a response body
- `400 Bad Request` for invalid request shape
- `401 Unauthorized` when authentication is missing or invalid
- `403 Forbidden` when the caller is authenticated but not allowed
- `404 Not Found` when the resource does not exist
- `409 Conflict` when the request conflicts with current state

Example create endpoint:

```csharp
[HttpPost]
public IActionResult Create(CreateProductRequest request)
{
    var product = new { Id = 42, request.Name, request.Price };
    return Created($"/api/products/{product.Id}", product);
}
```

Why `201 Created` matters:
- it signals that a new resource now exists
- it usually includes the resource location
- clients can distinguish creation from a generic success

Do not return `200 OK` for every success just because it is easy.

Pagination for collection endpoints
------
Large collections should be paged. Returning thousands of rows in one response hurts performance and creates unstable client behavior.

Offset pagination is the easiest starting point:

```text
GET /api/products?page=2&pageSize=25
```

Example response model:

```csharp
public sealed record PagedResult<T>(
    IReadOnlyList<T> Items,
    int Page,
    int PageSize,
    int TotalCount);
```

Controller example:

```csharp
[HttpGet]
public IActionResult GetAll([FromQuery] int page = 1, [FromQuery] int pageSize = 25)
{
    page = Math.Max(page, 1);
    pageSize = Math.Clamp(pageSize, 1, 100);

    var items = productService.GetPage(page, pageSize);
    var totalCount = productService.GetCount();

    return Ok(new PagedResult<ProductDto>(items, page, pageSize, totalCount));
}
```

Rules worth enforcing:
- clamp page size to a safe maximum
- document default values
- return enough metadata for clients to navigate

For very large or fast-changing datasets, cursor-based pagination can be a better fit, but offset pagination is the easiest baseline to teach and support.

Filtering and sorting
------
Filtering should usually live in query parameters:

```text
GET /api/products?category=keyboards&minPrice=50&maxPrice=200&sort=name
```

Minimal API example:

```csharp
app.MapGet("/api/products", (
    string? category,
    decimal? minPrice,
    decimal? maxPrice,
    string? sort) =>
{
    var query = productService.Query();

    if (!string.IsNullOrWhiteSpace(category))
        query = query.Where(p => p.Category == category);

    if (minPrice.HasValue)
        query = query.Where(p => p.Price >= minPrice.Value);

    if (maxPrice.HasValue)
        query = query.Where(p => p.Price <= maxPrice.Value);

    query = sort?.ToLowerInvariant() switch
    {
        "price" => query.OrderBy(p => p.Price),
        "name" => query.OrderBy(p => p.Name),
        _ => query.OrderBy(p => p.Id)
    };

    return Results.Ok(query.ToList());
});
```

Good filtering design:
- keeps query keys predictable
- avoids inventing a different format for every endpoint
- validates inputs instead of accepting arbitrary sort fields blindly

Versioning strategy
------
Versioning matters when your API will have external consumers or long-lived clients. Breaking changes eventually happen. Versioning gives you room to evolve deliberately.

Common strategies:
- URL segment versioning, such as `/api/v1/products`
- query string versioning, such as `/api/products?api-version=1.0`
- header-based versioning

URL versioning is the easiest to understand:

```text
GET /api/v1/products
GET /api/v2/products
```

Why teams often choose it:
- simple to document
- obvious in logs and routes
- easy for clients to test manually

Whichever strategy you choose, the key is consistency. Do not version one part of the API in the URL and another part through headers unless you have a very specific reason.

A practical checklist
------
For most real-world APIs, this checklist is a solid baseline:
- noun-based URLs
- correct status codes
- pagination for lists
- filtering and sorting through query parameters
- versioning planned before the API becomes widely consumed
- consistent error responses

If these are in place, your API will feel much more professional even before you add advanced features.

Common mistakes to avoid
------
Watch for these issues:
- action-style URLs like `/createUser`
- returning unbounded collections
- using `POST` for every operation
- returning `200` when a `201`, `204`, or `404` would be more accurate
- introducing breaking response changes with no versioning plan

A well-designed REST API is predictable. Clients should not have to guess what your endpoint means or how it behaves.

------------------------------------------------------------------------

**Next Article:** Authentication Basics for .NET APIs: Cookies vs JWT vs OAuth2/OIDC
