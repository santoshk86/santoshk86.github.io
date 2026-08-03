---
title: 'Upgrading from .NET 8 to .NET 10 LTS: C# 14, Breaking Changes, and a Safe Migration Plan'
date: 2026-07-26
permalink: /posts/2026/07/upgrading_dotnet8_to_dotnet10_lts/
tags:
  - dotnet
  - dotnet10
  - csharp14
  - migration
  - lts
  - advanced
---

.NET 10 is the current Long Term Support release, while .NET 8 reaches the end of support in November 2026. An upgrade should be treated as an engineering change, not a search-and-replace operation. The safest approach separates framework migration, package updates, language adoption, and production rollout so that each source of risk can be verified independently.

Start with an inventory
------
Before changing target frameworks, capture what the solution depends on:

- installed SDKs and `global.json`
- target frameworks in every project
- direct and transitive NuGet packages
- workloads and .NET tools
- runtime and SDK container images
- CI/CD setup actions and build agents
- hosting-platform runtime settings
- analyzers, source generators, and test adapters

Useful commands include:

```bash
dotnet --info
dotnet --list-sdks
dotnet workload list
dotnet list package --outdated
dotnet list package --vulnerable --include-transitive
```

Commit or archive a successful .NET 8 build report before the migration. It gives the team a known baseline for test counts, warnings, artifact size, startup time, and critical performance measurements.

Pin the .NET 10 SDK
------
Update `global.json` so developer machines and CI select the same SDK feature band.

```json
{
  "sdk": {
    "version": "10.0.100",
    "rollForward": "latestFeature",
    "allowPrerelease": false
  }
}
```

The exact version should be the supported patch approved by the team, not necessarily `10.0.100`. Keep the file in source control and update it through a normal dependency-maintenance process.

Update target frameworks deliberately
------
Change application projects to `net10.0` first.

```xml
<PropertyGroup>
  <TargetFramework>net10.0</TargetFramework>
  <Nullable>enable</Nullable>
  <ImplicitUsings>enable</ImplicitUsings>
</PropertyGroup>
```

Libraries may temporarily multi-target when downstream consumers cannot move at the same time:

```xml
<TargetFrameworks>net8.0;net10.0</TargetFrameworks>
```

Do not multi-target every project automatically. It increases build time and test combinations. Use it only where a real compatibility boundary exists.

Separate framework and package changes
------
First make the solution compile on .NET 10 with the smallest reasonable package changes. Then upgrade packages in focused groups:

1. Microsoft framework-aligned packages
2. data-access providers and EF Core
3. authentication and security packages
4. observability and resilience packages
5. test frameworks, adapters, and analyzers

Review release notes and transitive dependency changes. A package that restores successfully can still change serialization, database translation, authentication defaults, trimming behavior, or generated code.

Review breaking changes and warnings
------
Build the entire solution and treat new warnings as migration work rather than hiding them globally.

```bash
dotnet clean
dotnet restore --locked-mode
dotnet build --configuration Release --warnaserror
dotnet test --configuration Release --no-build
```

Pay special attention to:

- ASP.NET Core authentication and authorization behavior
- JSON serialization and model binding
- EF Core query translation and migrations
- obsolete APIs and analyzer diagnostics
- culture, time zone, and globalization behavior
- Native AOT or trimming warnings
- test runner and code-coverage output

If the existing solution has warning debt, enable warnings-as-errors only for new or migration-relevant diagnostics instead of turning the upgrade into an unrelated cleanup project.

Adopt C# 14 after the runtime upgrade
------
C# 14 is available with the .NET 10 SDK. Its features can simplify code, but language changes should follow a successful framework migration.

Null-conditional assignment can reduce repetitive guards:

```csharp
order?.ProcessedAt = timeProvider.GetUtcNow();
```

The `field` keyword can enforce property rules without declaring a separate backing field:

```csharp
public string Name
{
    get;
    set => field = string.IsNullOrWhiteSpace(value)
        ? throw new ArgumentException("Name is required.")
        : value;
}
```

Extension blocks support extension properties and grouped extension members:

```csharp
public static class OrderExtensions
{
    extension(Order order)
    {
        public bool IsClosed => order.Status is OrderStatus.Completed or OrderStatus.Cancelled;
    }
}
```

Adopt these features through team conventions and analyzer rules. Avoid mixing a broad syntax rewrite with behavioral migration changes.

Update containers and delivery pipelines
------
Move both build and runtime images to .NET 10.

```dockerfile
FROM mcr.microsoft.com/dotnet/sdk:10.0 AS build
WORKDIR /src
COPY . .
RUN dotnet publish -c Release -o /app

FROM mcr.microsoft.com/dotnet/aspnet:10.0
WORKDIR /app
COPY --from=build /app .
ENTRYPOINT ["dotnet", "Orders.Api.dll"]
```

Update CI SDK setup, caching keys, artifact names, hosting configuration, and deployment health checks. Rebuild the image rather than changing only the hosting runtime beneath an old artifact.

Test the behavior that matters
------
In addition to the ordinary test suite, compare .NET 8 and .NET 10 for:

- API contracts and status codes
- authentication challenges and token validation
- representative EF Core queries
- message serialization and consumer compatibility
- background-worker shutdown
- latency, allocations, and container memory
- startup and readiness timing

Contract tests and recorded production-like payloads are especially valuable because they catch changes that unit tests may miss.

Roll out in stages
------
Deploy the .NET 10 build to a production-like environment, run smoke and load tests, and then release gradually. Watch error rate, latency, dependency calls, GC behavior, memory, and business metrics. Keep the previous artifact and database-compatible rollback path available until the new version has completed its observation window.

Do not combine the runtime upgrade with a database redesign or hosting-platform migration unless there is no alternative. Small, observable changes are easier to diagnose and reverse.

Common mistakes to avoid
------
Watch for these issues:

- updating the target framework without updating CI and container images
- upgrading every package and rewriting code in one change
- ignoring new compiler, analyzer, or trimming warnings
- enabling C# 14 syntax before the team and build agents use the same SDK
- validating only compilation instead of runtime contracts
- deploying without a tested rollback path

A successful upgrade is boring: the application behaves the same, the team understands every intentional change, and the production rollout can be reversed safely.

------------------------------------------------------------------------

**Next Article:** Modern ASP.NET Core 10 APIs: OpenAPI 3.1, Validation, ProblemDetails, and Server-Sent Events
