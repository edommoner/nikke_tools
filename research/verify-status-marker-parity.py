"""Extend the frozen snapshot proof by one nullable-marker program only."""
import hashlib,importlib.util,json,struct,sys
from pathlib import Path
R=Path(__file__).resolve().parents[1];P=R/'research';sys.path[:0]=[str(R/d) for d in ('app','scripts')]
import portable_runtime
s=importlib.util.spec_from_file_location('marker_main',R/'scripts/verify-portable-combat.py');v=importlib.util.module_from_spec(s);s.loader.exec_module(v)
prior=json.loads((P/'portable-status-before-marker-metal.json').read_text());names=[c['name'] for c in v.fixtures()];old_names=[c['name'] for c in prior['cases']]
indices=[names.index(name) for name in old_names]+list(range(len(names),len(names)+len(prior['rejected_cases'])))
delta=[i for i,name in enumerate(names) if name not in old_names];assert [names[i] for i in delta]==['status-null-and-omitted-state-share-identity']
original=portable_runtime.execute;calls=0

def execute(source,entry,packed,iw,ow,backend):
 global calls
 calls+=1;assert calls==1 and backend=='metal' and (iw,ow)==(77824,102400)
 raw,e=original(source,entry,packed,iw,ow,backend);assert e['source_sha256']==prior['source_sha256']
 def inp(selected):return struct.pack('<I',len(selected))+b''.join(packed[4+i*iw*4:4+(i+1)*iw*4] for i in selected)
 def out(selected):return b''.join(raw[i*ow*4:(i+1)*ow*4] for i in selected)
 sha=lambda b:hashlib.sha256(b).hexdigest();assert sha(inp(indices))==prior['input_sha256'];assert sha(out(indices))==prior['output_sha256']
 result=dict(passed=True,parent_metal_report='portable-status-before-marker-metal.json',parent_incremental_proof='portable-status-snapshot-incremental.json',old_inputs=len(indices),current_inputs=struct.unpack_from('<I',packed)[0],old_positive_inputs=len(old_names),new_positive_inputs=len(names),old_input_sha256=prior['input_sha256'],old_output_sha256=prior['output_sha256'],old_subset_input_sha256=sha(inp(indices)),old_subset_output_sha256=sha(out(indices)),delta_cases=[names[i] for i in delta],delta_input_sha256=sha(inp(delta)),delta_output_sha256=sha(out(delta)),gpu_source_unchanged=True,no_input_or_output_word_normalization=True,subset_mapping=indices,delta_indices=delta,source_sha256=e['source_sha256'],current_full_execution=e,current_full_cuda_batch_executed=False)
 (P/'portable-status-marker-incremental.json').write_text(json.dumps(result,indent=2)+'\n');return raw,e
portable_runtime.execute=execute
v.main();assert calls==1
m=json.loads((P/'portable-combat-metal.json').read_text());changed=[k for k,h in m['validation_sha256'].items() if prior['validation_sha256'].get(k)!=h];assert set(changed)=={'app/portable_runtime.py','tests/fixtures/portable-status.json'},changed
p=P/'portable-status-marker-incremental.json';x=json.loads(p.read_text());x['changed_validation_paths']=changed;x['validation_sha256']=m['validation_sha256'];x['entry_thread_index_used_only_for_guard_and_wire_offsets']=(R/'gpu/event_runtime.slang').read_text().split('void portableEvents',1)[1].count('id.x')==3;assert x['entry_thread_index_used_only_for_guard_and_wire_offsets'];p.write_text(json.dumps(x,indent=2)+'\n');print('1624 old programs unchanged; one nullable-marker program isolated.')
