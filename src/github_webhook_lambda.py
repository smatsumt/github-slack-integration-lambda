#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
GitHub WebHook で呼び出され、Slack に必要な通知を飛ばす

- mention された
- review request された
- review submitted された
"""

import logging
import json
import os

import slackweb

logger = logging.getLogger(__name__)

SLACK_URL = os.getenv("SLACK_URL")


def lambda_handler(event, context):
    _lambda_logging_init()
    body = event["body"]

    notify_slack()

    result = body
    logger.info(result)
    return {"statusCode": 200, "body": json.dumps({"result": "ok"})}


def notify_slack():
    slack = slackweb.Slack(url=SLACK_URL)
    slack.notify(text="Hi, <@smatsumoto>!")


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
