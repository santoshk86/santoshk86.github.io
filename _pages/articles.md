---
layout: archive
title: "All Technical Articles"
author_profile: true
redirect_from: 
  - /articles/
  - /articles.html
---

{% assign sorted_articles = site.data.articles | sort: "date" | reverse %}

{% for article in sorted_articles %}
  <div style="margin-bottom: 25px;">
    <h3>{{ article.title }}</h3>
    <p>{{ article.description }}</p>
    <a href="{{ article.link }}" target="_blank" rel="noopener noreferrer">
      Read Article →
    </a>
  </div>
{% endfor %}
