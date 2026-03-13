---
title: 'Building Your First Web API in .NET 8: Controllers, Minimal APIs, and Routing'
date: 2026-03-08
permalink: /posts/2026/03/building_your_first_web_api/
tags:
  - dotnet
  - dotnet8
  - aspnetcore
  - webapi
  - beginner
  - fundamentals
---

This post shows how to build your first ASP.NET Core Web API and, more importantly, how to think about the choices you make along the way. The two main styles are **controllers** and **minimal APIs**, and both rely on the same routing system underneath. Once you understand those pieces, building new endpoints stops feeling mysterious.

What a Web API actually does
------
A Web API exposes HTTP endpoints that clients can call over the network. Those clients might be:
- a browser-based frontend
- a mobile app
- another microservice
- a background job

At a high level, every request follows the same path:
1. the server receives an HTTP request
2. routing matches the request to an endpoint
3. ASP.NET Core binds request data to .NET values
4. your code runs
5. the app returns an HTTP response, usually JSON

That flow is the same whether you use controllers or minimal APIs.

Creating a new API project
------
Start with the CLI:

```bash
dotnet new webapi -n FirstApi
cd FirstApi
dotnet run
```

The default template gives you:
- a `Program.cs` entry point
- OpenAPI/Swagger support
- HTTPS development configuration
- a sample endpoint

Once the app is running, open the Swagger URL shown in the terminal. That page is useful because it lets you test your API quickly without writing a frontend first.

Controllers vs minimal APIs
------
ASP.NET Core supports two primary styles.

Controllers:
- class-based
- good for larger apps and teams
- familiar if you prefer MVC-like organization
- work well with filters and conventions

Minimal APIs:
- function-based
- less ceremony
- great for smaller services or vertical slices
- easy to read in compact apps

Neither style is "the real one". They are both first-class options. Choose the one that fits the size and structure of your project.

Your first controller-based API
------
To use controllers, register controller services and map them:

```csharp
var builder = WebApplication.CreateBuilder(args);

builder.Services.AddControllers();
builder.Services.AddEndpointsApiExplorer();
builder.Services.AddSwaggerGen();

var app = builder.Build();

if (app.Environment.IsDevelopment())
{
    app.UseSwagger();
    app.UseSwaggerUI();
}

app.UseHttpsRedirection();
app.MapControllers();

app.Run();
```

Now add a controller:

```csharp
using Microsoft.AspNetCore.Mvc;

[ApiController]
[Route("api/todos")]
public sealed class TodosController : ControllerBase
{
    [HttpGet]
    public IActionResult GetAll()
    {
        var todos = new[]
        {
            new { Id = 1, Title = "Learn routing", IsDone = false },
            new { Id = 2, Title = "Build first API", IsDone = true }
        };

        return Ok(todos);
    }

    [HttpGet("{id:int}")]
    public IActionResult GetById(int id)
    {
        return Ok(new { Id = id, Title = "Sample todo", IsDone = false });
    }
}
```

Important details:
- `[ApiController]` enables API-focused behavior such as automatic validation responses
- `[Route("api/todos")]` defines the base route
- `[HttpGet]` and `[HttpGet("{id:int}")]` map HTTP verbs and templates

Your first minimal API
------
The same functionality can be written with minimal APIs:

```csharp
var builder = WebApplication.CreateBuilder(args);

builder.Services.AddEndpointsApiExplorer();
builder.Services.AddSwaggerGen();

var app = builder.Build();

if (app.Environment.IsDevelopment())
{
    app.UseSwagger();
    app.UseSwaggerUI();
}

app.UseHttpsRedirection();

app.MapGet("/api/todos", () =>
{
    return Results.Ok(new[]
    {
        new { Id = 1, Title = "Learn routing", IsDone = false },
        new { Id = 2, Title = "Build first API", IsDone = true }
    });
});

app.MapGet("/api/todos/{id:int}", (int id) =>
{
    return Results.Ok(new { Id = id, Title = "Sample todo", IsDone = false });
});

app.Run();
```

This is shorter because you define the endpoints directly in `Program.cs`. In larger apps, you can still keep minimal APIs organized by moving mappings into extension methods or route groups.

Routing fundamentals
------
Routing matches a URL and HTTP verb to your code.

Common examples:

```text
GET    /api/todos
GET    /api/todos/10
POST   /api/todos
PUT    /api/todos/10
DELETE /api/todos/10
```

Route templates can include parameters and constraints:

```csharp
[HttpGet("{id:int}")]
public IActionResult GetById(int id) => Ok(id);
```

Or in minimal APIs:

```csharp
app.MapGet("/api/orders/{orderId:guid}", (Guid orderId) => Results.Ok(orderId));
```

Why constraints matter:
- they reject invalid route shapes early
- they reduce ambiguity
- they make endpoint intent clearer

Without a constraint, `/api/orders/abc` might reach code that expected a number or GUID.

Grouping and organizing endpoints
------
Minimal APIs support route groups, which help keep related endpoints together:

```csharp
var todos = app.MapGroup("/api/todos");

todos.MapGet("/", () => Results.Ok(Array.Empty<object>()));
todos.MapGet("/{id:int}", (int id) => Results.Ok(new { id }));
todos.MapPost("/", (CreateTodoRequest request) => Results.Created("/api/todos/1", request));
```

Controllers provide organization through classes and folders. Minimal APIs provide organization through groups and extension methods. Both approaches are valid.

Choosing between controllers and minimal APIs
------
Use controllers when:
- the team prefers class-based conventions
- you want filter-heavy MVC organization
- you have many endpoints and want them separated by controller

Use minimal APIs when:
- you want low ceremony
- your service is small or focused
- you prefer endpoint-first design
- you are building lightweight internal APIs or prototypes

A common mistake is turning this into a dogmatic choice. The better question is: **which style will keep this codebase easier to navigate six months from now?**

A small CRUD example
------
This minimal API demonstrates common HTTP verbs:

```csharp
var todos = new Dictionary<int, string>();
var nextId = 1;

app.MapPost("/api/todos", (CreateTodoRequest request) =>
{
    var id = nextId++;
    todos[id] = request.Title;

    return Results.Created($"/api/todos/{id}", new { id, request.Title });
});

app.MapPut("/api/todos/{id:int}", (int id, UpdateTodoRequest request) =>
{
    if (!todos.ContainsKey(id))
        return Results.NotFound();

    todos[id] = request.Title;
    return Results.NoContent();
});

app.MapDelete("/api/todos/{id:int}", (int id) =>
{
    return todos.Remove(id)
        ? Results.NoContent()
        : Results.NotFound();
});
```

This is not production-ready, but it teaches the main mechanics:
- route matching
- request input
- status codes
- resource URLs

What to learn next
------
Once you can define endpoints, the next question is how request data becomes .NET objects and how invalid input is rejected consistently. That is where model binding and validation enter the picture.

------------------------------------------------------------------------

**Next Article:** Model Binding and Validation in ASP.NET Core: DataAnnotations and FluentValidation Basics
