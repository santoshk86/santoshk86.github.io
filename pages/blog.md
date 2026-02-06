---
title: Blogs
permalink: /blog/
---

## Blog Posts

{% for post in site.posts %}
- **[{{ post.title }}]({{ post.url }})**
  <br>
  <small>{{ post.date | date: "%b %d, %Y" }} • {{ post.tags | join: ", " }}</small>
{% endfor %}
