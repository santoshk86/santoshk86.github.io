---
title: 'Authorization in ASP.NET Core: Policies, Roles, Claims, and Resource-Based Access'
date: 2026-03-13
permalink: /posts/2026/03/authorization_in_aspnetcore/
tags:
  - dotnet
  - dotnet8
  - aspnetcore
  - security
  - authorization
  - intermediate
---

This post covers the part of security that decides what an authenticated user is allowed to do. In ASP.NET Core, authorization usually builds on **roles, claims, named policies, and sometimes resource-specific checks performed in code**. If authentication answers "who are you?", authorization answers "may you do this?".

Role-based authorization
------
Roles are the simplest starting point. If your app already has obvious role categories such as `Admin`, `Manager`, or `Support`, role checks are easy to explain and quick to implement.

Controller example:

```csharp
[Authorize(Roles = "Admin")]
[HttpDelete("{id:int}")]
public IActionResult Delete(int id)
{
    return NoContent();
}
```

Minimal API example:

```csharp
app.MapDelete("/api/users/{id:int}", (int id) => Results.NoContent())
   .RequireAuthorization(policy => policy.RequireRole("Admin"));
```

Roles are useful, but they become coarse quickly. Many systems need more nuance than "admin or not".

Claims-based authorization
------
Claims are key-value facts about the authenticated user. Examples:
- `name`
- `email`
- `role`
- `department`
- `scope`
- `permission`

Policy example:

```csharp
builder.Services.AddAuthorization(options =>
{
    options.AddPolicy("CanReadReports", policy =>
        policy.RequireClaim("permission", "reports.read"));
});
```

Use the policy:

```csharp
[Authorize(Policy = "CanReadReports")]
[HttpGet("reports")]
public IActionResult GetReports()
{
    return Ok();
}
```

Claims-based authorization is more flexible than hard-coded roles because it lets the identity system express richer capabilities.

Using named policies
------
Policies are the preferred way to organize authorization logic. They let you define rules centrally and reuse them across endpoints.

Example setup:

```csharp
builder.Services.AddAuthorization(options =>
{
    options.AddPolicy("FinanceOnly", policy =>
    {
        policy.RequireAuthenticatedUser();
        policy.RequireClaim("department", "finance");
    });

    options.AddPolicy("AdminOrSupport", policy =>
    {
        policy.RequireRole("Admin", "Support");
    });
});
```

Apply them declaratively:

```csharp
[Authorize(Policy = "FinanceOnly")]
public IActionResult GetPayroll() => Ok();
```

Benefits of policies:
- rules are named
- repeated logic stays out of controllers
- changes happen in one central place

This scales far better than sprinkling ad hoc `if` checks through every action.

Resource-based authorization
------
Sometimes the rule depends on the specific resource, not just the user claims. Example:
- a user can edit their own profile
- a manager can view only orders for their region
- a document can be edited only by its owner

That is where resource-based authorization comes in.

Requirement:

```csharp
public sealed class DocumentOwnerRequirement : IAuthorizationRequirement
{
}
```

Handler:

```csharp
public sealed class DocumentOwnerHandler
    : AuthorizationHandler<DocumentOwnerRequirement, Document>
{
    protected override Task HandleRequirementAsync(
        AuthorizationHandlerContext context,
        DocumentOwnerRequirement requirement,
        Document resource)
    {
        var userId = context.User.FindFirst("sub")?.Value;

        if (userId is not null && resource.OwnerId == userId)
        {
            context.Succeed(requirement);
        }

        return Task.CompletedTask;
    }
}
```

Registration:

```csharp
builder.Services.AddAuthorization();
builder.Services.AddSingleton<IAuthorizationHandler, DocumentOwnerHandler>();
```

Usage in an endpoint:

```csharp
app.MapPut("/api/documents/{id:int}", async (
    int id,
    ClaimsPrincipal user,
    IAuthorizationService authorizationService,
    IDocumentRepository repository) =>
{
    var document = await repository.GetByIdAsync(id);
    if (document is null)
        return Results.NotFound();

    var authResult = await authorizationService.AuthorizeAsync(
        user,
        document,
        new DocumentOwnerRequirement());

    if (!authResult.Succeeded)
        return Results.Forbid();

    return Results.NoContent();
}).RequireAuthorization();
```

This is the right pattern when the answer depends on both the caller and the actual record being accessed.

`401` vs `403`
------
These two are often mixed up.

Use `401 Unauthorized` when:
- the caller is not authenticated
- the token is missing or invalid

Use `403 Forbidden` when:
- the caller is authenticated
- the caller is not allowed to perform the action

That distinction matters for clients and logs. One indicates "login problem"; the other indicates "permission problem".

Keep authorization logic out of business code where possible
------
A common anti-pattern is scattering permission checks across service methods with raw claim parsing. Prefer:
- named policies for broad reusable rules
- `IAuthorizationService` for resource checks
- thin controllers/endpoints that delegate clearly

This keeps security logic visible and consistent.

Common mistakes to avoid
------
Watch for these issues:
- using only roles when claims or resource checks are needed
- mixing up authentication failures and authorization failures
- duplicating policy logic inline across many endpoints
- trusting client-supplied flags instead of server-side user claims

Authorization is where security becomes domain-specific. The framework gives you the building blocks, but you still need clear rules and consistent usage.

------------------------------------------------------------------------

**Next Article:** EF Core Fundamentals: DbContext, Migrations, Tracking, and Relationships
