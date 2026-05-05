---
title: 'gRPC in .NET: Contracts, Streaming, and Interop'
date: 2026-03-28
permalink: /posts/2026/03/grpc_in_dotnet/
tags:
  - dotnet
  - grpc
  - aspnetcore
  - api
  - advanced
---

This post introduces gRPC in .NET: **contract-first service definitions, generated clients, streaming calls, and interop considerations**. REST and JSON are still excellent for many APIs, but gRPC is useful when strongly typed contracts and efficient service-to-service communication matter.

What gRPC is
------
gRPC is a remote procedure call framework that commonly uses:
- Protocol Buffers for contracts and serialization
- HTTP/2 as the transport
- generated clients and server base classes
- unary and streaming communication patterns

It is a good fit for:
- internal service-to-service calls
- low-latency APIs
- strongly typed contracts
- streaming scenarios

It is not always the best fit for public browser APIs unless you use gRPC-Web and account for ecosystem constraints.

Defining a contract
------
Contracts live in `.proto` files.

```proto
syntax = "proto3";

option csharp_namespace = "Store.Grpc";

service ProductCatalog {
  rpc GetProduct (GetProductRequest) returns (ProductReply);
}

message GetProductRequest {
  int32 id = 1;
}

message ProductReply {
  int32 id = 1;
  string name = 2;
  double price = 3;
}
```

The field numbers are part of the wire contract. Do not reuse them casually.

Server implementation
------
.NET generates a base class from the `.proto` file.

```csharp
public sealed class ProductCatalogService : ProductCatalog.ProductCatalogBase
{
    public override Task<ProductReply> GetProduct(
        GetProductRequest request,
        ServerCallContext context)
    {
        return Task.FromResult(new ProductReply
        {
            Id = request.Id,
            Name = "Mechanical Keyboard",
            Price = 129.00
        });
    }
}
```

Register gRPC:

```csharp
builder.Services.AddGrpc();

var app = builder.Build();

app.MapGrpcService<ProductCatalogService>();
```

Client usage
------
Generated clients make calls strongly typed.

```csharp
var channel = GrpcChannel.ForAddress("https://localhost:5001");
var client = new ProductCatalog.ProductCatalogClient(channel);

var product = await client.GetProductAsync(new GetProductRequest { Id = 42 });
```

In real applications, configure gRPC clients through DI rather than constructing channels everywhere.

Streaming
------
gRPC supports:
- unary calls
- server streaming
- client streaming
- bidirectional streaming

Server streaming example:

```proto
rpc StreamProducts (StreamProductsRequest) returns (stream ProductReply);
```

Implementation concept:

```csharp
public override async Task StreamProducts(
    StreamProductsRequest request,
    IServerStreamWriter<ProductReply> responseStream,
    ServerCallContext context)
{
    await foreach (var product in productService.GetProductsAsync(context.CancellationToken))
    {
        await responseStream.WriteAsync(new ProductReply
        {
            Id = product.Id,
            Name = product.Name,
            Price = (double)product.Price
        });
    }
}
```

Streaming is useful when data arrives over time or when a response is too large to buffer comfortably.

Interop considerations
------
Think about:
- HTTP/2 support in hosting infrastructure
- load balancer and reverse proxy configuration
- gRPC-Web for browser clients
- versioning `.proto` files carefully
- deadlines and cancellation

Common mistakes to avoid
------
Watch for these issues:
- using gRPC for public APIs when simple REST would be easier
- changing field numbers in `.proto` files
- ignoring deadlines and cancellation
- exposing internal domain models directly as generated contracts
- forgetting infrastructure requirements for HTTP/2

gRPC is a strong tool for typed service communication. Use it when its contract and streaming model simplify the system, not just because it is faster on paper.

------------------------------------------------------------------------

**Next Article:** Deploying ASP.NET Core Apps: Docker, Linux Hosting, Nginx, and Health Checks
