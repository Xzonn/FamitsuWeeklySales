#!/usr/bin/python3
# -*- coding: UTF-8 -*-

import datetime
import json
import os
import re
import requests
from bs4 import BeautifulSoup

def try_write(path, text):
  paths = path.split("/")
  sub_path = ""
  for i in paths[:-1]:
    sub_path += f"{i}/"
    if not os.path.exists(sub_path):
      os.mkdir(sub_path)
  with open(path, "w", -1, "utf-8") as f:
    f.write(text)

def parse_num(text):
  try:
    parse = re.search(r"([\d,\.]+)", text).groups()[0]
    parse = parse.replace(",", "")
    return json.loads(parse)
  except Exception as e:
    print(f"Error: {e}")
    return 0

download = requests.get("https://www.famitsu.com/ranking/game-sales/")
text = download.content.decode("utf-8")
parser = BeautifulSoup(text, "html.parser")
file_name = f"Html/Temp/{datetime.date.today()}.html"
sub_name = ""
print(file_name)
try:
  date = parser.find(class_="heading__sub-text-body").get_text()
  print(date)
  y1, m1, d1, y2, m2, d2 = [int(i) for i in re.search(r"^(\d+)年(\d+)月(\d+)日～(\d+)年(\d+)月(\d+)日$", date).groups()]
  sub_name = f"{y1}/{m1}/{y1:04d}-{m1:02d}-{d1:02d}__{y2:04d}-{m2:02d}-{d2:02d}"
  file_name = f"Html/{sub_name}.html"
except Exception as e:
  print(f"Error: {e}")

try_write(file_name, text)

cards = parser.find_all(class_="card-game-sale-rank")
data = []
now = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9))).isoformat(timespec = "seconds")
markdown_content = f"""---
from: {y1:04d}-{m1:02d}-{d1:02d}
to: {y2:04d}-{m2:02d}-{d2:02d}
last_modified_at: {now}
---
# Famitsu Sales: {y1:04d}-{m1:02d}-{d1:02d} ~ {y2:04d}-{m2:02d}-{d2:02d}
| Rank | Platform | Title | Publisher | Sales | Total | Rate | New |
| -: | -- | -- | -- | -: | -: | -: | -- |
"""
for card in cards:
  info = {
    "rank": parse_num(card.find(class_="icon-ranking").get_text()),
    "is_new": bool(card.find(class_="card-game-sale-rank__status-info")),
    "platform": card.find(class_="icon-console").get_text(),
    "title": card.find(class_="card-game-sale-rank__title").get_text(),
    "publisher": card.find(class_="card-game-sale-rank__publisher").get_text(),
    "num_past": parse_num(card.find(class_="card-game-sale-rank__sales-num-past").get_text()),
    "num_total": parse_num(card.find(class_="card-game-sale-rank__sales-num-total").get_text()),
    "sales_meter": card.find(class_="card-game-sale-rank__sales-meter-num").get_text()
  }
  data.append(info)
  markdown_content += "| {rank} | {platform} | {title} | {publisher} | {num_past:,} | {num_total:,} | {sales_meter} | {new} |\n".format(new = info["is_new"] and "**New**" or "",**info)

file_name = f"Json/{sub_name}.json"
try_write(file_name, json.dumps(data, ensure_ascii=False))

file_name = f"Markdown/{sub_name}.md"
try_write(file_name, markdown_content)