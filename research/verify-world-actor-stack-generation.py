"""CPU compiler-only regression:normal,fields,and state generated text unchanged."""
import importlib.util,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app'),str(ROOT/'research')]
from portable_backend import build,source_hashes
s=importlib.util.spec_from_file_location('mutation_digest',ROOT/'research/summarize-portable-cross-gpu.py');d=importlib.util.module_from_spec(s);s.loader.exec_module(d)
def main():
 expected=[('normal','gpu/event_runtime.slang',dict(cuda='e9c368f169736fc8282845a44ea9d0bc0c5c4ec76c4b5d6bda6ccf121b22f882',metal='571dd80e5ec6c3d21e011f6e939b02b152f19df4d73c84403f4f23080588dd46')),('fields','gpu/world_actor_fields_entry.slang',json.loads((ROOT/'research/portable-world-actor-fields-short-expected.json').read_text())['generated_normalized']),('state','gpu/world_actor_state_entry.slang',json.loads((ROOT/'research/portable-world-actor-state-short-expected.json').read_text())['generated_normalized']),('mutation','gpu/world_actor_mutation_entry.slang',json.loads((ROOT/'research/portable-world-actor-mutation-short-expected.json').read_text())['generated_normalized']),('recipient','gpu/world_actor_recipient_entry.slang',json.loads((ROOT/'research/portable-world-actor-recipient-short-expected.json').read_text())['generated_normalized']),('status','gpu/world_actor_status_entry.slang',json.loads((ROOT/'research/portable-world-actor-status-short-expected.json').read_text())['generated_normalized'])]
 results=[]
 for name,source,golden in expected:
  outputs,hashes=build(source,'portableEvents');actual={backend:d.normalized(path.read_bytes()) for backend,path in outputs.items()};results.append(dict(name=name,passed=actual==golden,actual=actual,expected=golden,source_sha256=hashes))
 report=dict(passed=all(x['passed'] for x in results),cases=results,gpu_executions=0,normalization_unchanged=True)
 (ROOT/'research/portable-build/world-actor-stack-generation.json').write_text(json.dumps(report,indent=2)+'\n');assert report['passed'],[(x['name'],x['actual']) for x in results if not x['passed']];print('Normal/fields/state/mutation/recipient/status CUDA and MSL strict generated parity;GPU executions0')
if __name__=='__main__':main()
