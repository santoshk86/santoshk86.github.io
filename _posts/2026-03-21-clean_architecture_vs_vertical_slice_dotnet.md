---
title: 'Clean Architecture vs Vertical Slice in .NET: Pragmatic Guidance'
date: 2026-03-21
permalink: /posts/2026/03/clean_architecture_vs_vertical_slice_dotnet/
tags:
  - dotnet
  - architecture
  - clean-architecture
  - vertical-slice
  - advanced
---

This post compares two popular ways to structure .NET applications: **Clean Architecture** and **Vertical Slice Architecture**. Both can produce maintainable systems, and both can become over-engineered if applied mechanically. The useful question is not "which one is best?" The useful question is "which structure reduces change friction for this codebase?"

Clean Architecture in one picture
------
Clean Architecture separates code into layers where dependencies point inward.

Typical layers:
- Domain
- Application
- Infrastructure
- Web/API

The domain and application layers do not depend on the database, web framework, or external services. Infrastructure implements interfaces defined by inner layers.

Example dependency direction:

```text
Web API -> Application -> Domain
Infrastructure -> Application
Infrastructure -> Domain
```

This is useful when:
- business rules are complex
- persistence details may change
- the team wants strong boundaries
- multiple frontends or hosts use the same application core

Clean Architecture tradeoffs
------
The benefits are real:
- clear dependency direction
- testable use cases
- business logic protected from framework code
- easier substitution of infrastructure

The costs are also real:
- more projects and files
- more mapping code
- more interfaces
- more ceremony for simple CRUD

Clean Architecture is not a magic quality generator. If the domain is simple, too many layers can slow the team down.

Vertical Slice Architecture
------
Vertical Slice Architecture organizes code by feature instead of technical layer.

Example:

```text
Features/
  Products/
    CreateProduct/
      CreateProductEndpoint.cs
      CreateProductCommand.cs
      CreateProductValidator.cs
      CreateProductHandler.cs
    GetProduct/
      GetProductEndpoint.cs
      GetProductQuery.cs
      GetProductHandler.cs
```

Each feature contains the request, validation, handler, and endpoint pieces needed for that use case.

This is useful when:
- features change independently
- the app has many endpoints
- you want local reasoning
- teams own product areas instead of technical layers

Vertical slices reduce cross-folder jumping. A developer can open one feature folder and see most of the code that changes together.

Vertical Slice tradeoffs
------
Benefits:
- feature code stays close together
- less shared abstraction up front
- easier to delete or rewrite one feature
- natural fit for CQRS-style requests and handlers

Costs:
- shared behavior can be duplicated if the team is careless
- conventions must be clear
- cross-cutting concerns need deliberate placement
- domain concepts can become scattered if not protected

Vertical Slice does not mean "everything goes anywhere". It still needs boundaries.

A pragmatic hybrid
------
Many production .NET systems use a hybrid:
- shared domain concepts live in a domain layer
- infrastructure concerns stay behind clear adapters
- feature code is organized in vertical slices
- only real reuse becomes shared abstraction

Example:

```text
src/
  Store.Api/
  Store.Domain/
  Store.Infrastructure/
  Store.Features/
    Orders/
    Products/
    Customers/
```

This keeps the domain stable while letting application workflows stay feature-oriented.

When to choose Clean Architecture
------
Choose Clean Architecture when:
- domain behavior is the center of the system
- business rules are complex and long-lived
- infrastructure changes are expected
- you need strong separation for testing or team boundaries

Examples:
- finance workflows
- policy engines
- pricing systems
- regulated business processes

When to choose Vertical Slice
------
Choose Vertical Slice when:
- the app is endpoint-heavy
- features change independently
- most logic is workflow orchestration
- the team wants fast local navigation

Examples:
- SaaS admin APIs
- internal business apps
- product feature APIs
- modular monoliths

Practical guidance
------
Start with the smallest structure that preserves important boundaries. Add layers when they protect real complexity. Add slices when they reduce feature-change friction.

Avoid these extremes:
- putting every CRUD operation through five projects and eight abstractions
- putting all code in endpoint files with no domain model
- creating interfaces for classes that have one implementation and no test seam
- sharing helpers before duplication proves a pattern

Architecture should make changes easier. If a structure makes every change feel heavier, it is not serving the codebase.

------------------------------------------------------------------------

**Next Article:** Domain Modeling in .NET: Aggregates, Value Objects, and Invariants
