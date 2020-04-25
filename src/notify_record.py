#!/usr/bin/env python3
# -*- coding: utf-8 -*-


"""
通知記録のためのモジュール

ローカルのファイルに通知済みの review_requested を保存
インスタンス 1 にすることで、常に同じ環境が使われるようにする
また、インスタンスがなくなるのは長時間使われなかった場合。そのときは通知記録が消えて OK なので問題ない
"""

import datetime
import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

RECORD_FILE = "/tmp/notify_record.json"
g_record_dict = {}

SEC_BORDER = 60


def load():
    global g_record_dict
    record_file = Path(RECORD_FILE)
    if record_file.exists():
        contents = json.loads(record_file.read_text())
        g_record_dict = contents["records"]
        logger.info(f"loaded {g_record_dict}")
    else:
        logger.info(f"{RECORD_FILE} does not exist")
    return g_record_dict


def query_pr_reviewers(pr_id):
    record = g_record_dict.get(str(pr_id))  # JSON 保存時の数値が文字列になるので、文字列で統一する
    if not record:
        return []
    record_dt = datetime.datetime.fromisoformat(record["datetime"])
    if SEC_BORDER < (datetime.datetime.now() - record_dt).seconds:
        return []
    return record["reviewers"]


def insert_pr_reviewers(pr_id, reviewers):
    now_str = datetime.datetime.now().isoformat()
    g_record_dict[str(pr_id)] = {"reviewers": reviewers, "datetime": now_str}  # JSON 保存時の数値が文字列になるので、文字列で統一する


def store():
    global g_record_dict
    logger.info(f"storeing info {g_record_dict}")
    record_file = Path(RECORD_FILE)
    g_record_dict = {k: v for k, v in g_record_dict.items()
                     if (datetime.datetime.now() - datetime.datetime.fromisoformat(v["datetime"])).seconds < SEC_BORDER}
    record_file.write_text(json.dumps({"records": g_record_dict}))
