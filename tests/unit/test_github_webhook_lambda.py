#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
from pathlib import Path
from unittest.mock import MagicMock

SCRIPT_PATH = Path(__file__).parent.resolve()


def test_find_mentioned_user():
    """ メッセージ中の mention を拾うことのテスト """
    import github_webhook_lambda

    # 通常のケース
    r = github_webhook_lambda._find_mentioned_user("@hoge @huga text text")
    assert r == {"@hoge", "@huga"}

    # 同じ人へのメンションはまとめる
    r = github_webhook_lambda._find_mentioned_user("@hoge @hoge text text")
    assert r == {"@hoge"}

    # e-mail の後ろの、、、除くべきだけど、この段階では拾うことにする
    # （GITHUT_TO_SLACK の ID 変換で対象なしとなるので、トータルでは問題ない）
    r = github_webhook_lambda._find_mentioned_user("@hoge @huga text text test@test.com")
    assert r == {"@hoge", "@huga", "@test"}


def test_notify_slack(monkeypatch):
    """ notify_slack で意図どおりに attachments が作られるかをテスト """
    import github_webhook_lambda
    mock = MagicMock()
    monkeypatch.setattr(github_webhook_lambda.slackweb, "Slack", MagicMock(return_value=mock))
    r = github_webhook_lambda.notify_slack("main message", attach_message="some attachment")

    name, args, kwargs = mock.mock_calls[0]
    assert name == "notify"
    assert kwargs["text"] == "main message"
    assert kwargs["attachments"] == [{'color': '#36a64f', 'mrkdwn_in': ['text'], 'text': 'some attachment'}]


def test_handler_issue_pr_mentioned(monkeypatch):
    """ handler_issue_pr_mentioned にサンプル入力を入れて動作確認 """
    mentioned_header_path = SCRIPT_PATH.parent / "testdata/mentioned-header.json"
    mentioned_body_path = SCRIPT_PATH.parent / "testdata/mentioned-body.json"
    header = json.loads(mentioned_header_path.read_text())
    body = json.loads(mentioned_body_path.read_text())

    import github_webhook_lambda
    mock = MagicMock()
    monkeypatch.setattr(github_webhook_lambda, "GITHUB_TO_SLACK", {"@smatsumt": "@smatsumt"})
    monkeypatch.setattr(github_webhook_lambda, "notify_slack", mock)
    r = github_webhook_lambda.handler_issue_pr_mentioned(header, body)

    args, kwargs = mock.call_args
    assert args[0] == ":wave: <@smatsumt>, *mentioned* by smatsumt in https://github.com/smatsumt/testrepo2/issues/1#issuecomment-619470010"
    assert kwargs["attach_message"] == "@smatsumt "


def test_handler_review_requested(monkeypatch):
    """ handler_issue_pr_mentioned にサンプル入力を入れて動作確認 """
    mentioned_header_path = SCRIPT_PATH.parent / "testdata/review-requested-header.json"
    mentioned_body_path = SCRIPT_PATH.parent / "testdata/review-requested-body.json"
    header = json.loads(mentioned_header_path.read_text())
    body = json.loads(mentioned_body_path.read_text())

    import github_webhook_lambda
    mock = MagicMock()
    monkeypatch.setattr(github_webhook_lambda, "GITHUB_TO_SLACK", {"@smatsumt": "@smatsumt", "@skawagt": "@skawagt", "@smatsumoto78": "@smatsumoto78"})
    monkeypatch.setattr(github_webhook_lambda, "notify_slack", mock)
    monkeypatch.setattr(github_webhook_lambda.notify_record, "query_pr_reviewers", MagicMock(return_value=[]))
    monkeypatch.setattr(github_webhook_lambda.notify_record, "insert_pr_reviewers", MagicMock())
    monkeypatch.setattr(github_webhook_lambda.notify_record, "store", MagicMock())
    r = github_webhook_lambda.handler_review_requested(header, body)

    args, kwargs = mock.call_args
    assert args[0] == ':triangular_flag_on_post: <@skawagt> <@smatsumoto78>, *review requested* by smatsumt in https://github.com/smatsumt/testrepo2/pull/3'
    assert kwargs["attach_message"] == ""


def test_handler_review_submitted(monkeypatch):
    """ handler_issue_pr_mentioned にサンプル入力を入れて動作確認 """
    mentioned_header_path = SCRIPT_PATH.parent / "testdata/review-submitted-header.json"
    mentioned_body_path = SCRIPT_PATH.parent / "testdata/review-submitted-body.json"
    header = json.loads(mentioned_header_path.read_text())
    body = json.loads(mentioned_body_path.read_text())

    import github_webhook_lambda
    mock = MagicMock()
    monkeypatch.setattr(github_webhook_lambda, "GITHUB_TO_SLACK", {"@smatsumt": "@smatsumt"})
    monkeypatch.setattr(github_webhook_lambda, "notify_slack", mock)
    r = github_webhook_lambda.handler_review_submitted(header, body)

    args, kwargs = mock.call_args
    assert args[0] == ':speech_balloon: <@smatsumt>, *review commented* by skawagt in https://github.com/smatsumt/testrepo2/pull/2#pullrequestreview-394584166'
    assert kwargs["attach_message"] == "yappari comment"


