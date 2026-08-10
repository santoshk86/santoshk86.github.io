---
title: 'Production RAG in .NET: Hybrid Search, Reranking, Citations, and Security Trimming'
date: 2026-08-06
permalink: /posts/2026/08/production_rag_vector_search_dotnet/
tags:
  - dotnet
  - dotnet10
  - ai
  - rag
  - vector-search
  - hybrid-search
  - security
  - evaluation
  - advanced
---

Retrieval-augmented generation is reliable only when retrieval is treated as an application subsystem rather than a prompt trick. The query path must enforce access, combine exact and semantic evidence, control context size, preserve citations, and abstain when evidence is weak. This article focuses on that read path; document parsing, chunking, and embedding belong to the ingestion pipeline.

Define a retrieval contract
------
Make the inputs and outputs explicit before selecting a vector store.

```csharp
public sealed record RetrievalRequest(
    string TenantId,
    string SubjectId,
    string Query,
    IReadOnlySet<string> AccessGroups,
    int MaximumResults);

public sealed record Evidence(
    string SourceId,
    string Title,
    string Anchor,
    string Text,
    double Score);
```

The result should contain evidence, source identity, and ranking metadata. It should not return an already generated answer. Keeping retrieval separate makes ranking testable without a model judging its own work.

Normalize without erasing intent
------
Reject empty and oversized questions, normalize obvious whitespace, and detect the language when it affects analyzers or embedding selection. Do not rewrite every query with a model by default. Query expansion adds latency and can change names, identifiers, dates, or negation.

When expansion is useful, retain the original query and record generated alternatives. Apply the same authorization filters to every alternative and bound how many searches one request may produce.

Apply security trimming inside retrieval
------
Build filters from authenticated identity and authoritative permissions. The vector or search store must apply tenant and access filters while selecting candidates.

```csharp
var request = new RetrievalRequest(
    tenant.Id,
    user.Id,
    question,
    user.AccessGroups,
    MaximumResults: 20);

IReadOnlyList<Evidence> candidates =
    await evidenceStore.SearchAuthorizedAsync(
        request,
        cancellationToken);
```

Retrieving a cross-tenant chunk and removing it in application memory is too late: the sensitive content already crossed a boundary. Test negative authorization cases with documents that would otherwise rank highly.

Combine lexical and vector search
------
Vector search captures semantic similarity, while lexical search is strong for product codes, error messages, names, and exact phrases. Hybrid search combines both candidate sets and fuses their rankings.

`Microsoft.Extensions.VectorData` provides common vector-store abstractions, and several stores support hybrid search. Provider behavior still differs, so keep search configuration behind a repository and test against the production engine rather than relying only on an in-memory provider.

Use filters, keyword fields, and vector fields intentionally. Embedding large identifiers is not a replacement for exact indexing.

Retrieve broadly, then rerank narrowly
------
Initial search should gather a bounded candidate set efficiently. A reranker can then apply a more expensive relevance model to the query and candidates.

```text
lexical candidates ---\
                       -> rank fusion -> security-safe candidate set
vector candidates ----/                         |
                                                 -> rerank -> top evidence
```

Do not rerank hundreds of full documents. Select small passages, limit parallel calls, and keep a total latency and cost budget. If the reranker fails, define whether the application returns fused results or abstains.

Assemble context as evidence
------
Order the final passages by usefulness, but preserve document structure where adjacent chunks are needed for meaning. Deduplicate overlapping text and reserve context space for system instructions, the question, tool results, and the answer.

Wrap each passage with a stable evidence identifier and source metadata. Clearly label retrieved text as untrusted data, not instructions.

```text
[Evidence E1 | handbook-42 | section 7.3]
...authorized source text...

[Evidence E2 | runbook-18 | database-failover]
...authorized source text...
```

Generate citations from identifiers
------
Ask the model to cite evidence IDs, then resolve those IDs through application code. Do not accept a URL or document title invented by the model.

Return a citation only when its evidence was actually supplied to the model and remains visible to the caller. A source link may require a separate authorization check because access can change between retrieval and response rendering.

Treat retrieved content as hostile
------
Documents can contain instructions designed to override the application, request secrets, or trigger tools. Keep system policy separate, delimit evidence, and state that evidence is data. Tool access should be narrow and authorized independently of retrieval.

Scan or classify high-risk sources when appropriate, but do not rely on one prompt-injection detector as a security boundary. The strongest control is minimizing what the model can access and what tools can do.

Abstain when evidence is insufficient
------
A production RAG system needs a supported no-answer path. Low scores alone do not provide a universal threshold because score ranges vary by model, index, and query type.

Combine signals such as candidate presence, reranker confidence, source freshness, citation coverage, and evaluation results. Return a clear limitation and safe next action rather than filling the gap from model memory when the product promises source-grounded answers.

Evaluate retrieval before generation
------
For a curated query set, measure whether expected evidence appears in the top results. Useful retrieval metrics include recall at `k`, reciprocal rank, precision, permission correctness, and citation-anchor accuracy.

Then evaluate the generated answer for groundedness, relevance, completeness, and correct citation use. Separating the layers tells the team whether a failure came from ingestion, retrieval, reranking, context assembly, or generation.

Observe the query path
------
Trace query normalization, each search, rank fusion, reranking, context assembly, and generation. Record bounded metadata:

- index and embedding version
- filters and policy version without sensitive values
- candidate and final evidence counts
- stage latency and failures
- context and answer token usage
- citations returned and abstention reason

Avoid logging raw questions or evidence by default. They may contain the most sensitive data in the system.

Test failure and change
------
Run integration tests against the real search technology with production-like analyzers and filters. Cover empty results, stale indexes, deleted documents, permission changes, reranker timeout, multilingual queries, exact identifiers, and cancellation.

Before changing embeddings, chunking, fusion weights, filters, or rerankers, run the same evaluation set and compare latency and cost alongside quality.

Common mistakes to avoid
------
Watch for these issues:

- filtering unauthorized results after retrieval
- using vector similarity for exact identifiers
- sending too many candidates directly to the model
- trusting citations written as free-form model text
- allowing retrieved instructions to control tools
- forcing an answer when evidence is weak
- tuning generation prompts when the expected document was never retrieved
- changing search configuration without a versioned evaluation

Production RAG is an evidence pipeline. Hybrid retrieval finds candidates, security trimming limits what may be seen, reranking chooses useful passages, and deterministic citation handling keeps the final answer connected to authorized sources.

------------------------------------------------------------------------

**Next Article:** Reliable AI Contracts in .NET: Structured Outputs, JSON Schema, Tool Calls, and Validation
