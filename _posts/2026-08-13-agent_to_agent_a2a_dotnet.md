---
title: 'Agent-to-Agent Systems in .NET: A2A Protocol, Remote Agents, Identity, and Trust Boundaries'
date: 2026-08-13
permalink: /posts/2026/08/agent_to_agent_a2a_dotnet/
tags:
  - dotnet
  - dotnet10
  - ai
  - agents
  - agent-framework
  - a2a
  - distributed-systems
  - security
  - advanced
---

Agent-to-Agent (A2A) provides a standard way for agents built with different frameworks or languages to discover capabilities, exchange messages, and represent long-running work as tasks. Microsoft Agent Framework can expose and consume A2A agents from .NET. The protocol creates interoperability, not trust: production systems must authenticate peers, authorize every task and context, protect durable state, and handle remote agents like distributed services.

Choose the simplest composition boundary
------
Not every pair of agents needs a network protocol.

```text
same process, known agent     -> agent as a tool
standard tool or data access  -> MCP
remote autonomous capability  -> A2A
fixed ordered process         -> workflow
```

In-process composition has lower latency and simpler failure handling. Use A2A when an independent deployment, ownership boundary, technology stack, or long-running task justifies remote communication.

Understand what A2A standardizes
------
A2A supports:

- discovery through agent cards
- messages and supported content modes
- task creation and status transitions
- streaming and asynchronous updates
- artifacts produced by completed work
- context and continuation across interactions

It does not standardize the remote agent's internal reasoning, domain authorization, data retention, quality, or operational guarantees. Those remain service contracts between owners.

Treat agent cards as advertised metadata
------
An agent card describes name, description, endpoint, protocol bindings, capabilities, input and output modes, and version. It helps clients decide whether an agent may fit a task.

Discovery metadata is not proof of identity or permission. Retrieve cards from configured trusted endpoints or a governed registry, validate transport security, and maintain an allowlist for production peers. Do not let a model discover and call arbitrary internet agents.

Host a .NET agent through ASP.NET Core
------
Agent Framework hosting can register an `AIAgent` and expose A2A endpoints.

```csharp
var hostedAgent = builder.AddAIAgent(
    "inventory-agent",
    instructions: "Answer inventory questions using authorized tools only.",
    description: "Queries inventory visible to the authenticated caller.");

builder.Services.AddA2AServer();

var app = builder.Build();

app.UseAuthentication();
app.UseAuthorization();
app.MapA2AServer();
app.Run();
```

Hosting packages and endpoint APIs can be prerelease. Pin versions, follow migration guidance, and keep protocol mapping separate from the agent's application services.

Authenticate before task handling
------
Use workload identity, OAuth access tokens, mutual TLS, or another approved service identity appropriate to the environment. Validate audience and issuer for this agent service.

The remote agent needs enough delegated caller context to authorize work, but it should not receive broad credentials from the host agent. Prefer token exchange or narrowly scoped downstream identity over forwarding one powerful bearer token through several agents.

Authorize every remote identifier
------
A2A context IDs, task IDs, continuation tokens, artifact IDs, and cancellation requests are untrusted inputs. Before loading or changing state:

1. authenticate the peer and represented caller
2. derive tenant and subject from trusted identity
3. load state from the correct partition
4. verify ownership and allowed transition
5. audit the decision

An unpredictable task ID is not an authorization mechanism.

Partition conversation and task state
------
Map remote context to an application-owned session key that includes trusted tenant and subject identity. Persist state durably when replicas can restart or scale out.

```csharp
public sealed record RemoteSessionKey(
    string TenantId,
    string SubjectId,
    string PeerAgentId,
    string ContextId);
```

Set retention, encryption, concurrency, and deletion policy. Do not assume an in-memory default task store is suitable for multi-tenant production hosting.

Model long-running work as tasks
------
Remote work may return immediately, stream updates, or continue as an asynchronous task. Define legal task states and terminal outcomes such as completed, failed, cancelled, rejected, and expired.

Clients should resume with protocol continuation data rather than resubmitting the original request blindly. Servers should make task creation and finalization idempotent so uncertain network failures do not create duplicate work.

Control artifact boundaries
------
Artifacts may contain reports, files, structured data, or references to data stored elsewhere. Enforce media type, size, malware scanning, classification, and caller access.

Prefer authorized references for large or sensitive artifacts instead of embedding them in protocol messages. Re-check access when the artifact is downloaded because task completion and retrieval may occur at different times.

Version capabilities, not only endpoints
------
An agent's description, tools, model, policies, and output behavior can change even when its URL does not. Record card and capability versions with each task.

Use additive changes when possible. When meaning or required fields change, publish a new capability version and keep compatibility for active tasks. Reject unsupported combinations explicitly rather than allowing the model to improvise a conversion.

Apply distributed-systems resilience
------
Every remote call needs a total timeout, cancellation, bounded retry policy, and correlation. Retry only safe protocol operations. Task creation should accept an idempotency key when duplicate creation would be harmful.

Use circuit breakers to stop repeated calls to an unhealthy peer. Define whether a fallback agent provides genuinely equivalent authorization, data location, quality, and output contracts before routing work to it.

Keep delegation bounded
------
The host agent should call only approved remote capabilities with explicit budgets for hops, time, tokens, cost, and parallel tasks. Prevent unbounded delegation chains where agents repeatedly call one another.

Carry a correlation and delegation policy across hops, but do not expose hidden prompts, secrets, or internal reasoning. Each service should receive the minimum context required for its capability.

Observe and evaluate the remote boundary
------
Trace peer identity, card and capability version, task transitions, network attempts, streaming updates, artifact metadata, token usage where available, cost, and final result. Protect message content through redaction and access control.

Evaluation scenarios should test discovery mismatch, unauthorized task access, peer timeout, duplicate creation, cancellation, restart and resume, invalid artifacts, version incompatibility, and misleading remote results.

Common mistakes to avoid
------
Watch for these issues:

- using A2A for agents that can compose safely in one process
- trusting an agent card as identity or authorization
- allowing the model to call arbitrary discovered endpoints
- treating context, task, or continuation IDs as bearer credentials
- using in-memory task state across production replicas
- retrying task creation without idempotency
- forwarding broad caller credentials through several agents
- assuming a fallback agent has equivalent policy and quality
- permitting unlimited delegation depth or cost

A2A makes agent communication interoperable across service and technology boundaries. Production safety comes from the same disciplines as other distributed systems: authenticated peers, least privilege, durable owned state, idempotency, versioned contracts, bounded execution, and observable recovery.

------------------------------------------------------------------------

**Series Complete:** These ten articles extend the production-ready .NET roadmap from controlled AI access through data, contracts, evaluation, durable execution, interoperability, observability, and safe release.
