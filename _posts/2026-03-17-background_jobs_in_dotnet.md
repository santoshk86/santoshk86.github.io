---
title: 'Background Jobs in .NET: HostedService, BackgroundService, and Worker Services'
date: 2026-03-17
permalink: /posts/2026/03/background_jobs_in_dotnet/
tags:
  - dotnet
  - dotnet8
  - aspnetcore
  - background-jobs
  - worker-service
  - intermediate
---

This post covers the background processing options built into modern .NET applications. Web APIs handle request/response work, but real systems also need jobs that run outside a single HTTP request: **queue consumers, scheduled cleanup, report generation, synchronization, and long-running workers**.

Why background jobs matter
------
Background jobs help you keep HTTP endpoints fast and predictable. Instead of making a user wait while the server sends emails, imports files, or calls slow third-party systems, your API can accept the request, persist work, and let a worker process it asynchronously.

Common use cases:
- sending emails or notifications
- consuming messages from a queue
- processing uploaded files
- refreshing caches
- running periodic cleanup
- synchronizing with external systems

The key design rule is: **background work must be observable, cancellable, and safe to retry**.

`IHostedService`
------
`IHostedService` is the low-level contract for services that start and stop with the application host.

```csharp
public sealed class StartupTask(ILogger<StartupTask> logger) : IHostedService
{
    public Task StartAsync(CancellationToken cancellationToken)
    {
        logger.LogInformation("Startup task running.");
        return Task.CompletedTask;
    }

    public Task StopAsync(CancellationToken cancellationToken)
    {
        logger.LogInformation("Startup task stopping.");
        return Task.CompletedTask;
    }
}
```

Register it in DI:

```csharp
builder.Services.AddHostedService<StartupTask>();
```

Use `IHostedService` when you need direct control over startup and shutdown. For most continuous workers, `BackgroundService` is easier.

`BackgroundService`
------
`BackgroundService` is an abstract base class that implements `IHostedService` and gives you one main method: `ExecuteAsync`.

```csharp
public sealed class CleanupWorker(
    ILogger<CleanupWorker> logger,
    IServiceScopeFactory scopeFactory) : BackgroundService
{
    protected override async Task ExecuteAsync(CancellationToken stoppingToken)
    {
        while (!stoppingToken.IsCancellationRequested)
        {
            logger.LogInformation("Cleanup cycle started.");

            using var scope = scopeFactory.CreateScope();
            var service = scope.ServiceProvider.GetRequiredService<ICleanupService>();

            await service.DeleteExpiredRecordsAsync(stoppingToken);

            await Task.Delay(TimeSpan.FromMinutes(15), stoppingToken);
        }
    }
}
```

Important details:
- honor `stoppingToken`
- do not swallow exceptions silently
- create scopes when you need scoped services such as `DbContext`
- keep each loop iteration small and observable

Why `IServiceScopeFactory` appears
------
Hosted services are registered as singletons. That means they must not directly depend on scoped services such as EF Core `DbContext`.

This is wrong:

```csharp
public sealed class BadWorker(StoreDbContext dbContext) : BackgroundService
{
    protected override Task ExecuteAsync(CancellationToken stoppingToken)
        => Task.CompletedTask;
}
```

This is safer:

```csharp
using var scope = scopeFactory.CreateScope();
var dbContext = scope.ServiceProvider.GetRequiredService<StoreDbContext>();
```

Each cycle gets a fresh scope and the scoped dependencies are disposed correctly.

Worker Service template
------
For standalone background processes, use the Worker Service template:

```bash
dotnet new worker -n ImportWorker
cd ImportWorker
dotnet run
```

The template creates:
- a generic host
- a `Worker` class derived from `BackgroundService`
- logging and configuration support

Worker Services are a good fit when:
- the process does not need to expose HTTP endpoints
- the job will run in a container
- the worker consumes a queue or stream continuously

Queue-based background work
------
For production systems, avoid storing important work only in memory. A queue gives you durability and retry behavior.

A simple interface might look like:

```csharp
public interface IBackgroundTaskQueue
{
    ValueTask QueueAsync(Func<CancellationToken, ValueTask> workItem);
    ValueTask<Func<CancellationToken, ValueTask>> DequeueAsync(CancellationToken cancellationToken);
}
```

That can be useful for local in-process work, but for critical jobs consider durable infrastructure:
- Azure Service Bus
- RabbitMQ
- Kafka
- AWS SQS
- database-backed job tables

The more important the job, the more you should prefer durable storage over in-memory queues.

Shutdown behavior
------
When the host stops, .NET asks hosted services to stop gracefully. Your worker should:
- stop accepting new work
- finish or cancel current work
- release external resources
- log shutdown progress

Do not ignore cancellation tokens. A worker that refuses to stop cleanly causes deployment and container shutdown problems.

Common mistakes to avoid
------
Watch for these issues:
- running long jobs directly inside HTTP endpoints
- injecting scoped services into singleton hosted services
- using `Task.Run` as a substitute for durable background processing
- ignoring cancellation tokens
- failing silently when a background job throws

Background jobs are part of your production system, not a side feature. Treat them with the same care as APIs: logging, retries, cancellation, and health checks all matter.

------------------------------------------------------------------------

**Next Article:** Caching in .NET: IMemoryCache, Distributed Cache with Redis, and Response Caching
