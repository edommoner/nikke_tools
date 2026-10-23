"""GPU0 audit of the exact input-offset to logical-control-row transition."""
import argparse,array,hashlib,importlib.util,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','scripts')]
spec=importlib.util.spec_from_file_location('partial_state_cli',ROOT/'scripts/nikke_gpu.py');cli=importlib.util.module_from_spec(spec);spec.loader.exec_module(cli)
from portable_specs import LIMITS as L
from portable_charge_control_specs import CLICK_BASE
from portable_capture_storage import file_digest

CHANGES={
 'gpu/world_charge_control_runtime.slang':[
  ('results[a+17]=row+1;uint64_t interval','results[a+17]=i+1;uint64_t interval'),
  ('handled=true;row--;s.chargeUntil[who]','handled=true;row=controlClick(s,who,row-1);s.chargeUntil[who]')],
 'gpu/weapon_frame_phases.slang':[
  ('uint row=w.partialTapRow-1;s.nextShot[who]','uint row=controlClick(s,who,w.partialTapRow-1);s.nextShot[who]')],
}


def capture(root,folder):
 m=cli.verify_package(root);inventory=cli.load(folder/'artifacts.json')['files']
 anchors=[r for r in inventory if r['path'] in ('evidence.json','comparison.json')]
 assert len(anchors)==2,'Missing immutable evidence/comparison anchors';cli.check_records(folder,anchors)
 e=cli.load(folder/'evidence.json');c=cli.load(folder/'comparison.json');result=cli.load(folder/'result.json')
 assert c['calculation_verified'] and result['passed'] and e['gpu_execution_verified'],'Unverified capture'
 assert e['source_sha256']==m['golden']['source_sha256'],'Source closure differs from package'
 assert file_digest(folder/'input.bin')==e['input_sha256']==c['input_sha256'],'Input bytes changed'
 return m,e,c


def audit(before_package,before,after_package,after):
 a,ae,ac=capture(before_package,before);b,be,bc=capture(after_package,after)
 assert ae['source_sha256'].keys()==be['source_sha256'].keys(),'Source closures differ'
 changed={name for name in ae['source_sha256'] if ae['source_sha256'][name]!=be['source_sha256'][name]}
 assert changed==set(CHANGES),'Unreviewed GPU sources changed'
 for name,changes in CHANGES.items():
  source=(before_package/name).read_text()
  for old,new in changes:
   assert source.count(old)==1,'Missing exact prior statement';source=source.replace(old,new,1)
  assert source==(after_package/name).read_text(),'Transition includes another source change'
 assert ae['input_sha256']==be['input_sha256'],'Input transition is not position-only'
 assert len(ac['entries'])==len(bc['entries'])
 for x,y in zip(ac['entries'],bc['entries']):
  assert x['name']==y['name'] and x['input_sha256']==y['input_sha256'] and x.get('native_sha256')==y.get('native_sha256'),'Input/native fingerprint changed'
 n=len(ac['entries']);stride=786432*4;before_hash=hashlib.sha256();after_hash=hashlib.sha256();adjustments=[]
 assert sys.byteorder=='little'
 with (before/'readback.bin').open('rb') as f,(after/'readback.bin').open('rb') as g:
  for i in range(n):
   left=f.read(stride);right=g.read(stride);assert len(left)==len(right)==stride,'Short raw'
   before_hash.update(left);after_hash.update(right);old=array.array('I');old.frombytes(left);new=array.array('I');new.frombytes(right)
   for who in range(5):
    at=L['WORLD_CONTROL_STATE_BASE']+who*32+17
    if old[at]==new[at]:continue
    row=new[at];assert 1<=row<=8,'New row outside static bound'
    expected=2+i*104400+L['WORLD_CONTROL_INPUT_BASE']+CLICK_BASE+(who*8+row-1)*16
    assert old[at]==expected,'Prior word is not the exact corresponding input offset'
    adjustments.append(dict(case=i,owner=who,before=old[at],after=row));old[at]=row
   assert old.tobytes()==right,'Another raw word changed'
  assert not f.read(1) and not g.read(1),'Trailing raw'
 assert before_hash.hexdigest()==ae['output_sha256'] and after_hash.hexdigest()==be['output_sha256'],'Raw evidence hashes differ'
 return dict(passed=True,gpu_calls=0,calculation_verified=False,before_package_id=a['package_id'],after_package_id=b['package_id'],cases=n,raw_bytes=n*stride,logical_row_adjustments=adjustments,other_raw_bytes_identical=n*stride-4*len(adjustments),before_raw_sha256=before_hash.hexdigest(),after_raw_sha256=after_hash.hexdigest(),scope='Exact source/input/native/raw representation transition only; independent calculation seals remain separate')


def main():
 p=argparse.ArgumentParser();p.add_argument('--before-package',type=Path,required=True);p.add_argument('--before',type=Path,required=True);p.add_argument('--after-package',type=Path,required=True);p.add_argument('--after',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
 with a.out.open('x') as f:f.write('{}\n')
 result=audit(a.before_package,a.before,a.after_package,a.after);cli.write(a.out,result)
 print(json.dumps({k:v for k,v in result.items() if k!='logical_row_adjustments'},indent=2))


if __name__=='__main__':main()
