#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import datetime
import json


def test_load_from_empty():
    import notify_record
    r = notify_record.load()
    assert r == {}


def test_load_with_record(tmp_path, monkeypatch):
    import notify_record
    record_file = tmp_path / "record.json"
    test_record = {
        "records": {
            "0000": {"reviewers": ["@aaa", "@bbb"], "datetime": "2020-04-25T21:50:00.000000"}
        }
    }
    record_file.write_text(json.dumps(test_record))
    monkeypatch.setattr(notify_record, "RECORD_FILE", str(record_file))

    r = notify_record.load()
    assert r == test_record["records"]


def test_store(tmp_path, monkeypatch):
    import notify_record
    record_file = tmp_path / "record.json"
    test_record = {
        "records": {
            "0000": {"reviewers": ["@aaa", "@bbb"], "datetime": datetime.datetime.now().isoformat()}
        }
    }
    monkeypatch.setattr(notify_record, "RECORD_FILE", str(record_file))
    monkeypatch.setattr(notify_record, "g_record_dict", test_record["records"])

    notify_record.store()
    r = json.loads(record_file.read_text())
    assert r == test_record


def test_store_fresh(tmp_path, monkeypatch):
    import notify_record
    record_file = tmp_path / "record.json"
    test_record = {
        "records": {
            "0000": {"reviewers": ["@aaa", "@bbb"], "datetime": "2020-04-20T20:00:00.000000"}
        }
    }
    monkeypatch.setattr(notify_record, "RECORD_FILE", str(record_file))
    monkeypatch.setattr(notify_record, "g_record_dict", test_record["records"])

    notify_record.store()
    r = json.loads(record_file.read_text())
    assert r == {"records": {}}


def test_load_and_store(tmp_path, monkeypatch):
    import notify_record
    record_file = tmp_path / "record.json"
    test_record = {
        "records": {
            "0000": {"reviewers": ["@aaa", "@bbb"], "datetime": datetime.datetime.now().isoformat()}
        }
    }
    record_file.write_text(json.dumps(test_record))
    monkeypatch.setattr(notify_record, "RECORD_FILE", str(record_file))

    records = notify_record.load()
    records["1111"] = {"reviewers": ["@aaa", "@bbb"], "datetime": datetime.datetime.now().isoformat()}
    notify_record.store()

    r = json.loads(record_file.read_text())
    assert "0000" in r["records"]
    assert "1111" in r["records"]
