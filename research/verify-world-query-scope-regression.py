"""CPU-only full-native retention audit after making enemy query scope explicit."""
import hashlib,importlib.util,json,sys
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','scripts','research')]
from world_frame_native import observe
def main():
 stages=[
 ('counter-fields','verify-world-counter-fields.py','portable-world-counter-field-metal.json'),
 ('counter-context','verify-world-counter-context.py','portable-world-counter-context-metal.json'),
 ('counter-landings','verify-world-counter-landings.py','portable-world-counter-landing-metal.json'),
 ('stacks','verify-world-actor-stacks.py','portable-world-actor-stack-metal.json'),
 ('status','verify-world-actor-status.py','portable-world-actor-status-metal.json'),
 ('recipients','verify-world-actor-recipients.py','portable-world-actor-recipient-metal.json'),
 ('mutation','verify-world-actor-mutation.py','portable-world-actor-mutation-metal.json'),
 ('state','verify-world-actor-state.py','portable-world-actor-state-metal.json'),
 ('fields','verify-world-actor-fields.py','portable-world-actor-fields-metal.json'),
 ('pools','verify-world-actor-pools.py','portable-world-actor-pools-metal.json')]
 checked=[];reports={}
 with patch('portable_backend.build',side_effect=AssertionError('GPU forbidden')),patch('portable_backend.execute',side_effect=AssertionError('GPU forbidden')),patch('portable_backend.execute_batches',side_effect=AssertionError('GPU forbidden')):
  for stage,driver,report in stages:
   spec=importlib.util.spec_from_file_location('scope_retention_'+stage.replace('-','_'),ROOT/'research'/driver);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
   p=ROOT/'research'/report;stored=json.loads(p.read_text());assert stored['passed'];reports[report]=hashlib.sha256(p.read_bytes()).hexdigest();rows=m.fixtures();old={r['name']:r['native'] for r in stored['cases']}
   for c in rows:
    before=old[c['name']];after=observe(c)
    if 'target_counters' in after and 'events' not in before['target_counters']:after['target_counters'].pop('events')
    a=json.loads(json.dumps(after));b=dict(before);a.pop('scope',None);b.pop('scope',None)
    changed=[k for k in a.keys()|b.keys() if a.get(k)!=b.get(k)];checked.append(dict(stage=stage,name=c['name'],passed=not changed,changed=changed))
   print(stage,len(rows),'native dictionaries checked',flush=True)
 result=dict(passed=all(c['passed'] for c in checked),native_dictionaries=len(checked),checks=checked,prior_reports_sha256=reports,gpu_executions=0,excluded_metadata=['scope explanatory prose only'],source_sha256={'app/enemy_recipient_runtime.py':hashlib.sha256((ROOT/'app/enemy_recipient_runtime.py').read_bytes()).hexdigest()},full_goal_complete=False)
 (ROOT/'research/portable-world-query-scope-regression.json').write_text(json.dumps(result,indent=2)+'\n');assert result['passed'],[x for x in checked if not x['passed']]
 print('Native retention audit',len(checked),'passed;GPU0')
if __name__=='__main__':main()
