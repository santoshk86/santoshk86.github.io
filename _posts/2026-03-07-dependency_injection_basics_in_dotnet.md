---
title: 'Dependency Injection Basics in .NET 8: Lifetimes, Service Registration, and the Options Pattern'
date: 2026-03-07
permalink: /posts/2026/03/dependency_injection_basics_in_dotnet/
tags:
  - dotnet
  - dotnet8
  - aspnetcore
  - dependency-injection
  - beginner
  - fundamentals
---

This post covers the built-in Dependency Injection container in .NET and the concepts you need to use it safely. If you remember only one idea, make it this: **services should declare what they need through constructor parameters, and the container should create those dependencies with the correct lifetime**.

What Dependency Injection means in practice
------
Dependency Injection, usually shortened to DI, is a pattern where objects receive the services they need from the outside instead of creating them internally.

Without DI:

```csharp
public sealed class OrderService
{
    private readonly EmailSender _emailSender = new();
    private readonly PaymentGateway _paymentGateway = new();
}
```

This code is tightly coupled:
- the implementation types are fixed
- testing becomes harder
- configuration is hidden
- object creation logic is scattered through the app

With DI:

```csharp
public sealed class OrderService(
    IEmailSender emailSender,
    IPaymentGateway paymentGateway,
    ILogger<OrderService> logger)
{
    public async Task PlaceOrderAsync(Order order, CancellationToken cancellationToken)
    {
        logger.LogInformation("Placing order {OrderId}", order.Id);

        await paymentGateway.CaptureAsync(order, cancellationToken);
        await emailSender.SendConfirmationAsync(order, cancellationToken);
    }
}
```

Now the class clearly declares its dependencies and does not decide how they are created.

The built-in container in ASP.NET Core
------
When you create a .NET app with:

```csharp
var builder = WebApplication.CreateBuilder(args);
```

you also get a service container at:

```csharp
builder.Services
```

This is where you register services before the app is built:

```csharp
builder.Services.AddScoped<IOrderService, OrderService>();
builder.Services.AddScoped<IEmailSender, SmtpEmailSender>();
builder.Services.AddSingleton<ISystemClock, UtcSystemClock>();
```

After `builder.Build()`, the container becomes read-only and the application resolves services from it as requests arrive.

Service lifetimes
------
The most important DI concept is lifetime. The built-in container supports three main lifetimes.

`Singleton`
- one instance for the entire app lifetime
- good for stateless utilities, caches, and shared configuration helpers
- must be thread-safe because the instance is reused everywhere

`Scoped`
- one instance per request in web apps
- the most common choice for business services and database contexts
- all services resolved within the same request share the same scoped instance

`Transient`
- a new instance each time the service is requested
- good for lightweight, stateless helpers
- can create too many objects if overused carelessly

Example registration:

```csharp
builder.Services.AddSingleton<ISystemClock, UtcSystemClock>();
builder.Services.AddScoped<IOrderService, OrderService>();
builder.Services.AddTransient<IEmailFormatter, EmailFormatter>();
```

Choosing the wrong lifetime is a common cause of subtle bugs.

Lifetime rules you should remember
------
These rules prevent many problems:
- a singleton must not depend on a scoped service
- scoped services can depend on singletons and transients
- transient services can depend on any lifetime, but repeated construction may have a cost

The most famous mistake is capturing a scoped dependency inside a singleton. For example, a singleton service must not hold onto a `DbContext` because `DbContext` is normally scoped per request.

Basic service registration patterns
------
The simplest registration maps an interface to an implementation:

```csharp
builder.Services.AddScoped<IProductRepository, SqlProductRepository>();
builder.Services.AddScoped<IProductService, ProductService>();
```

You can also register a concrete type directly:

```csharp
builder.Services.AddSingleton<TimeProvider>(TimeProvider.System);
```

Or create an object with a factory:

```csharp
builder.Services.AddSingleton(sp =>
{
    var logger = sp.GetRequiredService<ILogger<ApiClient>>();
    return new ApiClient("https://api.example.com", logger);
});
```

Factories are useful, but use them deliberately. If every registration becomes a large lambda, your startup code becomes hard to reason about.

Resolving services in endpoints and controllers
------
Once a service is registered, ASP.NET Core can inject it where needed.

Minimal API example:

```csharp
var builder = WebApplication.CreateBuilder(args);

builder.Services.AddScoped<IProductService, ProductService>();

var app = builder.Build();

app.MapGet("/products", async (
    IProductService service,
    CancellationToken cancellationToken) =>
{
    var products = await service.GetAllAsync(cancellationToken);
    return Results.Ok(products);
});

app.Run();
```

