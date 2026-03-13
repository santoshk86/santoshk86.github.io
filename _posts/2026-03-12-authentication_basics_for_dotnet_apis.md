---
title: 'Authentication Basics for .NET APIs: Cookies vs JWT vs OAuth2/OIDC'
date: 2026-03-12
permalink: /posts/2026/03/authentication_basics_for_dotnet_apis/
tags:
  - dotnet
  - dotnet8
  - aspnetcore
  - security
  - authentication
  - intermediate
---

This post gives an overview of the most common authentication approaches you will see in .NET applications: **cookies, JWT bearer tokens, and OAuth2/OIDC-based sign-in flows**. The important thing is not memorizing every protocol detail. The important thing is understanding what each approach is for and when it fits.

Authentication vs authorization
------
Authentication answers:

```text
Who is the user or client?
```

Authorization answers:

```text
What is that user or client allowed to do?
```

Do not mix them up. A request can be authenticated but still unauthorized for a specific operation.

Cookie authentication
------
Cookie authentication is common in server-rendered web apps and traditional browser-based applications. After sign-in, the server issues an authentication cookie and the browser sends it automatically on later requests.

Good fit:
- MVC apps
- Razor Pages
- server-rendered admin portals
- browser sessions where the server manages login state

Basic registration:

```csharp
builder.Services
    .AddAuthentication("Cookies")
    .AddCookie("Cookies", options =>
    {
        options.LoginPath = "/account/login";
        options.AccessDeniedPath = "/account/denied";
    });
```

Then in the pipeline:

```csharp
app.UseAuthentication();
app.UseAuthorization();
```

Benefits:
- natural fit for browser apps
- server controls session behavior
- easy integration with page-based login flows

Tradeoffs:
- not ideal for public APIs consumed by many non-browser clients
- requires CSRF awareness in browser scenarios
- feels less natural for mobile apps or separate SPA/API architectures

JWT bearer authentication
------
JWT bearer authentication is common for APIs. The client sends a bearer token in the `Authorization` header:

```text
Authorization: Bearer eyJ...
```

Typical API registration:

```csharp
builder.Services
    .AddAuthentication("Bearer")
    .AddJwtBearer("Bearer", options =>
    {
        options.Authority = "https://identity.example.com";
        options.Audience = "store-api";
    });
```

Why APIs often use bearer tokens:
- no cookie session is required
- mobile apps and SPAs can send tokens explicitly
- APIs can validate tokens issued by a central identity provider

Important idea:
- the API usually does not issue the token itself
- it validates a token issued by an authentication server or identity platform

JWTs are not automatically the right answer for every project. They are useful when you actually need token-based API access.

What OAuth2 and OpenID Connect do
------
OAuth2 is an authorization framework. OpenID Connect (OIDC) adds identity on top of it.

In practice:
- OAuth2 is about delegated access and access tokens
- OIDC is about user authentication and identity information

A common pattern is:
1. the user signs in through an external identity provider
2. the app receives tokens
3. the API validates the access token

Examples of identity providers:
- Microsoft Entra ID
- Auth0
- Okta
- IdentityServer-based platforms

When someone says "we use OAuth login", what they often really mean in modern web apps is "we use OIDC sign-in with OAuth2 token flows underneath".

Choosing between cookies, JWT, and OIDC
------
Use cookies when:
- the client is primarily a browser
- your server renders the UI or manages the session
- you want classic web-app sign-in behavior

Use JWT bearer tokens when:
- you are protecting APIs
- clients are SPAs, mobile apps, or other services
- tokens come from a trusted identity provider

Use OIDC when:
- users sign in through an external identity provider
- you need federated identity
- you want modern authentication flows for web apps

A typical real-world setup is mixed:
- the web frontend signs users in with OIDC
- the frontend gets tokens
- the backend API uses JWT bearer validation

That is common and not a contradiction.

Minimal pipeline setup
------
No matter which scheme you use, the middleware order matters:

```csharp
app.UseRouting();
app.UseAuthentication();
app.UseAuthorization();
```

If `UseAuthorization()` runs before authentication, authorization cannot evaluate the user identity correctly.

Common claims you will see
------
After successful authentication, ASP.NET Core builds a `ClaimsPrincipal`. That user principal often contains claims such as:
- subject identifier
- name
- email
- role
- scopes or permissions

You can inspect them in an endpoint:

```csharp
app.MapGet("/me", (ClaimsPrincipal user) =>
{
    return Results.Ok(new
    {
        Name = user.Identity?.Name,
        Claims = user.Claims.Select(c => new { c.Type, c.Value })
    });
}).RequireAuthorization();
```

This is useful when debugging token contents and identity mapping.

Common mistakes to avoid
------
Watch for these issues:
- choosing JWT just because it sounds modern
- using cookie auth for third-party API clients that are not browsers
- confusing OAuth2 with user authentication instead of delegated authorization
- skipping token validation settings such as authority and audience
- exposing APIs without `UseAuthentication()` and then wondering why `User` is empty

Authentication works best when the scheme matches the client type. The protocol should serve the app architecture, not the other way around.

------------------------------------------------------------------------

**Next Article:** Authorization in ASP.NET Core: Policies, Roles, Claims, and Resource-Based Access
