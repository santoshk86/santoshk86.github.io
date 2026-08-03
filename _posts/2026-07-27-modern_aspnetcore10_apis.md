---
title: 'Modern ASP.NET Core 10 APIs: OpenAPI 3.1, Validation, ProblemDetails, and Server-Sent Events'
date: 2026-07-27
permalink: /posts/2026/07/modern_aspnetcore10_apis/
tags:
  - dotnet
  - dotnet10
  - aspnetcore
  - openapi
  - validation
  - sse
  - advanced
---

ASP.NET Core 10 modernizes several API fundamentals that previously required more third-party setup. Built-in OpenAPI generation produces OpenAPI 3.1 documents, Minimal APIs can validate inputs automatically, `ProblemDetails` can shape consistent failures, and Server-Sent Events provide a simple option for one-way real-time updates. These features work best when they are treated as parts of one stable API contract.

Create the API baseline
------
A compact Minimal API can register the main contract services directly:

```csharp
var builder = WebApplication.CreateBuilder(args);

builder.Services.AddOpenApi();
builder.Services.AddValidation();
builder.Services.AddProblemDetails();

var app = builder.Build();

app.UseExceptionHandler();

if (app.Environment.IsDevelopment())
{
    app.MapOpenApi();
}

app.MapOrderEndpoints();
app.Run();
```

`AddOpenApi` generates the contract. It does not automatically add Swagger UI or another interactive viewer. That separation is useful: contract generation can remain part of the application while the team chooses whether and where to expose a UI.

Generate OpenAPI 3.1 documents
------
ASP.NET Core 10 uses OpenAPI 3.1 and the newer JSON Schema model. Endpoint metadata should describe the contract explicitly.

```csharp
app.MapGet("/orders/{id:guid}", async Task<Results<Ok<OrderDto>, NotFound>> (
    Guid id,
    IOrderQueries queries,
    CancellationToken cancellationToken) =>
{
    var order = await queries.GetAsync(id, cancellationToken);
    return order is null ? TypedResults.NotFound() : TypedResults.Ok(order);
})
.WithName("GetOrder")
.WithTags("Orders")
.Produces<OrderDto>(StatusCodes.Status200OK)
.Produces(StatusCodes.Status404NotFound);
```

Typed results improve runtime code and generated documentation because success and failure shapes are visible to the framework.

Generate contracts during the build
------
Build-time generation lets CI compare the current API contract with a reviewed baseline. Add the document-generation package and configure an output directory in the project file:

```xml
<PropertyGroup>
  <OpenApiGenerateDocuments>true</OpenApiGenerateDocuments>
  <OpenApiDocumentsDirectory>$(MSBuildProjectDirectory)/openapi</OpenApiDocumentsDirectory>
</PropertyGroup>

<ItemGroup>
  <PackageReference Include="Microsoft.Extensions.ApiDescription.Server"
                    Version="10.0.0"
                    PrivateAssets="all" />
</ItemGroup>
```

The pipeline can then validate the generated JSON, detect accidental breaking changes, and publish the approved document to consumers.

Use document transformers for cross-cutting metadata
------
OpenAPI transformers are a better place for shared descriptions, security schemes, or organization-specific extensions than editing generated JSON after the build.

```csharp
builder.Services.AddOpenApi(options =>
{
    options.AddDocumentTransformer((document, context, cancellationToken) =>
    {
        document.Info.Title = "Orders API";
        document.Info.Version = "v1";
        document.Info.Description = "Order lookup and fulfillment operations.";
        return Task.CompletedTask;
    });
});
```

Operation transformers can modify individual operations based on endpoint metadata. Keep transformers deterministic so runtime and build-time documents stay identical.

Validate Minimal API inputs
------
With validation services registered, DataAnnotations on request models are evaluated before the handler runs.

```csharp
public sealed record CreateOrderRequest(
    [property: Required, MinLength(3)] string CustomerReference,
    [property: Range(1, 100)] int Quantity);

app.MapPost("/orders", async Task<Created<OrderDto>> (
    CreateOrderRequest request,
    IOrderCommands commands,
    CancellationToken cancellationToken) =>
{
    var order = await commands.CreateAsync(request, cancellationToken);
    return TypedResults.Created($"/orders/{order.Id}", order);
})
.ProducesValidationProblem();
```

Framework validation is appropriate for structural rules such as required values and ranges. Business invariants such as inventory availability or allowed state transitions still belong in application or domain logic.

Standardize errors with ProblemDetails
------
Clients should not parse a different error shape for validation, missing resources, conflicts, and unexpected exceptions. `ProblemDetails` provides a consistent baseline.

```csharp
app.MapPost("/orders/{id:guid}/cancel", async (
    Guid id,
    IOrderCommands commands,
    CancellationToken cancellationToken) =>
{
    var result = await commands.CancelAsync(id, cancellationToken);

    return result switch
    {
        CancelResult.NotFound => Results.NotFound(),
        CancelResult.AlreadyShipped => Results.Conflict(new ProblemDetails
        {
            Title = "Order cannot be cancelled",
            Detail = "The order has already shipped.",
            Status = StatusCodes.Status409Conflict
        }),
        _ => Results.NoContent()
    };
});
```

Add safe extensions such as a trace identifier or stable application error code. Do not expose exception messages, stack traces, connection strings, or internal type names.

Stream updates with Server-Sent Events
------
Server-Sent Events send a sequence of events from the server over one HTTP connection. They fit progress updates, notifications, and live dashboards when the client does not need to send messages back on the same channel.

```csharp
app.MapGet("/orders/{id:guid}/events", (
    Guid id,
    IOrderEventStream events,
    CancellationToken cancellationToken) =>
{
    return TypedResults.ServerSentEvents(
        events.ReadAsync(id, cancellationToken),
        eventType: "order-status");
});
```

The stream should honor cancellation immediately when the client disconnects. Add heartbeat behavior where infrastructure timeouts require it, and design event identifiers if clients must resume after reconnecting.

Choose SSE, SignalR, or ordinary HTTP
------
Use ordinary HTTP when the client can request current state occasionally. Use SSE when updates are server-to-client, text-based, and naturally ordered. Use SignalR when the application needs bidirectional messages, connection groups, hub methods, or richer transport handling.

Do not introduce a persistent connection for data that changes once every few minutes. Polling with caching can be simpler and cheaper.

Contract testing
------
An API contract deserves automated verification:

- generate the OpenAPI document during the build
- compare breaking changes against the approved contract
- test validation and `ProblemDetails` payloads
- verify authentication requirements appear in the document
- integration-test an SSE stream and cancellation
- confirm production does not expose development-only documentation endpoints

Common mistakes to avoid
------
Watch for these issues:

- treating an interactive API UI as the contract itself
- returning untyped or undocumented response shapes
- putting business validation entirely in attributes
- leaking exception details through `ProblemDetails`
- using SSE for bidirectional workflows
- leaving long-running streams without cancellation or reconnect design

ASP.NET Core 10 reduces the plumbing around API contracts. The engineering responsibility remains the same: make inputs, outputs, failures, and streaming behavior explicit and testable.

------------------------------------------------------------------------

**Next Article:** EF Core 10 Advanced Data Patterns: Named Query Filters, JSON, Complex Types, and Vector Search
