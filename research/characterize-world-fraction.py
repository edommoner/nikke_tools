"""Full-native fractional notification snapshot and ordering contract;GPU0."""
import hashlib,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','scripts','research')]
from world_fraction_cases import fixtures
from world_skill_native import inspect
from unittest.mock import patch

def main():
 rows=[]
 with patch('portable_backend.build',side_effect=AssertionError('GPU build forbidden')),patch('portable_backend.execute',side_effect=AssertionError('GPU execute forbidden')):
  for c in fixtures():
   n,t=inspect(c);rows.append(dict(name=c['name'],case=c,native=n,skill_trace=t))
 r=dict(passed=False,cases=rows,full_native_battles=len(rows),gpu_builds=0,gpu_executions=0,source_sha256={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in ['research/world_frame_native.py','research/world_fraction_native.py','research/world_fraction_cases.py','research/characterize-world-fraction.py']},full_goal_complete=False,full_character_verified=0,canonical_world_admission=False,normal_ui='CPU')
 p=ROOT/'research/portable-world-fraction-native-contract.json';p.write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n')
 by={x['name']:x['native'] for x in rows};samples=lambda name:[x for x in by[name]['fractional_hits'] if x['owner']==0 and x['event']==22]
 assert all(x['fraction']==1 and x['fired']==1 and not x['created'] for x in samples('critical-clamp-200'))
 assert all(x['fraction']==0 and x['fired']==0 and not x['created'] for x in samples('critical-clamp--100'))
 assert len({x['fraction'] for x in samples('critical-callback-does-not-resample-same-shot')[:10]})==1
 assert all(x['fraction']>0 for x in by['core-kept-on-add-route']['fractional_hits'] if x['event']==23)
 r.update(passed=True,direct_zero_and_one_do_not_create_accumulator=True,fractional_call_snapshot_native_observed=True);p.write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n');print('Native critical/core',len(rows),'full battles;GPU0')
if __name__=='__main__':main()
