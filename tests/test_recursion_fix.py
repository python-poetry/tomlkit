"""
Test for recursion depth fix in tomlkit parser.
Verifies that deeply nested input raises ParseError instead of RecursionError.
"""
import sys
sys.path.insert(0, ".")  # Use local patched version if available

import tomlkit
from tomlkit.exceptions import TOMLKitError

def test_deeply_nested_arrays():
    """Deeply nested arrays should raise ParseError, not RecursionError."""
    payload = "x = " + "[" * 500 + "1" + "]" * 500
    try:
        tomlkit.parse(payload)
        print("[FAIL] No exception raised for 500-deep nested arrays")
    except RecursionError:
        print("[FAIL] RecursionError — fix not applied")
    except TOMLKitError as e:
        print(f"[PASS] ParseError raised: {e}")
    except Exception as e:
        print(f"[????] Unexpected: {type(e).__name__}: {e}")

def test_deeply_nested_inline_tables():
    """Deeply nested inline tables should raise ParseError, not RecursionError."""
    payload = "x = " + "{a = " * 200 + "1" + "}" * 200
    try:
        tomlkit.parse(payload)
        print("[FAIL] No exception raised for 200-deep nested inline tables")
    except RecursionError:
        print("[FAIL] RecursionError — fix not applied")
    except TOMLKitError as e:
        print(f"[PASS] ParseError raised: {e}")
    except Exception as e:
        print(f"[????] Unexpected: {type(e).__name__}: {e}")

def test_normal_nesting_still_works():
    """Reasonable nesting depth should still parse fine."""
    # 10 levels deep — well within limit
    payload = "x = " + "[" * 10 + "1" + "]" * 10
    try:
        doc = tomlkit.parse(payload)
        print(f"[PASS] 10-deep arrays parse OK")
    except Exception as e:
        print(f"[FAIL] Normal nesting broken: {e}")

    # 5 levels inline tables
    payload2 = 'x = {a = {b = {c = {d = {e = 1}}}}}'
    try:
        doc2 = tomlkit.parse(payload2)
        print(f"[PASS] 5-deep inline tables parse OK")
    except Exception as e:
        print(f"[FAIL] Normal inline tables broken: {e}")

def test_mixed_nesting():
    """Mixed arrays and inline tables at depth."""
    payload = "x = " + "[{a = " * 50 + "1" + "}]" * 50
    try:
        tomlkit.parse(payload)
        print("[PASS] 50-deep mixed nesting parsed (within default limit)")
    except RecursionError:
        print("[FAIL] RecursionError on mixed nesting")
    except TOMLKitError as e:
        print(f"[PASS] ParseError on mixed nesting: {e}")

if __name__ == "__main__":
    print("=== tomlkit recursion depth fix tests ===\n")
    test_normal_nesting_still_works()
    test_deeply_nested_arrays()
    test_deeply_nested_inline_tables()
    test_mixed_nesting()
    print("\nDone")
