#!/usr/bin/env python3
# -*- coding: utf-8 -*-


"""
通知記録のためのモジュール

ローカルのファイルに通知済みの review_requested を保存
インスタンス 1 にすることで、常に同じ環境が使われるようにする
また、インスタンスがなくなるのは長時間使われなかった場合。そのときは通知記録が消えて OK なので問題ない
"""

import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

RECORD_FILE = "/tmp/notify_record.json"
g_record_dict = {}


def load():
    global g_record_dict
    record_file = Path(RECORD_FILE)
    if record_file.exists():
        contents = json.loads(record_file.read_text())
        g_record_dict = contents["records"]
    return g_record_dict


def store():
    record_file = Path(RECORD_FILE)
    record_file.write_text(json.dumps({"records": g_record_dict}))
