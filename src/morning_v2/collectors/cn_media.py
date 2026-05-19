from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List
from urllib.parse import urlparse

from morning_v2.common import compact_text, positive_int
from morning_v2.models import RawItem

from .baidu_search import run_baidu_search
from .items import make_raw_item


def collect_cn_media(config: Dict[str, Any]) -> List[RawItem]:
    queries = config.get("queries", [])
    if not isinstance(queries, list):
        return []

    top_k = positive_int(config.get("search_top_k"), 10)
    news_count = positive_int(config.get("news_count"), 50)
    script_dir = Path(str(config.get("baidu_search_script_dir") or ""))
    if not script_dir.exists():
        raise FileNotFoundError(f"baidu-search script dir not found: {script_dir}")

    source = {
        "id": "cn_media_search",
        "source_name": config.get("source_name", "中文媒体搜索"),
        "source_group": config.get("source_group", "primary"),
        "source_type": config.get("source_type", "cn_media_search"),
    }
    items: List[RawItem] = []
    seen_urls: set[str] = set()

    for query in queries:
        if len(items) >= news_count:
            break
        query_text = compact_text(query)
        results = run_baidu_search(
            script_dir,
            query_text,
            top_k=top_k,
            recency=compact_text(config.get("recency_filter")) or "week",
        )
        for rank, raw in enumerate(results, 1):
            if len(items) >= news_count:
                break
            title = compact_text(raw.get("title"))
            url = compact_text(raw.get("url") or raw.get("link"))
            snippet = compact_text(raw.get("summary") or raw.get("snippet") or raw.get("content"))
            if not title or not url or url in seen_urls:
                continue
            seen_urls.add(url)
            items.append(make_raw_item(
                source,
                title=title,
                url=url,
                raw_snippet=snippet,
                raw_metadata={
                    "search_engine": "baidu-search",
                    "rank": rank,
                    "query": query_text,
                    "detected_source": detect_cn_media_source(query_text, url),
                },
            ))
    return items


def detect_cn_media_source(query: str, url: str) -> str:
    for name in ["机器之心", "新智元", "量子位"]:
        if name in query:
            return name
    host = urlparse(url).netloc.lower()
    if "jiqizhixin.com" in host:
        return "机器之心"
    if "aiera.com" in host:
        return "新智元"
    if "qbitai.com" in host:
        return "量子位"
    return host
