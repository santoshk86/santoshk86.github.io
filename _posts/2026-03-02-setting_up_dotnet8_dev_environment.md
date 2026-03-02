---
title: 'Setting Up Your .NET 8 Development Environment (SDK, VS Code/Visual Studio, and CLI Basics)'
date: 2026-03-02
permalink: /posts/2026/03/setting_up_dotnet8_dev_environment/
tags:
  - dotnet
  - dotnet8
  - aspnetcore
  - webapi
  - beginner
  - fundamentals
---
Setting Up Your .NET 8 Development Environment

## SDK Installation, VS Code / Visual Studio Setup, and .NET CLI Deep Dive

A properly configured development environment is the foundation of
efficient, scalable, and production-ready .NET development. Whether you
are building console apps, enterprise APIs, microservices, or
cloud-native systems, your tooling must be correctly installed and
understood.

This guide goes beyond installation --- it explains *why* each component
matters and how they work together.

------------------------------------------------------------------------

# 1. Understanding the .NET Ecosystem

Before installation, it is important to understand the components:

## 1.1 .NET Runtime

Executes compiled .NET applications.

## 1.2 ASP.NET Core Runtime

Required specifically for web applications.

## 1.3 .NET SDK (Software Development Kit)

Includes: - Runtime - CLI (Command Line Interface) - Project templates -
MSBuild - Compilers (Roslyn) - NuGet tooling

> For development, always install the **SDK**, not just the runtime.

------------------------------------------------------------------------

# 2. Installing .NET 8 SDK (LTS)

.NET 8 is a **Long-Term Support (LTS)** release, meaning: - 3 years of
support - Enterprise-ready stability - Security patches and performance
updates

## 2.1 Download

Official site:\
https://dotnet.microsoft.com/download

Select **.NET 8 SDK** for your OS: - Windows (x64 / ARM64) - macOS
(Intel / Apple Silicon) - Linux (Debian, Ubuntu, RHEL, etc.)

## 2.2 Installation

Run the installer and complete setup using default options unless
enterprise constraints require customization.

------------------------------------------------------------------------

## 2.3 Verify Installation

Open terminal / command prompt:

``` bash
dotnet --version
```

Expected:

``` text
8.0.xxx
```

Detailed environment information:

``` bash
dotnet --info
```

List installed SDKs:

``` bash
dotnet --list-sdks
```

List installed runtimes:

``` bash
dotnet --list-runtimes
```

------------------------------------------------------------------------

# 3. Setting Up Visual Studio Code (Cross-Platform Lightweight Setup)

VS Code is ideal for: - Microservices - Containerized development -
Cross-platform teams - Lightweight workflows

## 3.1 Install VS Code

Download from: https://code.visualstudio.com/

------------------------------------------------------------------------

## 3.2 Install Required Extensions

Search and install:

-   **C# Dev Kit**
-   **C# (Microsoft)**
-   **.NET Install Tool**
-   (Optional) Docker
-   (Optional) REST Client

These provide: - IntelliSense - Debugging - Solution Explorer -
Integrated test support - Project scaffolding

------------------------------------------------------------------------

## 3.3 Create First Project Using CLI

``` bash
dotnet new console -n DevSetupDemo
cd DevSetupDemo
code .
```

Run:

``` bash
dotnet run
```

------------------------------------------------------------------------

# 4. Setting Up Visual Studio 2022 (Full IDE Experience)

Recommended for: - Enterprise applications - Large solutions -
Debug-heavy development - Designers & profiling tools

## 4.1 Installation

Download from: https://visualstudio.microsoft.com/

Choose: - Community (Free) - Professional - Enterprise

------------------------------------------------------------------------

## 4.2 Select Workloads

During installation, choose:

-   ✔ ASP.NET and web development\
-   ✔ .NET desktop development\
-   ✔ Azure development (optional)\
-   ✔ .NET Multi-platform App UI (if needed)

This installs: - SDK - IIS Express - Debugger - Profilers - Azure
publishing tools

------------------------------------------------------------------------

## 4.3 Confirm Target Framework

Create a new project → ensure target framework is:

    .NET 8.0 (Long-term support)

------------------------------------------------------------------------

# 5. .NET CLI Deep Dive

Even when using an IDE, mastering the CLI improves productivity and
CI/CD automation skills.

------------------------------------------------------------------------

