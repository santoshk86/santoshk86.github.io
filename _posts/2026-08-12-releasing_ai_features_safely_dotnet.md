---
title: 'Releasing AI Features Safely in .NET: Prompt Versioning, Offline Evals, Shadow Traffic, and Rollback'
date: 2026-08-12
permalink: /posts/2026/08/releasing_ai_features_safely_dotnet/
tags:
  - dotnet
  - dotnet10
  - ai
  - deployment
  - cicd
  - evaluation
  - feature-flags
  - observability
  - advanced
---

An AI feature can change without a traditional code change. A provider may update a model, a prompt may be edited, retrieval data may be reindexed, or a tool schema may evolve. Safe release engineering treats all behavior-affecting inputs as one versioned unit, evaluates them before promotion, limits exposure, observes real outcomes, and preserves a tested rollback path.

Define the release unit
------
A deployable AI behavior includes:

- application code and configuration
- model provider, deployment, and parameters
- system prompt and templates
- embedding model, index, and retrieval settings
- tool schemas and workflow definition
- safety, authorization, and gateway policy
- evaluation dataset and thresholds

Promoting only a container image while changing the prompt directly in production does not produce a reproducible release.

Create a version manifest
------
Record the effective versions together and attach the manifest ID to telemetry and evaluation reports.

```csharp
public sealed record AiReleaseManifest(
    string ReleaseId,
    string ApplicationVersion,
    string ModelRouteVersion,
    string PromptVersion,
    string RetrievalVersion,
    string ToolSchemaVersion,
    string PolicyVersion,
    string EvaluationSetVersion);
```

Store immutable prompt and policy artifacts in source control or a versioned registry. Do not use a mutable display name as the only identity of a production model deployment.

Separate one source of behavioral change
------
Avoid upgrading the runtime, provider SDK, model, prompt, retrieval configuration, and tools in one release. When behavior changes, the team needs to know which input caused it.

Use a sequence such as:

1. establish evaluation and production baselines
2. change one major behavioral component
3. run offline and integration evaluation
4. deploy behind a disabled or internal flag
5. expand exposure gradually

Urgent security fixes may require combining changes, but should still record exactly what moved.

Run deterministic gates before model evaluation
------
Build, unit, contract, security, and authorization tests remain the first CI gates. They catch failures more cheaply and precisely than model-based evaluation.

```yaml
- name: Test application contracts
  run: dotnet test --filter "Category!=AiEvaluation"

- name: Run AI evaluation suite
  run: dotnet test --filter "Category=AiEvaluation"

- name: Generate evaluation report
  run: >-
    dotnet tool run aieval report
    --path artifacts/ai-evaluation
    --output artifacts/ai-evaluation/report.html
```

Publish the report and manifest as build artifacts. Protect model credentials used by CI and limit evaluation concurrency and cost.

Compare with a stable baseline
------
Evaluate the candidate and current production behavior against the same scenario set. Compare critical-category pass rates, retrieval, groundedness, tool accuracy, latency, tokens, and estimated cost.

Inspect changed cases instead of accepting one aggregate score. A small average improvement can hide a new authorization or high-impact workflow failure.

Use feature flags at the server boundary
------
Evaluate flags from authenticated, server-owned context. Do not let a client request an unapproved model or prompt version directly.

Flags can control:

- whether the feature is available
- which release manifest handles a request
- internal or tenant allowlists
- percentage rollout
- fallback and kill-switch behavior

Record the flag decision and manifest version in the request trace. Keep a deterministic non-AI path when the product requires continuity.

Shadow traffic carefully
------
Shadowing sends a copy of a production input to a candidate path without showing its result to the user. It reveals realistic latency, compatibility, and cost before user exposure.

Shadow traffic duplicates data processing. Confirm privacy purpose, regional boundaries, provider approval, retention, and deletion before enabling it. Do not execute write tools or external side effects in the shadow path. Use tool simulators or recorded safe responses.

Start with an internal canary
------
Release to team members or a controlled tenant set, then expand by percentage or cohort. Choose cohorts that represent languages, workloads, document sources, and tool paths rather than only the easiest cases.

Define promotion criteria and observation windows in advance. Include minimum sample size, quality and safety results, user corrections, latency, error rate, token use, and cost.

Make rollback a configuration operation
------
A rollback should restore the previous complete release manifest, not only the previous container. Keep the prior prompt, model route, index alias, tool schema, and policy available for the rollback window.

Test rollback before broad rollout. Verify that active conversations and durable workflows can continue safely or fail with a controlled compatibility response.

Plan data and schema compatibility
------
Retrieval migrations should build a new index and switch an alias after evaluation. Keep the old index until rollback expires. Tool and structured-output changes should be additive where possible, with adapters for in-flight work.

Version durable workflow state. A release must not strand checkpoints because an executor or serialized field disappeared.

Monitor leading and lagging signals
------
Leading signals appear quickly: provider errors, validation failures, latency, token use, rate limits, tool denials, and fallback. Lagging signals include user corrections, task completion, support escalation, groundedness samples, and business outcomes.

Compare the candidate with a concurrent control cohort. Account for traffic mix and source-data changes before attributing every difference to the model.

Keep a kill switch narrow
------
Operators should be able to disable one feature, model route, tool, tenant cohort, or release manifest without taking down unrelated application paths.

Document who may activate the switch, what evidence is required, how the decision is audited, and how recovery is verified. A kill switch that has never been exercised is an assumption.

Learn from release incidents
------
Capture the manifest, affected cohorts, traces, evaluation gaps, source-data changes, and recovery timeline. Add confirmed failures to the evaluation set and update promotion criteria when the previous process failed to detect risk.

Avoid storing sensitive production examples in an unrestricted regression repository. Redact, synthesize, or secure them according to classification.

Common mistakes to avoid
------
Watch for these issues:

- versioning code while prompts and model routes remain mutable
- changing several behavioral components in one release
- relying only on model-based evaluation in CI
- letting clients select unapproved release versions
- shadowing private data without a separate processing review
- allowing write tools to run in the shadow path
- rolling back code without rolling back prompts, indexes, tools, and policy
- expanding a canary without predetermined success criteria

Safe AI delivery is controlled behavior promotion. Version the complete system, compare it with a baseline, expose it gradually, measure real outcomes, and make rollback restore a known configuration.

------------------------------------------------------------------------

**Next Article:** Agent-to-Agent Systems in .NET: A2A Protocol, Remote Agents, Identity, and Trust Boundaries
