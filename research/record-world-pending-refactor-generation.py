"""Measure the intentionally refactored skill entry; do not relax old11 gates."""
import importlib.util,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app'),str(ROOT/'research')]
from portable_backend import build
def main():
 s=importlib.util.spec_from_file_location('pending_generation_digest',ROOT/'research/summarize-portable-cross-gpu.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
 paths,hashes=build('gpu/world_skill_entry.slang','portableEvents');actual={b:m.normalized(p.read_bytes()) for b,p in paths.items()};before=json.loads((ROOT/'research/portable-world-skill-short-expected.json').read_text())['generated_normalized']
 r=dict(gpu_calls=0,entry='gpu/world_skill_entry.slang',matches_prior_generated=actual==before,actual=actual,prior=before,source_sha256=hashes,reason='Direct and pending share extracted Actor landing helper;old11 strict and841 full outputs are separate required gates',normalization_unchanged=True)
 (ROOT/'research/portable-world-pending-refactor-generation.json').write_text(json.dumps(r,indent=2)+'\n');print('Refactored direct entry unchanged?',r['matches_prior_generated'])
if __name__=='__main__':main()
