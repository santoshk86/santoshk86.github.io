---
title: 'Production AI Data Ingestion in .NET: Documents, Chunking, Enrichment, Embeddings, and Reindexing'
date: 2026-08-05
permalink: /posts/2026/08/production_ai_data_ingestion_dotnet/
tags:
  - dotnet
  - dotnet10
  - ai
  - data-ingestion
  - embeddings
  - rag
  - vector-search
  - background-jobs
  - advanced
---

Production retrieval starts before the user asks a question. Documents must be discovered, parsed, normalized, divided into useful chunks, enriched, embedded, and written with enough identity and authorization metadata to be replaced or removed later. `Microsoft.Extensions.DataIngestion` provides .NET building blocks for this pipeline, while application code must still own lifecycle, security, recovery, and quality decisions.

Separate the write plane from the read plane
------
Do not parse and embed documents inside an interactive chat request. Use a durable ingestion process that can run independently, retry work, and publish a completed document version atomically.

```text
source change
  -> discover
  -> extract
  -> normalize
  -> chunk and enrich
  -> embed
  -> stage
  -> publish searchable version
```

The query path should see either the previous complete version or the new complete version, not half of each. This separation also lets ingestion use different scaling, credentials, and timeouts from the API.

Give every source a stable identity
------
File paths and URLs can change. Define a source identifier from the authoritative system and track a version, content hash, and ingestion policy version.

```csharp
public sealed record SourceDocument(
    string SourceSystem,
    string SourceId,
    string Version,
    string ContentHash,
    Stream Content,
    IReadOnlySet<string> AccessGroups);
```

The identity must support three operations: replace one document version, delete all chunks for a removed document, and prove which source produced an answer citation. A random identifier generated on every run cannot do this reliably.

Extract structure, not only text
------
Preserve headings, page or section numbers, tables, lists, image alternatives, and source links when the document format provides them. Flattening everything into one string destroys boundaries that help retrieval and citations.

Treat parsers as untrusted-input handlers. Limit document size, decompression, nested archives, page count, and processing time. Run complex format conversion with minimal permissions. A malformed office document should fail one job, not the worker process or the entire batch.

Normalize deterministically
------
Remove repeated headers and footers, normalize whitespace, and reject content that is empty after extraction. Avoid transformations that change factual meaning. Store the extracted representation or its hash so a parser upgrade can be compared and reprocessed intentionally.

Determinism matters because a re-run of the same document and policy should produce the same chunk identities. Stable output makes updates, testing, and incident investigation much easier.

Choose chunking from document structure
------
Chunk size is not merely a token-limit calculation. Small chunks can lose context; large chunks can dilute retrieval relevance and waste the model context window. Prefer boundaries such as headings and sections, then enforce a maximum token size.

```csharp
Tokenizer tokenizer = TiktokenTokenizer.CreateForModel("gpt-5");

var options = new IngestionChunkerOptions(tokenizer)
{
    MaxTokensPerChunk = 1_200,
    OverlapTokens = 100
};

IngestionChunker<string> chunker = new HeaderChunker(options);
```

Package APIs can evolve, so isolate chunker creation behind an application interface and pin tested versions. Measure retrieval quality before copying one chunk size across every document type.

Carry authorization metadata into every chunk
------
A searchable chunk should include:

- tenant or security partition
- source and document identifiers
- document version and content hash
- section, page, or anchor
- access groups or policy reference
- language and content type
- embedding model and dimensions
- ingestion timestamp and policy version

Authorization metadata must come from the authoritative source, not from model-generated enrichment. If permissions change without document content changing, the pipeline still needs a way to update or replace searchable records.

Use enrichment selectively
------
Summaries, keywords, classifications, and image alternative text can improve retrieval, but enrichment adds cost and model-generated data. Keep original text separate from generated fields, record the model and prompt version, and validate bounded outputs.

Do not let enrichment grant access, invent a source title, or replace the original citation text. For regulated content, require review before generated metadata becomes visible to users.

Manage the embedding lifecycle
------
An embedding is derived data tied to a model, dimensions, normalization rules, and source content. Store those attributes with the vector. When the model changes, create a new index or collection and re-embed through a controlled migration.

```csharp
public sealed record EmbeddingVersion(
    string Provider,
    string Model,
    int Dimensions,
    string ChunkPolicyVersion);
```

Never write vectors from different dimensions or incompatible models into the same field. Use an alias or routing configuration to switch reads only after the new index is complete and evaluated.

Make writes idempotent
------
Derive a chunk key from stable inputs such as tenant, source ID, document version, and chunk ordinal or content hash. An upsert of the same version should replace the same records rather than create duplicates.

Stage the new version, verify expected chunk counts, and then publish it. After readers have switched, remove the old version through a separate, retryable cleanup step. This prevents a cleanup failure from making the new document unavailable.

Process changes incrementally
------
Compare source version and content hash before expensive parsing or embedding. Distinguish:

- new document
- content update
- permission-only update
- metadata-only update
- deletion
- parser or policy reprocessing

A permission-only update may not require new embeddings, but it must update every affected chunk consistently. A deletion should create a durable tombstone so a later retry cannot accidentally restore stale content.

Operate ingestion as a workflow
------
Use a queue or durable job store with bounded attempts and a dead-letter state. Track each stage so operators can tell whether failure occurred during extraction, enrichment, embedding, or storage.

Limit parallel model calls and vector-store writes. Respect provider rate limits, propagate cancellation during shutdown, and resume from durable document state rather than restarting a large corpus.

Verify ingestion quality
------
Create a controlled document set with expected sections, permissions, and retrieval questions. Assert chunk count ranges, stable identifiers, citations, token limits, and complete deletion. Compare retrieval metrics before changing parsers, chunking, enrichment, or embedding models.

Operational metrics should include queue age, documents processed, stage latency, failure category, tokens and cost, chunks per document, index growth, and time from source change to searchable publication.

Common mistakes to avoid
------
Watch for these issues:

- embedding documents during an interactive request
- generating new document and chunk IDs on every run
- discarding headings, pages, and citation anchors
- applying permissions after retrieval instead of storing filterable metadata
- mixing embedding models or dimensions in one index
- deleting the old version before the new version is complete
- retrying without idempotent chunk keys
- changing chunk policy without a retrieval evaluation

Ingestion is a data product with lineage, versions, access rules, and recovery behavior. When those controls are explicit, the retrieval layer can answer quickly without guessing where its knowledge came from.

------------------------------------------------------------------------

**Next Article:** Production RAG in .NET: Hybrid Search, Reranking, Citations, and Security Trimming
