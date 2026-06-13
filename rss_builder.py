# -*- coding: utf-8 -*-
"""
RSS 2.0 feed builder for the public API.
"""

import hashlib
from datetime import datetime, timezone
from email.utils import format_datetime
from xml.etree import ElementTree

CHANNEL_DESCRIPTION = "AI 与技术资讯聚合摘要"
CHANNEL_LINK = "https://www.gdufe888.top/ai/"
CHANNEL_TITLE = "每日AI前沿信息"


def build_rss_feed(snapshots):
    """Build an RSS 2.0 XML document from source snapshots."""
    rss = ElementTree.Element("rss", {"version": "2.0"})
    channel = ElementTree.SubElement(rss, "channel")
    _add_text(channel, "title", CHANNEL_TITLE)
    _add_text(channel, "link", CHANNEL_LINK)
    _add_text(channel, "description", CHANNEL_DESCRIPTION)

    feed_items = _flatten_snapshot_items(snapshots)
    latest_datetime = _latest_datetime(feed_items)
    if latest_datetime:
        _add_text(channel, "lastBuildDate", format_datetime(latest_datetime))

    for feed_item in sorted(feed_items, key=_sort_key, reverse=True):
        item_element = ElementTree.SubElement(channel, "item")
        _add_item_fields(item_element, feed_item)

    return ElementTree.tostring(
        rss,
        encoding="utf-8",
        xml_declaration=True,
    ).decode("utf-8")


def _flatten_snapshot_items(snapshots):
    feed_items = []
    for snapshot in snapshots or []:
        source = snapshot.get("source") or {}
        generated_at = _parse_datetime(snapshot.get("generated_at", ""))
        for item in snapshot.get("items", []) or []:
            feed_items.append({
                "item": item,
                "source": source,
                "generated_at": generated_at,
                "published_at": _parse_datetime(item.get("published_at", "")),
            })
    return feed_items


def _add_item_fields(item_element, feed_item):
    item = feed_item["item"]
    source = feed_item["source"]

    title = item.get("title", "")
    link = item.get("url", "")
    description = item.get("chinese_summary") or item.get("original_summary", "")
    pub_datetime = feed_item["published_at"] or feed_item["generated_at"]

    _add_text(item_element, "title", title)
    if link:
        _add_text(item_element, "link", link)
    if description:
        _add_text(item_element, "description", description)
    if pub_datetime:
        _add_text(item_element, "pubDate", format_datetime(pub_datetime))

    guid = _build_guid(item, source)
    guid_element = _add_text(item_element, "guid", guid["value"])
    guid_element.set("isPermaLink", guid["is_permalink"])

    category = item.get("category", "")
    source_label = source.get("label", "")
    if category:
        _add_text(item_element, "category", category)
    if source_label and source_label != category:
        _add_text(item_element, "category", source_label)


def _build_guid(item, source):
    url = item.get("url", "")
    if url:
        return {
            "value": url,
            "is_permalink": "true",
        }

    raw_value = "{}|{}".format(source.get("id", ""), item.get("title", ""))
    digest = hashlib.sha1(raw_value.encode("utf-8")).hexdigest()
    return {
        "value": "github-trending-spider:{}".format(digest),
        "is_permalink": "false",
    }


def _parse_datetime(value):
    if value is None:
        return None

    text = str(value).strip()
    if not text:
        return None

    if text.isdigit():
        try:
            return datetime.fromtimestamp(int(text), tz=timezone.utc)
        except (OverflowError, ValueError):
            return None

    iso_text = text.replace("Z", "+00:00")
    try:
        parsed_datetime = datetime.fromisoformat(iso_text)
    except ValueError:
        try:
            parsed_datetime = datetime.strptime(text, "%Y-%m-%d")
        except ValueError:
            return None

    if parsed_datetime.tzinfo is None:
        return parsed_datetime.replace(tzinfo=timezone.utc)
    return parsed_datetime.astimezone(timezone.utc)


def _latest_datetime(feed_items):
    datetimes = [
        feed_item["published_at"] or feed_item["generated_at"]
        for feed_item in feed_items
        if feed_item["published_at"] or feed_item["generated_at"]
    ]
    if not datetimes:
        return None
    return max(datetimes)


def _sort_key(feed_item):
    return feed_item["published_at"] or feed_item["generated_at"] or datetime.min.replace(
        tzinfo=timezone.utc,
    )


def _add_text(parent, tag, text):
    element = ElementTree.SubElement(parent, tag)
    element.text = str(text or "")
    return element
