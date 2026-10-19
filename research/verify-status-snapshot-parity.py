"""Prove the old full CUDA batch remains identical; expose only the two new programs."""
import hashlib,importlib.util,json,struct,sys
from pathlib import Path
R=Path(__file__).resolve().parents[1];P=R/'research';sys.path[:0]=[str(R/d) for d in ('app','scripts')]
import portable_runtime
from portable_specs import LIMITS as L
s=importlib.util.spec_from_file_location('snapshot_main',R/'scripts/verify-portable-combat.py');v=importlib.util.module_from_spec(s);s.loader.exec_module(v)
prior=json.loads((P/'windows-portable-combat-v53.json').read_text());names=[c['name'] for c in v.fixtures()];old_names=[c['name'] for c in prior['cases']]
indices=[names.index(name) for name in old_names]+list(range(len(names),len(names)+len(prior['rejected_cases'])))
delta=[i for i,name in enumerate(names) if name not in old_names];assert [names[i] for i in delta]==['status-cleanse-snapshot-health--10','status-cleanse-snapshot-health-10']
original=portable_runtime.execute;calls=0

def execute(source,entry,packed,iw,ow,backend):
 global calls
 calls+=1;assert calls==1 and backend=='metal' and (iw,ow)==(77824,102400)
 raw,e=original(source,entry,packed,iw,ow,backend);assert e['source_sha256']==prior['source_sha256'],'This incremental proof requires byte-identical GPU source.'
 def input_subset(selected):
  return struct.pack('<I',len(selected))+b''.join(packed[4+i*iw*4:4+(i+1)*iw*4] for i in selected)
 def output_subset(selected):return b''.join(raw[i*ow*4:(i+1)*ow*4] for i in selected)
 sha=lambda b:hashlib.sha256(b).hexdigest()
 assert sha(input_subset(indices))==prior['input_sha256'];assert sha(output_subset(indices))==prior['output_sha256']
 result=dict(passed=True,baseline_report='windows-portable-combat-v53.json',baseline_source_commit=prior['execution']['commit'],old_inputs=len(indices),current_inputs=struct.unpack_from('<I',packed)[0],old_positive_inputs=len(old_names),new_positive_inputs=len(names),old_input_sha256=prior['input_sha256'],old_output_sha256=prior['output_sha256'],old_subset_input_sha256=sha(input_subset(indices)),old_subset_output_sha256=sha(output_subset(indices)),delta_cases=[names[i] for i in delta],delta_input_sha256=sha(input_subset(delta)),delta_output_sha256=sha(output_subset(delta)),gpu_source_unchanged=True,no_input_or_output_word_normalization=True,subset_mapping=indices,delta_indices=delta,source_sha256=e['source_sha256'],current_full_execution=e,scope='Old inputs/readbacks are extracted from a completed full Metal dispatch in the original CUDA batch order. Only a two-case CUDA delta is needed because the GPU source is byte-identical. Thread index selects disjoint wire offsets only; no current full CUDA batch execution is claimed.')
 (P/'portable-status-snapshot-incremental.json').write_text(json.dumps(result,indent=2)+'\n');return raw,e
portable_runtime.execute=execute
v.main();assert calls==1
entry=(R/'gpu/event_runtime.slang').read_text().split('void portableEvents',1)[1];assert entry.count('id.x')==3,'Thread index is restricted to the guard and input/output offsets.'
current=json.loads((P/'portable-combat-metal.json').read_text());changed=[k for k,v in current['validation_sha256'].items() if prior['validation_sha256'].get(k)!=v];assert set(changed)=={'app/reference_health_runtime.py','tests/fixtures/portable-status.json'},changed
p=P/'portable-status-snapshot-incremental.json';x=json.loads(p.read_text());x['entry_thread_index_used_only_for_guard_and_wire_offsets']=True;x['changed_validation_paths']=changed;x['validation_sha256']=current['validation_sha256'];p.write_text(json.dumps(x,indent=2)+'\n');print('1622 old input/output programs unchanged; two new snapshot programs isolated.')
