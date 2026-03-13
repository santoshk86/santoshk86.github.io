---
title: 'Testing ASP.NET Core Apps: xUnit and Integration Tests with WebApplicationFactory'
date: 2026-03-16
permalink: /posts/2026/03/testing_aspnetcore_apps/
tags:
  - dotnet
  - dotnet8
  - testing
  - xunit
  - aspnetcore
  - intermediate
---

This post covers the two testing layers most .NET teams rely on heavily: **unit tests with xUnit and integration tests with `WebApplicationFactory`**. Unit tests give you fast feedback on isolated logic. Integration tests prove that your application actually boots, routes requests, resolves dependencies, and returns the expected HTTP responses.

Why both unit and integration tests matter
------
Unit tests answer questions like:
- does this service calculate the right value
- does this validator reject bad input
- does this mapper transform data correctly

Integration tests answer questions like:
- does the app start successfully
- does the route exist
- do middleware and DI configuration work
- does the endpoint return the expected status code and payload

If you only write unit tests, wiring problems can slip through. If you only write integration tests, feedback gets slower and failures become harder to pinpoint. You usually want both.

Getting started with xUnit
------
Create a test project:

```bash
dotnet new xunit -n StoreApp.Tests
dotnet add StoreApp.Tests reference src/StoreApp.Application/StoreApp.Application.csproj
```

A simple unit test looks like:

```csharp
public sealed class PriceCalculatorTests
{
    [Fact]
    public void ApplyDiscount_ReturnsDiscountedPrice()
    {
        var calculator = new PriceCalculator();

        var result = calculator.ApplyDiscount(100m, 10);

        Assert.Equal(90m, result);
    }
}
```

That test follows the common pattern:
- arrange
- act
- assert

Keep unit tests small and focused. Each one should explain exactly one expected behavior.

Testing a service with a fake dependency
------
Suppose `OrderService` depends on a repository:

```csharp
public interface IOrderRepository
{
    Task<Order?> GetByIdAsync(int id, CancellationToken cancellationToken);
}
```

You can fake the dependency in the test:

```csharp
public sealed class FakeOrderRepository : IOrderRepository
{
    public Task<Order?> GetByIdAsync(int id, CancellationToken cancellationToken)
        => Task.FromResult<Order?>(new Order { Id = id, Total = 100m });
}
```

Then test the service:

```csharp
public sealed class OrderServiceTests
{
    [Fact]
    public async Task GetTotalAsync_ReturnsOrderTotal()
    {
        var repository = new FakeOrderRepository();
        var service = new OrderService(repository);

        var total = await service.GetTotalAsync(42, CancellationToken.None);

        Assert.Equal(100m, total);
    }
}
```

This keeps the test fast and deterministic.

Why `WebApplicationFactory` is useful
------
`WebApplicationFactory<TEntryPoint>` boots your ASP.NET Core app in memory for integration testing. That means you can send real HTTP requests to the test server without deploying the app.

Typical use cases:
- verify routing
- verify middleware behavior
- verify authentication or authorization configuration
- verify JSON responses and status codes

Example:

```csharp
using System.Net;
using Microsoft.AspNetCore.Mvc.Testing;

public sealed class HealthEndpointTests
    : IClassFixture<WebApplicationFactory<Program>>
{
    private readonly HttpClient _client;

    public HealthEndpointTests(WebApplicationFactory<Program> factory)
    {
        _client = factory.CreateClient();
    }

    [Fact]
    public async Task Health_ReturnsOk()
    {
        var response = await _client.GetAsync("/health");

        Assert.Equal(HttpStatusCode.OK, response.StatusCode);
    }
}
```

This proves:
- the app can boot
- the route exists
- the HTTP pipeline returns the expected status

Customizing test services
------
Integration tests often need alternative registrations for databases, queues, or external services.

You can customize the factory:

```csharp
using Microsoft.AspNetCore.Hosting;
using Microsoft.AspNetCore.Mvc.Testing;
using Microsoft.Extensions.DependencyInjection;

public sealed class TestApiFactory : WebApplicationFactory<Program>
{
    protected override void ConfigureWebHost(IWebHostBuilder builder)
    {
        builder.ConfigureServices(services =>
        {
            services.AddSingleton<IEmailSender, FakeEmailSender>();
        });
    }
}
```

This is useful when:
- you want predictable test doubles
- you need an in-memory or temporary database
- a real external dependency would make the test slow or flaky

Testing with an in-memory database
------
For EF Core-backed integration tests, teams often swap the production database registration for a test database.

Example idea:
- remove the production `DbContext` registration
- register a test-specific database provider
- seed known data before the test runs

The exact database choice depends on the level of realism you want, but the important pattern is the same: **the app under test should boot with deterministic dependencies**.

What to assert in integration tests
------
Good integration assertions often include:
- status code
- response headers
- JSON body shape
- important field values
- side effects that matter to the use case

Example:

```csharp
[Fact]
public async Task GetProduct_ReturnsExpectedPayload()
{
    var response = await _client.GetAsync("/api/products/1");
    response.EnsureSuccessStatusCode();

    var json = await response.Content.ReadAsStringAsync();

    Assert.Contains("\"id\":1", json);
    Assert.Contains("\"name\":\"Keyboard\"", json);
}
```

As your test suite grows, you may want to deserialize JSON into DTOs instead of using string assertions, but the principle stays the same.

Testing strategy by layer
------
A useful baseline strategy looks like this:
- unit test pure business logic heavily
- integration test important endpoints and infrastructure wiring
- avoid writing huge end-to-end tests for every tiny behavior

You want the cheapest test that can prove the behavior reliably.

Common mistakes to avoid
------
Watch for these issues:
- testing private methods directly instead of testing behavior through public APIs
- writing brittle tests that depend on random time, order, or external state
- using integration tests for logic that should be covered by fast unit tests
- skipping integration tests and assuming startup, DI, and routes are correct

A healthy test suite gives you confidence to refactor. When unit tests protect the core logic and integration tests protect the app wiring, you can move faster with fewer regressions.

------------------------------------------------------------------------

**Next Article:** Deployment and Containerizing ASP.NET Core Apps
