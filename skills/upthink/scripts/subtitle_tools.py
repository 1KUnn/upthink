#!/usr/bin/env python3
"""Inspect timestamped Bilibili subtitle JSON and reconcile punctuation proposals.

All operations are local and read-only. Output is written to stdout; redirect it
only when a persistent file is explicitly wanted.
"""
import argparse
import difflib
import json
import math
import re
import sys
import unicodedata
from pathlib import Path


def punctuation_or_space(char):
    return char.isspace() or unicodedata.category(char).startswith("P")


def reconcile(original, proposed):
    """Preserve every original character; accept only inserted punctuation/space."""
    matcher = difflib.SequenceMatcher(None, original, proposed, autojunk=False)
    out = []
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == "equal":
            out.append(original[i1:i2])
        elif tag == "insert":
            insertion = proposed[j1:j2]
            if all(punctuation_or_space(c) for c in insertion):
                out.append(insertion)
        else:
            out.append(original[i1:i2])
    result = "".join(out)
    # The original, including its existing punctuation, must remain a subsequence.
    it = iter(result)
    if not all(any(c == candidate for candidate in it) for c in original):
        raise ValueError("original characters were not preserved")
    return result


def load_subtitles(path):
    data = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    rows = data.get("body") if isinstance(data, dict) else None
    if not isinstance(rows, list) or not rows:
        raise ValueError("subtitle JSON needs a nonempty body array")
    previous = -1.0
    for index, row in enumerate(rows):
        if not isinstance(row, dict) or not isinstance(row.get("content"), str):
            raise ValueError(f"body[{index}] has no string content")
        start, end = row.get("from"), row.get("to")
        if (isinstance(start, bool) or isinstance(end, bool)
                or not isinstance(start, (int, float)) or not isinstance(end, (int, float))
                or not math.isfinite(start) or not math.isfinite(end)
                or start < 0 or end < start or start < previous):
            raise ValueError(f"body[{index}] has invalid or unordered timestamps")
        previous = start
    return rows


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    inspect = sub.add_parser("inspect", help="check structure and summarize timing")
    inspect.add_argument("subtitle_json")
    inspect.add_argument("--duration", type=float, help="video duration in seconds")
    find = sub.add_parser("find", help="find text in timestamped subtitle segments")
    find.add_argument("subtitle_json")
    find.add_argument("text")
    fix = sub.add_parser("reconcile", help="accept punctuation-only insertions")
    fix.add_argument("original_txt")
    fix.add_argument("proposed_txt")
    args = parser.parse_args()
    try:
        if args.command == "reconcile":
            print(reconcile(Path(args.original_txt).read_text(encoding="utf-8-sig"),
                            Path(args.proposed_txt).read_text(encoding="utf-8-sig")), end="")
            return 0
        rows = load_subtitles(args.subtitle_json)
        if args.command == "inspect":
            end = max(row["to"] for row in rows)
            result = {"segments": len(rows), "characters": sum(len(r["content"]) for r in rows),
                      "start_seconds": rows[0]["from"], "end_seconds": end}
            if args.duration is not None:
                if not math.isfinite(args.duration) or args.duration < 0:
                    raise ValueError("duration must be finite and nonnegative")
                result["duration_gap_seconds"] = round(args.duration - end, 3)
                result["note"] = "A gap does not by itself prove missing subtitles."
            print(json.dumps(result, ensure_ascii=False, indent=2))
        else:
            # Search across segment boundaries while preserving segment provenance.
            text = "".join(row["content"] for row in rows)
            spans, offset = [], 0
            for row in rows:
                end = offset + len(row["content"])
                spans.append((offset, end, row))
                offset = end
            matches = []
            for match in re.finditer(re.escape(args.text), text):
                touched = [row for start, end, row in spans if start < match.end() and end > match.start()]
                if touched:
                    matches.append({"from": touched[0]["from"], "to": touched[-1]["to"],
                                    "segments": [row["content"] for row in touched]})
            print(json.dumps(matches, ensure_ascii=False, indent=2))
        return 0
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
