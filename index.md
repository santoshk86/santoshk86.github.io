---
title: Home
---

## Hi, I'm {{ site.data.profile.name }} 👋

{{ site.data.profile.summary }}

### Skills
{% for skill in site.data.profile.skills %}
- {{ skill }}
{% endfor %}
