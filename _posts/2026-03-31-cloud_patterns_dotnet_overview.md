---
title: 'Cloud Patterns for .NET: Azure App Service, Azure Container Apps, AWS ECS, and Fargate'
date: 2026-03-31
permalink: /posts/2026/03/cloud_patterns_dotnet_overview/
tags:
  - dotnet
  - cloud
  - azure
  - aws
  - containers
  - advanced
---

This post gives a practical overview of cloud hosting patterns for .NET applications, focusing on **Azure App Service, Azure Container Apps, AWS ECS, and AWS Fargate**. The goal is not to memorize every platform feature. The goal is to understand the deployment shape each option encourages.

Start with the hosting model
------
Before choosing a platform, answer:
- is the app a web API, worker, or both
- does it need containers
- does it need scale-to-zero
- who manages the runtime and OS
- what observability and secrets tools are available
- how deployments and rollbacks work

Cloud choice is architecture. It affects configuration, networking, deployment, and operations.

Azure App Service
------
Azure App Service is a managed platform for web apps and APIs.

Good fit:
- straightforward ASP.NET Core APIs
- teams that want minimal infrastructure management
- apps that do not require custom orchestration
- deployments from GitHub Actions or Azure DevOps

Benefits:
- managed runtime
- deployment slots
- built-in TLS support
- easy custom domains
- integration with Application Insights

Tradeoffs:
- less control than container orchestration
- some platform behavior is specific to App Service
- workers and background jobs need careful planning

Azure Container Apps
------
Azure Container Apps runs containers on a managed platform with scaling features.

Good fit:
- containerized APIs
- worker services
- event-driven scale
- teams that want containers without managing Kubernetes directly

Useful capabilities:
- revision-based deployments
- scale rules
- managed ingress
- environment variables and secrets
- Dapr integration when needed

Container Apps is attractive when you want container packaging but not full cluster ownership.

AWS ECS and Fargate
------
Amazon ECS runs containers. Fargate lets you run ECS tasks without managing EC2 instances.

Good fit:
- containerized .NET APIs
- worker services
- teams already on AWS
- services that need VPC-level integration

Core concepts:
- task definition describes containers
- service keeps tasks running
- cluster groups capacity
- load balancer routes traffic
- CloudWatch collects logs and metrics

Fargate reduces infrastructure management by removing the need to manage the underlying servers.

Configuration and secrets
------
Across cloud platforms, keep the same .NET design:
- use `appsettings.json` for non-sensitive defaults
- override with environment variables
- store secrets in platform secret stores
- validate options at startup

Example environment variable:

```text
ConnectionStrings__Default=...
```

.NET configuration providers make this consistent across Azure, AWS, containers, and local development.

Health checks and scaling
------
Cloud platforms need to know whether the app is healthy.

```csharp
builder.Services.AddHealthChecks();

app.MapHealthChecks("/health");
```

For production, distinguish:
- liveness: process is running
- readiness: app can handle traffic

Scaling depends on the platform:
- App Service scales instances
- Container Apps can scale by HTTP traffic, queue length, or events
- ECS services scale task count based on metrics

Choosing pragmatically
------
Use Azure App Service when:
- you want a simple managed web app platform
- the app is mostly HTTP
- speed of setup matters

Use Azure Container Apps when:
- containers are part of your workflow
- you need event-driven scale
- you want less operational overhead than Kubernetes

Use ECS/Fargate when:
- AWS is the primary cloud
- containers are standard
- VPC networking and AWS service integration matter

Common mistakes to avoid
------
Watch for these issues:
- choosing Kubernetes-level complexity too early
- storing secrets in images or source control
- missing health checks
- failing to design logging and metrics before production
- assuming local container behavior matches cloud networking exactly

Cloud platforms differ, but the application fundamentals remain stable: external configuration, health checks, logs, metrics, secure secrets, and repeatable deployments.

------------------------------------------------------------------------

**Next Article:** Multi-Tenancy Patterns in ASP.NET Core
