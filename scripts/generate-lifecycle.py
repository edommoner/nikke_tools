"""Generate registered CUDA state hooks, leaving numerical handlers untouched."""
import argparse,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'app'))
from lifecycle_specs import BEGIN,END,render_cuda,gpu_source_matches
p=argparse.ArgumentParser();p.add_argument('--check',action='store_true');args=p.parse_args()
source=ROOT/'app/detail_effects.cu'
if args.check:
    assert gpu_source_matches(),'Regenerate lifecycle dispatch before building/running CUDA'
else:
    text=source.read_text(encoding='utf-8')
    if text.count(BEGIN)!=1 or text.count(END)!=1:
        raise SystemExit('Expected one lifecycle block; migrate legacy source explicitly before generation')
    prefix,rest=text.split(BEGIN,1);_,suffix=rest.split(END,1)
    updated=prefix+BEGIN+render_cuda()+END+suffix
    if updated!=text:source.write_text(updated,encoding='utf-8')
