---
title: 'Project Structure in .NET 8: Solutions, .csproj, NuGet, and Build Outputs'
date: 2026-03-03
permalink: /posts/2026/03/project_structure_solutions_csproj_nuget_build_outputs/
tags:
  - dotnet
  - dotnet8
  - csharp
  - architecture
  - beginner
  - fundamentals
---

This post covers how a typical .NET codebase is organized. New developers often focus on `Program.cs` and controllers, but production projects are shaped just as much by **how solutions are split, how project files are configured, how packages are restored, and where compiled artifacts are written**. If you understand those four pieces, you can navigate almost any .NET repository with less guesswork.

What a .NET solution is
------
A solution (`.sln`) is a container for one or more projects. It does not compile code by itself. Instead, it helps you group projects, manage references between them, and open the whole workspace in Visual Studio or the CLI.

Common solution members:
- an ASP.NET Core Web API
- one or more class libraries
- test projects
- worker services or console apps
- shared build configuration files

A realistic setup might look like:

```text
StoreApp/
  StoreApp.sln
  src/
    StoreApp.Api/
      StoreApp.Api.csproj
    StoreApp.Application/
      StoreApp.Application.csproj
    StoreApp.Domain/
      StoreApp.Domain.csproj
    StoreApp.Infrastructure/
      StoreApp.Infrastructure.csproj
  tests/
    StoreApp.Application.Tests/
      StoreApp.Application.Tests.csproj
```

The solution makes it easy to build everything with one command:

```bash
dotnet build StoreApp.sln
```

Creating a solution from the CLI
------
The .NET CLI can build your initial structure in a few minutes:

```bash
dotnet new sln -n StoreApp

dotnet new webapi -n StoreApp.Api -o src/StoreApp.Api
dotnet new classlib -n StoreApp.Application -o src/StoreApp.Application
dotnet new classlib -n StoreApp.Domain -o src/StoreApp.Domain
dotnet new classlib -n StoreApp.Infrastructure -o src/StoreApp.Infrastructure
dotnet new xunit -n StoreApp.Application.Tests -o tests/StoreApp.Application.Tests

dotnet sln StoreApp.sln add src/StoreApp.Api/StoreApp.Api.csproj
dotnet sln StoreApp.sln add src/StoreApp.Application/StoreApp.Application.csproj
dotnet sln StoreApp.sln add src/StoreApp.Domain/StoreApp.Domain.csproj
dotnet sln StoreApp.sln add src/StoreApp.Infrastructure/StoreApp.Infrastructure.csproj
dotnet sln StoreApp.sln add tests/StoreApp.Application.Tests/StoreApp.Application.Tests.csproj
```

Now add project references so the application layers can talk to each other explicitly:

```bash
dotnet add src/StoreApp.Api/StoreApp.Api.csproj reference src/StoreApp.Application/StoreApp.Application.csproj
dotnet add src/StoreApp.Application/StoreApp.Application.csproj reference src/StoreApp.Domain/StoreApp.Domain.csproj
dotnet add src/StoreApp.Infrastructure/StoreApp.Infrastructure.csproj reference src/StoreApp.Application/StoreApp.Application.csproj
```

This is one of the most important habits in .NET: **make dependencies visible through project references instead of hidden through copied code**.

Understanding the `.csproj` file
------
Every .NET project has a project file, usually ending in `.csproj`. This XML file tells the SDK:
- which target framework to compile for
- whether the output is an executable or library
- which NuGet packages are required
- which other projects are referenced
- which build settings should be enabled

A simple Web API project file looks like:

```xml
<Project Sdk="Microsoft.NET.Sdk.Web">

  <PropertyGroup>
    <TargetFramework>net8.0</TargetFramework>
    <Nullable>enable</Nullable>
    <ImplicitUsings>enable</ImplicitUsings>
    <RootNamespace>StoreApp.Api</RootNamespace>
  </PropertyGroup>

  <ItemGroup>
    <ProjectReference Include="..\StoreApp.Application\StoreApp.Application.csproj" />
  </ItemGroup>

  <ItemGroup>
    <PackageReference Include="Microsoft.AspNetCore.OpenApi" Version="8.0.0" />
    <PackageReference Include="Swashbuckle.AspNetCore" Version="6.5.0" />
  </ItemGroup>

</Project>
```

Important properties to recognize:
- `Sdk` chooses the build logic. Web projects usually use `Microsoft.NET.Sdk.Web`.
- `TargetFramework` defines the runtime contract, such as `net8.0`.
- `Nullable` enables compile-time null safety.
- `ImplicitUsings` reduces repetitive `using` statements.
- `OutputType` appears in console apps and determines whether the project produces an executable.

Project references vs NuGet packages
------
A `.csproj` can depend on code in two main ways.

Use a `ProjectReference` when:
- the code lives in the same repository
- you want changes to compile together
- you control both sides of the dependency

