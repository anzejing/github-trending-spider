# -*- coding: utf-8 -*-
"""
RSS builder tests.
"""

import sys
import unittest
from email.utils import parsedate_to_datetime
from xml.etree import ElementTree

sys.path.insert(0, ".")

from rss_builder import build_rss_feed  # noqa: E402


class TestRssBuilder(unittest.TestCase):
    def test_builds_valid_rss_xml(self):
        xml_text = build_rss_feed([
            {
                "generated_at": "2026-06-13T10:00:00",
                "source": {
                    "id": "openai",
                    "label": "OpenAI",
                },
                "items": [
                    {
                        "title": "A & B < C",
                        "url": "https://example.com/a",
                        "published_at": "2026-06-13T09:00:00Z",
                        "category": "AI 官方更新",
                        "chinese_summary": "中文摘要 & 重点",
                        "original_summary": "Original summary",
                    }
                ],
            }
        ])

        root = ElementTree.fromstring(xml_text)
        channel = root.find("channel")
        item = channel.find("item")

        self.assertEqual(root.tag, "rss")
        self.assertEqual(root.attrib["version"], "2.0")
        self.assertEqual(channel.findtext("title"), "每日AI前沿信息")
        self.assertEqual(channel.findtext("link"), "https://www.gdufe888.top/ai/")
        self.assertEqual(item.findtext("title"), "A & B < C")
        self.assertEqual(item.findtext("description"), "中文摘要 & 重点")
        self.assertEqual(item.findtext("guid"), "https://example.com/a")
        self.assertEqual(item.find("guid").attrib["isPermaLink"], "true")
        self.assertEqual(parsedate_to_datetime(item.findtext("pubDate")).year, 2026)

    def test_falls_back_to_original_summary_and_generated_at(self):
        xml_text = build_rss_feed([
            {
                "generated_at": "2026-06-13T10:00:00",
                "source": {
                    "id": "hacker-news",
                    "label": "Hacker News",
                },
                "items": [
                    {
                        "title": "No link item",
                        "url": "",
                        "published_at": "unknown",
                        "category": "社区讨论",
                        "chinese_summary": "",
                        "original_summary": "Original fallback",
                    }
                ],
            }
        ])

        item = ElementTree.fromstring(xml_text).find("channel").find("item")

        self.assertEqual(item.findtext("description"), "Original fallback")
        self.assertEqual(item.find("guid").attrib["isPermaLink"], "false")
        self.assertEqual(parsedate_to_datetime(item.findtext("pubDate")).hour, 10)


if __name__ == "__main__":
    unittest.main()
