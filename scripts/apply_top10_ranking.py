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
    parser = argparse.ArgumentParser(description="Apply ranked titles and build top10 publishable output.")
    parser.add_argument("--input", default=str(PROJECT_ROOT / "runtime" / "drafted_items.json"))
    parser.add_argument("--selected", default=str(PROJECT_ROOT / "runtime" / "top10_ranking_result.json"))
    parser.add_argument("--output", default=str(PROJECT_ROOT / "runtime" / "top10_publishable.json"))
    parser.add_argument("--report", default=str(PROJECT_ROOT / "runtime" / "top10_publishable_preview.md"))
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    input_path = Path(args.input)
    selected_path = Path(args.selected)
    if not input_path.exists():
        raise SystemExit(f"input not found: {input_path}")
    if not selected_path.exists():
        raise SystemExit(f"ranking result file not found: {selected_path}")

    input_payload = json.loads(input_path.read_text(encoding="utf-8"))
    selected_payload = json.loads(selected_path.read_text(encoding="utf-8"))
    items = input_payload.get("items", []) if isinstance(input_payload, dict) else []
    top10_titles = selected_payload.get("top10_titles", []) if isinstance(selected_payload, dict) else []
    if not isinstance(items, list) or not isinstance(top10_titles, list):
        raise SystemExit("invalid input format")

    ranking_map = {str(title).strip(): idx for idx, title in enumerate(top10_titles, 1) if str(title).strip()}
    publishable: List[Dict[str, Any]] = []
    for item in items:
        if not isinstance(item, dict):
            continue
        title = str(item.get("title", "")).strip()
        rank = ranking_map.get(title)
        if rank is None:
            continue
        publishable.append({
            "rank": rank,
            "item_id": str(item.get("item_id", "")).strip(),
            "title": str(item.get("title_zh", "")).strip() or title,
            "summary": str(item.get("summary_main", "")).strip(),
            "published_at": str(item.get("published_at", "")).strip(),
            "url": str(item.get("url", "")).strip(),
            "source_name": str(item.get("source_name", "")).strip(),
            "source_type": str(item.get("source_type", "")).strip(),
        })

    publishable.sort(key=lambda row: int(row.get("rank", 10**9)))
    write_json(Path(args.output), {
        "generated_at": utc_now_iso(),
        "input": str(input_path),
        "ranking_result_file": str(selected_path),
        "count": len(publishable),
        "items": publishable,
    })
    write_text(Path(args.report), _render_report(publishable))
    print(f"publishable items={len(publishable)}")
    print(f"wrote {args.output}")


def _render_report(items: List[Dict[str, Any]]) -> str:
    lines = [
        "# Top10 Publishable Preview",
        "",
        f"- generated_at: {utc_now_iso()}",
        f"- count: {len(items)}",
        "",
    ]
    for item in items:
        lines.append(
            f"{item.get('rank', '')}. {item.get('title', '')} "
            f"({item.get('published_at', '')})"
        )
    lines.append("")
    return "\n".join(lines)


if __name__ == "__main__":
    main()
