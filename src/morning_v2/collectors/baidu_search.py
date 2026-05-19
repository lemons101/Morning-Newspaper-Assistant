from __future__ import annotations

import json
from pathlib import Path
import subprocess
from typing import Any, Dict, List


def run_baidu_search(script_dir: Path, query: str, *, top_k: int, recency: str) -> List[Dict[str, Any]]:
    cmd = [
        "python3",
        "search.py",
        json.dumps({
            "query": query,
            "search_recency_filter": recency,
            "resource_type_filter": [{"type": "web", "top_k": top_k}],
        }, ensure_ascii=False),
    ]
    result = subprocess.run(cmd, cwd=str(script_dir), capture_output=True, text=True, timeout=30, check=False)
    if result.returncode != 0:
        return []
    lines = result.stdout.strip().splitlines()
    text = "\n".join(lines[1:]) if len(lines) > 1 else (lines[0] if lines else "")
    try:
        payload = json.loads(text)
    except Exception:
        return []
    return payload if isinstance(payload, list) else []
