from __future__ import annotations

import json
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
RUNTIME = PROJECT_ROOT / 'runtime'


def _load(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding='utf-8'))
    except Exception:
        return {}
    return data if isinstance(data, dict) else {}


def _count(name: str) -> int:
    return int(_load(RUNTIME / name).get('count', 0) or 0)


def main() -> None:
    collect = _load(RUNTIME / 'collect_report.json')
    sources = collect.get('sources', []) if isinstance(collect.get('sources'), list) else []
    failed_sources = [row for row in sources if isinstance(row, dict) and str(row.get('status', '')).strip() != 'ok']

    publishable = _load(RUNTIME / 'top10_publishable.json')
    items = publishable.get('items', []) if isinstance(publishable.get('items'), list) else []
    summary_placeholders = [
        row.get('title', '') for row in items
        if isinstance(row, dict) and str(row.get('summary', '')).strip().startswith('[TEST]')
    ]

    report = {
        'collected_total': _count('collected_raw.json'),
        'candidate_count': _count('shortlist.json'),
        'drafted_count': _count('drafted_items.json'),
        'top10_count': _count('top10_publishable.json'),
        'mailbox_count': _count('executive_mailbox.json'),
        'failed_source_count': len(failed_sources),
        'failed_sources': [row.get('source_id', '') for row in failed_sources],
        'dashboard_exists': (RUNTIME / 'dashboard.html').exists(),
        'summary_placeholders': summary_placeholders,
    }
    print(json.dumps(report, ensure_ascii=False, indent=2))

    errors: list[str] = []
    if report['top10_count'] != 10:
        errors.append(f"top10_count={report['top10_count']}")
    if not report['dashboard_exists']:
        errors.append('dashboard_missing')
    if report['summary_placeholders']:
        errors.append('summary_placeholders_present')

    if errors:
        raise SystemExit('runtime check failed: ' + ', '.join(errors))


if __name__ == '__main__':
    main()
