"""Audit static caster references for every catalog actor; not GPU certification."""
import hashlib
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'app')]
import engine_worker
from calculator import buff_manager,timeline
from portable_burst_charge_specs import from_roster,pack
from portable_specs import LIMITS as L
from portable_runtime import double_words


def main():
    names=[n for n,data in engine_worker.META.items() if isinstance(data,dict)
           and not n.startswith(('_','test_')) and not engine_worker.spec.is_preview(n)]
    assert len(names)==203
    rows=[]
    for name in names:
        ref=from_roster([dict(name=name)])[0]
        words=[0]*L['INPUT_WORDS'];pack(words,[ref]*5,L,double_words)
        expected_mask=31 if 'burst_energy_raw' in ref else 0
        assert words[L['BURST_REFERENCE_BASE']:L['BURST_REFERENCE_BASE']+2]==[1,expected_mask]
        effective=ref.get('burst_energy',0);raw=ref.get('burst_energy_raw',effective/2)
        rows.append(dict(character=name,reference=ref,effective_raw=raw,
                         raw_is_half=raw==effective/2,
                         timeline_metadata_energy=timeline._NIKKE[name].get('burst_energy',0)))
    paths=['app/portable_burst_charge_specs.py','research/audit-burst-reference-inputs.py',
           'research/upstream/nikke-calc-master/calculator/buff_manager.py',
           'research/upstream/nikke-calc-master/calculator/timeline.py']
    report=dict(passed=True,cpu_only=True,characters=len(rows),cases=rows,
        missing_raw=sum('burst_energy_raw' not in r['reference'] for r in rows),
        raw_not_half=sum(not r['raw_is_half'] for r in rows),
        maximum_energy=max(r['reference'].get('burst_energy',0) for r in rows),
        maximum_effective_raw=max(r['effective_raw'] for r in rows),
        scope='Original static caster reference input/range audit only. No battle, equipment/favorite variant or GPU certification.',
        source_sha256={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in paths})
    (ROOT/'research/portable-burst-reference-catalog-audit.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print({k:report[k] for k in ('passed','characters','missing_raw','raw_not_half','maximum_energy','maximum_effective_raw')})


if __name__=='__main__':main()
