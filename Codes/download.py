#!/usr/bin/python3
# -*- coding: UTF-8 -*-

import datetime
import json
import os
import re
from typing import TypedDict
import requests
import time
from bs4 import BeautifulSoup

requests.packages.urllib3.util.ssl_.DEFAULT_CIPHERS = "ALL:@SECLEVEL=1"


class Software(TypedDict):
  rank: int
  is_new: bool
  platform: str
  title: str
  publisher: str
  num_past: int
  num_total: int
  sales_meter: str


class Hardware(TypedDict):
  rank: int
  platform: str
  num_past: int
  num_total: int


class PageInfo(TypedDict):
  software: list[Software]
  hardware: list[Hardware]
  date: tuple[int | None, int, int, int | None, int, int]


def try_write(path: str, text: str) -> bool:
  paths = path.split("/")
  sub_path = ""
  for i in paths[:-1]:
    sub_path += f"{i}/"
    if not os.path.exists(sub_path):
      os.mkdir(sub_path)
  with open(path, "w", -1, "utf-8") as f:
    f.write(text)
  print(f"Saved successfully: {path}\n  on `try_write`.")
  return True


def try_archive(url: str, proxies: dict[str, str] = {}, headers: dict[str, str] = {}) -> bool:
  print("Sleep 10 seconds\n  on `try_archive`.")
  try_archive_time = 10
  while try_archive_time:
    time.sleep(110 - 10 * try_archive_time)
    try:
      archive = requests.get(f"https://web.archive.org/save/{url}", proxies=proxies, headers=headers, timeout=80)
      if not archive.ok:
        print(f"Archived failed: {url}\n  {archive.status_code} {archive.reason}\n  on `try_archive`.")
        try_archive_time -= 1
        if try_archive_time == 0:
          return False
        else:
          continue
    except Exception as e:
      print(f"Error: {e}\n  on `try_archive`.")
      try_archive_time -= 1
      if try_archive_time == 0:
        return False
      else:
        continue
    print(f"Archived successfully: {url}\n  {archive.status_code} {archive.reason}\n  on `try_archive`.")
    return True
  return False


def parse_num(text: str) -> int | float:
  if not text:
    return 0
  try:
    parse = re.search(r"([\d,万億兆\.]+)", text).groups()[0]
    parse = re.sub(r"[,万億兆]", "", parse)
    return json.loads(parse)
  except Exception as e:
    print(f"Error: {e}\n  on `parse_num`.")
    return 0


def parse_date(date: str) -> tuple[int | None, int, int, int | None, int, int]:
  return tuple(
    (int(i) if i else None)
    for i in re.search(r"^(?:(\d+)年)?(\d+)月(\d+)日[~〜～](?:(\d+)年)?(\d+)月(\d+)日$", date).groups()
  )


def sub_name(date: tuple[int | None, int, int, int | None, int, int]) -> str:
  y1, m1, d1, y2, m2, d2 = date
  return f"{y1 or y2:04d}/{m1:02d}/{y1 or y2:04d}-{m1:02d}-{d1:02d}__{y2 or y1:04d}-{m2:02d}-{d2:02d}"


def download_html(url: str, proxies: dict[str, str] = {}, headers: dict[str, str] = {}) -> str:
  download = requests.get(url, proxies=proxies, headers=headers)
  text = download.content.decode("utf-8")
  parser = BeautifulSoup(text, "html.parser")
  try:
    body_class = re.search(r"ArticleDetailBody_articleBody_[_a-zA-Z0-9]+", text).group()
    body = parser.find(class_=body_class).get_text("\n")
    re.search(r"^(\d+)年(\d+)月(\d+)日～(\d+)年(\d+)月(\d+)日$", body).groups()
    print(f"Downloaded and parsed successfully: {url}\n  on `download_html`.")
  except Exception:
    try:
      date = parser.find(class_="article-body__contents").get_text()
      re.search(r"(?:(\d+)年)?(\d+)月(\d+)日[~〜～](?:(\d+)年)?(\d+)月(\d+)日", date).groups()
      print(f"Downloaded and parsed successfully: {url}\n  on `download_html`.")
    except Exception as e:
      print(f"Downloaded successfully: {url}\n  on `download_html`.")
      print(f"Error: {e}\n  on `download_html` when parsing date.")
      try_write(f"Html_Temp/{datetime.datetime.now().strftime('%Y%m%d%H%M%S%f')}.html", text)

  try_archive(url, proxies, headers)

  return text


