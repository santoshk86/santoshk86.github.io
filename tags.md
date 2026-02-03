---
layout: page
title: Tags
permalink: /tags/
---

Browse posts by tag:

{% for tag in site.tags %}
## {{ tag[0] }}

<ul>
{% for post in tag[1] %}
  <li>
    <a href="{{ post.url }}">{{ post.title }}</a>
    <small>({{ post.date | date: "%b %d, %Y" }})</small>
  </li>
{% endfor %}
</ul>
{% endfor %}
