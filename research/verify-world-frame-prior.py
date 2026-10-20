"""Existing4682 full-word preservation and new world-frame raw admission failures."""
import argparse,array,datetime,hashlib,importlib.util,json,struct,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app')]
from portable_backend import execute,source_hashes
OLD_IN=86016;NEW_IN=88848;OLD_OUT=159744;NEW_OUT=225280
sha=lambda b:hashlib.sha256(b).hexdigest()
def negative_inputs():
 s=importlib.util.spec_from_file_location('world_frame_fixture',ROOT/'research/verify-world-frame.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
 words,_=m.compile_case(m.fixtures()[0]);rows=[]
 for name,word,value in [('graph-magic',86016,1),('graph-count',86017,33),('manual-frame-count',86018,1),('wrong-clock',86019,2),('finish-disabled',86020,0),('graph-reserved',86021,1),('graph-tail',86031,1),('authored-clear-mask',86016+2064+2,1),('payload-op',88336,31),('payload-time',88337,1),('payload-pierce',88339,2),('cpu-cover-mask',88340,1),('cpu-victim-mask',88341,1),('payload-reserved',88342,1),('bad-victim-rule',88348,4),('all-count',88349,1),('all-slots',88350,1),('all-taunt-flag',88351,1),('unused-payload',88352,1),('rng-disabled',0,0)]:
  v=list(words)
  if name=='rng-disabled':v[m.L['ENEMY_TARGET_META_BASE']]=0
  else:v[word]=value
  rows.append((name,v))
 for name,at,value in [('nan-attack',88344,float('nan')),('negative-attack',88344,-1),('infinite-coefficient',88346,float('inf')),('oversized-coefficient',88346,1000001),('duration-without-final-advance',86022,2)]:
  v=list(words);v[at:at+2]=list(struct.unpack('<II',struct.pack('<d',value)));rows.append((name,v))
 return rows
def main():
 p=argparse.ArgumentParser();p.add_argument('--candidate',required=True,type=Path);p.add_argument('--backend',choices=['metal','cuda'],default='metal');p.add_argument('--batch',type=int,default=1024);args=p.parse_args()
 assert 1<=args.batch<=2048
 candidate=args.candidate.resolve();prep=json.loads((candidate/'candidate-preparation.json').read_text());source=prep['source'];fixed_hashes=source_hashes(source)
 old=Path(json.loads((ROOT/'research/portable-enemy-target-scalar-canonical-core.json').read_text())['canonical_capture']);original=old.with_name('input.bin')
 folder=ROOT/'research/portable-build'/('world-frame-prior-'+datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ'));folder.mkdir()
 report=dict(passed=False,complete=False,candidate=str(candidate),source_sha256=fixed_hashes,captured=str(folder),batches=[],changed=[],negative_cases=[],abi_upgrade='Only valid0x50455673->74;intentional invalid70/71/72 unchanged',old_input=str(original),old_readback=str(old),all_input_words_except_valid_abi_preserved=True,all_old_output_words_equal=False,canonical_world_admission=False,full_goal_complete=False,normal_ui='CPU')
 report_path=ROOT/f'research/portable-world-frame-prior-{args.backend}.json'
 def save():report_path.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
 save();all_prefix=hashlib.sha256();all_old=hashlib.sha256();abi_counts={}
 with original.open('rb') as fi,old.open('rb') as fo:
  count=struct.unpack('<I',fi.read(4))[0];assert count==4682
  for begin in range(0,count,args.batch):
   size=min(args.batch,count-begin);data=array.array('I',[size])
   for _ in range(size):
    block=fi.read(OLD_IN*4);assert len(block)==OLD_IN*4;words=array.array('I');words.frombytes(block)
    if sys.byteorder!='little':words.byteswap()
    abi=words[0];abi_counts[hex(abi)]=abi_counts.get(hex(abi),0)+1
    if abi==0x50455673:words[0]=0x50455674
    else:assert abi in (0x50455670,0x50455671,0x50455672)
    words.extend([0]*(NEW_IN-OLD_IN));data.extend(words)
   if sys.byteorder!='little':data.byteswap()
   bfolder=folder/f'old-{begin:04d}';bfolder.mkdir();packed=data.tobytes();(bfolder/'input.bin').write_bytes(packed)
   raw,evidence=execute(source,'portableEvents',packed,NEW_IN,NEW_OUT,args.backend)
   (bfolder/'readback.bin').write_bytes(raw);(bfolder/'evidence.json').write_text(json.dumps(evidence,indent=2)+'\n')
   assert evidence['source_sha256']==fixed_hashes
   for local in range(size):
    expected=fo.read(OLD_OUT*4);assert len(expected)==OLD_OUT*4
    start=local*NEW_OUT*4;prefix=raw[start:start+OLD_OUT*4];tail=raw[start+OLD_OUT*4:start+NEW_OUT*4]
    all_prefix.update(prefix);all_old.update(expected)
    if prefix!=expected or any(tail):
     report['changed'].append(dict(index=begin+local,old_sha256=sha(expected),new_prefix_sha256=sha(prefix),new_tail_zero=not any(tail)));save()
   report['batches'].append(dict(begin=begin,programs=size,retained=str(bfolder),all_old_output_words_equal=not report['changed'],**evidence));save()
   assert not report['changed'],report['changed'][:8]
   print(begin+size,'/4682 full legacy output blocks preserved',flush=True)
 negatives=negative_inputs();data=array.array('I',[len(negatives)])
 for _,words in negatives:data.extend(words)
 if sys.byteorder!='little':data.byteswap()
 packed=data.tobytes();nfolder=folder/'negative';nfolder.mkdir();(nfolder/'input.bin').write_bytes(packed)
 raw,evidence=execute(source,'portableEvents',packed,NEW_IN,NEW_OUT,args.backend);(nfolder/'readback.bin').write_bytes(raw);(nfolder/'evidence.json').write_text(json.dumps(evidence,indent=2)+'\n');assert evidence['source_sha256']==fixed_hashes
 report['negative_evidence']=evidence
 for i,(name,_) in enumerate(negatives):
  status=struct.unpack_from('<I',raw,i*NEW_OUT*4)[0];report['negative_cases'].append(dict(name=name,status=status,passed=status==64))
 report.update(complete=True,passed=not report['changed'] and all(r['passed'] for r in report['negative_cases']),programs=4682,all_old_output_words_equal=not report['changed'],legacy_prefix_sha256=all_prefix.hexdigest(),old_full_output_sha256=all_old.hexdigest(),abi_counts=abi_counts)
 save();assert report['passed'],report['negative_cases'];assert all_prefix.hexdigest()==all_old.hexdigest()
 print('All4682 legacy input roles/output words plus',len(negatives),'new world-frame raw rejections verified',args.backend)
if __name__=='__main__':main()