Use a `PackageReference` when:
- the dependency is versioned and distributed as a package
- the code comes from a third-party library
- the dependency should be shared across many repos

Example:

```xml
<ItemGroup>
  <ProjectReference Include="..\StoreApp.Domain\StoreApp.Domain.csproj" />
  <PackageReference Include="Dapper" Version="2.1.35" />
</ItemGroup>
```

That distinction matters. Project references give you source-level integration. NuGet packages give you versioned distribution.

How NuGet fits into the build
------
NuGet is the package manager for .NET. When you run `dotnet restore`, the CLI:
- reads all `PackageReference` items
- resolves dependency versions
- downloads missing packages
- writes restore metadata into the `obj` folder

Common package commands:

```bash
dotnet add package Serilog.AspNetCore
dotnet remove package Serilog.AspNetCore
dotnet restore
dotnet list package
```

In modern SDK-style projects, `dotnet build` automatically performs restore if needed. Still, it is useful to know that restore is a separate phase, especially in CI pipelines.

What lives in `bin` and `obj`
------
Two folders appear after you build a project:

- `obj/` contains intermediate build data
- `bin/` contains the final compiled output

Example output after `dotnet build`:

```text
src/StoreApp.Api/
  bin/
    Debug/
      net8.0/
        StoreApp.Api.dll
        StoreApp.Api.exe
        appsettings.json
        Swashbuckle.AspNetCore.dll
  obj/
    Debug/
      net8.0/
        StoreApp.Api.AssemblyInfo.cs
        project.assets.json
```

What these folders are for:
- `obj` is used by MSBuild during compilation. It holds generated files and restore state.
- `bin` is what you normally run, inspect, or publish.

Important files you may see:
- `project.assets.json` in `obj` tracks resolved NuGet dependencies
- `.dll` files in `bin` are your compiled assemblies
- `.pdb` files contain debug symbols
- copied configuration files, such as `appsettings.json`, appear in output if marked appropriately

Debug vs Release builds
------
By default, `dotnet build` creates a Debug build. Debug is optimized for development, not performance. Release is optimized for deployment.

```bash
dotnet build -c Debug
dotnet build -c Release
```

The folder structure reflects that choice:

```text
bin/Debug/net8.0/
bin/Release/net8.0/
```

When you are troubleshooting locally, Debug is fine. When you are benchmarking or preparing deployment artifacts, build or publish in Release.

Build vs publish
------
New developers often confuse `build` and `publish`.

`dotnet build`:
- compiles the code
- produces assemblies in `bin`
- is intended mainly for development and CI validation

`dotnet publish`:
- prepares a deployable output
- copies only what is needed to run the app
- can generate framework-dependent or self-contained output

Example:

```bash
dotnet publish src/StoreApp.Api/StoreApp.Api.csproj -c Release -o publish
```

That `publish` folder is what you usually ship to a server, container build, or deployment pipeline.

A practical multi-project example
------
Suppose your API needs a service and a domain model:

```csharp
namespace StoreApp.Domain;

public sealed record Product(int Id, string Name, decimal Price);
```

```csharp
namespace StoreApp.Application;

using StoreApp.Domain;

public interface IProductService
{
    IReadOnlyList<Product> GetAll();
}

public sealed class ProductService : IProductService
{
    public IReadOnlyList<Product> GetAll() =>
    [
        new Product(1, "Mechanical Keyboard", 129.00m),
        new Product(2, "USB-C Dock", 89.00m)
    ];
}
```

Your API project can reference the application project and inject the service:

```csharp
var builder = WebApplication.CreateBuilder(args);

builder.Services.AddScoped<IProductService, ProductService>();

var app = builder.Build();

app.MapGet("/products", (IProductService service) => Results.Ok(service.GetAll()));

app.Run();
```

That separation is only possible because the solution and project references describe the structure clearly.

Useful build files beyond `.csproj`
------
As your repo grows, you will see more build-related files:

- `global.json` locks the SDK version
- `Directory.Build.props` centralizes shared MSBuild properties
- `Directory.Packages.props` centralizes NuGet package versions
- `NuGet.config` customizes package sources

You do not need all of them on day one, but you should recognize their purpose when you join an existing team.

Best practices for project structure
------
A solid baseline looks like this:
- keep one solution at the repo root
- group production code under `src/`
- group tests under `tests/`
- keep project names aligned with folders and namespaces
- prefer small, focused class libraries over one giant "shared" project
- use project references for internal code and package references for external dependencies
- avoid committing `bin/` and `obj/` to source control

If you understand the structure, you can answer questions faster:
- Where does this type come from?
- Which project owns this dependency?
- Why did restore fail?
- Which folder contains the files that will actually deploy?

------------------------------------------------------------------------

**Next Article:** C# Essentials for .NET Developers: Types, LINQ, and Async/Await
