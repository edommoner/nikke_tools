"""CPU-only strict generated-text preservation for all ten prior entries."""
import importlib.util,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app'),str(ROOT/'research')]
from portable_backend import build
s=importlib.util.spec_from_file_location('counter_generated_digest',ROOT/'research/summarize-portable-cross-gpu.py');d=importlib.util.module_from_spec(s);s.loader.exec_module(d)
def main():
 rows=[('normal','gpu/event_runtime.slang',dict(cuda='e9c368f169736fc8282845a44ea9d0bc0c5c4ec76c4b5d6bda6ccf121b22f882',metal='571dd80e5ec6c3d21e011f6e939b02b152f19df4d73c84403f4f23080588dd46'))]
 for name,entry in [('fields','world_actor_fields'),('state','world_actor_state'),('mutation','world_actor_mutation'),('recipient','world_actor_recipient'),('status','world_actor_status'),('stack','world_actor_stack')]:
  rows.append((name,'gpu/'+entry+'_entry.slang',json.loads((ROOT/('research/portable-world-actor-'+name+'-short-expected.json')).read_text())['generated_normalized']))
 rows.append(('counter','gpu/target_counter_entry.slang',json.loads((ROOT/'research/portable-world-target-counter-short-expected.json').read_text())['generated_normalized']))
 rows.append(('physical','gpu/counter_landing_entry.slang',json.loads((ROOT/'research/portable-world-counter-landing-short-expected.json').read_text())['generated_normalized']))
 rows.append(('context','gpu/counter_context_entry.slang',json.loads((ROOT/'research/portable-world-counter-context-short-expected.json').read_text())['generated_normalized']))
 results=[]
 for name,entry,expected in rows:
  outputs,hashes=build(entry,'portableEvents');actual={b:d.normalized(p.read_bytes()) for b,p in outputs.items()};results.append(dict(name=name,passed=actual==expected,actual=actual,expected=expected,source_sha256=hashes))
  print(name,'strict generated parity',actual==expected,flush=True)
 report=dict(passed=all(r['passed'] for r in results),cases=results,gpu_executions=0,normalization_unchanged=True)
 (ROOT/'research/portable-build/world-counter-field-generation.json').write_text(json.dumps(report,indent=2)+'\n')
 assert report['passed'],[r['name'] for r in results if not r['passed']]
if __name__=='__main__':main()
