---
title: 'Domain Modeling in .NET: Aggregates, Value Objects, and Invariants'
date: 2026-03-22
permalink: /posts/2026/03/domain_modeling_aggregates_value_objects/
tags:
  - dotnet
  - domain-driven-design
  - architecture
  - domain-modeling
  - advanced
---

This post covers practical domain modeling in .NET using **aggregates, value objects, and invariants**. The goal is not to turn every app into a textbook DDD system. The goal is to put important business rules in places where they are hard to bypass.

Why domain modeling matters
------
In weak domain models, business rules are scattered across controllers, services, validators, and database scripts. That makes behavior hard to understand and easy to break.

A stronger domain model:
- names important concepts clearly
- protects valid state
- keeps related rules together
- makes illegal operations harder to represent

Domain modeling is most valuable when rules matter more than simple data storage.

Value objects
------
A value object is defined by its values, not an identity. Examples:
- money
- email address
- date range
- address
- percentage

Example:

```csharp
public sealed record Money
{
    public decimal Amount { get; }
    public string Currency { get; }

    public Money(decimal amount, string currency)
    {
        if (amount < 0)
            throw new ArgumentOutOfRangeException(nameof(amount));

        if (string.IsNullOrWhiteSpace(currency))
            throw new ArgumentException("Currency is required.", nameof(currency));

        Amount = amount;
        Currency = currency.ToUpperInvariant();
    }
}
```

Why this helps:
- invalid money values cannot be created
- formatting and comparison rules can live with the concept
- method signatures become more expressive than raw `decimal`

Invariants
------
An invariant is a rule that must always be true.

Examples:
- an order total cannot be negative
- a shipped order cannot be cancelled
- an invoice must have at least one line item
- a date range start must be before its end

The domain object should protect these rules:

```csharp
public sealed class Order
{
    private readonly List<OrderLine> _lines = [];

    public int Id { get; private set; }
    public OrderStatus Status { get; private set; } = OrderStatus.Draft;
    public IReadOnlyCollection<OrderLine> Lines => _lines;

    public void AddLine(int productId, int quantity, Money unitPrice)
    {
        if (Status != OrderStatus.Draft)
            throw new InvalidOperationException("Only draft orders can be changed.");

        if (quantity <= 0)
            throw new ArgumentOutOfRangeException(nameof(quantity));

        _lines.Add(new OrderLine(productId, quantity, unitPrice));
    }

    public void Submit()
    {
        if (_lines.Count == 0)
            throw new InvalidOperationException("An order requires at least one line.");

        Status = OrderStatus.Submitted;
    }
}
```

The API layer should not be the only place protecting the rule. APIs change. Domain rules should survive.

Aggregates
------
An aggregate is a consistency boundary. It groups entities and value objects that must change together.

In an ordering system:
- `Order` may be an aggregate root
- `OrderLine` may be inside the aggregate
- external code modifies lines through `Order`, not directly

Aggregate root:

```csharp
public sealed class Order
{
    private readonly List<OrderLine> _lines = [];

    public IReadOnlyCollection<OrderLine> Lines => _lines.AsReadOnly();

    public void RemoveLine(int productId)
    {
        var line = _lines.SingleOrDefault(x => x.ProductId == productId);
        if (line is null)
            return;

        _lines.Remove(line);
    }
}
```

The aggregate root controls how internal state changes. This keeps invariants centralized.

Persistence concerns
------
EF Core can persist rich domain models, but you need to design carefully:
- use private setters where possible
- expose read-only collections
- configure backing fields when needed
- avoid letting persistence requirements dominate domain behavior

Example:

```csharp
modelBuilder.Entity<Order>()
    .Navigation(o => o.Lines)
    .UsePropertyAccessMode(PropertyAccessMode.Field);
```

Domain modeling and EF Core can work together, but the model should still communicate business intent.

Common mistakes to avoid
------
Watch for these issues:
- using anemic classes with only public setters
- putting all rules in services while entities become data bags
- making aggregates too large
- throwing DDD patterns at simple CRUD screens
- confusing validation rules with permanent business invariants

Good domain modeling makes important rules obvious and enforceable. Use it where the business behavior deserves that protection.

------------------------------------------------------------------------

**Next Article:** Messaging and Event-Driven Design in .NET: MassTransit, RabbitMQ, and Kafka Basics
