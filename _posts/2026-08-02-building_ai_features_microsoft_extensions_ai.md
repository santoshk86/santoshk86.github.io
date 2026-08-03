---
title: 'Building AI Features in .NET: Microsoft.Extensions.AI, Chat, Embeddings, RAG, and Telemetry'
date: 2026-08-02
permalink: /posts/2026/08/building_ai_features_microsoft_extensions_ai/
tags:
  - dotnet
  - dotnet10
  - ai
  - microsoft-extensions-ai
  - embeddings
  - rag
  - opentelemetry
  - advanced
---

`Microsoft.Extensions.AI` provides common .NET abstractions for generative AI services. `IChatClient` represents chat and streaming interactions, while `IEmbeddingGenerator` represents embedding generation. The abstractions support familiar dependency injection and middleware patterns for telemetry, caching, function invocation, and testing. They let application code depend on capabilities instead of spreading one provider's SDK types through every layer.

Begin with a product capability
------
Do not begin with a model name. Define what the user needs and how success will be measured.

Examples include:

- summarize a support case with cited source messages
- classify an incoming document into approved categories
- answer a question from an internal knowledge base
- extract structured fields for human review
- propose a response that an employee can edit

Define quality, latency, cost, safety, and fallback requirements. A feature without an evaluation set is a demo that cannot be improved safely.

Depend on IChatClient
------
Application services can request the abstraction through dependency injection:

```csharp
public sealed class CaseSummaryService(IChatClient chatClient)
{
    public async Task<string> SummarizeAsync(
        string caseHistory,
        CancellationToken cancellationToken)
    {
        var response = await chatClient.GetResponseAsync(
            [
                new ChatMessage(
                    ChatRole.System,
                    "Summarize support cases using only supplied facts."),
                new ChatMessage(ChatRole.User, caseHistory)
            ],
            cancellationToken: cancellationToken);

        return response.Text;
    }
}
```

The composition root selects and configures the provider. Business code remains easier to test and migrate.

Compose client middleware
------
`ChatClientBuilder` can add cross-cutting behavior around the provider client:

```csharp
IChatClient client = new ChatClientBuilder(providerClient)
    .UseFunctionInvocation()
    .UseOpenTelemetry(loggerFactory, sourceName: "SupportAssistant")
    .Build();

builder.Services.AddSingleton(client);
```

Middleware is useful for telemetry, caching, logging, retries, and tool invocation. Keep the order intentional and avoid logging raw prompts or responses when they may contain sensitive data.

Stream long responses
------
Streaming improves perceived latency when the interface can display partial output.

```csharp
await foreach (var update in chatClient.GetStreamingResponseAsync(
    messages,
    cancellationToken: cancellationToken))
{
    await writer.WriteAsync(update.Text, cancellationToken);
}
```

Cancellation must stop both the client stream and provider request. The UI should distinguish a complete answer from a cancelled or failed partial response.

Generate embeddings through an abstraction
------
`IEmbeddingGenerator<TInput, TEmbedding>` converts inputs into vectors. The application can use those vectors for semantic search, clustering, or retrieval.

```csharp
public sealed class ArticleEmbeddingService(
    IEmbeddingGenerator<string, Embedding<float>> generator)
{
    public async Task<float[]> GenerateAsync(
        string text,
        CancellationToken cancellationToken)
    {
        var embedding = await generator.GenerateAsync(
            text,
            cancellationToken: cancellationToken);

        return embedding.Vector.ToArray();
    }
}
```

Store the model identifier, vector dimensions, source hash, and generation time with each vector. Re-embedding after a model change should be a durable background process.

Build a retrieval-augmented generation flow
------
A basic RAG request has controlled stages:

1. validate and normalize the question
2. generate a query embedding
3. retrieve authorized candidate documents
4. rank and limit context
5. construct a grounded prompt
6. generate the answer
7. return citations and confidence signals

The retrieval query should enforce access before context reaches the model:

```csharp
var context = await dbContext.KnowledgeArticles
    .AsNoTracking()
    .Where(article => article.TenantId == tenantId)
    .Where(article => article.IsPublished)
    .OrderBy(article => EF.Functions.VectorDistance(
        article.Embedding,
        queryEmbedding))
    .Take(5)
    .Select(article => new ContextItem(
        article.Id,
        article.Title,
        article.Content))
    .ToListAsync(cancellationToken);
```

Retrieval is part of the security boundary. Filtering documents after model generation is too late.

Treat retrieved text as untrusted
------
Documents, web pages, and tool output can contain instructions intended to override the application's rules. Keep system instructions separate, label retrieved content as data, restrict tools, and validate structured outputs.

Do not place secrets or broad credentials in prompts. The model should receive the minimum context needed for the current operation.

Use tools for narrow operations
------
Function calling lets a model request an application operation. Expose small, typed tools rather than general database or HTTP access.

```csharp
[Description("Gets the current shipping status for an order the caller can access.")]
public Task<OrderStatusDto?> GetOrderStatusAsync(
    [Description("The order identifier")] Guid orderId,
    CancellationToken cancellationToken)
{
    return authorizedOrderQueries.GetStatusAsync(orderId, cancellationToken);
}
```

The tool implementation must authenticate, authorize, validate input, enforce timeouts, and audit sensitive operations. A model choosing a tool is not authorization.

Make AI calls observable
------
Track operational and product signals:

- provider and model deployment
- end-to-end and provider latency
- input and output token usage
- estimated cost
- retries, rate limits, and failures
- retrieval document count and scores
- tool calls and outcomes
- user acceptance or correction rate
- evaluation scores by prompt version

Use identifiers or redacted summaries in telemetry instead of full sensitive content. Apply sampling carefully because rare failures may matter more than ordinary successes.

Test without calling a model everywhere
------
Unit tests can use a fake `IChatClient` to verify prompt assembly, cancellation, response parsing, and fallback behavior. Integration tests should cover the selected provider and model with a small deterministic scenario set. Evaluation tests should measure meaning and safety across a larger curated dataset.

Pin the prompt, model deployment, tool schema, and retrieval configuration in evaluation results. Otherwise a quality change is difficult to explain.

Common mistakes to avoid
------
Watch for these issues:

- coupling application services directly to one provider SDK
- sending entire documents when only small passages are needed
- performing authorization after retrieval or generation
- allowing models to call broad, privileged tools
- logging sensitive prompts and outputs
- evaluating only a few happy-path questions
- changing prompts or models without versioned evaluation results

`Microsoft.Extensions.AI` makes AI integrations feel like other .NET infrastructure. That is useful because the same engineering disciplines still apply: explicit contracts, dependency injection, least privilege, cancellation, telemetry, testing, and controlled rollout.

------------------------------------------------------------------------

**Next Article:** Engineering AI Agents in .NET: Agent Framework, MCP Tools, Evaluation, and Guardrails
