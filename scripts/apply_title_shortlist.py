from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any, Dict, List


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC = PROJECT_ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from morning_v2.common import write_json, write_text
from morning_v2.models import utc_now_iso


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Apply selected titles to content_enriched.json and build shortlist.")
    parser.add_argument("--input", default=str(PROJECT_ROOT / "runtime" / "content_enriched.json"))
    parser.add_argument("--selected", default=str(PROJECT_ROOT / "runtime" / "title_shortlist_result.json"))
    parser.add_argument("--output", default=str(PROJECT_ROOT / "runtime" / "shortlist.json"))
    parser.add_argument("--report", default=str(PROJECT_ROOT / "runtime" / "shortlist_preview.md"))
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    input_path = Path(args.input)
    selected_path = Path(args.selected)
    if not input_path.exists():
        raise SystemExit(f"input not found: {input_path}")
    if not selected_path.exists():
        raise SystemExit(f"selected titles file not found: {selected_path}")

    input_payload = json.loads(input_path.read_text(encoding="utf-8"))
    selected_payload = json.loads(selected_path.read_text(encoding="utf-8"))
    items = input_payload.get("items", []) if isinstance(input_payload, dict) else []
    selected_titles = selected_payload.get("selected_titles", []) if isinstance(selected_payload, dict) else []
    if not isinstance(items, list) or not isinstance(selected_titles, list):
        raise SystemExit("invalid input format")

    selected_map = {str(title).strip(): idx for idx, title in enumerate(selected_titles, 1) if str(title).strip()}
    shortlist: List[Dict[str, Any]] = []
    for item in items:
        if not isinstance(item, dict):
            continue
        title = str(item.get("title", "")).strip()
        rank = selected_map.get(title)
        if rank is None:
            continue
        row = dict(item)
        row["shortlist_rank"] = rank
        shortlist.append(row)

    shortlist.sort(key=lambda row: int(row.get("shortlist_rank", 10**9)))
    write_json(Path(args.output), {
        "generated_at": utc_now_iso(),
        "input": str(input_path),
        "selected_titles_file": str(selected_path),
        "count": len(shortlist),
        "items": shortlist,
    })
    write_text(Path(args.report), _render_report(shortlist, selected_titles))
    print(f"shortlist items={len(shortlist)}")
    print(f"wrote {args.output}")


def _render_report(items: List[Dict[str, Any]], selected_titles: List[str]) -> str:
    lines = [
        "# Shortlist Preview",
        "",
        f"- generated_at: {utc_now_iso()}",
        f"- selected_titles: {len(selected_titles)}",
        f"- matched_items: {len(items)}",
        "",
    ]
    for item in items:
        lines.append(
            f"{item.get('shortlist_rank', '')}. [{item.get('source_type', '')}] "
            f"{item.get('title', '')} ({item.get('fetch_status', '')}, len={item.get('body_length', 0)})"
        )
    lines.append("")
    return "\n".join(lines)


if __name__ == "__main__":
    main()
