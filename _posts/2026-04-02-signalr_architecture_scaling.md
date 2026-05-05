---
title: 'Real-Time Systems in .NET: SignalR Architecture and Scaling'
date: 2026-04-02
permalink: /posts/2026/04/signalr_architecture_scaling/
tags:
  - dotnet
  - aspnetcore
  - signalr
  - realtime
  - advanced
---

This post covers real-time systems in .NET using SignalR. SignalR lets servers push messages to connected clients over WebSockets and fallback transports. It is useful for **notifications, dashboards, collaborative features, chat, live status updates, and workflow monitoring**.

What SignalR provides
------
SignalR abstracts connection management and real-time messaging.

Core concepts:
- hub: server-side entry point
- connection: a connected client
- group: named collection of connections
- client method: function invoked on the client

Basic hub:

```csharp
public sealed class NotificationsHub : Hub
{
    public async Task JoinTenantGroup(string tenantId)
    {
        await Groups.AddToGroupAsync(Context.ConnectionId, $"tenant:{tenantId}");
    }
}
```

Register and map:

```csharp
builder.Services.AddSignalR();

var app = builder.Build();

app.MapHub<NotificationsHub>("/hubs/notifications");
```

Sending messages
------
Send from outside a hub using `IHubContext`.

```csharp
public sealed class NotificationService(
    IHubContext<NotificationsHub> hubContext)
{
    public Task NotifyTenantAsync(string tenantId, string message)
    {
        return hubContext.Clients
            .Group($"tenant:{tenantId}")
            .SendAsync("notificationReceived", message);
    }
}
```

This is useful when background jobs or API endpoints need to push updates.

Groups
------
Groups are essential for targeting messages.

Examples:
- `tenant:acme`
- `order:42`
- `user:123`
- `dashboard:operations`

Groups are not a security boundary by themselves. You still need to authorize who can join a group.

Authentication and authorization
------
SignalR connections can use the same ASP.NET Core authentication system.

```csharp
app.MapHub<NotificationsHub>("/hubs/notifications")
   .RequireAuthorization();
```

Inside the hub, use claims to verify access:

```csharp
var tenantId = Context.User?.FindFirst("tenant_id")?.Value;
```

Do not let clients join arbitrary tenant or resource groups without server-side validation.

Scaling SignalR
------
Single-instance SignalR is straightforward. Multiple app instances need a backplane or managed service so messages reach clients connected to any instance.

Common options:
- Azure SignalR Service
- Redis backplane
- sticky sessions in limited scenarios

For large real-time systems, prefer managed SignalR infrastructure when it fits the cloud platform. It reduces connection scaling burden.

Common mistakes to avoid
------
Watch for these issues:
- sending messages to all clients when groups are required
- trusting client-supplied group names
- ignoring reconnect behavior
- assuming in-memory connection state works across multiple servers
- using SignalR for workflows that only need polling or ordinary HTTP

SignalR is best when users benefit from immediate updates. Design groups, authorization, and scale-out from the beginning.

------------------------------------------------------------------------

**Next Article:** Advanced Dependency Injection in .NET: Keyed Services, Decorators, and Composition Roots
