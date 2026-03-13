---
title: 'Configuration and Secrets in .NET 8: appsettings.json, Environment Variables, and User Secrets'
date: 2026-03-05
permalink: /posts/2026/03/configuration_and_secrets_in_dotnet/
tags:
  - dotnet
  - dotnet8
  - aspnetcore
  - configuration
  - beginner
  - fundamentals
---

This post covers how configuration works in modern .NET applications and how to keep secrets out of source control. The core idea is simple: **settings should come from configuration providers, secrets should be stored outside your repo, and your code should read configuration through strongly typed options whenever possible**.

Why configuration matters
------
Applications rarely run with the same settings everywhere. Local development, test environments, staging, and production each need different values for:
- connection strings
- API keys
- logging levels
- feature flags
- third-party endpoints

Hard-coding these values leads to brittle deployments and leaked secrets. The .NET configuration system exists to solve that problem cleanly.

Default configuration providers in ASP.NET Core
------
When you create an ASP.NET Core app with:

```csharp
var builder = WebApplication.CreateBuilder(args);
```

the framework already wires up common configuration sources, including:
- `appsettings.json`
- `appsettings.{Environment}.json`
- user secrets in Development
- environment variables
- command-line arguments

Later providers override earlier ones. That means an environment variable can replace a value from `appsettings.json` without changing the file itself.

Using `appsettings.json`
------
`appsettings.json` holds default configuration for the application.

Example:

```json
{
  "ConnectionStrings": {
    "Default": "Server=localhost;Database=StoreDb;Trusted_Connection=True;TrustServerCertificate=True"
  },
  "Mail": {
    "Host": "smtp.example.com",
    "Port": 587,
    "Sender": "noreply@example.com"
  },
  "Features": {
    "EnableDetailedErrors": false
  },
  "Logging": {
    "LogLevel": {
      "Default": "Information",
      "Microsoft.AspNetCore": "Warning"
    }
  }
}
```

This file is the right place for:
- defaults
- non-sensitive settings
- environment-independent application behavior

It is not the right place for:
- API keys
- passwords
- production certificates
- any secret that would be dangerous if committed to Git

Environment-specific settings
------
You can override defaults with environment-specific files such as:

- `appsettings.Development.json`
- `appsettings.Staging.json`
- `appsettings.Production.json`

Example `appsettings.Development.json`:

```json
{
  "Features": {
    "EnableDetailedErrors": true
  },
  "Mail": {
    "Host": "localhost"
  }
}
```

If `ASPNETCORE_ENVIRONMENT=Development`, those values override the base file.

This is useful for:
- enabling verbose logs only in development
- using local infrastructure endpoints
- replacing real services with sandboxes or emulators

Reading configuration directly
------
You can access values through `builder.Configuration`:

```csharp
var builder = WebApplication.CreateBuilder(args);

string? connectionString =
    builder.Configuration.GetConnectionString("Default");

string? sender =
    builder.Configuration["Mail:Sender"];
```

This works, but it does not scale well if your code accesses many related values across many classes. That is where strongly typed options help.

Binding configuration to a class
------
Create a settings class:

```csharp
public sealed class MailOptions
{
    public const string SectionName = "Mail";

    public string Host { get; set; } = string.Empty;
    public int Port { get; set; }
    public string Sender { get; set; } = string.Empty;
}
```

Bind it in `Program.cs`:

```csharp
var builder = WebApplication.CreateBuilder(args);

builder.Services.Configure<MailOptions>(
    builder.Configuration.GetSection(MailOptions.SectionName));
```

Consume it in a service:

```csharp
using Microsoft.Extensions.Options;

public sealed class MailService(IOptions<MailOptions> options)
{
    private readonly MailOptions _mail = options.Value;

    public void PrintSettings()
    {
        Console.WriteLine($"{_mail.Host}:{_mail.Port} from {_mail.Sender}");
    }
}
```

This approach gives you:
- grouped settings
- one place to validate defaults
- clearer dependencies
- easier testing

