#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GitHub + HN + TLDR AI 热点报告 Spider 主入口

协调 GitHub Trending 爬虫、Hacker News 数据获取、TLDR AI 抓取、AI 总结和邮件发送。
"""

import logging
import json
import sys
import time
from datetime import datetime

from config import EMAIL_SEND_TIMES, LOG_FILE, MAIL_TO_BY_TIME, OUTPUT_JSON_PATH, SEND_EMAIL_ENABLED

# ---------------------------------------------------------------------------
# 日志配置（全局初始化，其他模块通过 logging.getLogger 获取）
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE, encoding="utf-8"),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)


def _parse_email_send_times(value):
    """解析 HH:MM,HH:MM 格式的邮件发送时间白名单。"""
    result = set()
    for item in (value or "").split(","):
        text = item.strip()
        if not text:
            continue
        hour_text, minute_text = text.split(":", 1)
        hour = int(hour_text)
        minute = int(minute_text)
        if hour < 0 or hour > 23 or minute < 0 or minute > 59:
            raise ValueError("邮件发送时间超出范围: {}".format(text))
        result.add("{:02d}:{:02d}".format(hour, minute))
    return result


def _normalize_scheduled_time(scheduled_time):
    """把调度器传入的计划时间规整为 HH:MM。"""
    if scheduled_time is None:
        return ""
    if hasattr(scheduled_time, "strftime"):
        return scheduled_time.strftime("%H:%M")
    return str(scheduled_time).strip()[:5]


def _parse_recipient_list(value):
    """解析字符串或列表形式的收件人。"""
    if isinstance(value, str):
        return [item.strip() for item in value.split(",") if item.strip()]
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    return []


def _parse_mail_to_by_time(value):
    """解析按时间配置的收件人映射。"""
    if not value:
        return {}
    data = json.loads(value)
    if not isinstance(data, dict):
        raise ValueError("MAIL_TO_BY_TIME 必须是 JSON 对象")

    result = {}
    for time_text, recipients in data.items():
        allowed_times = _parse_email_send_times(str(time_text))
        if len(allowed_times) != 1:
            raise ValueError("MAIL_TO_BY_TIME 时间格式无效: {}".format(time_text))
        normalized_time = next(iter(allowed_times))
        result[normalized_time] = _parse_recipient_list(recipients)
    return result


def _email_send_decision(scheduled_time):
    """返回本次运行是否允许发邮件、日志原因和可选收件人列表。"""
    if not SEND_EMAIL_ENABLED:
        return False, "--- 邮件发送已关闭（SEND_EMAIL_ENABLED=false）---", None

    scheduled_text = _normalize_scheduled_time(scheduled_time)
    if not scheduled_text:
        return False, "--- 本次非定时调度触发，跳过邮件发送 ---", None

    if MAIL_TO_BY_TIME:
        try:
            recipients_by_time = _parse_mail_to_by_time(MAIL_TO_BY_TIME)
        except (TypeError, ValueError, json.JSONDecodeError) as e:
            return False, "--- MAIL_TO_BY_TIME 配置无效，跳过邮件发送: {} ---".format(e), None

        recipients = recipients_by_time.get(scheduled_text, [])
        if not recipients:
            return False, "--- 本次调度时间 {} 未配置收件人，跳过邮件发送 ---".format(
                scheduled_text,
            ), None

        return True, "--- 本次调度时间 {} 命中邮件收件人配置 ---".format(scheduled_text), recipients

    try:
        allowed_times = _parse_email_send_times(EMAIL_SEND_TIMES)
    except ValueError as e:
        return False, "--- 邮件发送时间配置无效，跳过邮件发送: {} ---".format(e), None

    if scheduled_text not in allowed_times:
        return False, "--- 本次调度时间 {} 不在 EMAIL_SEND_TIMES={} 中，跳过邮件发送 ---".format(
            scheduled_text,
            EMAIL_SEND_TIMES,
        ), None

    return True, "--- 本次调度时间 {} 命中邮件发送时间 ---".format(scheduled_text), None


def run_spider(scheduled_time=None):
    """执行一次完整采集流程。"""
    logger.info("=" * 60)
    logger.info("AI 后端专项信息源 Spider 启动 - %s", datetime.now().isoformat())
    if scheduled_time is not None:
        logger.info("本次计划调度时间: %s", _normalize_scheduled_time(scheduled_time))
    logger.info("=" * 60)

    # 延迟导入，确保日志配置已初始化
    from github_trending import fetch_trending, ai_summarize
    from hacker_news import fetch_hn_top_stories, fetch_all_comments, ai_summarize_hn
    from linux_do_news import fetch_linux_do_daily_items, ai_summarize_linux_do_items
    from v2ex import fetch_v2ex_hot_topics, fetch_topic_replies, ai_summarize_v2ex
    from tldr_ai import fetch_latest_tldr_ai_issue, ai_translate_tldr_ai
    from official_ai_sources import fetch_anthropic_news, fetch_infoq_ai_development, fetch_openai_news
    from content_items import build_all_content_items, summarize_content_items, write_content_json
    from content_store import persist_source_snapshots
    from email_builder import build_email_html
    from email_sender import send_email, send_failure_notify

    errors = []

    # ==========================
    # GitHub 阶段
    # ==========================
    logger.info("--- [GitHub] 开始爬取每日热点 ---")
    daily_repos = fetch_trending(since="daily")
    logger.info("每日热点: 获取到 %d 个仓库", len(daily_repos))
    if not daily_repos:
        errors.append("爬取 GitHub 每日热点失败")

    time.sleep(3)

    logger.info("--- [GitHub] 开始爬取每周热点 ---")
    weekly_repos = fetch_trending(since="weekly")
    logger.info("每周热点: 获取到 %d 个仓库", len(weekly_repos))
    if not weekly_repos:
        errors.append("爬取 GitHub 每周热点失败")

    # GitHub AI 总结
    if daily_repos:
        logger.info("--- [GitHub] AI 总结每日热点 ---")
        daily_repos = ai_summarize(daily_repos, "每日热点")
        time.sleep(5)

    if weekly_repos:
        logger.info("--- [GitHub] AI 总结每周热点 ---")
        weekly_repos = ai_summarize(weekly_repos, "每周热点")

    # ==========================
    # Hacker News 阶段
    # ==========================
    hn_stories = []
    logger.info("--- [HN] 开始获取 Top Stories ---")
    try:
        hn_stories = fetch_hn_top_stories()
        if hn_stories:
            logger.info("HN Top Stories: 获取到 %d 个帖子", len(hn_stories))

            logger.info("--- [HN] 开始获取评论 ---")
            hn_stories = fetch_all_comments(hn_stories)

            logger.info("--- [HN] AI 总结 ---")
            time.sleep(5)
            hn_stories = ai_summarize_hn(hn_stories)
        else:
            errors.append("获取 HN Top Stories 失败")
    except Exception as e:
        logger.error("HN 阶段异常: %s", e)
        errors.append("HN 阶段异常: {}".format(e))
        hn_stories = []

    # ==========================
    # Linux.do 技术日报阶段
    # ==========================
    linux_do_items = []
    logger.info("--- [Linux.do] 开始获取技术日报 ---")
    try:
        linux_do_items = fetch_linux_do_daily_items()
        if linux_do_items:
            logger.info("Linux.do 技术日报: 获取到 %d 条原帖", len(linux_do_items))

            logger.info("--- [Linux.do] AI 总结 ---")
            time.sleep(5)
            linux_do_items = ai_summarize_linux_do_items(linux_do_items)
        else:
            errors.append("获取 Linux.do 技术日报失败")
    except Exception as e:
        logger.error("Linux.do 阶段异常: %s", e)
        errors.append("Linux.do 阶段异常: {}".format(e))
        linux_do_items = []

    # ==========================
    # V2EX 阶段
    # ==========================
    v2ex_topics = []
    logger.info("--- [V2EX] 开始获取全站热帖 ---")
    try:
        v2ex_topics = fetch_v2ex_hot_topics()
        if v2ex_topics:
            logger.info("V2EX 热帖: 获取到 %d 个技术帖", len(v2ex_topics))

            logger.info("--- [V2EX] 开始获取回复 ---")
            v2ex_topics = fetch_topic_replies(v2ex_topics)

            logger.info("--- [V2EX] AI 总结 ---")
            time.sleep(5)
            v2ex_topics = ai_summarize_v2ex(v2ex_topics)
        else:
            errors.append("获取 V2EX 热帖失败")
    except Exception as e:
        logger.error("V2EX 阶段异常: %s", e)
        errors.append("V2EX 阶段异常: {}".format(e))
        v2ex_topics = []

    # ==========================
    # TLDR AI 阶段
    # ==========================
    tldr_items = []
    logger.info("--- [TLDR AI] 开始获取最新一期 ---")
    try:
        tldr_items = fetch_latest_tldr_ai_issue()
        if tldr_items:
            logger.info("TLDR AI: 获取到 %d 条精选内容", len(tldr_items))

            logger.info("--- [TLDR AI] 中文整理 ---")
            time.sleep(5)
            tldr_items = ai_translate_tldr_ai(tldr_items)
        else:
            errors.append("获取 TLDR AI 最新内容失败")
    except Exception as e:
        logger.error("TLDR AI 阶段异常: %s", e)
        errors.append("TLDR AI 阶段异常: {}".format(e))
        tldr_items = []

    # ==========================
    # 官方 AI / AI 工程实践阶段
    # ==========================
    openai_items = []
    logger.info("--- [OpenAI] 开始获取官方 News ---")
    try:
        openai_items = fetch_openai_news()
        if openai_items:
            logger.info("OpenAI News: 获取到 %d 条内容", len(openai_items))
        else:
            errors.append("获取 OpenAI News 失败")
    except Exception as e:
        logger.error("OpenAI 阶段异常: %s", e)
        errors.append("OpenAI 阶段异常: {}".format(e))
        openai_items = []

    anthropic_items = []
    logger.info("--- [Anthropic] 开始获取官方 Newsroom ---")
    try:
        anthropic_items = fetch_anthropic_news()
        if anthropic_items:
            logger.info("Anthropic News: 获取到 %d 条内容", len(anthropic_items))
        else:
            errors.append("获取 Anthropic News 失败")
    except Exception as e:
        logger.error("Anthropic 阶段异常: %s", e)
        errors.append("Anthropic 阶段异常: {}".format(e))
        anthropic_items = []

    infoq_items = []
    logger.info("--- [InfoQ] 开始获取 AI Development RSS ---")
    try:
        infoq_items = fetch_infoq_ai_development()
        if infoq_items:
            logger.info("InfoQ AI Development: 获取到 %d 条内容", len(infoq_items))
        else:
            errors.append("获取 InfoQ AI Development 失败")
    except Exception as e:
        logger.error("InfoQ 阶段异常: %s", e)
        errors.append("InfoQ 阶段异常: {}".format(e))
        infoq_items = []

    ai_source_items = openai_items + anthropic_items + infoq_items
    if ai_source_items:
        logger.info("--- [官方 AI / AI 工程实践] AI 摘要 ---")
        time.sleep(5)
        ai_source_items = summarize_content_items(ai_source_items, "AI 官方更新与 AI 工程实践")

    # ==========================
    # 判断是否有数据
    # ==========================
    if not daily_repos and not weekly_repos and not hn_stories and not linux_do_items and not v2ex_topics and not tldr_items and not ai_source_items:
        logger.error("所有数据源均获取失败")
        should_send_email, email_skip_reason, recipients = _email_send_decision(scheduled_time)
        if should_send_email:
            send_failure_notify(
                "所有数据源均获取失败：{}".format("; ".join(errors)),
                recipients=recipients,
            )
        else:
            logger.info(email_skip_reason)
        return False

    content_items = build_all_content_items(
        daily_repos,
        weekly_repos,
        hn_stories,
        v2ex_topics,
        tldr_items,
        ai_source_items,
        linux_do_items=linux_do_items,
    )

    logger.info("--- 写出统一 JSON ---")
    try:
        write_content_json(content_items, OUTPUT_JSON_PATH)
    except Exception as e:
        logger.error("统一 JSON 写出失败: %s", e)
        errors.append("统一 JSON 写出失败: {}".format(e))

    logger.info("--- 写出来源归档并刷新 Redis ---")
    try:
        store_result = persist_source_snapshots(content_items)
        logger.info("来源快照处理完成: %s", store_result)
    except Exception as e:
        logger.error("来源快照处理失败: %s", e)
        errors.append("来源快照处理失败: {}".format(e))

    # ==========================
    # 生成邮件并发送
    # ==========================
    should_send_email, email_skip_reason, recipients = _email_send_decision(scheduled_time)
    if not should_send_email:
        logger.info(email_skip_reason)
        if errors:
            logger.warning("部分数据源获取失败（已降级处理）: %s", errors)
        return True

    logger.info(email_skip_reason)

    logger.info("--- 生成邮件内容 ---")
    html = build_email_html(daily_repos, weekly_repos, hn_stories, v2ex_topics, tldr_items, content_items)

    today = datetime.now().strftime("%Y-%m-%d")
    subject = "AI 后端专项信息源报告 - {}".format(today)

    logger.info("--- 发送邮件 ---")
    success = send_email(html, subject, recipients=recipients)
    if success:
        logger.info("全部完成！")
    else:
        logger.error("邮件发送失败")
        send_failure_notify("邮件发送失败", recipients=recipients)
        return False

    if errors:
        logger.warning("部分数据源获取失败（已降级处理）: %s", errors)

    return True


def main():
    """命令行入口。"""
    success = run_spider()
    if not success:
        sys.exit(1)


if __name__ == "__main__":
    main()
