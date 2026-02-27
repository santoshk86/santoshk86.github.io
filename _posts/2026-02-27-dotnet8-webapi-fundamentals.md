---
title: '.NET 8 Web API Fundamentals: Routing, Models, Validation, and the Request Pipeline'
date: 2026-02-27
permalink: /posts/2026/02/dotnet8-webapi-fundamentals/
tags:
  - dotnet
  - dotnet8
  - aspnetcore
  - webapi
  - beginner
  - fundamentals
---

This post covers the fundamentals of building a Web API with **.NET 8 (ASP.NET Core)**. If you’re new to the ecosystem, your goal isn’t to memorize every feature—it’s to understand the core mechanics: **how requests flow through your app, how endpoints are defined, how data is validated, and how responses are shaped**. Once these pieces click, everything else becomes “just configuration”.

What is an ASP.NET Core Web API?
------
An ASP.NET Core Web API is an HTTP service built on top of the **Kestrel** web server and the ASP.NET Core framework. It exposes endpoints (URLs) that accept requests (GET/POST/PUT/DELETE), runs them through a pipeline (middleware), binds inputs to .NET types (model binding), validates them, executes your endpoint logic, and returns HTTP responses (JSON by default).

In .NET 8 you can build APIs using:
- **Minimal APIs** (endpoint-first, low ceremony)
- **Controllers** (MVC-style, attributes, filters)

Both are valid. Minimal APIs are great for smaller services and vertical slices. Controllers are still excellent for larger teams and conventions. The fundamentals below apply to both.

Your first API in .NET 8
------
Create a project using the .NET CLI:

```bash
dotnet new webapi -n FundamentalsApi
cd FundamentalsApi
dotnet run
```

Open the `https://localhost:xxxx/swagger` URL printed in the console. Swagger/OpenAPI is not “magic”—it’s a contract generator that helps you explore and test your endpoints.

A quick look at Program.cs
------
In .NET 8, your app starts in `Program.cs`. This is where you:
1) register services (Dependency Injection container)
2) configure middleware (HTTP pipeline)
3) map endpoints

A typical minimal API setup looks like:

```csharp
var builder = WebApplication.CreateBuilder(args);

builder.Services.AddEndpointsApiExplorer();
builder.Services.AddSwaggerGen();

var app = builder.Build();

app.UseHttpsRedirection();

if (app.Environment.IsDevelopment())
{
    app.UseSwagger();
    app.UseSwaggerUI();
}

app.MapGet("/health", () => Results.Ok(new { status = "ok" }));

app.Run();
```

Even if you prefer controllers, the same idea exists:
- `builder.Services.AddControllers()`
- `app.MapControllers()`

The important concept is: **services first, pipeline second, endpoints last**.

The request pipeline (middleware)
------
When an HTTP request hits your server, it flows through a chain of middleware in the order you configure them. Each middleware can:
- short-circuit the request (return a response immediately), or
- do work and pass control to the next middleware

Common middleware responsibilities:
- HTTPS redirection
- routing
- authentication/authorization
- exception handling
- CORS
- rate limiting
- logging

Order matters. For example:
- `UseAuthentication()` must run before `UseAuthorization()`
- `UseRouting()` must be set before endpoint execution (controllers handle this implicitly with modern templates)

A useful mental model:

**Request → Middleware A → Middleware B → Endpoint → Middleware B (return) → Middleware A (return) → Response**

If you understand this, you can reason about bugs like “why is authorization not firing?” or “why does my exception handler not catch errors?”

Routing and endpoints
------
Routing maps a URL + HTTP verb to an endpoint. Minimal APIs make this very explicit:

```csharp
app.MapGet("/todos/{id:int}", (int id) => Results.Ok(new { id }));
```

Key details:
- `"{id:int}"` is a route parameter with an **int constraint**
- If the client calls `/todos/abc`, routing won’t match (good!)

Controllers do the same with attributes:

```csharp
[ApiController]
[Route("todos")]
public class TodosController : ControllerBase
{
    [HttpGet("{id:int}")]
    public IActionResult Get(int id) => Ok(new { id });
}
```

Minimal APIs vs controllers is mostly about style and structure. The underlying routing system is consistent.

Model binding: getting data into your code
------
Model binding is how ASP.NET Core turns incoming HTTP data into .NET objects. Inputs can come from:
- route parameters (`/todos/5`)
- query string (`/todos?status=open`)
- headers
- body (JSON)

Minimal APIs infer binding rules from parameter types:
- simple types (int/string) often bind from route or query
- complex types often bind from the JSON body

Example request model:

```csharp
public sealed record CreateTodoRequest(string Title, DateOnly? DueDate);
```

Minimal API endpoint:

