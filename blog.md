---
layout: page
title: Blog
permalink: /blog/
---

{% for post in paginator.posts %}
### [{{ post.title }}]({{ post.url }})
{{ post.excerpt }}
{% endfor %}

{% if paginator.total_pages > 1 %}
<nav>
  {% if paginator.previous_page %}
    <a href="{{ paginator.previous_page_path }}">Prev</a>
  {% endif %}
  {% if paginator.next_page %}
    <a href="{{ paginator.next_page_path }}">Next</a>
  {% endif %}
</nav>
{% endif %}