def json_to_markdown(data: dict) -> str:
  if "software" in data:
    software = data["software"]
  else:
    software = []
  if "hardware" in data:
    hardware = data["hardware"]
  else:
    hardware = []
  y1, m1, d1, y2, m2, d2 = data["date"]
  now = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9))).isoformat(timespec="seconds")
  markdown_content = f"""---
from: {y1 or y2:04d}-{m1:02d}-{d1:02d}
to: {y2 or y1:04d}-{m2:02d}-{d2:02d}
top_30: {len(software) > 20}
top_10: {bool(hardware)}
last_modified_at: {now}
---
# Famitsu Sales: {y1 or y2:04d}-{m1:02d}-{d1:02d} ~ {y2 or y1:04d}-{m2:02d}-{d2:02d}
"""
  if software:
    markdown_content += """## Software
| Rank | Platform | Title | Publisher | Sales | Total | Rate | New |
| -: | -- | -- | -- | -: | -: | -: | -- |
"""
    for soft in software:
      markdown_content += "| {rank} | {platform} | {title} | {publisher} | {num_past:,} | {num_total:,} | {sales_meter} | {new} |\n".format(
        new=soft["is_new"] and "**New**" or "", **soft
      )
    markdown_content += "\n"
  if hardware:
    markdown_content += """## Hardware
| Rank | Platform | Sales | Total |
| -: | -- | -: | -: |
"""
    for hard in hardware:
      markdown_content += "| {rank} | {platform} | {num_past:,} | {num_total:,} |\n".format(**hard)
    markdown_content += "\n"

  return markdown_content.strip()


def save_markdown(data: PageInfo) -> bool:
  file_name = f"Json/{sub_name(data['date'])}.json"
  try:
    if os.path.exists(file_name):
      with open(file_name, "r", -1, "utf-8") as json_file:
        old_data = json.load(json_file)
        if old_data == data:
          return False
        else:
          if isinstance(old_data, list):
            old_software = old_data
          elif "software" in old_data:
            old_software = old_data["software"]
          else:
            old_software = []
          if "hardware" in old_data:
            old_hardware = old_data["hardware"]
          else:
            old_hardware = []
          if old_software and (("software" not in data) or (len(data["software"]) < len(old_software))):
            data.update({"software": old_software})
          if old_hardware and (("hardware" not in data) or (len(data["hardware"]) < len(old_hardware))):
            data.update({"hardware": old_hardware})
          if old_data.get("software") == data.get("software") and old_data.get("hardware") == data.get("hardware"):
            return False
  except Exception as e:
    print(f"Error: {e}\n  on `save_markdown`.")
  try_write(file_name, json.dumps(data, ensure_ascii=False))

  file_name = f"Markdown/{sub_name(data['date'])}.md"
  try_write(file_name, json_to_markdown(data))
  return True


def save_html(text:str, path:str, date:tuple[int | None, int, int, int | None, int, int]) -> bool:
  file_name = f"{path}/{sub_name(date)}.html"
  return try_write(file_name, text)


def download_software(proxies:dict[str,str]={}, headers:dict[str,str]={}) -> str:
  return download_html("https://www.famitsu.com/ranking/game-sales/", proxies, headers)


def parse_software(text: str) -> PageInfo:
  parser = BeautifulSoup(text, "html.parser")
  date = parse_date(parser.find(class_="heading__sub-text-body").get_text())

  cards = parser.find_all(class_="card-game-sale-rank")
  software: list[Software] = []
  for card in cards:
    info: Software = {
      "rank": parse_num(card.find(class_="icon-ranking").get_text()),
      "is_new": bool(card.find(class_="card-game-sale-rank__status-info")),
      "platform": card.find(class_="icon-console").get_text(),
      "title": card.find(class_="card-game-sale-rank__title").get_text(),
      "publisher": card.find(class_="card-game-sale-rank__publisher").get_text(),
      "num_past": parse_num(card.find(class_="card-game-sale-rank__sales-num-past").get_text()),
      "num_total": parse_num(card.find(class_="card-game-sale-rank__sales-num-total").get_text()),
      "sales_meter": card.find(class_="card-game-sale-rank__sales-meter-num").get_text(),
    }
    software.append(info)
  return {"software": software, "date": date,}


def download_hardware(index: int = 0, proxies: dict[str, str] = {}, headers: dict[str, str] = {}) -> str:
  download = requests.get(
    r"https://www.famitsu.com/api/search?type=article&q=%E3%82%BD%E3%83%95%E3%83%88%20%E3%83%8F%E3%83%BC%E3%83%89%20%E9%80%B1%E9%96%93%E8%B2%A9%E5%A3%B2%E6%95%B0&max=100&order=desc&platform=alldevice&page=1",
    proxies=proxies,
    headers=headers,
  )
  results = download.json()
  first_result = results["data"][index]
  article_id = first_result["id"]
  published_at = time.strptime(first_result["publishedAt"], "%Y-%m-%dT%H:%M:%S+09:00")
  link = f"https://www.famitsu.com/article/{published_at.tm_year:04d}{published_at.tm_mon:02d}/{article_id}"
  return download_html(link, proxies, headers)


