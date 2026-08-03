---
title: 'Native AOT for ASP.NET Core APIs: Trimming, Source Generation, Containers, and Trade-offs'
date: 2026-07-31
permalink: /posts/2026/07/native_aot_aspnetcore_apis/
tags:
  - dotnet
  - dotnet10
  - aspnetcore
  - native-aot
  - performance
  - containers
  - advanced
---

Native Ahead-of-Time compilation publishes a .NET application as a platform-specific native executable. For suitable ASP.NET Core APIs, it can reduce startup time, memory use, and deployment size. Those benefits come with constraints: runtime code generation and unbounded reflection do not fit the model, some ASP.NET Core features are unsupported, and every dependency must be compatible with trimming and AOT analysis.

Start with a workload hypothesis
------
Native AOT is especially valuable for:

- small APIs deployed across many instances
- scale-to-zero or bursty container workloads
- command-line tools and short-lived workers
- environments where fast startup matters
- services where lower memory increases deployment density

It is not automatically faster for every request, and it can increase build time and artifact complexity. Define what improvement matters before changing the deployment model:

```text
Cold start: below 250 ms
Container memory at idle: below 80 MB
Compressed image size: below 100 MB
Publish time: acceptable in CI
```

Measure the same workload with JIT, trimming, ReadyToRun where relevant, and Native AOT.

Create an AOT-ready API
------
The `webapiaot` template provides a small compatible baseline:

```bash
dotnet new webapiaot -n Catalog.AotApi
cd Catalog.AotApi
dotnet run
dotnet publish -c Release -r linux-x64
```

The project enables AOT publishing:

```xml
<PropertyGroup>
  <TargetFramework>net10.0</TargetFramework>
  <PublishAot>true</PublishAot>
  <InvariantGlobalization>true</InvariantGlobalization>
</PropertyGroup>
```

Enable invariant globalization only when the application does not require culture-specific formatting, collation, or parsing. Test real locale behavior before accepting the smaller deployment.

Use the slim application builder
------
AOT-oriented APIs commonly use `CreateSlimBuilder` to register a smaller framework surface.

```csharp
var builder = WebApplication.CreateSlimBuilder(args);

builder.Services.AddProblemDetails();
builder.Services.AddHealthChecks();

var app = builder.Build();

app.UseExceptionHandler();
app.MapHealthChecks("/health");
app.MapGet("/products/{id:int}", GetProductAsync);

app.Run();
```

Start with only the features the service needs. Add packages one at a time and publish frequently so new AOT warnings are associated with a small change.

Generate JSON metadata at build time
------
Reflection-based serializer discovery is not compatible with aggressive trimming. Define the JSON types the application uses:

```csharp
[JsonSerializable(typeof(ProductDto))]
[JsonSerializable(typeof(ProductDto[]))]
[JsonSerializable(typeof(ProblemDetails))]
internal partial class AppJsonSerializerContext : JsonSerializerContext
{
}
```

Register the generated context:

```csharp
builder.Services.ConfigureHttpJsonOptions(options =>
{
    options.SerializerOptions.TypeInfoResolverChain.Insert(
        0,
        AppJsonSerializerContext.Default);
});
```

Integration-test every request and response shape. Missing metadata may appear only on less common error or polymorphic paths.

Understand feature compatibility
------
Minimal APIs, gRPC, JWT authentication, CORS, health checks, output caching, rate limiting, static files, and WebSockets have useful AOT support. MVC controllers, SignalR, session state, and several dynamic authentication or UI patterns remain unsuitable or unsupported.

Compatibility also depends on third-party libraries. Common problem areas include:

- runtime assembly scanning
- dynamic proxy generation
- reflection-based object mapping
- serializers that discover types at runtime
- dependency injection registration by convention
- plug-in systems that load unknown assemblies

Do not suppress warnings until the team understands why the code will remain reachable and correct after trimming.

Treat AOT warnings as correctness warnings
------
Publish for the actual runtime identifier used in production:

```bash
dotnet publish \
  --configuration Release \
  --runtime linux-x64 \
  --self-contained true
```

Review `IL2026`, `IL3050`, and related diagnostics. They identify paths that may require reflection annotations, source generation, a different API, or removal of an incompatible dependency.

A warning-free build is the target, not a guarantee that every business path works. Run the published native binary through integration and smoke tests rather than testing only `dotnet run`, which still uses the development runtime.

Build a minimal container image
------
Native output does not need the ASP.NET Core runtime image.

```dockerfile
FROM mcr.microsoft.com/dotnet/sdk:10.0 AS build
WORKDIR /src
COPY . .
RUN dotnet publish -c Release -r linux-x64 -o /out

FROM mcr.microsoft.com/dotnet/runtime-deps:10.0
WORKDIR /app
COPY --from=build /out .
USER $APP_UID
ENTRYPOINT ["./Catalog.AotApi"]
```

Select a base image compatible with the binary's target runtime and native dependencies. Test DNS, TLS, globalization, time zones, diagnostics, and health probes inside the final image.

Keep observability available
------
A smaller runtime surface should not remove operational visibility. Confirm that the chosen OpenTelemetry exporters, logging providers, metrics, and diagnostic tools support the AOT deployment.

Measure:

- process startup and readiness time
- working set and allocation rate
- image and extracted artifact size
- request throughput and tail latency
- publish duration
- CPU architecture-specific behavior

Use the same configuration and workload for each deployment model comparison.

Plan platform-specific artifacts
------
A native executable targets an operating system and architecture. A service that deploys to Linux x64 and Linux ARM64 needs separate publish outputs and container manifests. CI should build, scan, sign, and test each supported artifact.

Framework-dependent JIT deployments are more portable and receive runtime servicing through the installed runtime or base image. Native AOT artifacts contain the runtime, so rebuilding and redeploying is required for runtime security updates.

Know when not to use Native AOT
------
Prefer a normal ASP.NET Core deployment when:

- the application depends heavily on MVC or SignalR
- dynamic plug-ins are a core requirement
- important libraries produce unresolved AOT warnings
- startup and memory are not material constraints
- platform-specific build complexity outweighs savings

The right deployment model is the simplest one that meets the service objectives.

Common mistakes to avoid
------
Watch for these issues:

- enabling `PublishAot` without testing the published binary
- suppressing trimming warnings broadly
- assuming every ASP.NET Core or NuGet feature is compatible
- forgetting error and polymorphic JSON types in source generation
- benchmarking different configurations or workloads
- shipping one runtime identifier to a different platform
- failing to rebuild after runtime security updates

Native AOT is a production optimization with architectural consequences. Adopt it when measured startup, memory, or deployment gains justify the stricter application model.

------------------------------------------------------------------------

**Next Article:** Aspire for Distributed .NET Apps: AppHost, Service Discovery, Telemetry, and Kubernetes Deployment
