---
title: 'Evaluating .NET AI Applications: Quality, Safety, Regression Tests, and CI Gates'
date: 2026-08-08
permalink: /posts/2026/08/evaluating_ai_apps_dotnet_ci/
tags:
  - dotnet
  - dotnet10
  - ai
  - evaluation
  - testing
  - cicd
  - microsoft-extensions-ai
  - security
  - advanced
---

AI behavior changes when prompts, models, retrieval, tools, policies, or source data change. Ordinary unit tests remain essential, but exact string assertions cannot measure every useful answer. `Microsoft.Extensions.AI.Evaluation` adds quality, safety, agent, caching, and reporting components so .NET teams can turn representative scenarios into repeatable release evidence.

Start with product failure modes
------
Do not begin by collecting every available metric. Write down how the feature can fail for a user or the business.

For a grounded support assistant, important failures may include:

- the expected document was not retrieved
- the answer contradicts supplied evidence
- a citation points to an unrelated passage
- the agent selected the wrong tool
- an unauthorized request was answered
- latency or cost exceeds the product budget
- unsafe content or indirect prompt injection changes behavior

Each failure needs the strongest available test, not necessarily an LLM-based score.

Build a versioned scenario set
------
Represent each scenario as data that can run against multiple application versions.

```csharp
public sealed record EvaluationCase(
    string Id,
    string Query,
    IReadOnlyList<string> ExpectedEvidenceIds,
    string? ReferenceAnswer,
    bool ShouldRefuse,
    string Category);
```

Include ordinary cases, boundary conditions, past incidents, multilingual inputs, missing information, malicious retrieved text, and permission failures. Review the set with product, domain, security, and operations stakeholders.

Keep private or regulated data out of test fixtures unless the environment and retention policy explicitly support it.

Layer deterministic assertions first
------
Deterministic checks are fast, explainable, and stable. Use them for:

- HTTP and structured-output contracts
- allowed evidence and citation identifiers
- authorization and tenant isolation
- tool name and argument validation
- required approval steps
- token, latency, turn, and cost limits
- idempotent side effects

```csharp
Assert.All(run.Citations, citation =>
    Assert.Contains(citation.EvidenceId, testCase.ExpectedEvidenceIds));

Assert.True(run.TotalToolCalls <= 4);
Assert.True(run.EstimatedCost <= budget.MaximumCost);
```

No model judge should be the only proof that an access-control test passed.

Select evaluators by responsibility
------
The evaluation libraries include quality metrics such as relevance, completeness, groundedness, retrieval, intent resolution, task adherence, and tool-call accuracy. Safety packages cover content harms, protected material, and indirect attacks where their service requirements fit.

Use a metric only when the team can explain what a good or bad result means for the feature. A fluent answer can still be false, and a relevant answer can still be unauthorized.

Evaluate retrieval and generation separately
------
For RAG, first test whether expected evidence appears in the top `k` authorized results. Then evaluate whether the generated response is grounded in that evidence.

```text
ingestion evaluation -> chunk and metadata correctness
retrieval evaluation -> expected authorized evidence found
answer evaluation    -> claims supported and citations used
```

This separation prevents teams from repeatedly changing prompts when the source was missing, filtered incorrectly, or ranked too low.

Evaluate agents as executions
------
An agent response is only the visible end of a trace. Evaluate tool choice, arguments, ordering, approvals, retries, side effects, recovery, and termination.

Create scenarios where tools time out, return partial data, reject authorization, or report conflicts. Confirm that the agent does not invent success after a failure. For write operations, assert the stored result and audit event, not just the final wording.

Control judge variability
------
Model-based evaluators are useful for meaning that exact assertions cannot capture, but their scores can vary. Pin the judge deployment and evaluator configuration, use clear rubrics, and inspect examples near the pass threshold.

Compare distributions and category-level results instead of treating one aggregate number as truth. Re-run a stable baseline when the judge model changes so a scoring shift is not mistaken for a product regression.

Cache responses for offline evaluation
------
The reporting library can cache model responses and persist evaluation results. Caching makes local and CI runs faster and reduces cost when the prompt, model, context, and other request parameters have not changed.

Do not let a cache hide the change being tested. Include every behavior-affecting input in the cache key, set an appropriate expiry, and provide a deliberate way to refresh baselines.

Generate reviewable reports
------
The `dotnet aieval` tool can produce reports from stored evaluation runs.

```powershell
dotnet tool run aieval report `
  --path artifacts/ai-evaluation `
  --output artifacts/ai-evaluation/report.html
```

Publish the report as a CI artifact with prompt, application, model, retrieval-index, tool-schema, policy, and dataset versions. A score without those inputs is difficult to reproduce.

Use staged CI gates
------
Run fast deterministic and cached smoke scenarios on every pull request. Run broader or safety-focused suites on scheduled builds and before production promotion.

Useful gates include:

- zero authorization or prohibited-tool failures
- no regression beyond an agreed quality margin
- minimum pass rate for each critical category
- latency and cost within budgets
- manual review for changed model, prompt, retrieval, or policy versions

Do not block a release because one low-risk style score moved slightly. Gates should reflect user impact and measurement confidence.

Continue evaluation after deployment
------
Offline datasets cannot represent every production input. Sample privacy-safe operational cases, collect explicit user corrections, and turn confirmed incidents into new test scenarios.

Online evaluation should not add unacceptable latency or expose raw content to an unapproved judge. Prefer asynchronous sampling, redacted inputs, and strict retention. Monitor score drift by feature, tenant cohort, language, and version without creating unbounded telemetry dimensions.

Review failures, not only averages
------
A stable average can hide a severe regression in one category. Review worst cases, new failures, authorization denials, tool errors, and scenarios that changed classification.

Assign ownership for updating datasets and resolving flaky metrics. Evaluation data is production engineering evidence, not a dashboard that maintains itself.

Common mistakes to avoid
------
Watch for these issues:

- using a handful of happy-path questions as the complete dataset
- replacing deterministic security assertions with an LLM judge
- measuring answer quality while ignoring retrieval and tool behavior
- changing the judge model without recalibrating the baseline
- caching responses without complete behavior keys
- gating on one opaque aggregate score
- storing sensitive prompts indefinitely in reports
- failing to add production incidents back into the scenario set

Evaluation makes AI change reviewable. Strong suites combine deterministic invariants, targeted quality and safety metrics, operational budgets, versioned reports, and human investigation of important failures.

------------------------------------------------------------------------

**Next Article:** Durable AI Workflows in .NET: Checkpoints, Human Approval, Recovery, and Idempotency