## 5.1 Creating Projects

Console:

``` bash
dotnet new console -n ConsoleApp
```

Web API:

``` bash
dotnet new webapi -n WebApiApp
```

MVC:

``` bash
dotnet new mvc -n MvcApp
```

List all templates:

``` bash
dotnet new list
```

------------------------------------------------------------------------

## 5.2 Building Applications

``` bash
dotnet build
```

Output directory:

    bin/Debug/net8.0/

------------------------------------------------------------------------

## 5.3 Running Applications

``` bash
dotnet run
```

Run specific project:

``` bash
dotnet run --project WebApiApp.csproj
```

------------------------------------------------------------------------

## 5.4 Managing Dependencies (NuGet)

Add package:

``` bash
dotnet add package Serilog
```

Restore packages:

``` bash
dotnet restore
```

Remove package:

``` bash
dotnet remove package Serilog
```

------------------------------------------------------------------------

# 6. Understanding Project Structure

Example:

    ConsoleApp/
    │
    ├── Program.cs
    ├── ConsoleApp.csproj
    ├── obj/
    └── bin/

------------------------------------------------------------------------

## 6.1 Minimal Program in .NET 8

``` csharp
Console.WriteLine("Development environment is ready!");
```

.NET 8 uses: - Top-level statements - Implicit usings - Nullable
reference types enabled by default

------------------------------------------------------------------------

# 7. Understanding the .csproj File

Example:

``` xml
<Project Sdk="Microsoft.NET.Sdk">

  <PropertyGroup>
    <OutputType>Exe</OutputType>
    <TargetFramework>net8.0</TargetFramework>
    <ImplicitUsings>enable</ImplicitUsings>
    <Nullable>enable</Nullable>
  </PropertyGroup>

</Project>
```

### Key Concepts

-   `TargetFramework` → Determines runtime compatibility\
-   `ImplicitUsings` → Reduces boilerplate imports\
-   `Nullable` → Enables compile-time null safety

------------------------------------------------------------------------

# 8. Creating and Running an ASP.NET Core Web API

``` bash
dotnet new webapi -n MyApi
cd MyApi
dotnet run
```

Open:

    https://localhost:5001/swagger

Swagger UI confirms: - Routing works - API is running - Development
certificate is trusted

------------------------------------------------------------------------

# 9. Using global.json for SDK Version Control

In team environments, SDK drift causes build inconsistencies.

Create version lock:

``` bash
dotnet new globaljson --sdk-version 8.0.100
```

Generated file:

``` json
{
  "sdk": {
    "version": "8.0.100"
  }
}
```

This ensures every developer and CI server uses the same SDK version.

------------------------------------------------------------------------

# 10. Environment Configuration

Check environment:

Windows:

``` bash
echo %ASPNETCORE_ENVIRONMENT%
```

Mac/Linux:

``` bash
echo $ASPNETCORE_ENVIRONMENT
```

Set development environment:

Windows:

``` bash
set ASPNETCORE_ENVIRONMENT=Development
```

Mac/Linux:

``` bash
export ASPNETCORE_ENVIRONMENT=Development
```

------------------------------------------------------------------------

# 11. Common Setup Issues & Solutions

### Issue: dotnet not recognized

-   Restart terminal
-   Check PATH variable
-   Reinstall SDK

### Issue: HTTPS certificate error

``` bash
dotnet dev-certs https --trust
```

### Issue: Port already in use

``` bash
dotnet run --urls="http://localhost:5055"
```

------------------------------------------------------------------------

# 12. Professional Setup Best Practices

-   Use .NET 8 LTS for production
-   Lock SDK using global.json
-   Learn CLI for automation
-   Keep SDK updated
-   Enable nullable reference types
-   Use consistent formatting (EditorConfig)

------------------------------------------------------------------------

# Conclusion

Your .NET 8 development environment is now fully configured and
production-ready.

You understand:

-   SDK vs Runtime
-   IDE setup (VS Code & Visual Studio)
-   CLI fundamentals
-   Project structure
-   Dependency management
-   Version control via global.json

This foundation prepares you for advanced topics such as: - Solution
architecture - Dependency Injection - Middleware pipeline - Minimal
APIs - Clean Architecture patterns

------------------------------------------------------------------------

**Next Article:** Project Structure and Solution Architecture in .NET 8