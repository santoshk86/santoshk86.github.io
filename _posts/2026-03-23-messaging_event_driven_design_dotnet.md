---
title: 'Messaging and Event-Driven Design in .NET: MassTransit, RabbitMQ, and Kafka Basics'
date: 2026-03-23
permalink: /posts/2026/03/messaging_event_driven_design_dotnet/
tags:
  - dotnet
  - messaging
  - masstransit
  - rabbitmq
  - kafka
  - advanced
---

This post covers the basics of messaging and event-driven design in .NET. When systems grow, not every operation should be a direct HTTP call. Messaging lets services communicate through **commands, events, queues, topics, and streams** so work can happen asynchronously and systems can be less tightly coupled.

Commands vs events
------
A command asks another component to do something.

Examples:
- `SendWelcomeEmail`
- `ChargePayment`
- `GenerateMonthlyReport`

An event says something already happened.

Examples:
- `OrderSubmitted`
- `PaymentCaptured`
- `CustomerRegistered`

The difference matters:
- commands have an intended handler
- events may have zero, one, or many subscribers
- events should be named in past tense

RabbitMQ basics
------
RabbitMQ is a message broker. It is often used for queues and pub/sub patterns.

Common concepts:
- producer sends a message
- exchange routes messages
- queue stores messages
- consumer processes messages

RabbitMQ is a strong fit for:
- task queues
- business events
- work distribution
- retry and dead-letter patterns

Kafka basics
------
Kafka is a distributed event streaming platform. It stores ordered logs of events in topics.

Common concepts:
- topic stores event records
- partition provides ordering and scaling
- consumer group coordinates readers
- offsets track progress

Kafka is a strong fit for:
- high-throughput event streams
- analytics pipelines
- event replay
- integration between many systems

RabbitMQ and Kafka overlap in some scenarios, but they are not identical tools. RabbitMQ often feels like messaging. Kafka often feels like event streaming.

MassTransit in .NET
------
MassTransit is a .NET messaging framework that can work with brokers such as RabbitMQ and Azure Service Bus.

Message contract:

```csharp
public sealed record OrderSubmitted(Guid OrderId, decimal TotalAmount);
```

Consumer:

```csharp
public sealed class OrderSubmittedConsumer(
    ILogger<OrderSubmittedConsumer> logger) : IConsumer<OrderSubmitted>
{
    public Task Consume(ConsumeContext<OrderSubmitted> context)
    {
        logger.LogInformation(
            "Order {OrderId} submitted for {TotalAmount}",
            context.Message.OrderId,
            context.Message.TotalAmount);

        return Task.CompletedTask;
    }
}
```

Registration concept:

```csharp
builder.Services.AddMassTransit(x =>
{
    x.AddConsumer<OrderSubmittedConsumer>();

    x.UsingRabbitMq((context, cfg) =>
    {
        cfg.Host("rabbitmq://localhost");
        cfg.ConfigureEndpoints(context);
    });
});
```

MassTransit gives you useful infrastructure patterns without writing broker plumbing by hand.

Message design rules
------
Good messages are:
- small
- explicit
- versionable
- named around business meaning
- independent from internal entity classes

Prefer:

```csharp
public sealed record CustomerEmailChanged(Guid CustomerId, string NewEmail);
```

Avoid sending entire EF Core entities across the wire. Messages are contracts. Treat them like public APIs.

Retries and dead-letter queues
------
Message processing must handle failure.

Common patterns:
- retry transient failures
- move poison messages to a dead-letter queue
- log correlation IDs
- make consumers idempotent

Idempotency means processing the same message twice does not corrupt state. This matters because at-least-once delivery can produce duplicate messages.

Common mistakes to avoid
------
Watch for these issues:
- using messaging to hide unclear service boundaries
- treating events as remote procedure calls
- publishing messages before the database transaction commits
- ignoring duplicate delivery
- sending huge internal object graphs as message payloads

Messaging is powerful when the workflow is naturally asynchronous. Use it to decouple time and ownership, not to avoid designing clear boundaries.

------------------------------------------------------------------------

**Next Article:** Outbox Pattern in .NET: Reliable Messaging and Eventual Consistency
