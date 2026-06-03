# -*- coding: utf-8 -*-
"""
Linux.do 技术日报接入测试。
"""

import sys
import unittest

sys.path.insert(0, ".")

from content_items import CATEGORY_COMMUNITY, SOURCE_LINUX_DO, _linux_do_to_items
from linux_do_news import parse_linux_do_daily_html
from source_registry import get_source_by_content_source


SAMPLE_HTML = """
<!doctype html>
<html>
<head><title>linux.do 技术聚合日报</title></head>
<body>
  <div class="page-module__metaBar">
    <span>2026年6月2日星期二</span>
    <span>新帖 104 篇</span>
    <span>数据来源: linux.do 前沿快讯 + 人工智能 + 开发调优</span>
  </div>
  <p class="page-module__dailyHeadline">开发接入与工程实操，模型发布与能力变化成为当天主线</p>
  <p class="page-module__overview">今天整理出的 104 个话题，都是当天互动更集中的讨论。</p>
  <ul class="page-module__highlightList">
    <li>开发接入与工程实操是当天主线。</li>
  </ul>
  <section class="page-module__articleSection">
    <h4>1<!-- -->. <!-- -->开发接入与工程实操</h4>
    <p>开发调优相关内容更偏向可执行经验，包括接入方式、部署路径、工具链兼容和具体排障。</p>
    <ul class="page-module__articleLinks">
      <li>
        <a href="https://linux.do/t/topic/2289668">codex桌面端卡顿怎么解决啊</a>
        <span class="page-module__linkMeta">35 回复</span>
      </li>
      <li>
        <a href="/t/topic/2290307">悲报，team 也变成月限了</a>
        <span class="page-module__linkMeta">80 回复</span>
      </li>
    </ul>
  </section>
</body>
</html>
"""


class TestLinuxDoParser(unittest.TestCase):
    def test_parse_daily_html(self):
        report = parse_linux_do_daily_html(SAMPLE_HTML, "https://news.linuxe.top/")

        self.assertEqual(report["published_at"], "2026-06-02")
        self.assertEqual(report["daily_title"], "linux.do 技术聚合日报")
        self.assertEqual(len(report["items"]), 2)

        first = report["items"][0]
        self.assertEqual(first["title"], "codex桌面端卡顿怎么解决啊")
        self.assertEqual(first["reply_count"], 35)
        self.assertEqual(first["section_title"], "开发接入与工程实操")
        self.assertEqual(first["published_at"], "2026-06-02")

        second = report["items"][1]
        self.assertEqual(second["url"], "https://linux.do/t/topic/2290307")

    def test_content_item_adapter_and_source_registry(self):
        raw_items = parse_linux_do_daily_html(SAMPLE_HTML, "https://news.linuxe.top/")["items"]
        raw_items[0]["ai_summary"] = "这是一个关于 Codex 桌面端性能排障的社区讨论。"
        items = _linux_do_to_items(raw_items[:1])

        self.assertEqual(items[0]["source"], SOURCE_LINUX_DO)
        self.assertEqual(items[0]["category"], CATEGORY_COMMUNITY)
        self.assertEqual(items[0]["meta"]["reply_count"], 35)
        self.assertEqual(
            get_source_by_content_source(SOURCE_LINUX_DO)["id"],
            "linux-do",
        )


if __name__ == "__main__":
    unittest.main()
