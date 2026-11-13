"""Embed only Python-validated fiction data and report into the actual v0.5 workbench.

Never recompute ledger amounts in browser. Render only the deterministic Python
read-only evaluation; use --check in CI to prove fixture and HTML stay paired.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from konaklamaflow.hotel_ops import build_operations_report, validate_fictional_hotel  # noqa: E402

BEGIN="// BEGIN GENERATED_HOTEL_OPERATIONS"
END="// END GENERATED_HOTEL_OPERATIONS"


def safe_json(data):
    return (json.dumps(data,ensure_ascii=False,separators=(",",":"),allow_nan=False)
            .replace("&","\\u0026").replace("<","\\u003c").replace(">","\\u003e")
            .replace("\u2028","\\u2028").replace("\u2029","\\u2029"))


def embed(text,data,report):
    if text.count(BEGIN)!=1 or text.count(END)!=1:
        raise ValueError("Missing or ambiguous generated operational fixture markers")
    start=text.index(BEGIN)
    end=text.index(END,start)+len(END)
    block=(BEGIN+"\nconst HOTEL_OPS_DATA="+safe_json(data)+";\n"
           +"const HOTEL_OPS_REPORT="+safe_json(report)+";\n"+END)
    updated=text[:start]+block+text[end:]
    for left,right,filename in (
        ("/* BEGIN GENERATED_HOTEL_OPS_STYLES */",
         "/* END GENERATED_HOTEL_OPS_STYLES */","demo/hotel-ops-styles.css"),
        ("// BEGIN GENERATED_HOTEL_OPS_UI",
         "// END GENERATED_HOTEL_OPS_UI","demo/hotel-ops-module.js"),
    ):
        if updated.count(left)!=1 or updated.count(right)!=1:
            raise ValueError("Missing or ambiguous hotel operations source markers")
        start_at=updated.index(left)
        end_at=updated.index(right,start_at)+len(right)
        raw=(ROOT/filename).read_text(encoding="utf-8")
        block=left+"\n"+raw+"\n"+right
        updated=updated[:start_at]+block+updated[end_at:]
    return updated


def main(argv=None):
    parser=argparse.ArgumentParser()
    parser.add_argument("--check",action="store_true")
    args=parser.parse_args(argv)
    try:
        data=validate_fictional_hotel(json.loads(
            (ROOT/"examples/hotel-operations-fictional.json").read_text(encoding="utf-8")))
        report=build_operations_report(data)
        path=ROOT/"demo/v04-integrated-preview.html"
        actual=path.read_text(encoding="utf-8")
        expected=embed(actual,data,report)
        if actual!=expected:
            if args.check:
                print("Fictional hotel operations fixture out of sync",file=sys.stderr)
                return 1
            path.write_text(expected,encoding="utf-8")
        print("Integrated hotel operations fixture matches read-only Python reports.")
        return 0
    except (ValueError,OSError,TypeError,RecursionError,OverflowError):
        print("Could not safely generate fictional hotel operations",file=sys.stderr)
        return 2


if __name__=="__main__":
    raise SystemExit(main())
