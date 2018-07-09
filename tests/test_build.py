import datetime

from tomllib import aot
from tomllib import array
from tomllib import document
from tomllib import item
from tomllib import parse
from tomllib import table
from tomllib._utils import _utc


def test_build_example(example):
    content = example("example")

    doc = document()
    doc.comment("This is a TOML document. Boom.")
    doc.nl()
    doc.append("title", "TOML Example")

    owner = table()
    owner.append("name", "Tom Preston-Werner")
    owner.append("organization", "GitHub")
    owner.append("bio", "GitHub Cofounder & CEO\\nLikes tater tots and beer.")
    dob = owner.append("dob", datetime.datetime(1979, 5, 27, 7, 32, tzinfo=_utc))
    dob.comment("First class dates? Why not?")

    doc.append("owner", owner)

    database = table()
    database["server"] = "192.168.1.1"
    database["ports"] = [8001, 8001, 8002]
    database["connection_max"] = 5000
    database["enabled"] = True

    doc["database"] = database

    servers = table()
    alpha = servers.append("alpha", table())
    alpha.indent(2)
    alpha.comment(
        "You can indent as you please. Tabs or spaces. TOML don't care.", False
    )
    alpha.append("ip", "10.0.0.1")
    alpha.append("dc", "eqdc10")

    beta = servers.append("beta", table())
    beta.nl()
    beta.append("ip", "10.0.0.2")
    beta.append("dc", "eqdc10")
    beta.append("country", "中国").comment("This should be parsed as UTF-8")
    beta.indent(2)

    doc["servers"] = servers

    clients = doc.append("clients", table())
    clients["data"] = item([["gamma", "delta"], [1, 2]]).comment(
        "just an update to make sure parsers support it"
    )

    doc.nl()
    doc.comment("Line breaks are OK when inside arrays")
    doc["hosts"] = array(
        """[
  "alpha",
  "omega"
]"""
    )

    doc.nl()
    doc.comment("Products")

    products = aot()
    doc["products"] = products

    hammer = table().indent(2)
    hammer["name"] = "Hammer"
    hammer["sku"] = 738594937

    nail = table().indent(2)
    nail["name"] = "Nail"
    nail["sku"] = 284758393
    nail["color"] = "gray"

    products.append(hammer)
    products.append(nail)

    doc.nl()
    doc["float"] = 3.14
    doc["date"] = datetime.date(1979, 5, 27)
    doc["time"] = datetime.time(7, 32)

    assert content == doc.as_string()


def test_add_remove():
    content = ""

    doc = parse(content)
    doc.append("foo", "bar")

    assert (
        doc.as_string()
        == """foo = "bar"
"""
    )

    doc.remove("foo")

    assert doc.as_string() == ""
