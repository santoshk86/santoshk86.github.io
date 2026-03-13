---
title: 'Model Binding and Validation in ASP.NET Core: DataAnnotations and FluentValidation Basics'
date: 2026-03-09
permalink: /posts/2026/03/model_binding_and_validation/
tags:
  - dotnet
  - dotnet8
  - aspnetcore
  - webapi
  - validation
  - fundamentals
---

This post covers two important jobs the framework performs for you: **model binding** and **validation**. Model binding turns incoming HTTP data into .NET values. Validation checks whether those values satisfy your rules. If you understand where each responsibility begins and ends, your endpoints become much easier to reason about.

What model binding does
------
Model binding reads data from the incoming request and maps it into method parameters or request models.

Common sources include:
- route values
- query string values
- headers
- form fields
- JSON request body

Controller example:

```csharp
[HttpGet("{id:int}")]
public IActionResult GetById(int id, [FromQuery] bool includeHistory = false)
{
    return Ok(new { id, includeHistory });
}
```

Here:
- `id` comes from the route
- `includeHistory` comes from the query string

POST example:

```csharp
[HttpPost]
public IActionResult Create([FromBody] CreateProductRequest request)
{
    return Created($"/api/products/1", request);
}
```

In many cases, ASP.NET Core can infer the source without an explicit attribute, but the attributes make intent clear.

Binding in minimal APIs
------
Minimal APIs use parameter shape and type to infer binding as well.

```csharp
app.MapGet("/api/products/{id:int}", (int id, bool includeReviews) =>
{
    return Results.Ok(new { id, includeReviews });
});
```

Complex types are commonly read from the request body:

```csharp
app.MapPost("/api/products", (CreateProductRequest request) =>
{
    return Results.Created("/api/products/1", request);
});
```

That is binding, not validation. A request can bind successfully and still be logically invalid.

Using DataAnnotations
------
DataAnnotations are the built-in starting point for validation. They work well for required fields, lengths, ranges, and simple formatting rules.

Example request model:

```csharp
using System.ComponentModel.DataAnnotations;

public sealed class CreateProductRequest
{
    [Required]
    [StringLength(100, MinimumLength = 3)]
    public string Name { get; set; } = string.Empty;

    [Range(0.01, 100000)]
    public decimal Price { get; set; }

    [StringLength(1000)]
    public string? Description { get; set; }
}
```

This tells the framework:
- `Name` must exist
- `Name` must be between 3 and 100 characters
- `Price` must be greater than zero

Validation with controllers
------
Controllers paired with `[ApiController]` provide a very useful default behavior: if model validation fails, the framework automatically returns a `400 Bad Request` response with validation details.

```csharp
[ApiController]
[Route("api/products")]
public sealed class ProductsController : ControllerBase
{
    [HttpPost]
    public IActionResult Create(CreateProductRequest request)
    {
        return Created("/api/products/1", request);
    }
}
```

If the JSON body omits `Name` or sends a negative `Price`, the action does not need to build the error response manually. ASP.NET Core handles it because `[ApiController]` is active.

That default behavior is one reason controller-based APIs feel productive for standard CRUD endpoints.

Manual validation in minimal APIs
------
Minimal APIs do not automatically give you the same controller-style validation flow for every case, so beginners often validate explicitly.

```csharp
app.MapPost("/api/products", (CreateProductRequest request) =>
{
    var errors = new Dictionary<string, string[]>();

    if (string.IsNullOrWhiteSpace(request.Name) || request.Name.Length < 3)
        errors["Name"] = ["Name must be at least 3 characters."];

    if (request.Price <= 0)
        errors["Price"] = ["Price must be greater than zero."];

    if (errors.Count > 0)
        return Results.ValidationProblem(errors);

    return Results.Created("/api/products/1", request);
});
```

This is more manual, but it teaches an important rule: **binding gets the data into your code, validation decides whether the data is acceptable**.

When DataAnnotations are enough
------
DataAnnotations are a good fit when:
- rules are simple and local to one property
- the validation is mostly structural
- you want built-in framework support

Examples:
- required name
- max length
- email format
- numeric range

They become less comfortable when rules involve:
- multiple properties together
- conditional rules
- reusable validation logic
- richer custom messages

That is where FluentValidation becomes attractive.

FluentValidation basics
------
FluentValidation expresses rules in code rather than attributes. The syntax is easier to compose when validation gets more complex.

Example validator:

```csharp
public sealed class CreateProductRequestValidator
    : AbstractValidator<CreateProductRequest>
{
    public CreateProductRequestValidator()
    {
        RuleFor(x => x.Name)
            .NotEmpty()
            .MinimumLength(3)
            .MaximumLength(100);

        RuleFor(x => x.Price)
            .GreaterThan(0);

        RuleFor(x => x.Description)
            .MaximumLength(1000);
    }
}
```

A validator like this reads closer to business intent than a large pile of attributes.

After registering validators in DI, you can invoke them in an endpoint or service:

```csharp
app.MapPost("/api/products", async (
    CreateProductRequest request,
    IValidator<CreateProductRequest> validator,
    CancellationToken cancellationToken) =>
{
    var result = await validator.ValidateAsync(request, cancellationToken);

    if (!result.IsValid)
    {
        return Results.ValidationProblem(
            result.Errors
                .GroupBy(e => e.PropertyName)
                .ToDictionary(
                    g => g.Key,
                    g => g.Select(e => e.ErrorMessage).ToArray()));
    }

    return Results.Created("/api/products/1", request);
});
```

This approach keeps rules centralized and reusable.

DataAnnotations vs FluentValidation
------
Use DataAnnotations when:
- rules are small and obvious
- you want the simplest built-in option
- the request model is straightforward

Use FluentValidation when:
- rules are complex or conditional
- you want validators separate from transport models
- several endpoints share the same validation logic

You do not need to treat this as an all-or-nothing decision. Many teams start with DataAnnotations and introduce FluentValidation when complexity justifies it.

Validation should return useful errors
------
Good validation responses are:
- consistent
- specific
- mapped to the right field
- free of implementation details

Bad validation response:

```json
{
  "message": "Invalid request"
}
```

Better validation response:

```json
{
  "errors": {
    "Name": ["Name must be at least 3 characters."],
    "Price": ["Price must be greater than zero."]
  }
}
```

Clients need to know exactly what to fix. Generic error text slows down frontend and API integration work.

Common mistakes to avoid
------
Watch for these issues:
- mixing binding logic and business logic together in large actions
- validating only on the frontend and trusting the client
- using DataAnnotations for highly conditional rules that belong in dedicated validators
- returning inconsistent validation response shapes across endpoints

The core mental model is simple: **bind early, validate clearly, fail fast**.

------------------------------------------------------------------------

**Next Article:** Error Handling in ASP.NET Core: Middleware, Exception Filters, and ProblemDetails
