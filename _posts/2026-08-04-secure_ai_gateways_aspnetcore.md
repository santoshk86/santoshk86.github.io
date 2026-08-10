---
title: 'Secure AI Gateways in ASP.NET Core: Identity, Rate Limits, Cost Controls, and Auditability'
date: 2026-08-04
permalink: /posts/2026/08/secure_ai_gateways_aspnetcore/
tags:
  - dotnet
  - dotnet10
  - aspnetcore
  - ai
  - security
  - rate-limiting
  - observability
  - advanced
---

An AI gateway gives applications one controlled boundary for model access. It authenticates callers, applies tenant and workload policy, protects provider credentials, records usage, and returns a stable contract even when model providers differ. The gateway is not a substitute for provider safety controls or application authorization. Its job is to make every model request enter through a measurable, enforceable path.

Define the gateway boundary
------
Keep the gateway focused on cross-cutting model concerns:

- caller and tenant identity
- allowed models and capabilities
- request, token, concurrency, and cost limits
- provider selection and credential isolation
- timeout, cancellation, and streaming behavior
- sanitized audit and operational telemetry

Business decisions still belong in the calling application. A gateway may enforce that a tenant can use an embedding model, but it should not decide whether a user may view a particular document. That resource authorization must happen before sensitive context is sent to the gateway.

Choose mediated endpoints over blind proxying
------
A transparent reverse proxy works for simple routing, but AI policies often need semantic information such as requested model, estimated input tokens, streaming mode, and tool availability. An ASP.NET Core endpoint that parses a narrow internal contract can validate those fields before calling a provider.

```csharp
public sealed record ChatGatewayRequest(
    string Capability,
    IReadOnlyList<GatewayMessage> Messages,
    bool Stream = false);

public sealed record GatewayMessage(string Role, string Content);
```

Keep provider-specific request types behind adapters. Otherwise each client can bypass policy by using a different provider option or payload shape.

Establish trusted caller identity
------
Authenticate before applying tenant policy. Derive tenant, subject, workload, and scopes from the validated principal, not from request headers or prompt text supplied by the caller.

```csharp
app.UseAuthentication();
app.UseRateLimiter();
app.UseAuthorization();

app.MapPost("/ai/chat", HandleChatAsync)
    .RequireAuthorization("ai.chat");
```

For service-to-service calls, prefer workload identity or short-lived tokens. The gateway should receive the original caller context needed for policy and audit, but it should never accept a tenant identifier merely because the model or client asserted it.

Partition admission control by identity
------
ASP.NET Core rate limiting can partition capacity by an authenticated tenant or workload. Use a bounded fallback partition for unauthenticated failures so arbitrary keys cannot create unlimited limiter state.

```csharp
builder.Services.AddRateLimiter(options =>
{
    options.GlobalLimiter = PartitionedRateLimiter.Create<HttpContext, string>(
        context =>
        {
            var tenant = context.User.FindFirst("tenant_id")?.Value
                ?? "unauthenticated";

            return RateLimitPartition.GetTokenBucketLimiter(
                tenant,
                _ => new TokenBucketRateLimiterOptions
                {
                    TokenLimit = 60,
                    TokensPerPeriod = 20,
                    ReplenishmentPeriod = TimeSpan.FromMinutes(1),
                    AutoReplenishment = true,
                    QueueLimit = 0
                });
        });
});
```

Request limits are only the first gate. Add a concurrency limit so long streams cannot occupy all connections, and load-test the policy with realistic response times.

Budget tokens and cost explicitly
------
Two requests can have radically different cost. Estimate input size before admission, cap maximum output tokens, and reserve budget against a durable tenant ledger. Reconcile the reservation with provider-reported usage after completion.

```text
authorize capability
  -> estimate and reserve budget
  -> invoke provider
  -> record actual usage
  -> release unused reservation
```

Budget decisions must be atomic enough that concurrent requests cannot all spend the same remaining allowance. Define behavior for exhausted budgets: reject, downgrade to an approved lower-cost model, or require an explicit exception. Never silently change to a model that violates quality or data-boundary requirements.

Keep provider credentials inside the boundary
------
Clients should authenticate to the gateway, not receive model-provider keys. Store provider credentials in a managed secret system or use managed identity where supported. Give each deployed gateway identity only the provider deployments it needs.

Route by an internal capability such as `support-summary` rather than accepting any model name. A capability can map to a tested model, deployment region, timeout, tool set, and data policy. This also makes model changes a controlled configuration release instead of a client code change.

Handle streaming and cancellation deliberately
------
Streaming improves perceived latency but extends the lifetime of gateway resources. Forward caller cancellation to the provider, stop writing when the client disconnects, and distinguish a completed response from a partial stream.

Do not buffer an unlimited response merely to audit it. Record bounded metadata and usage, and capture content only under an explicit privacy policy. Apply idle and total timeouts separately so a stream cannot remain open forever by sending occasional bytes.

Make retries cost-aware
------
Retry only failures that are transient and safe. A retry after the provider accepted a request may create duplicate cost or repeated tool execution. Keep a total time budget across all attempts and honor provider retry guidance.

Model failover is not a neutral retry. Different models can change structured-output support, safety behavior, context limits, and answer quality. Test fallback routes with the same evaluation suite used for the primary route.

Create an auditable decision record
------
An audit event should explain the policy decision without storing secrets or unnecessary prompt content.

```csharp
public sealed record AiGatewayAudit(
    string RequestId,
    string TenantId,
    string SubjectId,
    string Capability,
    string ProviderRoute,
    string Decision,
    int? InputTokens,
    int? OutputTokens,
    decimal? EstimatedCost);
```

Record denials, policy version, approvals, provider route, completion state, and sanitized error category. Protect audit storage from modification and apply a documented retention period.

Observe policy and provider behavior
------
Correlate gateway spans with the calling application and provider request. Measure queue time, time to first token, total duration, cancellations, rate-limit rejections, token usage, cost, provider errors, and fallback frequency. Avoid high-cardinality dimensions such as raw prompts or arbitrary user text.

Alert on user-impacting symptoms and budget anomalies. A sudden fall in average output tokens may indicate truncated responses just as a latency increase may indicate provider pressure.

Common mistakes to avoid
------
Watch for these issues:

- trusting tenant or user identity from the request body
- limiting request count while ignoring tokens, concurrency, and cost
- accepting arbitrary model names or unrestricted provider parameters
- retrying streamed or tool-enabled calls without understanding side effects
- logging raw prompts, credentials, or tool arguments by default
- treating model fallback as equivalent behavior
- using an in-memory budget counter across multiple replicas

A secure AI gateway turns model access into an explicit platform contract. Identity, admission control, budgets, routing, telemetry, and audit remain deterministic even when the model response is not.

------------------------------------------------------------------------

**Next Article:** Production AI Data Ingestion in .NET: Documents, Chunking, Enrichment, Embeddings, and Reindexing
