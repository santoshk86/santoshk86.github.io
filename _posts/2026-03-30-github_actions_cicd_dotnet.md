---
title: 'CI/CD with GitHub Actions for .NET: Build, Test, Publish, Secrets, and Environments'
date: 2026-03-30
permalink: /posts/2026/03/github_actions_cicd_dotnet/
tags:
  - dotnet
  - github-actions
  - cicd
  - devops
  - advanced
---

This post covers a practical CI/CD pipeline for .NET using GitHub Actions. A good pipeline should **restore, build, test, publish artifacts, handle secrets correctly, and separate environments such as development, staging, and production**.

Why CI/CD matters
------
CI/CD reduces manual deployment risk. Every change should pass the same repeatable checks before it reaches users.

A baseline pipeline should answer:
- does the code restore successfully
- does it compile
- do tests pass
- can the app be packaged
- which environment receives the deployment

Basic build and test workflow
------
Create `.github/workflows/dotnet.yml`:

```yaml
name: dotnet-ci

on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]

jobs:
  build:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-dotnet@v4
        with:
          dotnet-version: '8.0.x'

      - run: dotnet restore
      - run: dotnet build --configuration Release --no-restore
      - run: dotnet test --configuration Release --no-build
```

This is the minimum useful loop for most .NET repos.

Publishing artifacts
------
After tests pass, publish the app:

```yaml
      - run: dotnet publish src/Store.Api/Store.Api.csproj --configuration Release --output ./publish

      - uses: actions/upload-artifact@v4
        with:
          name: store-api
          path: ./publish
```

Artifacts give later jobs a known package to deploy. This is better than rebuilding separately for every environment.

Secrets
------
Never hard-code credentials in workflow files.

Use GitHub Actions secrets:

```yaml
env:
  ConnectionStrings__Default: ${{ secrets.STAGING_DATABASE_CONNECTION }}
```

Rules:
- store secrets in GitHub secret stores
- scope secrets by repository, organization, or environment
- do not echo secrets in logs
- rotate credentials when needed

Environments
------
GitHub environments help control deployments.

Example:

```yaml
deploy-staging:
  runs-on: ubuntu-latest
  environment: staging
  needs: build
```

Production environments can require approvals, protection rules, and separate secrets.

Build once, deploy many
------
A strong pipeline builds once and promotes the same artifact.

Why:
- staging and production receive the same compiled output
- fewer "works in staging but not prod" surprises
- deployment becomes a promotion decision

For containers, the equivalent is:
- build an image once
- tag it with the commit SHA
- promote that image across environments

Quality gates
------
Useful checks include:
- unit tests
- integration tests
- formatting checks
- static analysis
- dependency vulnerability scanning
- container image scanning

Do not add gates just to make the pipeline look sophisticated. Add checks that catch real risk for your project.

Common mistakes to avoid
------
Watch for these issues:
- deploying from a developer machine manually
- rebuilding different artifacts for each environment
- storing secrets in YAML
- skipping tests on pull requests
- letting production deploys happen with no approval or audit trail

CI/CD is not just automation. It is a reliability control that makes releases repeatable and traceable.

------------------------------------------------------------------------

**Next Article:** Cloud Patterns for .NET: Azure App Service, Azure Container Apps, AWS ECS, and Fargate
