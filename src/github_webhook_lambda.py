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

from collections import defaultdict
import json
import logging
import os
import re
import textwrap

import slackweb

import notify_record

logger = logging.getLogger(__name__)

SLACK_URL = os.getenv("SLACK_URL")

MENTION_REGEXP = r"@\w+"


GITHUB_TO_SLACK = {
    # "@smatsumt": "@smatsumoto"
}

# 絵文字の dict
NOTIFY_EMOTICON = defaultdict(lambda: ":bell:")
NOTIFY_EMOTICON.update({
    "mentioned": ":wave:",
    "review_requested": ":triangular_flag_on_post:",
    "commented": ":speech_balloon:",
    "changes_requested": ":construction:",
    "approved": ":white_check_mark:",
})


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
    logger.info("handler_review_requested fired")
    message_url = body["pull_request"]["html_url"]
    reviewee = body["pull_request"]["user"]["login"]
    message = body["pull_request"]["body"]
    icon = NOTIFY_EMOTICON["review_requested"]

    reviewers_at = [f"@{x['login']}" for x in body["pull_request"]["requested_reviewers"]]
    records = notify_record.load()
    notified_reviewers = records.get(body["pull_request"]["id"], {}).get("reviewers", [])
    logger.info(f"notified_reviewers = {notified_reviewers}")
    targets = set(reviewers_at) - set(notified_reviewers)
    records[body["pull_request"]["id"]] = {"reviewers": reviewers_at}
    notify_record.store()
    user = _mention_str(targets)
    if len(user) < 1:  # 対象者なければ通知しない
        logger.info("no mentioned_user. skipped")
        return
    if message:
        message = f"```{message}```"
    notify_message_format = textwrap.dedent("""
    {icon} {user}, *review requested* by {reviewee} in {url}
    {message}
    """)
    notify_message = notify_message_format.format(icon=icon, user=user, reviewee=reviewee, url=message_url, message=message)
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
    logger.info("handler_review_submitted fired")
    message_url = body["review"]["html_url"]
    reviewer = body["review"]["user"]["login"]
    message = body["review"].get("body") or ""
    state = body["review"]["state"]
    icon = NOTIFY_EMOTICON[state]

    # 本人の reveiw_submit （コメント時に発生）は無視
    reviewee = body["pull_request"]["user"]["login"]
    if reviewer == reviewee:
        logger.info(f"reviewer is same with reviewee, skiped. reviewer {reviewer}, reviewee {reviewee}")
        return

    u_at = f"@{body['pull_request']['user']['login']}"
    user = _mention_str([u_at])
    if message:
        message = f"```{message}```"
    notify_message_format = textwrap.dedent("""
    {icon} {user}, *review {state}* by {reviewer} in {url}
    {message}
    """)
    notify_message = notify_message_format.format(icon=icon, user=user, state=state, reviewer=reviewer, url=message_url, message=message)
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
    if body["action"] == "opened" or body["action"] == "created":
        mentioned_user = _find_mentioned_user(body[data_key]["body"])
    elif body["action"] == "edited":
        mentioned_user_all = _find_mentioned_user(body[data_key]["body"])
        mentioned_user_before = _find_mentioned_user(body["changes"].get("body", {}).get("from", ""))
        mentioned_user = mentioned_user_all - mentioned_user_before  # 新しく加わった mention だけを対象にする
    else:
        return  # deleted など、ほかイベントのときは何もしない

    # 通知!
    logger.info("handler_issue_pr_mentioned fired")
    message_url = body[data_key]["html_url"]
    commenter = body[data_key]["user"]["login"]
    message = body[data_key]["body"]
    icon = NOTIFY_EMOTICON["mentioned"]

    user = _mention_str(mentioned_user)
    if len(user) < 1:  # 対象者なければ通知しない
        logger.info("no mentioned_user. skipped")
        return
    if message:
        message = f"```{message}```"
    notify_message_format = textwrap.dedent("""
    {icon} {user}, *mentioned* by {commenter} in {url}
    {message}
    """)
    notify_message = notify_message_format.format(icon=icon, user=user, commenter=commenter, url=message_url, message=message)
    notify_slack(notify_message)


def _find_mentioned_user(text: str) -> set:
    """
    テキストから、 "@hogehoge" な文字列を探す
    :param text:
    :return: "@hogehoge" の set
    """
    return set(re.findall(MENTION_REGEXP, text or ""))


def _mention_str(users) -> str:
    """
    ユーザ名の list から、mention 用文字列を生成
    :param users:
    :return:
    """
    # 対象は GITHUB_TO_SLACK 登録済みユーザのみ
    uid_mention_strs = [f"<{GITHUB_TO_SLACK[x]}>" for x in users if x in GITHUB_TO_SLACK]
    r = " ".join(uid_mention_strs)
    return r


def notify_slack(text: str):
    """
    mention する場合、 "<@username>" と <> で囲う必要があることに注意
    :param text: Slack に入れる文字列
    :return:
    """
    slack = slackweb.Slack(url=SLACK_URL)
    slack.notify(text=text)
    logger.info(f"slack notify: {text}")


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
