---
title: 'Advanced Dependency Injection in .NET: Keyed Services, Decorators, and Composition Roots'
date: 2026-04-03
permalink: /posts/2026/04/advanced_dependency_injection_dotnet/
tags:
  - dotnet
  - dependency-injection
  - architecture
  - advanced
---

This post covers advanced dependency injection patterns in .NET: **keyed services, decorators, and composition roots**. Basic DI teaches lifetimes and constructor injection. Advanced DI is about keeping object creation centralized while supporting real variation in behavior.

Composition root
------
The composition root is where the application wires dependencies together. In ASP.NET Core, this usually lives in `Program.cs` and extension methods called from it.

Example:

```csharp
builder.Services.AddOrderProcessing(builder.Configuration);
builder.Services.AddPayments(builder.Configuration);
builder.Services.AddMessaging(builder.Configuration);
```

The goal is:
- register dependencies in one predictable place
- keep business classes free from container usage
- avoid scattering `IServiceProvider` calls through the codebase

Keyed services
------
Keyed services let you register multiple implementations of the same service type and choose by key.

Example:

```csharp
builder.Services.AddKeyedScoped<IPaymentProcessor, StripePaymentProcessor>("stripe");
builder.Services.AddKeyedScoped<IPaymentProcessor, PaypalPaymentProcessor>("paypal");
```

Resolve in a minimal API:

```csharp
app.MapPost("/payments/stripe", (
    [FromKeyedServices("stripe")] IPaymentProcessor processor) =>
{
    return processor.ProcessAsync();
});
```

Use keyed services when the key is a real application concept. Avoid using them to hide unclear design decisions.

Decorators
------
A decorator wraps another implementation to add behavior.

Use cases:
- logging
- caching
- metrics
- retries
- validation

Example:

```csharp
public sealed class CachedProductService(
    IProductService inner,
    IMemoryCache cache) : IProductService
{
    public Task<ProductDto?> GetByIdAsync(int id, CancellationToken cancellationToken)
    {
        return cache.GetOrCreateAsync(
            $"products:{id}",
            entry =>
            {
                entry.AbsoluteExpirationRelativeToNow = TimeSpan.FromMinutes(5);
                return inner.GetByIdAsync(id, cancellationToken);
            });
    }
}
```

Decorators keep cross-cutting behavior outside the core implementation.

Factory patterns
------
Sometimes runtime values determine which implementation to use.

```csharp
public sealed class PaymentProcessorFactory(IServiceProvider serviceProvider)
{
    public IPaymentProcessor GetProcessor(string provider)
    {
        return provider switch
        {
            "stripe" => serviceProvider.GetRequiredKeyedService<IPaymentProcessor>("stripe"),
            "paypal" => serviceProvider.GetRequiredKeyedService<IPaymentProcessor>("paypal"),
            _ => throw new InvalidOperationException("Unknown payment provider.")
        };
    }
}
```

Use factories carefully. If every class starts asking the container for dependencies, you are drifting toward the service locator anti-pattern.

Avoid service locator
------
This is usually a smell:

```csharp
public sealed class OrderService(IServiceProvider serviceProvider)
{
    public Task SubmitAsync()
    {
        var repository = serviceProvider.GetRequiredService<IOrderRepository>();
        return Task.CompletedTask;
    }
}
```

Prefer explicit constructor dependencies. They make requirements visible and testing easier.

Common mistakes to avoid
------
Watch for these issues:
- injecting `IServiceProvider` everywhere
- using keyed services where a strategy object would be clearer
- registering singletons that depend on scoped services
- hiding complex composition in controllers
- creating decorators that change business behavior unexpectedly

Advanced DI should clarify composition, not make dependency graphs harder to understand.

------------------------------------------------------------------------

**Next Article:** Refactoring and Code Quality in .NET: Analyzers, Sonar, Style, and Architecture Tests
