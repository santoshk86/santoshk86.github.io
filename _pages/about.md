---
permalink: /
title: ""
author_profile: true
redirect_from: 
  - /about/
  - /about.html
---

Principal Software Engineer | Full-Stack & Microsoft Technologies

---

17+ years of experience in software engineering, architecture, and technical leadership.

I design, build, and lead the development of scalable, secure, and high-performance enterprise applications using Microsoft technologies.
My work spans full-stack development, system architecture, cloud platforms, and engineering leadership, with a strong focus on long-term maintainability and business impact.

---

## Latest Technical Articles

<div class="articles-grid">

{% assign sorted_articles = site.data.articles | sort: "date" | reverse %}
{% for article in sorted_articles limit:2 %}

  <div class="article-card">
    <h3>{{ article.title }}</h3>
    <p>{{ article.description }}</p>
    <a href="{{ article.link }}" target="_blank" rel="noopener noreferrer">
      Read Article →
    </a>
  </div>

{% endfor %}

</div>

<p style="margin-top:20px;">
  <a href="/articles/">View All Articles →</a>
</p>

---

[Portfolio](/portfolio/) • [Blogs](/year-archive/) • [CV](/cv/)

