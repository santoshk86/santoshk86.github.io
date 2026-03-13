---
title: 'Logging and Diagnostics in .NET 8: ILogger, Structured Logging, and Log Levels'
date: 2026-03-06
permalink: /posts/2026/03/logging_and_diagnostics_in_dotnet/
tags:
  - dotnet
  - dotnet8
  - aspnetcore
  - logging
  - diagnostics
  - fundamentals
---

This post covers the logging and diagnostics features you should understand before running a .NET application in any real environment. The short version is: **use `ILogger` everywhere, log structured data instead of string-concatenated messages, and configure log levels deliberately so production logs remain useful instead of noisy**.

Why logging matters
------
When an application fails, you usually learn about it in one of three ways:
- a user reports a bug
- an alert fires
- a dashboard shows abnormal behavior

At that point, logs are one of the first places you look. Good logs help you answer:
- What operation was the app performing?
- Which entity or request was involved?
- Was the failure expected, transient, or fatal?
- Did this happen once or repeatedly?

Without logs, debugging becomes guesswork.

`ILogger` basics
------
The built-in logging abstraction in .NET is `ILogger<T>`. You inject it into services, controllers, background workers, and any other application component.

Example:

```csharp
public sealed class CheckoutService(ILogger<CheckoutService> logger)
{
    public Task ProcessAsync(int orderId, CancellationToken cancellationToken)
    {
        logger.LogInformation("Starting checkout for order {OrderId}", orderId);

        return Task.CompletedTask;
    }
}
```

Why use `ILogger<T>` instead of static logging helpers:
- it participates in dependency injection
- it carries category information automatically
- it can route to different logging providers
- it is testable and framework-friendly

The generic type parameter becomes the log category, which helps filter or group logs by component.

Log levels
------
Every log entry has a level. This is how the system decides what should be written and what should be ignored.

Common levels:
- `Trace` for extremely detailed information
- `Debug` for development-focused diagnostics
- `Information` for normal operational events
- `Warning` for unusual but recoverable conditions
- `Error` for failures that affected an operation
- `Critical` for severe failures that may stop the app

Use them intentionally:
- successful request start or completion is usually `Information`
- a retry or fallback may be `Warning`
- a caught exception that prevented the operation is `Error`
- application startup failure may be `Critical`

If everything is logged as `Error`, your alerts become meaningless. If everything is logged as `Information`, important failures get buried.

Configuring log levels in `appsettings.json`
------
The simplest way to configure log levels is through configuration:

```json
{
  "Logging": {
    "LogLevel": {
      "Default": "Information",
      "Microsoft": "Warning",
      "Microsoft.AspNetCore": "Warning",
      "MyApp.Services.CheckoutService": "Debug"
    }
  }
}
```

This example means:
- application logs default to `Information`
- framework logs are reduced to `Warning`
- one service category is allowed to emit `Debug` logs

That selective filtering is how you keep logs useful instead of overwhelming.

Structured logging
------
Structured logging means you log message templates with named placeholders instead of manually building strings.

Good:

```csharp
logger.LogInformation(
    "Customer {CustomerId} placed order {OrderId} for {TotalAmount}",
    customerId,
    orderId,
    totalAmount);
```

Avoid:

```csharp
logger.LogInformation(
    "Customer " + customerId + " placed order " + orderId + " for " + totalAmount);
```

Why structured logging matters:
- log systems can index named properties
- you can search by `OrderId` or `CustomerId`
- data remains easier to parse in centralized tools
- the message template stays readable

This is a major difference between "some logs exist" and "the logs are operationally useful".

Logging exceptions correctly
------
When logging an exception, pass the exception object first:

```csharp
try
{
    await paymentGateway.CaptureAsync(orderId, cancellationToken);
}
catch (Exception ex)
{
    logger.LogError(ex, "Payment capture failed for order {OrderId}", orderId);
    throw;
}
```

That preserves the stack trace and exception details for the logging provider. Do not flatten exceptions into plain strings unless you want to lose valuable context.

Using scopes for request context
------
Scopes let you attach contextual values to every log inside a block.