```csharp
app.MapPost("/todos", (CreateTodoRequest req) =>
{
    // req.Title and req.DueDate come from JSON
    return Results.Created("/todos/1", new { id = 1, req.Title, req.DueDate });
});
```

If the client posts invalid JSON, the framework returns a 400 automatically. But that’s not the same as validation—validation is about business rules like “Title must not be empty”.

Validation with DataAnnotations (the baseline)
------
For fundamentals, start with **DataAnnotations**. They’re built-in and enough for many APIs.

```csharp
using System.ComponentModel.DataAnnotations;

public sealed class CreateTodoRequest
{
    [Required]
    [MinLength(3)]
    public string Title { get; set; } = default!;

    public DateOnly? DueDate { get; set; }
}
```

Now, how validation triggers depends on your style:
- With **controllers** and `[ApiController]`, invalid models automatically return a 400 with details.
- With **minimal APIs**, you commonly validate manually or use a validation library/middleware.

A straightforward manual approach for minimal APIs:

```csharp
app.MapPost("/todos", (CreateTodoRequest req) =>
{
    var errors = new List<string>();

    if (string.IsNullOrWhiteSpace(req.Title) || req.Title.Length < 3)
        errors.Add("Title must be at least 3 characters.");

    if (errors.Count > 0)
        return Results.ValidationProblem(new Dictionary<string, string[]>
        {
            ["Title"] = errors.ToArray()
        });

    return Results.Created("/todos/1", new { id = 1, req.Title, req.DueDate });
});
```

This is not the prettiest, but it teaches the mechanics: **validate inputs → return a consistent error response → keep endpoint logic clean**. As you advance, you’ll likely adopt FluentValidation or a dedicated validation layer.

Returning responses: status codes + shapes
------
A professional API is predictable. Two key rules:
1) Use correct status codes
2) Use consistent response bodies

Common status codes:
- `200 OK` (successful GET)
- `201 Created` (resource created; include location or resource)
- `204 No Content` (successful update/delete with no body)
- `400 Bad Request` (validation errors)
- `401 Unauthorized` (not authenticated)
- `403 Forbidden` (authenticated but not allowed)
- `404 Not Found` (missing resource)
- `409 Conflict` (concurrency/conflict)
- `500 Internal Server Error` (unexpected failure)

In minimal APIs, return typed results:
- `Results.Ok(...)`
- `Results.Created(...)`
- `Results.NotFound()`
- `Results.ValidationProblem(...)`

In controllers, return `IActionResult`:
- `Ok(...)`
- `Created(...)`
- `NotFound()`
- `BadRequest(...)`

Consistency tip: use **Problem Details** (RFC 7807 style) for errors. ASP.NET Core supports this pattern and many tooling ecosystems understand it.

Error handling: don’t leak exceptions
------
In early projects, errors often become:
- unhandled exceptions (500 with stack traces in dev)
- inconsistent error messages
- missing logs

At minimum:
- keep detailed errors only for development
- return clean problem details to clients
- log the exception server-side

Later in the series you can add a global exception handling middleware and a standard error contract. For fundamentals, remember: **clients need stable error formats, not stack traces**.

Dependency Injection (DI) in one paragraph
------
ASP.NET Core has built-in DI. You register services (like repositories, HTTP clients, business services) and then request them in endpoints/controllers.

Example:

```csharp
builder.Services.AddScoped<ITodoService, TodoService>();

app.MapGet("/todos/{id:int}", (int id, ITodoService service) =>
{
    var todo = service.GetById(id);
    return todo is null ? Results.NotFound() : Results.Ok(todo);
});
```

This keeps your code testable and reduces hard dependencies. The key concept to learn now is **service lifetime**:
- `Singleton`: one instance for app lifetime
- `Scoped`: one per request (most common for app services and DbContext)
- `Transient`: new each time

Putting it all together: a tiny “Todo” API
------
Here is a compact API that demonstrates routing, binding, validation, and responses:

```csharp
var todos = new Dictionary<int, string>();
var nextId = 1;

app.MapPost("/todos", (CreateTodoRequest req) =>
{
    if (string.IsNullOrWhiteSpace(req.Title) || req.Title.Length < 3)
    {
        return Results.ValidationProblem(new Dictionary<string, string[]>
        {
            ["Title"] = new[] { "Title must be at least 3 characters." }
        });
    }

    var id = nextId++;
    todos[id] = req.Title;

    return Results.Created($"/todos/{id}", new { id, title = req.Title });
});

app.MapGet("/todos/{id:int}", (int id) =>
{
    return todos.TryGetValue(id, out var title)
        ? Results.Ok(new { id, title })
        : Results.NotFound();
});
```

This isn’t “production-ready” (no persistence, no auth, no concurrency handling), but it’s a perfect fundamentals lab.