"""Publish owned-data acceptance only when all evidence matches current sources."""
import argparse
import hashlib
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def digest(path):
    return hashlib.sha256((ROOT / path).read_bytes()).hexdigest()


def checked_report(path):
    report = json.loads((ROOT / path).read_text(encoding='utf-8-sig'))
    assert report.get('passed'), f'Acceptance failed: {path}'
    hashes = report.get('source_sha256', {})
    assert hashes, f'Missing source provenance: {path}'
    for source, expected in hashes.items():
        assert digest(source) == expected, f'Stale evidence: {path}: {source}'
    return report


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--api-log', default='research/detail-owned-current-api.log')
    parser.add_argument('--ui-report', default='research/detail-owned-current-ui-verification.json')
    args = parser.parse_args()
    owned_path = 'research/detail-owned-acceptance.json'
    owned = checked_report(owned_path)
    rows = owned['cases']
    assert Counter(r['backend'] for r in rows) == {'native': 18, 'ptx': 18}
    assert all(r['passed'] and all(r['checks'].values()) for r in rows)
    controls = owned['positive_controls']
    assert len(controls) == 8 and all(all(c.values()) for c in controls.values())

    raw = (ROOT / args.api_log).read_bytes()
    log = raw.decode('utf-16' if raw.startswith(b'\xff\xfe') else 'utf-8-sig')
    reports = [json.loads(line) for line in log.splitlines() if line.startswith('{')]
    assert len(reports) == 1, 'Expected one successful API report'
    api = reports[0]
    assert api['passed'] and api['compute']['backend'] == 'cuda_detail'
    assert all(api['compute']['cpu_verification'].values())
    assert all(api[k] for k in ('normal_compare_gpu', 'board_gpu', 'cache_separated',
                               'unsupported_cpu_fallback', 'gauge_modes_separate',
                               'shooting_modes_separate', 'seed_cache_separated'))
    assert api['source_sha256'] and all(digest(p) == h for p, h in api['source_sha256'].items())
    api_path = 'research/detail-owned-current-api-verification.json'
    (ROOT / api_path).write_text(json.dumps(api, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

    ui = checked_report(args.ui_report)
    assert ui['backend'] == 'cuda_detail' and all(ui['cpu_verification'].values())
    build = json.loads((ROOT / 'app/detail_effects-sm86.json').read_text(encoding='utf-8'))
    assert build['source_sha256'] == digest('app/detail_effects.cu')
    assert build['binary_sha256'] == digest('app/detail_effects-sm86.cubin')
    report = dict(
        generated_at=datetime.now(timezone.utc).isoformat(), passed=True,
        abi=build['abi'], device=owned['device'], combined_cases=len(rows),
        backends=['native', 'ptx'], positive_controls=controls,
        cpu_trace_used_as_gpu_input=False,
        normal_api_total=api['total'], normal_ui_total=ui['total'],
        reports=[owned_path, api_path, args.ui_report],
        source_sha256={p: digest(p) for p in [owned_path, api_path, args.ui_report,
                                            'scripts/summarize-owned-acceptance.py']},
        limitations=[
            'Fictional owned growth; live BlaBlaLink import is not verified by this acceptance.',
            'Listed five-member squads and settings; not every character, favorite variant or combination.',
            'Unsupported GPU effects use the CPU fallback with the reason displayed.'
        ])
    output = ROOT / 'research/detail-owned-current-summary.json'
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(dict(passed=True, abi=report['abi'], combined_cases=len(rows)), ensure_ascii=True))


if __name__ == '__main__':
    main()
