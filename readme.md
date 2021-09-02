---
lang: en
permalink: /
---
# FamitsuWeeklySales
This repository provides weekly sales data collected from [Famitsu's website](https://www.famitsu.com/ranking/game-sales/). It is updated automatically by GitHub Actions.

In normal, Famitsu will update their data on 02:00 (UTC) every Friday. But in case of something going wrong, this repository will be updated on 15:00 (UTC, 24:00 JST) every Thursday and Friday.

Historical data (before 2021-08-16) was be updated from [Wayback Machine](https://web.archive.org/).

## List
* [Latest]({{ "latest.html" | relative_url }})
{% assign markdown_files = site.pages | where: "is_markdown", true | reverse %}{% for file in markdown_files %}{% assign this_year = file.from | date: "%Y" %}{% assign this_month = file.from | date: "%B" %}{% if this_year != last_year %}
### {{ this_year }}{% endif %}{% if this_month != last_month %}
#### {{ this_month }}{% endif %}
- [{{ file.from }} ~ {{ file.to }}]({{ file.url | relative_url }}) (W{{ file.from | date: "%W" }}){% assign last_month = this_month %}{% assign last_year = this_year %}{% endfor %}

## Links
- [Gematsu](https://www.gematsu.com/tag/famitsu-sales), archives from 2019-04-22
- [Perfectly Nintendo](https://www.perfectly-nintendo.com/japanese-sales-media-create-famitsu-dengeki/), archives from 2016 (together with data from Dengeki)