Environment variables
------
Environment variables are essential in containers, CI/CD pipelines, and cloud deployments. They are easy to inject without modifying files on disk.

Nested keys use double underscores:

```text
ConnectionStrings__Default=Server=db;Database=StoreDb;User Id=app;Password=secret
Mail__Host=smtp.internal.local
Mail__Port=2525
```

Examples for Windows PowerShell:

```powershell
$env:ASPNETCORE_ENVIRONMENT="Development"
$env:Mail__Sender="dev@example.com"
dotnet run
```

Examples for bash:

```bash
export ASPNETCORE_ENVIRONMENT=Development
export Mail__Sender=dev@example.com
dotnet run
```

Because environment variables override JSON files, they are a common way to provide deployment-specific values without editing the app bundle.

User secrets for local development
------
User secrets are designed for local development only. They keep sensitive settings out of the project directory while still integrating with the .NET configuration system.

Initialize secrets in a project:

```bash
dotnet user-secrets init
```

Set a secret:

```bash
dotnet user-secrets set "ConnectionStrings:Default" "Server=localhost;Database=StoreDb;User Id=sa;Password=LocalDevOnly123!"
dotnet user-secrets set "Mail:Sender" "dev-secrets@example.com"
```

List stored secrets:

```bash
dotnet user-secrets list
```

Why user secrets matter:
- they do not live in `appsettings.json`
- they are loaded automatically in Development
- they reduce the chance of leaking credentials into source control

Important limitation: user secrets are **not** a production secret store. For production, use the secret system offered by your host or cloud platform.

A complete configuration example
------
The following setup reads JSON, environment variables, and options:

```csharp
var builder = WebApplication.CreateBuilder(args);

builder.Services
    .AddOptions<MailOptions>()
    .Bind(builder.Configuration.GetSection(MailOptions.SectionName))
    .Validate(o => !string.IsNullOrWhiteSpace(o.Host), "Mail host is required.")
    .Validate(o => o.Port > 0, "Mail port must be greater than zero.")
    .ValidateOnStart();

var app = builder.Build();

app.MapGet("/config-check", (IOptions<MailOptions> options) =>
{
    var mail = options.Value;

    return Results.Ok(new
    {
        mail.Host,
        mail.Port,
        mail.Sender
    });
});

app.Run();
```

That code keeps configuration outside of business logic and fails early if required settings are missing.

How configuration files reach build output
------
Files like `appsettings.json` are copied to the build output so the app can read them at runtime. You usually do not need to edit the `.csproj` for the default templates, but it is useful to know that MSBuild controls this behavior.

If you ever need a custom file copied to the output directory, you can configure it explicitly:

```xml
<ItemGroup>
  <None Update="seed-data.json">
    <CopyToOutputDirectory>PreserveNewest</CopyToOutputDirectory>
  </None>
</ItemGroup>
```

That tells the build system to place the file in `bin/Debug/net8.0/` or the matching Release directory.

Production guidance
------
A simple rule set works well:
- keep defaults in `appsettings.json`
- keep machine- or environment-specific overrides outside Git
- use environment variables or a platform secret store in hosted environments
- use user secrets only for local development
- validate required settings on startup so bad config fails fast

If your app runs in Azure, AWS, Kubernetes, or another platform, the same pattern still applies. The provider changes, but the design principle stays the same: **configuration is external, and secrets are never hard-coded**.

Common mistakes to avoid
------
Watch for these issues:
- storing passwords in `appsettings.json`
- checking user secrets into documentation or screenshots
- scattering raw string keys like `"Mail:Host"` across the entire codebase
- assuming development settings will exist in production
- delaying validation until the first live request fails

Configuration bugs are often simple, but they cause real outages. Treat configuration as part of application architecture, not as an afterthought.

------------------------------------------------------------------------

**Next Article:** Logging and Diagnostics in .NET 8: ILogger, Structured Logging, and Log Levels