Controller example:

```csharp
[ApiController]
[Route("orders")]
public sealed class OrdersController(IOrderService orderService) : ControllerBase
{
    [HttpPost]
    public async Task<IActionResult> Create(Order request, CancellationToken cancellationToken)
    {
        await orderService.PlaceOrderAsync(request, cancellationToken);
        return Accepted();
    }
}
```

This keeps object creation out of endpoint logic and makes the app easier to test.

The options pattern
------
The options pattern is a clean way to inject configuration into services.

Suppose you have this configuration:

```json
{
  "Mail": {
    "Host": "smtp.example.com",
    "Port": 587,
    "Sender": "noreply@example.com"
  }
}
```

Create a class for the section:

```csharp
public sealed class MailOptions
{
    public const string SectionName = "Mail";

    public string Host { get; set; } = string.Empty;
    public int Port { get; set; }
    public string Sender { get; set; } = string.Empty;
}
```

Register it:

```csharp
builder.Services
    .AddOptions<MailOptions>()
    .Bind(builder.Configuration.GetSection(MailOptions.SectionName))
    .Validate(o => !string.IsNullOrWhiteSpace(o.Host), "Mail host is required.")
    .Validate(o => o.Port > 0, "Mail port must be greater than zero.")
    .ValidateOnStart();
```

Use it in a service:

```csharp
using Microsoft.Extensions.Options;

public sealed class SmtpEmailSender(IOptions<MailOptions> options)
    : IEmailSender
{
    private readonly MailOptions _mail = options.Value;

    public Task SendConfirmationAsync(Order order, CancellationToken cancellationToken)
    {
        Console.WriteLine(
            $"Sending order {order.Id} email using {_mail.Host}:{_mail.Port} as {_mail.Sender}");

        return Task.CompletedTask;
    }
}
```

This pattern is better than scattering raw configuration reads throughout the codebase.

`IOptions`, `IOptionsSnapshot`, and `IOptionsMonitor`
------
These three types solve slightly different problems:

- `IOptions<T>` gives a single bound value and is common for singleton-friendly scenarios
- `IOptionsSnapshot<T>` recomputes per request and is useful in scoped services
- `IOptionsMonitor<T>` supports change notifications and updated values over time

For most beginner applications:
- start with `IOptions<T>`
- use `IOptionsSnapshot<T>` in web requests when you need per-request freshness
- use `IOptionsMonitor<T>` for long-lived services that react to config changes

Common DI mistakes
------
Watch for these issues:
- injecting too many services into one class, which usually signals that the class has too many responsibilities
- resolving services manually from `IServiceProvider` everywhere, which turns DI into a service locator anti-pattern
- registering everything as singleton to "improve performance" without considering state and thread safety
- letting framework types such as `HttpClient` be created manually instead of using `AddHttpClient`

For example, this is better than constructing `HttpClient` yourself:

```csharp
builder.Services.AddHttpClient<WeatherClient>(client =>
{
    client.BaseAddress = new Uri("https://api.example.com/");
    client.Timeout = TimeSpan.FromSeconds(10);
});
```

That registration integrates with DI and uses the recommended HTTP client factory pattern.

A small end-to-end example
------
The following setup combines service registration, lifetimes, and options:

```csharp
var builder = WebApplication.CreateBuilder(args);

builder.Services
    .AddOptions<MailOptions>()
    .Bind(builder.Configuration.GetSection(MailOptions.SectionName))
    .ValidateDataAnnotations()
    .ValidateOnStart();

builder.Services.AddSingleton(TimeProvider.System);
builder.Services.AddScoped<IEmailSender, SmtpEmailSender>();
builder.Services.AddScoped<IOrderService, OrderService>();

var app = builder.Build();

app.MapPost("/orders", async (
    Order order,
    IOrderService orderService,
    CancellationToken cancellationToken) =>
{
    await orderService.PlaceOrderAsync(order, cancellationToken);
    return Results.Accepted($"/orders/{order.Id}");
});

app.Run();
```

That is the usual mental model for ASP.NET Core:
- configuration is bound to options
- services are registered with lifetimes
- endpoints ask for the services they need
- the container creates the object graph for each request

If that model is clear, much of the framework stops feeling magical.

------------------------------------------------------------------------

**Next Article:** Building Your First Web API in .NET 8: Controllers, Minimal APIs, and Routing
