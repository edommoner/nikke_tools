"""Prior21 entry preservation with the existing strict normalizer;GPU0."""
import importlib.util,json,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app'),str(ROOT/'research')]
from portable_backend import build

def main():
 subprocess.run([sys.executable,str(ROOT/'research/verify-world-reload-generation.py')],check=True,cwd=ROOT)
 s=importlib.util.spec_from_file_location('projectile_generation_digest',ROOT/'research/summarize-portable-cross-gpu.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
 report=json.loads((ROOT/'research/portable-build/world-reload-generation.json').read_text())
 for name in ('reload','roster'):
  paths,hashes=build('gpu/world_'+name+'_entry.slang','portableEvents');actual={b:m.normalized(p.read_bytes()) for b,p in paths.items()};expected=json.loads((ROOT/('research/portable-world-'+name+'-short-expected.json')).read_text())['generated_normalized']
  report['cases'].append(dict(name=name,passed=actual==expected,actual=actual,expected=expected,source_sha256=hashes))
 report['passed']=all(r['passed'] for r in report['cases']);assert len(report['cases'])==21
 (ROOT/'research/portable-world-projectile-generation.json').write_text(json.dumps(report,indent=2)+'\n');assert report['passed'];print('Old21 CUDA/MSL strict generated exact;GPU0')
if __name__=='__main__':main()
