#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
GitHub WebHook で呼び出され、Slack に必要な通知を飛ばす

- mention された
- review request された
- review submitted された

参考 - GitHub の Event でふってくる JSON
      https://developer.github.com/enterprise/2.19/v3/activity/events/types/
"""

import logging
import json
import os
import re
import textwrap

import slackweb

logger = logging.getLogger(__name__)

SLACK_URL = os.getenv("SLACK_URL")

MENTION_REGEXP = r"@\w+"


def lambda_handler(event, context):
    _lambda_logging_init()
    headers = event["headers"]
    body = event["body"]
    logger.info(headers)
    logger.info(body)
    body = json.loads(body)

    handler_issue_pr_mentioned(headers, body)
    handler_review_requested(headers, body)
    handler_review_submitted(headers, body)

    return {"statusCode": 200, "body": json.dumps({"result": "ok"})}


def handler_review_requested(headers: dict, body: dict):
    """
    review_requested されたら通知
    :param headers:
    :param body:
    :return:
    """
    github_event_kind = headers["X-GitHub-Event"]
    if github_event_kind != "pull_request":
        return
    if body["action"] != "review_requested":
        return

    # 通知!
    message_url = body["pull_request"]["html_url"]
    reviewee = body["pull_request"]["user"]["login"]
    message = body["pull_request"]["body"]

    for u in body["pull_request"]["requested_reviewers"]:
        notify_message_format = textwrap.dedent("""
        <{user}>, review requested by {reviewee} in {url}
        ```
        {message}
        ```
        """)
        notify_message = notify_message_format.format(user=u, reviewee=reviewee, url=message_url, message=message)
        notify_slack(notify_message)


def handler_review_submitted(headers: dict, body: dict):
    """
    review が submit されたときに通知
    :param headers:
    :param body:
    :return:
    """
    github_event_kind = headers["X-GitHub-Event"]
    if github_event_kind != "pull_request_review":
        return
    if body["action"] != "submitted":
        return

    # 通知!
    message_url = body["review"]["html_url"]
    reviewer = body["review"]["user"]["login"]
    message = body["review"].get("body") or ""

    for u in body["pull_request"]["requested_reviewers"]:
        notify_message_format = textwrap.dedent("""
        <{user}>, review submitted by {reviewer} in {url}
        ```
        {message}
        ```
        """)
        notify_message = notify_message_format.format(user=u, reviewer=reviewer, url=message_url, message=message)
        notify_slack(notify_message)


def handler_issue_pr_mentioned(headers: dict, body: dict):
    """
    Issue, PR の本文・コメントで mention されたら通知

    :param headers:
    :param body:
    :return:
    """
    github_event_kind = headers["X-GitHub-Event"]
    if github_event_kind == "issue" or github_event_kind == "pull_request":
        data_key = github_event_kind
    elif github_event_kind == "issue_comment" or github_event_kind == "pull_request_review_comment":
        # PR コメントも issue_comment で飛んでくる
        data_key = "comment"
    else:
        return

    # コメント本文から mentioned_user を取得
    if body["action"] == "created":
        mentioned_user = _find_mentioned_user(body[data_key]["body"])
    elif body["action"] == "edited":
        mentioned_user_all = _find_mentioned_user(body[data_key]["body"])
        mentioned_user_before = _find_mentioned_user(body["changes"].get("body", {}).get("from", ""))
        mentioned_user = mentioned_user_all - mentioned_user_before  # 新しく加わった mention だけを対象にする
    else:
        return  # deleted など、ほかイベントのときは何もしない

    # 通知!
    message_url = body[data_key]["html_url"]
    commenter = body[data_key]["user"]["login"]
    message = body[data_key]["body"]

    for u in mentioned_user:
        notify_message_format = textwrap.dedent("""
        <{user}>, mentioned by {commenter} in {url}
        ```
        {message}
        ```
        """)
        notify_message = notify_message_format.format(user=u, commenter=commenter, url=message_url, message=message)
        notify_slack(notify_message)


def _find_mentioned_user(text: str) -> set:
    """
    テキストから、 "@hogehoge" な文字列を探す
    :param text:
    :return: "@hogehoge" の set
    """
    return set(re.findall(MENTION_REGEXP, text))


def notify_slack(text: str):
    """
    mention する場合、 "<@username>" と <> で囲う必要があることに注意
    :param text: Slack に入れる文字列
    :return:
    """
    slack = slackweb.Slack(url=SLACK_URL)
    slack.notify(text=text)


def _lambda_logging_init():
    """
    logging の初期化。LOGGING_LEVEL, LOGGING_LEVELS 環境変数を見て、ログレベルを設定する。
      LOGGING_LEVELS - "module1=DEBUG,module2=INFO" という形の文字列を想定。自分のモジュールのみ DEBUG にするときなどに利用
    """
    logging.getLogger().setLevel(os.getenv('LOGGING_LEVEL', 'INFO'))  # lambda の場合はロガー設定済みのためこちらが必要
    if os.getenv('LOGGING_LEVELS'):
        for mod_lvl in os.getenv('LOGGING_LEVELS').split(','):
            mod, lvl = mod_lvl.split('=')
            logging.getLogger(mod.strip()).setLevel(lvl.strip())