```csharp
using var scope = logger.BeginScope(new Dictionary<string, object>
{
    ["OrderId"] = orderId,
    ["CustomerId"] = customerId
});

logger.LogInformation("Checkout started");
logger.LogWarning("Inventory service responded slowly");
```

This is useful when several log lines belong to the same operation. Instead of repeating identifiers in every message manually, the logging system can carry them as scope properties.

A realistic service example
------
The following service demonstrates levels, structured logging, and exception handling:

```csharp
public sealed class ReportService(
    ILogger<ReportService> logger,
    HttpClient httpClient)
{
    public async Task<string> DownloadDailyReportAsync(
        DateOnly reportDate,
        CancellationToken cancellationToken)
    {
        logger.LogInformation("Downloading daily report for {ReportDate}", reportDate);

        try
        {
            using var response = await httpClient.GetAsync(
                $"/reports/daily/{reportDate:yyyy-MM-dd}",
                cancellationToken);

            if (!response.IsSuccessStatusCode)
            {
                logger.LogWarning(
                    "Report endpoint returned status code {StatusCode} for {ReportDate}",
                    (int)response.StatusCode,
                    reportDate);
            }

            response.EnsureSuccessStatusCode();

            var content = await response.Content.ReadAsStringAsync(cancellationToken);

            logger.LogInformation("Downloaded report for {ReportDate}", reportDate);

            return content;
        }
        catch (Exception ex)
        {
            logger.LogError(ex, "Failed to download report for {ReportDate}", reportDate);
            throw;
        }
    }
}
```

This code tells a clear story:
- operation started
- a warning appears if the endpoint looks unhealthy
- a success entry is written when the response is complete
- failures are logged with full exception details

Logging providers
------
`ILogger` is an abstraction. Providers decide where logs go. Common built-in providers include:
- console
- debug
- EventSource
- EventLog on Windows

A minimal setup looks like:

```csharp
var builder = WebApplication.CreateBuilder(args);

builder.Logging.ClearProviders();
builder.Logging.AddConsole();
builder.Logging.AddDebug();
```

In production, teams often forward logs to a central system such as Application Insights, Seq, Elasticsearch, Grafana Loki, or a cloud platform sink. The application code still depends on `ILogger`, not the provider directly.

Diagnostics beyond logs
------
Logs tell you what happened. Diagnostics help you understand how the process is behaving.

Useful built-in diagnostics features include:
- health checks
- metrics and counters
- distributed tracing via `Activity`
- runtime tools such as `dotnet-counters` and `dotnet-trace`

A simple health check setup:

```csharp
var builder = WebApplication.CreateBuilder(args);

builder.Services.AddHealthChecks();

var app = builder.Build();

app.MapHealthChecks("/health");

app.Run();
```

That endpoint is often used by load balancers, orchestrators, or monitoring systems to confirm the app is alive.

If you are troubleshooting a live process, tools such as the following can help:

```bash
dotnet-counters monitor --process-id 12345
dotnet-trace collect --process-id 12345
```

Those tools are especially helpful when logs alone do not explain high CPU, memory pressure, or thread pool issues.

Practical logging rules
------
A few rules go a long way:
- do not log secrets, tokens, or passwords
- do not use `Information` for every loop iteration in hot paths
- log business identifiers that help investigation, such as `OrderId`
- prefer structured placeholders over interpolated log strings
- keep framework log levels tighter than application log levels
- make warnings actionable, not vague

Common mistakes to avoid
------
Watch for these problems:
- string concatenation instead of structured logging
- catching exceptions and logging them without rethrowing or handling them
- logging the same exception at multiple layers without purpose
- leaving `Debug` or `Trace` logging enabled everywhere in production
- burying request context so operators cannot correlate events

A clean logging strategy makes production support far easier. When logs are consistent, structured, and filtered correctly, you spend less time guessing and more time fixing the actual problem.

------------------------------------------------------------------------

**Next Article:** Dependency Injection Basics in .NET 8: Lifetimes, Service Registration, and the Options Pattern
