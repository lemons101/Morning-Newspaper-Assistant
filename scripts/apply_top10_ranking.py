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
    top10_rank_ids = selected_payload.get("top10_rank_ids", []) if isinstance(selected_payload, dict) else []
    top10_item_ids = selected_payload.get("top10_item_ids", []) if isinstance(selected_payload, dict) else []
    top10_titles = selected_payload.get("top10_titles", []) if isinstance(selected_payload, dict) else []
    if not isinstance(items, list):
        raise SystemExit("invalid input format")

    rank_id_map = {}
    for item in items:
        if not isinstance(item, dict):
            continue
        rank_id = str(item.get("rank_id", "")).strip()
        if not rank_id:
            shortlist_rank = item.get("shortlist_rank")
            rank_id = f"ID{shortlist_rank}" if shortlist_rank is not None else ""
        if rank_id:
            rank_id_map[rank_id] = item
    item_id_map = {
        str(item.get("item_id", "")).strip(): item
        for item in items
        if isinstance(item, dict) and str(item.get("item_id", "")).strip()
    }
    title_map = {}
    for item in items:
        if not isinstance(item, dict):
            continue
        title = str(item.get("title", "")).strip()
        title_zh = str(item.get("title_zh", "")).strip()
        if title:
            title_map[title] = item
        if title_zh:
            title_map[title_zh] = item

    ordered_items: List[Dict[str, Any]] = []
    seen_item_ids: set[str] = set()

    def _append_item(rank: int, item: Dict[str, Any]) -> None:
        item_id = str(item.get("item_id", "")).strip()
        dedupe_key = item_id or str(item.get("title", "")).strip()
        if not dedupe_key or dedupe_key in seen_item_ids:
            return
        seen_item_ids.add(dedupe_key)
        ordered_items.append({
            "rank": rank,
            "item_id": item_id,
            "title": str(item.get("title_zh", "")).strip() or str(item.get("title", "")).strip(),
            "summary": str(item.get("summary_main", "")).strip(),
            "published_at": str(item.get("published_at", "")).strip(),
            "url": str(item.get("url", "")).strip(),
            "source_name": str(item.get("source_name", "")).strip(),
            "source_type": str(item.get("source_type", "")).strip(),
        })

    if isinstance(top10_rank_ids, list) and top10_rank_ids:
        for idx, rank_id in enumerate(top10_rank_ids, 1):
            item = rank_id_map.get(str(rank_id).strip())
            if item:
                _append_item(idx, item)
    elif isinstance(top10_item_ids, list) and top10_item_ids:
        for idx, item_id in enumerate(top10_item_ids, 1):
            item = item_id_map.get(str(item_id).strip())
            if item:
                _append_item(idx, item)
    elif isinstance(top10_titles, list) and top10_titles:
        for idx, title in enumerate(top10_titles, 1):
            item = title_map.get(str(title).strip())
            if item:
                _append_item(idx, item)

    publishable: List[Dict[str, Any]] = ordered_items

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
