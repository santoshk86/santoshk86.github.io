---
title: 'API Documentation in .NET: OpenAPI, Swagger, Examples, and Versioning'
date: 2026-03-19
permalink: /posts/2026/03/api_documentation_openapi_swagger/
tags:
  - dotnet
  - dotnet8
  - aspnetcore
  - openapi
  - swagger
  - intermediate
---

This post covers how to document ASP.NET Core APIs using **OpenAPI, Swagger UI, examples, and version-aware contracts**. Good API documentation is not decoration. It is how frontend developers, mobile teams, integration partners, and future maintainers understand what your API promises.

OpenAPI vs Swagger
------
The terms are often mixed together:
- OpenAPI is the specification format
- Swagger UI is a browser UI for exploring that specification
- Swagger tooling is the ecosystem around generating and consuming OpenAPI documents

In .NET projects, most teams start with Swashbuckle:

```bash
dotnet add package Swashbuckle.AspNetCore
```

Basic setup:

```csharp
builder.Services.AddEndpointsApiExplorer();
builder.Services.AddSwaggerGen();

var app = builder.Build();

if (app.Environment.IsDevelopment())
{
    app.UseSwagger();
    app.UseSwaggerUI();
}
```

For internal APIs, Swagger UI is often enabled in non-production environments. For public APIs, published OpenAPI documents may be part of the formal contract.

Documenting controllers
------
Controllers produce better documentation when routes, response types, and request models are explicit.

```csharp
[ApiController]
[Route("api/products")]
public sealed class ProductsController : ControllerBase
{
    [HttpGet("{id:int}")]
    [ProducesResponseType(typeof(ProductDto), StatusCodes.Status200OK)]
    [ProducesResponseType(StatusCodes.Status404NotFound)]
    public IActionResult GetById(int id)
    {
        var product = productService.GetById(id);
        return product is null ? NotFound() : Ok(product);
    }
}
```

Those attributes help the generated contract describe success and failure paths.

Documenting minimal APIs
------
Minimal APIs can also describe metadata clearly:

```csharp
app.MapGet("/api/products/{id:int}", (int id) =>
{
    var product = productService.GetById(id);
    return product is null ? Results.NotFound() : Results.Ok(product);
})
.WithName("GetProductById")
.WithTags("Products")
.Produces<ProductDto>(StatusCodes.Status200OK)
.Produces(StatusCodes.Status404NotFound);
```

Names and tags matter because they shape the generated documentation and client experience.

Examples make contracts easier to use
------
Schema definitions are useful, but examples make APIs faster to understand.

Example response:

```json
{
  "id": 42,
  "name": "Mechanical Keyboard",
  "price": 129.00,
  "category": "Keyboards"
}
```

Good examples should show:
- realistic field values
- common success responses
- common validation failures
- authentication requirements where relevant

Do not put fake values that hide important constraints. If a field must be a GUID, date, currency, or enum, show it realistically.

Versioned API documentation
------
If your API has multiple versions, each version should have its own OpenAPI document.

Example setup concept:

```csharp
builder.Services.AddSwaggerGen(options =>
{
    options.SwaggerDoc("v1", new OpenApiInfo
    {
        Title = "Store API",
        Version = "v1"
    });

    options.SwaggerDoc("v2", new OpenApiInfo
    {
        Title = "Store API",
        Version = "v2"
    });
});
```

Swagger UI can expose both:

```csharp
app.UseSwaggerUI(options =>
{
    options.SwaggerEndpoint("/swagger/v1/swagger.json", "Store API v1");
    options.SwaggerEndpoint("/swagger/v2/swagger.json", "Store API v2");
});
```

Versioned documentation prevents consumers from guessing which contract applies to their client.

Security definitions
------
If your API uses bearer tokens, document that in OpenAPI.

```csharp
builder.Services.AddSwaggerGen(options =>
{
    options.AddSecurityDefinition("Bearer", new OpenApiSecurityScheme
    {
        Name = "Authorization",
        Type = SecuritySchemeType.Http,
        Scheme = "bearer",
        BearerFormat = "JWT",
        In = ParameterLocation.Header
    });
});
```

This makes Swagger UI usable for authenticated endpoints and communicates how clients should send credentials.

Documentation best practices
------
Use this baseline:
- define request and response DTOs clearly
- document expected status codes
- include examples for important payloads
- tag endpoints by feature area
- publish versioned OpenAPI documents when versions exist
- keep documentation generated from source as much as possible

Common mistakes to avoid
------
Watch for these issues:
- returning anonymous objects everywhere and producing weak schemas
- documenting only `200 OK` responses
- leaving auth requirements invisible
- letting old OpenAPI documents drift from implementation
- exposing internal-only endpoints in public docs

Good API documentation is part of the API contract. Treat it like code: reviewed, versioned, and verified.

------------------------------------------------------------------------

**Next Article:** Resilience in .NET: HttpClientFactory, Polly Policies, Retries, and Timeouts
