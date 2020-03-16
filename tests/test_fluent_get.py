# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from datetime import datetime

import pytest
from tomlkit import parse
from tomlkit.toml_document import TOMLDocument
from tomlkit._utils import _utc

@pytest.fixture
def example_doc(example):
    content = example("example")

    doc = parse(content)
    return doc

def test_get_simple_key(example_doc):
    doc = example_doc

    assert doc.get("title") == "TOML Example"

    # owner
    owner = doc["owner"]
    assert doc.get("owner") == owner
    assert owner.get("bio") == "GitHub Cofounder & CEO\nLikes tater tots and beer."
    assert owner.get("dob") == datetime(1979, 5, 27, 7, 32, tzinfo=_utc)

    # database
    database = doc["database"]
    assert database.get("server") == "192.168.1.1"
    assert database.get("ports") == [8001, 8001, 8002]
    assert database.get("connection_max") == 5000
    assert database.get("enabled") is True

    # server
    beta = doc["servers"]["beta"]
    assert beta.get("country") == "中国"

#     # Null quoted keys
#     # tomlkit does not currently support this
#     content = """
# '' = "sqvalue"
# "" = "dqvalue"
# """
#     doc = parse(content)
#     assert doc.get("''") == "sqvalue"
#     assert doc.get('""') == "dqvalue"

def test_get_dotted_key(example_doc, example):
    doc = example_doc

    # owner
    assert doc.get("owner.bio") == "GitHub Cofounder & CEO\nLikes tater tots and beer."
    assert doc.get("owner.dob") == datetime(1979, 5, 27, 7, 32, tzinfo=_utc)

    # database
    assert doc.get("database.server") == "192.168.1.1"
    assert doc.get("database.ports") == [8001, 8001, 8002]
    assert doc.get("database.connection_max") == 5000
    assert doc.get("database.enabled") is True

    # server
    assert doc.get("servers.beta.country") == "中国"

    # clients
    assert doc.get("clients.data")[0] == ["gamma", "delta"]
    assert doc.get("clients.data")[1] == [1, 2]

    assert doc.get("clients.hosts") == ["alpha", "omega"]

    # # Products
    # assert doc.get("products.hammer") == {"name": "Hammer", "sku": 738594937}
    # assert doc.get("products.nail.name") == "Nail"
    # assert doc.get("products.nail.sku") == "284758393"

    doc2 = parse(example("0.5.0"))
    assert "color" in doc2.get("physical")
    assert "shape" in doc2.get("physical")
    assert doc2.get("physical.color") == "orange"
    assert doc2.get("physical.shape") == "round"

    assert "google.com" in doc2.get("site")
    assert doc2.get("site.'google.com'")

    assert doc2.get("a.b.c") == 1
    assert doc2.get("a.b.d") == 2
    assert doc2.get("table.a.c") == 3

def test_get_mixed_quote_key():
    content = """
[foo]
"bar.baz" = 1
"192.168.1.1" = 2

    [foo.'key.1']
    thing = 3
    "double.quote" = 4

[3]
    [3.1415]
    dotted = true
"""
    doc = parse(content)

    assert doc.get("foo.'bar.baz'") == 1
    assert doc.get('foo."192.168.1.1"') == 2
    assert doc.get("foo.'key.1'.thing") == 3
    assert doc.get("foo.'key.1'.'double.quote'") == 4
    assert doc.get("3.1415.dotted") is True

def test_get_defaults(example_doc):
    doc = example_doc

    assert doc.get("owner.notbio", "Requested key does not exist") == "Requested key does not exist"
    assert doc.get("notowner.bio", "Default value") == "Default value"
    assert doc.get("owner.bio.notatable", "Default value") == "Default value"

    content = """
[foo]
key = "value"
    [foo."123.456"]
    "432.123" = 1
"""

    doc = parse(content)

    assert doc.get("foo.'123.456'.'not.thekey'", "Default value") == "Default value"
    assert doc.get("foo.'not.thekey'.'432.123'", "Default value") == "Default value"
    assert doc["foo"]["123.456"]["432.123"] == 1
    assert doc.get("foo.'123.456'.'432.123'", "Default value") == 1