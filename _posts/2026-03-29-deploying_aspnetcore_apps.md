---
title: 'Deploying ASP.NET Core Apps: Docker, Linux Hosting, Nginx, and Health Checks'
date: 2026-03-29
permalink: /posts/2026/03/deploying_aspnetcore_apps/
tags:
  - dotnet
  - aspnetcore
  - docker
  - linux
  - deployment
  - advanced
---

This post covers practical deployment patterns for ASP.NET Core apps: **Docker images, Linux hosting, reverse proxies such as Nginx, and health checks**. Deployment is part of application design. An app that cannot start, stop, report health, and receive traffic cleanly is not production-ready.

Publishing the app
------
The basic publish command:

```bash
dotnet publish src/Store.Api/Store.Api.csproj -c Release -o publish
```

This creates deployable output with compiled assemblies, dependencies, and configuration files.

Use Release builds for deployment:

```bash
dotnet publish -c Release
```

Debug builds are for local development.

Dockerfile
------
A typical multi-stage Dockerfile:

```dockerfile
FROM mcr.microsoft.com/dotnet/sdk:8.0 AS build
WORKDIR /src
COPY . .
RUN dotnet publish src/Store.Api/Store.Api.csproj -c Release -o /app/publish

FROM mcr.microsoft.com/dotnet/aspnet:8.0 AS runtime
WORKDIR /app
COPY --from=build /app/publish .
ENTRYPOINT ["dotnet", "Store.Api.dll"]
```

Build and run:

```bash
docker build -t store-api .
docker run -p 8080:8080 store-api
```

In containers, configuration usually comes from environment variables or mounted secrets, not edited files inside the image.

Linux hosting
------
ASP.NET Core runs well on Linux. Common hosting options:
- systemd service on a VM
- Docker container
- Kubernetes
- platform services such as Azure App Service or AWS ECS

For systemd, your service file usually starts the published app and restarts it on failure.

Reverse proxy with Nginx
------
In many Linux deployments, Nginx sits in front of Kestrel.

Nginx handles:
- TLS termination
- public ports
- request forwarding
- compression
- buffering
- static assets in some setups

Basic reverse proxy shape:

```nginx
server {
    listen 80;
    server_name api.example.com;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

In ASP.NET Core, enable forwarded headers when running behind a proxy:

```csharp
app.UseForwardedHeaders();
```

Health checks
------
Health checks let platforms know whether the app is alive and ready.

```csharp
builder.Services.AddHealthChecks();

var app = builder.Build();

app.MapHealthChecks("/health");
```

For production, consider separate endpoints:
- liveness: process is running
- readiness: app can serve traffic

Readiness may include database, cache, or message broker checks, but be careful not to make health checks too expensive.

Deployment checklist
------
Use this baseline:
- publish Release builds
- externalize configuration
- expose a health endpoint
- log to stdout in containers
- set resource limits
- validate reverse proxy headers
- automate deployment through CI/CD

Common mistakes to avoid
------
Watch for these issues:
- building Docker images with secrets baked in
- running Debug builds in production
- missing health checks
- ignoring graceful shutdown
- forgetting forwarded headers behind Nginx or load balancers

Deployment quality affects reliability directly. Treat startup, shutdown, logs, configuration, and health checks as part of the app contract.

------------------------------------------------------------------------

**Next Article:** CI/CD with GitHub Actions for .NET: Build, Test, Publish, Secrets, and Environments
