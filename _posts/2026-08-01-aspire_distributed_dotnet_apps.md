---
title: 'Aspire for Distributed .NET Apps: AppHost, Service Discovery, Telemetry, and Kubernetes Deployment'
date: 2026-08-01
permalink: /posts/2026/08/aspire_distributed_dotnet_apps/
tags:
  - dotnet
  - dotnet10
  - aspire
  - cloud-native
  - observability
  - kubernetes
  - advanced
---

Aspire is a code-first orchestration and observability layer for distributed applications. It lets a team describe APIs, workers, databases, caches, queues, containers, and their relationships in one AppHost. During development, the same model starts the system, supplies connection information, and exposes logs and traces through a dashboard. The application services remain ordinary .NET projects and can still be deployed through established platform pipelines.

Know what Aspire owns
------
Aspire helps model and operate the application topology. It is not:

- a replacement for ASP.NET Core
- a production runtime inside every service
- a cloud provider
- a requirement to rewrite existing projects
- a reason to hide infrastructure decisions

The AppHost is executable architecture documentation. It describes what runs, what depends on what, and which connection information crosses each boundary.

Create an AppHost
------
Add Aspire to an existing solution and model the main resources:

```csharp
var builder = DistributedApplication.CreateBuilder(args);

var cache = builder.AddRedis("cache");

var postgres = builder.AddPostgres("postgres");
var ordersDatabase = postgres.AddDatabase("orders");

var ordersApi = builder
    .AddProject<Projects.Orders_Api>("orders-api")
    .WithReference(cache)
    .WithReference(ordersDatabase)
    .WaitFor(cache)
    .WaitFor(ordersDatabase);

builder
    .AddProject<Projects.Orders_Worker>("orders-worker")
    .WithReference(ordersDatabase)
    .WaitFor(ordersDatabase);

builder.Build().Run();
```

Resource names become stable identifiers in configuration and telemetry. Choose names that describe business or platform responsibilities rather than local machine details.

Use references for dependency wiring
------
`WithReference` declares that one resource consumes another. Aspire supplies connection details through configuration rather than hard-coded ports.

In the consuming service, use ordinary configuration and client registrations:

```csharp
var builder = WebApplication.CreateBuilder(args);

builder.AddServiceDefaults();
builder.AddRedisDistributedCache("cache");
builder.AddNpgsqlDbContext<OrdersDbContext>("orders");

var app = builder.Build();

app.MapDefaultEndpoints();
app.MapOrderEndpoints();
app.Run();
```

This keeps the service independent from local container coordinates. In another environment, the same configuration keys can point to managed services.

Use WaitFor for startup ordering, not resilience
------
`WaitFor` can delay a dependent resource until a dependency is ready during orchestration. It improves the developer startup experience but does not replace runtime resilience.

Production services still need:

- bounded connection timeouts
- retry behavior for transient startup failures
- health checks
- graceful degradation
- reconnect logic
- observable dependency failures

Dependencies can fail after startup, and production schedulers may start resources in a different order.

Standardize service defaults
------
A shared ServiceDefaults project can register cross-cutting operational behavior:

- OpenTelemetry logging, metrics, and tracing
- service discovery
- resilient HTTP defaults
- liveness and readiness endpoints

Keep defaults conservative and overrideable. A shared extension should not silently give every service the same timeout, sampling rate, or health definition when their workloads differ.

Use the dashboard as a development tool
------
The Aspire dashboard presents:

- resource state and endpoints
- structured console logs
- distributed traces
- metrics
- environment and configuration information
- commands exposed by resources

Use it to follow one request from an API through a database, cache, or worker. Keep sensitive values out of logs and resource metadata. The dashboard makes development state convenient; it should not weaken secrets management.

Model containers and external services
------
An AppHost can combine .NET projects with existing containers and services:

```csharp
var broker = builder
    .AddContainer("rabbitmq", "rabbitmq", "management")
    .WithHttpEndpoint(targetPort: 15672, name: "management")
    .WithEndpoint(targetPort: 5672, name: "amqp");
```

Prefer maintained Aspire integrations when they express the resource correctly. Use generic containers when the system needs a tool without an integration or when validating a custom image.

Persist development data intentionally
------
By default, a development resource may be disposable. Add a volume only when developers need state across runs. Be clear about how to reset that state when schema or test data changes.

Do not treat a local volume as a backup. Development data should be reproducible through migrations, seeds, or fixtures.

Test the distributed system
------
Aspire's application model can support integration tests that start real dependencies. Focus tests on boundaries that in-memory substitutes cannot prove:

- database migrations and query behavior
- cache serialization
- message publication and consumption
- service discovery and HTTP wiring
- telemetry correlation
- startup and shutdown behavior

Keep the number of full-topology tests deliberate. Pure domain rules should remain fast unit tests.

Publish and deploy deliberately
------
Aspire can publish application topology and supports deployment workflows, including container and Kubernetes-oriented paths. Treat generated deployment assets as reviewable infrastructure.

Before production:

- map local resources to approved managed or self-hosted services
- define identities and least-privilege access
- configure secrets outside source control
- set resource requests, limits, and scaling rules
- distinguish liveness from readiness
- plan database migration execution
- integrate deployment with existing approvals and rollback

`aspire deploy` can streamline a workflow, but the team remains responsible for the resulting infrastructure, access boundaries, cost, and recovery model.

Avoid configuration drift
------
The AppHost, deployment configuration, and service code should agree on resource names and dependencies. Validate the topology in CI and update it in the same change that adds a dependency.

If production is intentionally different from local development, document the mapping. For example, local Redis may map to Azure Managed Redis, and a local PostgreSQL container may map to a managed PostgreSQL service.

Common mistakes to avoid
------
Watch for these issues:

- treating Aspire as a replacement for production resilience
- hard-coding local ports inside application services
- putting secrets in AppHost source code
- sharing one oversized ServiceDefaults policy across unlike workloads
- making every test start the full topology
- deploying generated infrastructure without review
- assuming local containers exactly match managed production services

Aspire is most valuable when it makes a real distributed system easier to understand and reproduce. Keep the AppHost explicit, the services independently testable, and production decisions visible.

------------------------------------------------------------------------

**Next Article:** Building AI Features in .NET: Microsoft.Extensions.AI, Chat, Embeddings, RAG, and Telemetry
