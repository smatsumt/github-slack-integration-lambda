#!/usr/bin/env python3
# -*- coding: utf-8 -*-


def test_find_mentioned_user():
    import github_webhook_lambda
    r = github_webhook_lambda._find_mentioned_user("@hoge @huga text text")
    assert r == {"@hoge", "@huga"}

    r = github_webhook_lambda._find_mentioned_user("@hoge @hoge text text")
    assert r == {"@hoge"}

    r = github_webhook_lambda._find_mentioned_user("@hoge @huga text text test@test.com")
    assert r == {"@hoge", "@huga", "@test"}
