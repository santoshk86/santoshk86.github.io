---
title: 'Outbox Pattern in .NET: Reliable Messaging and Eventual Consistency'
date: 2026-03-24
permalink: /posts/2026/03/outbox_pattern_eventual_consistency/
tags:
  - dotnet
  - architecture
  - messaging
  - outbox
  - eventual-consistency
  - advanced
---

This post covers the outbox pattern, one of the most important patterns for reliable messaging. The problem is simple: your application needs to save data and publish a message, but the database and message broker do not share one transaction. The outbox pattern solves this by storing messages in the database first and publishing them later.

The dual-write problem
------
Imagine this flow:

```text
1. Save order to database
2. Publish OrderSubmitted event
```

What happens if step 1 succeeds and step 2 fails? The order exists, but no event is published.

Now reverse it:

```text
1. Publish OrderSubmitted event
2. Save order to database
```

What happens if the event is published and then the database save fails? Other systems react to an order that does not exist.

This is the dual-write problem.

Outbox table
------
The outbox pattern writes business data and pending messages in the same database transaction.

Example table shape:

```text
OutboxMessages
  Id
  Type
  Payload
  OccurredOnUtc
  ProcessedOnUtc
  Error
```

When an order is submitted:

```csharp
order.Submit();

dbContext.Orders.Add(order);
dbContext.OutboxMessages.Add(new OutboxMessage
{
    Id = Guid.NewGuid(),
    Type = nameof(OrderSubmitted),
    Payload = JsonSerializer.Serialize(new OrderSubmitted(order.Id, order.Total)),
    OccurredOnUtc = DateTime.UtcNow
});

await dbContext.SaveChangesAsync(cancellationToken);
```

Now the order and event record commit together.

Outbox publisher
------
A background worker reads unprocessed outbox rows and publishes them.

```csharp
public sealed class OutboxPublisher(
    IServiceScopeFactory scopeFactory,
    ILogger<OutboxPublisher> logger) : BackgroundService
{
    protected override async Task ExecuteAsync(CancellationToken stoppingToken)
    {
        while (!stoppingToken.IsCancellationRequested)
        {
            using var scope = scopeFactory.CreateScope();
            var dbContext = scope.ServiceProvider.GetRequiredService<AppDbContext>();
            var publisher = scope.ServiceProvider.GetRequiredService<IEventPublisher>();

            var messages = await dbContext.OutboxMessages
                .Where(x => x.ProcessedOnUtc == null)
                .OrderBy(x => x.OccurredOnUtc)
                .Take(50)
                .ToListAsync(stoppingToken);

            foreach (var message in messages)
            {
                try
                {
                    await publisher.PublishAsync(message.Type, message.Payload, stoppingToken);
                    message.ProcessedOnUtc = DateTime.UtcNow;
                }
                catch (Exception ex)
                {
                    logger.LogError(ex, "Outbox publish failed for {MessageId}", message.Id);
                    message.Error = ex.Message;
                }
            }

            await dbContext.SaveChangesAsync(stoppingToken);
            await Task.Delay(TimeSpan.FromSeconds(5), stoppingToken);
        }
    }
}
```

This is the core mechanism. Production implementations add locking, retries, batching, and metrics.

Eventual consistency
------
The outbox pattern creates eventual consistency. The database update commits first. Other systems learn about it shortly after the outbox publisher sends the event.

This means:
- clients should not expect every read model to update immediately
- downstream handlers must tolerate delay
- duplicate event handling must be safe
- operations need correlation IDs for tracing

Eventual consistency is not a bug. It is a tradeoff for reliability and decoupling.

Idempotent consumers
------
Outbox publishing can produce duplicate messages if a publish succeeds but marking the row processed fails. Consumers must handle duplicates.

Common approaches:
- store processed message IDs
- use natural idempotency keys
- make updates based on current state
- use unique constraints where appropriate

Example:

```csharp
if (await dbContext.ProcessedMessages.AnyAsync(x => x.MessageId == messageId, cancellationToken))
    return;
```

Idempotency is not optional in message-based systems.

Common mistakes to avoid
------
Watch for these issues:
- publishing messages before the database transaction commits
- assuming a broker publish and database save are one atomic operation
- ignoring duplicate delivery
- leaving failed outbox rows invisible
- storing messages with no type or version information

The outbox pattern is a practical reliability tool. It turns a fragile dual-write into a durable process that can be retried, monitored, and repaired.

------------------------------------------------------------------------

**Next Article:** Observability in .NET: OpenTelemetry Traces, Metrics, and Logs
