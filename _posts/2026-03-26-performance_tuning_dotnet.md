---
title: 'Performance Tuning in .NET: Kestrel, GC, Allocations, and BenchmarkDotNet'
date: 2026-03-26
permalink: /posts/2026/03/performance_tuning_dotnet/
tags:
  - dotnet
  - performance
  - kestrel
  - benchmarkdotnet
  - advanced
---

This post covers practical performance tuning in .NET: **Kestrel configuration, garbage collection, allocation reduction, and benchmarking with BenchmarkDotNet**. Performance work should start with measurement. Guessing usually leads to busy code that is not actually faster.

Start with measurement
------
Before changing code, answer:
- which endpoint is slow
- what latency percentile matters
- whether CPU, memory, I/O, or locking is the bottleneck
- whether the database or a downstream service dominates time

Useful tools:
- application metrics
- OpenTelemetry traces
- `dotnet-counters`
- `dotnet-trace`
- load testing tools
- BenchmarkDotNet for isolated code paths

Do not optimize a method because it looks inefficient. Optimize because evidence shows it matters.

Kestrel basics
------
Kestrel is the cross-platform web server used by ASP.NET Core.

Example configuration:

```csharp
builder.WebHost.ConfigureKestrel(options =>
{
    options.Limits.MaxRequestBodySize = 10 * 1024 * 1024;
    options.Limits.KeepAliveTimeout = TimeSpan.FromMinutes(2);
    options.Limits.RequestHeadersTimeout = TimeSpan.FromSeconds(30);
});
```

Tune Kestrel when:
- request sizes need strict limits
- slow clients are tying up resources
- reverse proxy behavior requires alignment
- you need explicit endpoint configuration

Many apps should keep default Kestrel settings until measurements justify changes.

Garbage collection
------
.NET has a highly optimized garbage collector, but allocation-heavy code still creates pressure.

Signs of allocation problems:
- high Gen 0/Gen 1 collection rate
- large object heap growth
- memory spikes during load
- CPU spent in GC

Use `dotnet-counters`:

```bash
dotnet-counters monitor --process-id 12345 System.Runtime
```

Watch counters such as:
- GC heap size
- allocation rate
- Gen 0/1/2 collection counts
- thread pool queue length

Reducing allocations
------
Allocation reduction is most useful in hot paths.

Common improvements:
- avoid repeated string concatenation in loops
- use streaming instead of buffering large payloads
- project only needed data from EF Core
- avoid unnecessary LINQ in extremely hot loops
- reuse expensive objects where safe

Example:

```csharp
var builder = new StringBuilder();

foreach (var item in items)
{
    builder.Append(item.Code);
    builder.Append(',');
}

var result = builder.ToString();
```

Do not make code unreadable to avoid tiny allocations that do not matter. Keep optimization proportional to the measured cost.

BenchmarkDotNet
------
BenchmarkDotNet is the standard .NET library for microbenchmarks.

Install:

```bash
dotnet add package BenchmarkDotNet
```

Benchmark:

```csharp
[MemoryDiagnoser]
public class SlugBenchmarks
{
    private readonly string _title = "Performance Tuning in .NET";

    [Benchmark]
    public string ReplaceSpaces()
    {
        return _title.ToLowerInvariant().Replace(" ", "-");
    }
}
```

Run:

```csharp
BenchmarkRunner.Run<SlugBenchmarks>();
```

Use BenchmarkDotNet for isolated algorithms and utility code. It does not replace end-to-end load tests.

Performance checklist for APIs
------
A practical API tuning checklist:
- use pagination for lists
- avoid over-fetching data
- use `AsNoTracking` for read-only EF Core queries
- set downstream timeouts
- compress responses where appropriate
- cache expensive read models carefully
- measure p95 and p99 latency, not just averages

Common mistakes to avoid
------
Watch for these issues:
- optimizing without production-like data
- using microbenchmarks to make claims about whole-system performance
- ignoring database indexes
- returning unbounded result sets
- treating GC as the problem before checking allocation behavior

Performance tuning is disciplined measurement followed by focused changes. The best optimization is often changing what work the app does, not making unnecessary work slightly faster.

------------------------------------------------------------------------

**Next Article:** Security Deep Dive for .NET APIs: OWASP, Rate Limiting, Headers, and CORS
