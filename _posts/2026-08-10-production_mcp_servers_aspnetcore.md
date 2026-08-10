---
title: 'Production MCP Servers with ASP.NET Core: HTTP Transport, OAuth, Authorization, and Tool Auditing'
date: 2026-08-10
permalink: /posts/2026/08/production_mcp_servers_aspnetcore/
tags:
  - dotnet
  - dotnet10
  - aspnetcore
  - ai
  - mcp
  - oauth
  - authorization
  - security
  - advanced
---

The Model Context Protocol lets an AI host discover and invoke tools, read resources, and use prompts through a standard protocol. A production MCP server is still an application security boundary. ASP.NET Core must authenticate the transport, the server must authorize every capability and resource, and business services must validate each operation independently of what the model requested.

Choose MCP for interoperability
------
Use MCP when several compatible AI hosts need a standard way to discover application capabilities. An ordinary internal API may be simpler when one known application calls one known service.

MCP does not replace:

- domain service contracts
- authentication and authorization
- API versioning and operational policy
- idempotency for write operations
- Agent-to-Agent communication for remote agent tasks

Keep the protocol adapter thin so the same application services remain usable through APIs, jobs, or tests.

Separate tools, resources, and prompts
------
Publish each MCP primitive for its intended responsibility:

- **Tools** perform bounded queries or actions.
- **Resources** expose readable content identified by a URI.
- **Prompts** provide reusable prompt templates and arguments.

Do not turn every database table into a resource or every controller into a tool. Publish a small capability surface designed for model selection, least privilege, and human review.

Host HTTP transport in ASP.NET Core
------
The C# MCP SDK integrates with dependency injection and ASP.NET Core HTTP transport.

```csharp
builder.Services
    .AddAuthentication()
    .AddJwtBearer();

builder.Services.AddAuthorization();

builder.Services
    .AddMcpServer()
    .WithHttpTransport(options => options.Stateless = true)
    .AddAuthorizationFilters()
    .WithTools<OrderTools>();

var app = builder.Build();

app.UseAuthentication();
app.UseAuthorization();
app.MapMcp("/mcp");
```

Review package status and pin tested versions. Keep transport and SDK setup in the host project rather than allowing protocol types into domain services.

Use OAuth resource metadata correctly
------
A remote MCP server is an OAuth-protected resource, not an authorization server. Publish protected-resource metadata that identifies accepted authorization servers and resource indicators. Validate issuer, audience, signature, lifetime, and required token properties through standard ASP.NET Core authentication.

Clients obtain tokens from the trusted authorization server. Do not invent a custom login flow inside an MCP tool response, accept tokens in tool arguments, or forward a provider credential supplied by the model.

Propagate trusted caller identity
------
With authenticated ASP.NET Core HTTP transport, the SDK can propagate the caller principal through MCP request processing. Authorization filters make standard `[Authorize]` and `[AllowAnonymous]` attributes effective for tools, resources, and prompts.

```csharp
[McpServerToolType]
public sealed class OrderTools(IAuthorizedOrderQueries orders)
{
    [McpServerTool]
    [Authorize(Policy = "orders.read")]
    [Description("Gets shipment status for an order visible to the caller.")]
    public Task<OrderStatusDto?> GetShipmentStatusAsync(
        Guid orderId,
        CancellationToken cancellationToken) =>
        orders.GetVisibleStatusAsync(orderId, cancellationToken);
}
```

The authorization attribute controls access to the tool. The query service must still enforce resource-level access to `orderId` using trusted caller context.

Design scopes around capabilities
------
Avoid one broad `mcp.access` scope. Use scopes and policies such as:

- `orders.read`
- `refunds.draft`
- `refunds.approve`
- `knowledge.search`

Separate read, reversible write, financial, and administrative operations. Require stronger identity, approval, or network policy as impact increases. Consider excluding the highest-risk operations entirely.

Do not trust model-provided ownership
------
Tool arguments are untrusted, even when they look like identity fields. Ignore a model-provided tenant, user, role, or approval claim when determining access.

Derive ownership from the authenticated principal and server-side records. If a tool accepts an organization ID because it is part of the business key, verify that the caller may access that organization before using it in a query.

Choose stateless or stateful transport deliberately
------
Stateless HTTP handling simplifies horizontal scaling when each request contains everything required by the protocol and application. Stateful sessions may be useful for negotiated capabilities or server-managed state but require durable, authorized session storage and connection recovery.

Never store authorization decisions only in a process-local session. Re-evaluate access for sensitive resources and actions because roles, memberships, and object state can change.

Make tools bounded and idempotent
------
Read tools need limits for result count, fields, query complexity, and execution time. Write tools need a stable operation ID and duplicate-detection behavior.

```csharp
public sealed record CreateRefundDraftRequest(
    Guid OperationId,
    Guid OrderId,
    decimal Amount,
    string Reason);
```

Return structured, minimal results. Do not return stack traces, credentials, internal connection details, or an unlimited object graph. Validate cancellation and ensure a client disconnect does not leave an uncertain write without a recoverable operation record.

Treat output as another trust boundary
------
Tool and resource output can contain sensitive data or instructions that manipulate the calling model. Apply field-level filtering, size limits, content classification, and redaction where appropriate.

Describe output provenance so the host can distinguish authoritative application data from generated summaries. A tool description helps selection; it does not make returned content safe to follow as instructions.

Apply admission and network controls
------
Protect the endpoint with TLS, allowed hosts, request-size limits, timeouts, concurrency limits, and rate policies partitioned by authenticated client or tenant. Use a gateway or private network where the deployment requires it.

Do not create limiter partitions from arbitrary tool arguments. Load-test long-running tools and streaming behavior so one client cannot exhaust all server connections.

Audit capability decisions
------
Record request ID, authenticated subject and tenant, client identity, protocol version, capability name, sanitized arguments, policy decision, operation ID, latency, result category, and approval reference.

Keep prompts and full tool results out of audit records by default. Use hashes, stable identifiers, or redacted summaries when they are enough to investigate behavior.

Test the protocol and the business boundary
------
Contract tests should verify discovery, schemas, authentication challenges, scopes, authorization filters, cancellation, error mapping, and supported protocol versions. Business tests should verify object-level authorization, idempotency, validation, and audit events without requiring a model.

Add adversarial cases: cross-tenant identifiers, invented approval IDs, oversized arguments, repeated operation IDs, malicious resource content, expired tokens, and concurrent session continuation.

Common mistakes to avoid
------
Watch for these issues:

- exposing MCP when a small private API would be simpler
- adding `[Authorize]` without enabling authorization filters
- using one broad scope for every capability
- trusting tenant, role, or approval values from tool arguments
- exposing generic database, shell, filesystem, or HTTP tools
- storing sessions without authenticated ownership
- returning unlimited or sensitive tool results
- testing only through a model instead of testing the server contract directly

A production MCP server is a least-privilege protocol adapter. ASP.NET Core establishes identity, MCP filters enforce capability policy, and application services remain responsible for resource authorization and safe side effects.

------------------------------------------------------------------------

**Next Article:** Observability for .NET AI and Agents: OpenTelemetry, Token Cost, Tool Traces, and Privacy
