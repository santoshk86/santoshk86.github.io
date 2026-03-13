---
title: 'Error Handling in ASP.NET Core: Middleware, Exception Filters, and ProblemDetails'
date: 2026-03-10
permalink: /posts/2026/03/error_handling_in_aspnetcore/
tags:
  - dotnet
  - dotnet8
  - aspnetcore
  - webapi
  - error-handling
  - fundamentals
---

This post covers how to handle failures in an ASP.NET Core API without leaking stack traces or returning random error shapes. The goal is not to prevent every exception. The goal is to **catch failures at the right level, log them, and return a consistent response contract such as ProblemDetails**.

Why centralized error handling matters
------
If every controller and endpoint invents its own error handling approach, the result is usually:
- duplicated try/catch blocks
- inconsistent status codes
- error messages that are too vague or too revealing
- logs that miss important context

A better design is:
- expected validation or domain errors handled deliberately
- unexpected exceptions handled centrally
- responses returned in a consistent format

That is where middleware, exception filters, and ProblemDetails help.

Using middleware for global exception handling
------
Middleware is the best place for application-wide exception handling because every request flows through the pipeline.

A simple custom middleware looks like this:

```csharp
using Microsoft.AspNetCore.Mvc;

public sealed class ExceptionHandlingMiddleware(
    RequestDelegate next,
    ILogger<ExceptionHandlingMiddleware> logger)
{
    public async Task InvokeAsync(HttpContext context)
    {
        try
        {
            await next(context);
        }
        catch (Exception ex)
        {
            logger.LogError(ex, "Unhandled exception for request {Path}", context.Request.Path);

            var problem = new ProblemDetails
            {
                Title = "An unexpected error occurred.",
                Status = StatusCodes.Status500InternalServerError,
                Detail = "The server could not complete the request.",
                Instance = context.Request.Path
            };

            context.Response.StatusCode = problem.Status.Value;
            context.Response.ContentType = "application/problem+json";

            await context.Response.WriteAsJsonAsync(problem);
        }
    }
}
```

Register it early in the pipeline:

```csharp
var app = builder.Build();

app.UseMiddleware<ExceptionHandlingMiddleware>();
```

This approach is effective because it covers the whole app, not just one controller.

Mapping known exceptions to status codes
------
Not every exception should become a 500. Some failures map naturally to specific HTTP responses.

Example:

```csharp
catch (ProductNotFoundException ex)
{
    logger.LogWarning(ex, "Product was not found.");

    var problem = new ProblemDetails
    {
        Title = "Product not found.",
        Status = StatusCodes.Status404NotFound,
        Detail = ex.Message,
        Instance = context.Request.Path
    };

    context.Response.StatusCode = problem.Status.Value;
    context.Response.ContentType = "application/problem+json";

    await context.Response.WriteAsJsonAsync(problem);
}
```

That gives clients a meaningful status code instead of collapsing everything into a generic 500.

Using exception filters
------
Exception filters are controller-focused and run within the MVC action pipeline. They are useful when you want controller-specific handling behavior.

Example filter:

```csharp
using Microsoft.AspNetCore.Mvc;
using Microsoft.AspNetCore.Mvc.Filters;

public sealed class ApiExceptionFilter(ILogger<ApiExceptionFilter> logger)
    : IExceptionFilter
{
    public void OnException(ExceptionContext context)
    {
        logger.LogError(context.Exception, "Controller action failed.");

        context.Result = new ObjectResult(new ProblemDetails
        {
            Title = "Controller action failed.",
            Status = StatusCodes.Status500InternalServerError,
            Detail = "The request could not be completed."
        })
        {
            StatusCode = StatusCodes.Status500InternalServerError
        };

        context.ExceptionHandled = true;
    }
}
```

Register it with controllers:

```csharp
builder.Services.AddControllers(options =>
{
    options.Filters.Add<ApiExceptionFilter>();
});
```

When to use filters:
- you are already using controllers
- the handling is tied to MVC actions
- you want controller/action scoped behavior

When to prefer middleware:
- you want app-wide behavior
- you need coverage beyond MVC
- you want one central place for cross-cutting failure handling

ProblemDetails as the response standard
------
`ProblemDetails` is the standard error shape used in ASP.NET Core for HTTP APIs. It is based on RFC 7807 style semantics and gives clients a predictable contract.

Typical fields:
- `type`
- `title`
- `status`
- `detail`
- `instance`

Example response:

```json
{
  "title": "Product not found.",
  "status": 404,
  "detail": "Product 42 does not exist.",
  "instance": "/api/products/42"
}
```

Why it is useful:
- clients know what to parse
- frontend teams get consistent error contracts
- your API stops returning random anonymous objects for failures

ASP.NET Core also provides built-in ProblemDetails support that you can wire into your app configuration. Even if you use custom middleware, it is a good idea to keep the response shape aligned with ProblemDetails conventions.

Expected errors vs unexpected errors
------
You should think about failures in two groups.

Expected errors:
- validation failures
- missing resources
- conflict conditions
- unauthorized or forbidden access

Unexpected errors:
- null reference exceptions
- network failures you did not anticipate
- database outages
- programming bugs

Expected errors usually deserve explicit handling and non-500 status codes. Unexpected errors should be logged and turned into safe 500 responses.

A practical middleware example
------
The following middleware maps a few common cases:

```csharp
public sealed class ApiExceptionMiddleware(
    RequestDelegate next,
    ILogger<ApiExceptionMiddleware> logger)
{
    public async Task InvokeAsync(HttpContext context)
    {
        try
        {
            await next(context);
        }
        catch (ValidationException ex)
        {
            await WriteProblemAsync(
                context,
                StatusCodes.Status400BadRequest,
                "Validation failed.",
                ex.Message);
        }
        catch (EntityNotFoundException ex)
        {
            await WriteProblemAsync(
                context,
                StatusCodes.Status404NotFound,
                "Resource not found.",
                ex.Message);
        }
        catch (Exception ex)
        {
            logger.LogError(ex, "Unhandled server error.");

            await WriteProblemAsync(
                context,
                StatusCodes.Status500InternalServerError,
                "Server error.",
                "An unexpected error occurred.");
        }
    }

    private static Task WriteProblemAsync(
        HttpContext context,
        int statusCode,
        string title,
        string detail)
    {
        context.Response.StatusCode = statusCode;
        context.Response.ContentType = "application/problem+json";

        return context.Response.WriteAsJsonAsync(new ProblemDetails
        {
            Title = title,
            Status = statusCode,
            Detail = detail,
            Instance = context.Request.Path
        });
    }
}
```

This pattern keeps error translation in one place instead of scattered across the codebase.

Common mistakes to avoid
------
Watch for these issues:
- returning raw exception messages directly to public clients
- wrapping every action in copy-pasted try/catch blocks
- using 500 for validation or missing resource errors
- logging the same exception multiple times at multiple layers for no reason

Good error handling makes APIs easier to operate and easier to trust. Clients get consistent responses, and your team gets cleaner logs and fewer debugging surprises.

------------------------------------------------------------------------

**Next Article:** REST Best Practices for ASP.NET Core APIs: Status Codes, Pagination, Filtering, and Versioning
