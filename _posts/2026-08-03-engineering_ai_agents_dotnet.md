---
title: 'Engineering AI Agents in .NET: Agent Framework, MCP Tools, Evaluation, and Guardrails'
date: 2026-08-03
permalink: /posts/2026/08/engineering_ai_agents_dotnet/
tags:
  - dotnet
  - dotnet10
  - ai
  - agents
  - mcp
  - agent-framework
  - evaluation
  - security
  - advanced
---

AI agents combine a model with instructions, tools, state, and an execution loop. Microsoft Agent Framework provides agent and workflow abstractions for .NET, while the Model Context Protocol standardizes how an AI host discovers and invokes external tools and data sources. These technologies evolve quickly, so production adoption should pin tested package versions, isolate preview APIs, and place deterministic controls around every side effect.

Choose a function, workflow, or agent
------
Use ordinary code when the application can express the operation directly. Use a workflow when the steps and transitions are known. Use an agent when the task is open-ended and the model needs to decide which information or tool to use.

```text
Calculate invoice tax             -> function
Approve a refund through stages   -> workflow
Investigate an unfamiliar alert   -> agent with restricted tools
```

An agent introduces nondeterminism, latency, cost, and security risk. It should earn that complexity by solving a problem that fixed control flow cannot handle well.

Keep the agent boundary small
------
An agent needs:

- a narrow role and instruction set
- an authenticated caller context
- a limited collection of tools
- bounded turns, time, and token use
- explicit state storage
- cancellation
- telemetry and evaluation

Do not give one general-purpose agent access to every internal system. Split capabilities by trust boundary and business responsibility.

Create an agent through abstractions
------
Agent Framework can build an agent over a configured model client:

```csharp
var agent = chatClient.AsAIAgent(
    name: "OrderSupportAgent",
    instructions: """
        Help support staff investigate order status.
        Use only the provided tools.
        Never change an order or issue a refund.
        Cite the tool result used for each factual claim.
        """);

var response = await agent.RunAsync(
    "Why has order 7c21 not shipped?",
    cancellationToken: cancellationToken);
```

Treat preview framework APIs as an adapter boundary. Keep agent-framework types out of domain models so a package change does not require rewriting the core application.

Use workflows for controlled orchestration
------
When a process has known stages, model them explicitly:

```text
Collect evidence -> classify issue -> request approval -> execute action -> verify result
```

The model may assist inside a stage, but code controls transitions. Persist checkpoints before high-impact actions and support resuming after process failure.

Human approval should carry an immutable summary of the proposed action. Approval of one refund amount must not authorize a later tool call with different arguments.

Expose narrow MCP tools
------
An MCP server can publish application capabilities to compatible hosts. A tool should represent one bounded operation:

```csharp
[McpServerToolType]
public sealed class OrderTools(IAuthorizedOrderQueries orders)
{
    [McpServerTool]
    [Description("Gets shipment status for an order visible to the current caller.")]
    public Task<OrderStatusDto?> GetShipmentStatusAsync(
        [Description("Order identifier")] Guid orderId,
        CancellationToken cancellationToken)
    {
        return orders.GetStatusAsync(orderId, cancellationToken);
    }
}
```

The description helps the model choose the tool. It does not enforce security. Authorization belongs in the server-side implementation.

Choose the MCP transport by deployment model
------
Local tools commonly use standard input/output transport and run as a child process. Remote tools use HTTP and require production network controls.

For remote MCP servers, define:

- authenticated client identity
- OAuth scopes or equivalent permissions
- TLS and network boundaries
- allowed origins and hosts where applicable
- request size and rate limits
- connection and operation timeouts
- audit and retention policy

Do not expose a development stdio command as a remote production service without redesigning its trust model.

Authorize every tool invocation
------
Use identity supplied by the authenticated transport, not a user or tenant identifier invented by the model. Tools should enforce resource-level authorization just like API endpoints.

Separate tools into risk classes:

- read-only lookup
- reversible write
- irreversible or financial action
- administrative operation

Require stronger scopes, confirmation, or human approval as impact increases. Consider excluding the highest-impact operations from agent access entirely.

Make side effects idempotent
------
Agents and transports can retry. Every write tool needs a stable operation identifier and duplicate-detection behavior.

```csharp
public sealed record RefundRequest(
    Guid OperationId,
    Guid OrderId,
    decimal Amount,
    string Reason);
```

Persist the operation result under `OperationId`. A repeated call should return the original result instead of issuing a second refund.

Bound the execution loop
------
Configure limits for:

- total execution time
- model turns
- tool calls
- parallel actions
- tokens and estimated cost
- retrieved context size
- repeated failures

Stop when the task is complete, the caller cancels, a limit is reached, approval is denied, or a tool returns a non-recoverable error. Do not let the model decide whether platform safety limits apply.

Manage state deliberately
------
Separate:

- conversation messages
- durable workflow state
- user or tenant memory
- retrieved knowledge
- tool results and audit records

Each category needs its own retention, encryption, and access policy. Avoid storing the entire prompt history indefinitely. Summaries used for long-running sessions should be treated as model-generated data and validated when they drive decisions.

Evaluate behavior, not eloquence
------
An agent evaluation set should test:

- correct tool selection
- valid tool arguments
- grounded final answers
- refusal of unauthorized work
- resistance to instructions inside retrieved content
- recovery from tool timeout or partial failure
- adherence to approval requirements
- latency and cost limits

Use `Microsoft.Extensions.AI.Evaluation` quality and safety evaluators where they fit, alongside deterministic assertions for permissions and side effects. An LLM-based score must never be the only proof that authorization worked.

Observe the full agent trace
------
Correlate:

- caller and session identifiers
- prompt and agent version
- model requests and token usage
- tool selection and sanitized arguments
- tool latency and result category
- approvals and policy decisions
- final status and evaluation result

Protect sensitive content and credentials. Tool results may contain more sensitive data than the user's initial request.

Plan for framework evolution
------
Agent Framework and newer MCP capabilities can include prerelease packages or changing APIs. For production experiments:

- pin exact package versions
- keep provider and framework code behind adapters
- run contract and evaluation suites before upgrades
- record MCP protocol and tool-schema versions
- deploy to a limited user group
- maintain a deterministic fallback path

Latest does not mean ready for every critical workflow. Stability requirements should determine rollout scope.

Common mistakes to avoid
------
Watch for these issues:

- using an agent where a function or workflow is sufficient
- exposing broad database, shell, or HTTP tools
- trusting model-provided identity or authorization claims
- allowing retried tools to duplicate side effects
- giving approval without binding it to exact arguments
- storing unlimited conversation history
- evaluating answer style while ignoring tool safety
- automatically upgrading rapidly changing packages

Production agent engineering is controlled delegation. The model can choose among allowed actions, but code must own identity, authorization, limits, state, side effects, observability, and recovery.

------------------------------------------------------------------------

**Next Article:** Secure AI Gateways in ASP.NET Core: Identity, Rate Limits, Cost Controls, and Auditability
