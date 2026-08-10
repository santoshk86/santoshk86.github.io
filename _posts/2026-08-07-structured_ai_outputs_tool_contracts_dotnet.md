---
title: 'Reliable AI Contracts in .NET: Structured Outputs, JSON Schema, Tool Calls, and Validation'
date: 2026-08-07
permalink: /posts/2026/08/structured_ai_outputs_tool_contracts_dotnet/
tags:
  - dotnet
  - dotnet10
  - ai
  - microsoft-extensions-ai
  - structured-output
  - json-schema
  - validation
  - tool-calling
  - advanced
---

Free-form text is useful for conversation, but application workflows need contracts. `Microsoft.Extensions.AI` can request typed structured output, and model tools can expose typed arguments. Neither feature makes model output trustworthy. Production code must still validate syntax, semantics, authorization, version compatibility, and side effects before the result crosses a business boundary.

Choose structured output for machine decisions
------
Use structured output when code must inspect fields, branch, persist a value, or call another service. Keep prose when the response is only displayed to a person.

Good structured-output scenarios include:

- extracting fields from an approved document type
- classifying a support case into known categories
- proposing a bounded workflow decision
- returning cited answer sections
- creating a draft command for later approval

Do not use a model to calculate a value that deterministic code can derive more accurately.

Define a narrow .NET type
------
The response type should express the smallest useful contract.

```csharp
public enum CasePriority
{
    Low,
    Normal,
    High
}

public sealed record CaseTriage(
    CasePriority Priority,
    string Category,
    string Rationale,
    IReadOnlyList<string> EvidenceIds,
    bool NeedsHumanReview);
```

Avoid unbounded dictionaries and `object` properties. Constrained enums, required fields, maximum lengths, and explicit nullable values give the schema and validator useful information.

Request typed output through IChatClient
------
The structured-output extensions can derive a JSON schema from `T` and deserialize the response into `ChatResponse<T>`.

```csharp
ChatResponse<CaseTriage> response =
    await chatClient.GetResponseAsync<CaseTriage>(
        "Triage the supplied case using only evidence IDs E1-E4.",
        options: new ChatOptions
        {
            Temperature = 0
        },
        useJsonSchemaResponseFormat: true,
        cancellationToken: cancellationToken);
```

Schema support depends on the underlying client and model. Test the configured provider and keep a capability map. Do not silently disable schema enforcement and assume behavior remains equivalent.

Treat deserialization as the first check
------
A successful parse proves only that the payload matched enough of the JSON contract to deserialize. It does not prove that:

- the category is allowed for this tenant
- cited evidence exists
- the rationale follows from the evidence
- a length or numeric range is acceptable
- the decision is authorized
- the result is safe to persist or execute

Run ordinary .NET validation immediately after parsing and return a typed failure instead of passing a partially trusted object deeper into the application.

```csharp
public static IReadOnlyList<string> Validate(
    CaseTriage triage,
    IReadOnlySet<string> suppliedEvidence)
{
    var errors = new List<string>();

    if (triage.Rationale.Length > 1_000)
        errors.Add("Rationale exceeds the maximum length.");

    if (triage.EvidenceIds.Any(id => !suppliedEvidence.Contains(id)))
        errors.Add("The response cites evidence that was not supplied.");

    return errors;
}
```

Separate structural and semantic validation
------
Structural validation checks types, required values, ranges, and formats. Semantic validation checks business meaning: dates are in an allowed period, identifiers belong to the current tenant, amounts agree with source records, and state transitions are legal.

Use deterministic code for every semantic rule it can express. Model-based evaluation may identify unsupported reasoning, but it must not replace authorization or financial invariants.

Bound repair attempts
------
When output is invalid, decide whether the failure is retryable. A malformed response may justify one repair request that includes only validation errors and the original bounded context. An unsupported provider feature, policy denial, or missing source data should not be retried.

Keep repair within the original time, token, and cost budget. Record the attempt count and return a safe failure after the limit. An unlimited “ask the model to fix itself” loop can be slower and more expensive than the original call.

Distinguish structured output from tool calling
------
Structured output asks the model to return data. Tool calling lets the model propose an application operation. A tool call is a request, not permission to execute.

```csharp
public sealed record CreateRefundDraft(
    Guid OperationId,
    Guid OrderId,
    decimal Amount,
    string Reason);
```

The tool implementation must authenticate the caller, authorize the order, validate the amount, check current order state, and enforce idempotency. The model should not supply tenant identity, approval state, or effective permissions.

Design tools as business capabilities
------
Prefer `CreateRefundDraft` over `ExecuteSql`, `CallUrl`, or `UpdateEntity`. A narrow tool provides:

- a reviewable input schema
- an obvious authorization rule
- a bounded side effect
- an idempotency strategy
- meaningful audit events
- focused tests

Separate read tools from write tools. Require stronger scopes and explicit human approval as impact increases. Some administrative or irreversible capabilities should never be exposed to a model.

Version contracts deliberately
------
Prompts, schemas, model deployments, tools, and validators form one effective contract. Record their versions together.

Adding a required property is a breaking change. Renaming an enum value can break old evaluations or persisted drafts. Prefer additive optional changes, introduce a new contract version when semantics change, and keep adapters for in-flight workflows.

Do not persist provider response objects as domain records. Map a validated result into an application-owned type with its own version and provenance.

Test provider behavior and application rules
------
Unit tests should cover validators, mappings, authorization, idempotency, and error handling without calling a model. Provider integration tests should verify:

- the selected model honors the schema
- enum and nullable values deserialize correctly
- cancellation stops the call
- invalid output follows the repair policy
- streaming and non-streaming behavior match the contract

Evaluation tests should include ambiguous inputs, missing evidence, adversarial instructions, unexpected languages, and attempts to invent identifiers.

Observe contract failures
------
Track schema version, provider and model route, parse failures, validation categories, repair attempts, tool proposals, authorization decisions, and final status. Do not log raw structured output when it can contain personal or confidential data.

A rise in validation failures after a model or prompt change is a release signal. It should be visible before the failures become corrupted records or incorrect side effects.

Common mistakes to avoid
------
Watch for these issues:

- treating valid JSON as valid business data
- falling back silently when a model does not support JSON schema
- putting identity or approval fields under model control
- exposing generic SQL, shell, or HTTP tools
- retrying validation failures without a total budget
- allowing tool retries to duplicate side effects
- changing schemas without versioned evaluation data
- persisting provider types directly in the domain

Reliable AI integration means translating nondeterministic output into a small, validated application contract. JSON schema improves the shape; deterministic code still owns meaning, permission, and execution.

------------------------------------------------------------------------

**Next Article:** Evaluating .NET AI Applications: Quality, Safety, Regression Tests, and CI Gates
