---
title: 'Multi-Tenancy Patterns in ASP.NET Core'
date: 2026-04-01
permalink: /posts/2026/04/multitenancy_patterns_aspnetcore/
tags:
  - dotnet
  - aspnetcore
  - multi-tenancy
  - architecture
  - advanced
---

This post covers common multi-tenancy patterns in ASP.NET Core. Multi-tenancy means one application serves multiple customers, organizations, or logical tenants while keeping their data and configuration separated. The hard parts are **tenant identification, data isolation, configuration, security, and operations**.

Tenant identification
------
The app needs a reliable way to determine the current tenant.

Common strategies:
- subdomain: `acme.example.com`
- route: `/tenants/acme/orders`
- header: `X-Tenant-Id`
- token claim: `tenant_id`

Example middleware concept:

```csharp
public sealed class TenantMiddleware(RequestDelegate next)
{
    public async Task InvokeAsync(HttpContext context, ITenantResolver resolver)
    {
        var tenant = await resolver.ResolveAsync(context);

        if (tenant is null)
        {
            context.Response.StatusCode = StatusCodes.Status400BadRequest;
            await context.Response.WriteAsync("Tenant is required.");
            return;
        }

        context.Items["Tenant"] = tenant;
        await next(context);
    }
}
```

Tenant resolution must happen early enough that downstream services can use it.

Data isolation patterns
------
Common storage models:
- shared database, shared schema, tenant column
- shared database, separate schema per tenant
- separate database per tenant

Shared database with tenant column:
- simplest operationally
- requires strict filters
- works well for many small tenants

Separate database per tenant:
- strongest isolation
- easier tenant-level backup and restore
- more operational complexity

There is no universal best option. The right model depends on tenant count, isolation needs, compliance, and operational maturity.

Tenant-aware EF Core queries
------
For shared-schema models, every tenant-owned row needs a tenant key.

```csharp
public interface ITenantEntity
{
    string TenantId { get; set; }
}
```

Global query filters can help:

```csharp
modelBuilder.Entity<Order>()
    .HasQueryFilter(o => o.TenantId == _tenantContext.TenantId);
```

This reduces accidental cross-tenant reads, but it is not a substitute for careful testing and authorization.

Tenant-specific configuration
------
Tenants may have different settings:
- feature flags
- branding
- connection strings
- limits and quotas
- integration credentials

Model it explicitly:

```csharp
public sealed record TenantSettings(
    string TenantId,
    bool EnableAdvancedReports,
    int MaxUsers);
```

Cache tenant settings carefully and invalidate them when changed.

Security concerns
------
Multi-tenancy raises the cost of mistakes. A cross-tenant data leak is a serious incident.

Controls:
- authorize tenant membership from server-side identity
- do not trust tenant IDs supplied by the client alone
- add automated tests for tenant isolation
- log tenant context in security events
- avoid global admin shortcuts without auditing

Common mistakes to avoid
------
Watch for these issues:
- forgetting tenant filters in one query
- trusting headers from public clients without validation
- mixing tenant configuration with user preferences
- making tenant resolution inconsistent across APIs and workers
- ignoring background jobs that process tenant data

Multi-tenancy must be a first-class architectural concern. Add tenant context, isolation, testing, and observability early, because retrofitting them later is expensive.

------------------------------------------------------------------------

**Next Article:** Real-Time Systems in .NET: SignalR Architecture and Scaling
