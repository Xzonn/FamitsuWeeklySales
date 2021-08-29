---
title: Latest
---
{% assign markdown_file = site.pages | where: "is_markdown", true | reverse %}{{ markdown_file[0].content }}