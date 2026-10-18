"""Generate the shared impact enum/packet boundary; no numerical handlers."""
import argparse,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'app'))
from impact_specs import BEGIN,END,render_cuda,gpu_source_matches
p=argparse.ArgumentParser();p.add_argument('--check',action='store_true');args=p.parse_args()
source=ROOT/'app/detail_effects.cu'
if args.check:
    assert gpu_source_matches(),'Regenerate typed impact definitions before building/running CUDA'
else:
    text=source.read_text(encoding='utf-8')
    if text.count(BEGIN)!=1 or text.count(END)!=1:raise ValueError('Expected exactly one impact block')
    prefix,rest=text.split(BEGIN,1);_,suffix=rest.split(END,1)
    source.write_text(prefix+BEGIN+render_cuda()+END+suffix,encoding='utf-8')
