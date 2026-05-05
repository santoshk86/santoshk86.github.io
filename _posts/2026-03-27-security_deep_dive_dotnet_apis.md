---
title: 'Security Deep Dive for .NET APIs: OWASP, Rate Limiting, Headers, and CORS'
date: 2026-03-27
permalink: /posts/2026/03/security_deep_dive_dotnet_apis/
tags:
  - dotnet
  - aspnetcore
  - security
  - owasp
  - advanced
---

This post covers practical security controls for ASP.NET Core APIs: **OWASP API risks, rate limiting, security headers, CORS, authentication, authorization, and input handling**. Security is not one feature. It is a set of controls that reduce the chance and impact of abuse.

OWASP API risks
------
The OWASP API Security Top 10 highlights common API failure modes. Examples include:
- broken object-level authorization
- broken authentication
- excessive data exposure
- unrestricted resource consumption
- broken function-level authorization
- unsafe consumption of third-party APIs

For .NET APIs, the practical response is:
- authorize access to each resource
- validate inputs
- avoid exposing entity models directly
- limit request sizes and rates
- log security-relevant failures
- keep dependencies updated

Object-level authorization
------
A common bug is checking that a user is authenticated but not checking that they can access the specific record.

Bad:

```csharp
[Authorize]
[HttpGet("orders/{id:int}")]
public async Task<IActionResult> GetOrder(int id)
{
    return Ok(await repository.GetByIdAsync(id));
}
```

Better:

```csharp
var order = await repository.GetByIdAsync(id);
if (order is null)
    return NotFound();

if (order.CustomerId != currentUser.CustomerId)
    return Forbid();

return Ok(order);
```

Authentication is not enough. Resource access must be checked.

Rate limiting
------
Rate limiting protects APIs from abusive or accidental high-volume traffic.

Example:

```csharp
builder.Services.AddRateLimiter(options =>
{
    options.AddFixedWindowLimiter("api", limiter =>
    {
        limiter.PermitLimit = 100;
        limiter.Window = TimeSpan.FromMinutes(1);
    });
});

var app = builder.Build();

app.UseRateLimiter();

app.MapGet("/api/products", () => Results.Ok())
   .RequireRateLimiting("api");
```

Rate limiting is especially important for:
- login endpoints
- expensive search endpoints
- public APIs
- endpoints that trigger external calls

CORS
------
CORS controls which browser origins can call your API. It is not an authentication system.

Example:

```csharp
builder.Services.AddCors(options =>
{
    options.AddPolicy("frontend", policy =>
    {
        policy
            .WithOrigins("https://app.example.com")
            .AllowAnyHeader()
            .AllowAnyMethod();
    });
});

app.UseCors("frontend");
```

Avoid:

```csharp
.AllowAnyOrigin()
.AllowAnyHeader()
.AllowAnyMethod()
```

That may be acceptable for a local prototype, but it is usually too broad for production.

Security headers
------
APIs and web apps benefit from security headers.

Common headers:
- `Strict-Transport-Security`
- `X-Content-Type-Options`
- `Content-Security-Policy`
- `Referrer-Policy`

Example middleware:

```csharp
app.Use(async (context, next) =>
{
    context.Response.Headers["X-Content-Type-Options"] = "nosniff";
    context.Response.Headers["Referrer-Policy"] = "no-referrer";
    await next();
});
```

For browser-facing apps, Content Security Policy deserves careful design and testing.

Input and output safety
------
Use request DTOs and response DTOs. Avoid binding directly to EF Core entities.

Why:
- prevents over-posting
- prevents leaking internal fields
- keeps public contracts stable
- makes validation explicit

Example:

```csharp
public sealed record UpdateUserRequest(string DisplayName);
public sealed record UserResponse(int Id, string DisplayName);
```

Common mistakes to avoid
------
Watch for these issues:
- trusting client-side validation
- using CORS as a security boundary
- authorizing by role only when resource ownership matters
- logging tokens or passwords
- exposing internal entity fields in API responses
- leaving expensive endpoints without limits

API security is a set of repeated habits. Authentication gets users in the door, but authorization, validation, limits, and observability keep the system defensible.

------------------------------------------------------------------------

**Next Article:** gRPC in .NET: Contracts, Streaming, and Interop
