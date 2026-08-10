---
title: 'Observability for .NET AI and Agents: OpenTelemetry, Token Cost, Tool Traces, and Privacy'
date: 2026-08-11
permalink: /posts/2026/08/observability_ai_agents_opentelemetry_dotnet/
tags:
  - dotnet
  - dotnet10
  - ai
  - agents
  - opentelemetry
  - observability
  - privacy
  - cost
  - advanced
---

AI observability must explain more than whether an HTTP request returned `200`. Teams need to see model latency, time to first token, token usage, retrieval evidence, tool execution, workflow transitions, evaluation results, and cost while protecting the content that produced them. `Microsoft.Extensions.AI` and Agent Framework can emit OpenTelemetry data, but applications still own correlation, privacy policy, service objectives, and operational response.

Start with decisions the team must make
------
Telemetry should answer questions such as:

- Is the feature available and fast enough for users?
- Which model, prompt, retrieval, or tool version caused a change?
- Are responses becoming more expensive?
- Where did an agent spend its time?
- Did a tool fail, time out, or receive denial?
- Are evaluation scores or user corrections drifting?

Collecting raw prompts without these questions creates risk, not observability.

Preserve one distributed trace
------
Continue the incoming ASP.NET Core trace through gateway admission, retrieval, model calls, tools, queues, and downstream services. Propagate W3C trace context through HTTP and messaging.

```text
HTTP request
  -> authorization
  -> retrieval
  -> model generation
  -> tool call
  -> business service
  -> final response
```

Use span links when asynchronous evaluation or background work relates to an earlier request but is not its direct child.

Instrument IChatClient centrally
------
The `Microsoft.Extensions.AI` client pipeline can add OpenTelemetry around provider calls.

```csharp
IChatClient chatClient = new ChatClientBuilder(providerClient)
    .UseFunctionInvocation()
    .UseOpenTelemetry(
        loggerFactory,
        sourceName: "SupportAssistant")
    .Build();
```

Configure instrumentation once in the composition root. Application services should not manually create inconsistent provider spans.

Keep sensitive-content capture disabled
------
GenAI telemetry can include message content, function arguments, and function results when sensitive capture is enabled. The safe default is metadata without raw inputs and outputs.

Before enabling content capture, define:

- approved environments and users
- data classification and redaction
- encryption and access controls
- sampling and retention
- deletion and legal requirements
- whether tool results contain higher-risk data than prompts

Debugging convenience is not enough justification for copying customer content into another system.

Record stable versions
------
Operational behavior depends on more than the model name. Attach bounded identifiers for:

- feature and application version
- provider route and model deployment
- prompt and system-instruction version
- retrieval index and embedding version
- tool-schema and workflow version
- policy and evaluation-set version

Use low-cardinality version labels. Put request-specific identifiers in traces or logs, not metric dimensions.

Measure latency by stage
------
End-to-end duration alone cannot show whether a regression came from retrieval, provider queueing, generation, a tool, or response streaming.

Track:

- admission and queue time
- retrieval and reranking duration
- provider request duration
- time to first token
- streaming duration and completion state
- tool and downstream dependency duration
- workflow pause and approval time

Record cancellation and timeout separately from provider failure. A client abandoning a slow stream is useful product evidence.

Account for tokens and cost
------
Capture input, cached-input where available, output, embedding, and evaluation usage from provider response metadata. Convert usage to estimated cost through a versioned pricing configuration rather than hard-coding prices in business logic.

Aggregate by approved dimensions such as feature, tenant plan, environment, provider route, and model version. Do not create a metric label for every user or conversation. Detailed cost attribution can live in a durable usage ledger linked by request ID.

Trace agent tools and workflows
------
An agent trace should show model turns, tool selection, bounded argument metadata, tool latency, result category, approval, retries, and termination reason. Workflow telemetry should show executor and edge transitions, checkpoints, pending requests, and recovery.

Do not store hidden reasoning or unrestricted model content. Capture the observable execution decisions needed to operate the system.

```csharp
activity?.SetTag("ai.tool.name", toolName);
activity?.SetTag("ai.tool.result", resultCategory);
activity?.SetTag("ai.approval.required", approvalRequired);
activity?.SetTag("ai.operation.id", operationId);
```

Prefer emerging standard GenAI semantic conventions where supported, and isolate custom attributes under a documented application namespace.

Connect quality with operations
------
Join evaluation results and explicit user feedback to the version identifiers captured on the original request. Useful product signals include citation use, groundedness samples, task completion, correction rate, refusal correctness, and tool success.

Do not run expensive or privacy-sensitive evaluators synchronously on every request. Sample asynchronously and retain only the context approved for that evaluation purpose.

Define AI service objectives
------
Availability and latency objectives still matter, but AI features may also need objectives for:

- successful completion without fallback
- grounded answers with valid citations
- correct tool execution
- maximum cost per completed task
- approval completion time
- index freshness

Create objectives per user journey. A background document summary and an interactive support answer should not share one latency target.

Control cardinality and volume
------
Prompts, queries, tool arguments, document IDs, user IDs, and error messages are poor metric labels. They can be sensitive and create unbounded time series.

Use metrics for aggregates, traces for sampled execution detail, structured logs for discrete operational events, and an audit store for security or business evidence. Each signal has a different retention and access model.

Build useful dashboards and alerts
------
A practical dashboard combines:

- request rate, completion, and refusal
- p50, p95, and p99 latency plus time to first token
- token use and estimated cost
- provider and tool failures
- retrieval and citation signals
- evaluation and correction trends
- rate-limit and budget rejections

Alert on user impact, budget anomalies, stuck workflows, provider-route failure, and sustained quality regression. Avoid paging on every isolated model error.

Test telemetry as a contract
------
Integration tests can export to an in-memory OpenTelemetry collector and assert required spans, correlation, redaction, status, and version attributes. Test cancellation, provider failure, tool denial, fallback, and workflow resume.

Review telemetry after dependency upgrades because attribute names and prerelease conventions can evolve. Dashboard queries should fail visibly when expected data disappears.

Common mistakes to avoid
------
Watch for these issues:

- logging full prompts and tool results by default
- measuring only HTTP status and total duration
- omitting prompt, model, index, tool, and policy versions
- using user or document identifiers as metric labels
- estimating cost without versioned pricing
- evaluating quality synchronously on every request
- collecting traces without dashboards, objectives, or ownership
- enabling sensitive capture globally to investigate one incident

AI observability connects nondeterministic behavior to deterministic evidence. Trace the stages, measure usage and outcomes, version every behavioral input, and protect content as carefully as the production data it came from.

------------------------------------------------------------------------

**Next Article:** Releasing AI Features Safely in .NET: Prompt Versioning, Offline Evals, Shadow Traffic, and Rollback