def parse_hardware(text: str) -> PageInfo:
  parser = BeautifulSoup(text, "html.parser")
  body_class = re.search(r"ArticleDetailBody_articleBody_[_a-zA-Z0-9]+", text).group()
  body = parser.find(class_=body_class).get_text("\n")
  try:
    date = parse_date(re.search(r"(?<=集計期間は)(?:(\d+)年)?(\d+)月(\d+)日[~〜～](?:(\d+)年)?(\d+)月(\d+)日", body)[0])
  except TypeError:
    return {}
  if not (date[0] or date[3]):
    year = parse_num(parser.find("time").get("datetime")[0:4])
    date = (year, date[1], date[2], None, date[4], date[5])

  software_start = re.search(r"^\s*ソフト.*本数.*$\s*", body, re.M).end()
  software_all = re.findall(
    r"^\s*(\d+)位(?:（(.*?)）)?\s*([^　]*)　+(.*)\s*([\d万億兆]+)本\s*(?:（累計(?:販売本数)?：?\s*([\d万億兆]+)本）\s*)?／\s*(.*)\s*／\s*\d+年\d+月\d+日(?:発売)?\s*$",
    body[software_start:],
    re.M,
  )
  software: list[Software] = []
  for soft in software_all:
    info: Software = {
      "rank": parse_num(soft[0]),
      "is_new": soft[1] == "初登場",
      "platform": soft[2],
      "title": soft[3],
      "publisher": soft[6],
      "num_past": parse_num(soft[4]),
      "num_total": parse_num(soft[5]),
      "sales_meter": "",
    }
    if not info["num_total"]:
      if info["is_new"]:
        info["num_total"] = info["num_past"]
      else:
        info["num_total"] = -1
    software.append(info)

  hardware_start = re.search(r"^\s*ハード.*台数\s*$\s*", body, re.M).end()
  hardware_all = re.findall(
    r"^\s*(.*?)\s*／\s*([\d万億兆]+)台(?:\s*（累計(?:販売台数)?：?\s*([\d万億兆]+)台）\s*)?$",
    body[hardware_start:],
    re.M,
  )
  hardware_all.sort(key=lambda x: parse_num(x[1]), reverse=True)
  hardware: list[Hardware] = []
  for i, hard in enumerate(hardware_all):
    info: Hardware = {
      "rank": i + 1,
      "platform": hard[0],
      "num_past": parse_num(hard[1]),
      "num_total": parse_num(hard[2]),
    }
    if not info["num_total"]:
      info["num_total"] = -1
    hardware.append(info)
  return {
    "software": software,
    "hardware": hardware,
    "date": date,
  }


if __name__ == "__main__":
  headers = {
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 XzonnArchive/0.1"
  }

  # Test if proxies are needed
  proxies = {}
  try:
    google = requests.get(r"https://www.google.com/", headers=headers, timeout=5)
    if not google.ok:
      proxies = {"http": "http://127.0.0.1:7890/", "https": "http://127.0.0.1:7890/"}
      print("Proxies are needed")
  except Exception:
    proxies = {"http": "http://127.0.0.1:7890/", "https": "http://127.0.0.1:7890/"}
    print("Proxies are needed")

  software_text = download_software(proxies, headers)
  software = parse_software(software_text)
  hardware_text = download_hardware(0, proxies, headers)
  hardware = parse_hardware(hardware_text)
  if sub_name(software["date"]) == sub_name(hardware["date"]):
    if save_markdown({"software": software["software"], "hardware": hardware["hardware"], "date": software["date"]}):
      save_html(software_text, "Html_Top30", software["date"])
      save_html(hardware_text, "Html_Top10", hardware["date"])
  else:
    if save_markdown(software):
      save_html(software_text, "Html_Top30", software["date"])
    if save_markdown(hardware):
      save_html(hardware_text, "Html_Top10", hardware["date"])

  week_urls = [
    "https://www.famitsu.com/ranking/game-sales/last_week/",
    "https://www.famitsu.com/ranking/game-sales/before_last/",
  ]
  for week_url in week_urls:
    week_text = download_html(week_url, proxies, headers)
    week = parse_software(week_text)
    if save_markdown(week):
      save_html(week_text, "Html_Top30", week["date"])
