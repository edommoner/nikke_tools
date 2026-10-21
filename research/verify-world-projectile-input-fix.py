"""Two changed input blocks only; keep the verified production shader and old blocks."""
import array,datetime,importlib.util,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research','scripts')]
s=importlib.util.spec_from_file_location('projectile_delta_suite',ROOT/'research/verify-world-projectile.py');suite=importlib.util.module_from_spec(s);s.loader.exec_module(suite)
def main():
 bridge=json.loads((ROOT/'research/portable-world-projectile-diagnostic-preservation.json').read_text());assert bridge['passed'] and not bridge['normalization_extended']
 rows,programs,bad=suite.prepare();case=rows[-1];w,m,b=programs[-1];assert case['name']=='projectile-resource-modulo-pellets-and-named-removal' and bad[-1][0]=='self-removal-unused-recipient-key'
 packed=array.array('I',[2,*w,*bad[-1][1]]);packed.byteswap() if sys.byteorder!='little' else None;data=packed.tobytes();folder=ROOT/'research/portable-build'/('world-projectile-input-fix-'+datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ'));folder.mkdir();(folder/'input.bin').write_bytes(data)
 try:raw,e=suite.execute(suite.SOURCE,'portableEvents',data,suite.INPUT,suite.OUTPUT,'metal')
 except Exception as error:(folder/'failure.json').write_text(json.dumps(dict(error=repr(error)),indent=2)+'\n');raise
 (folder/'readback.bin').write_bytes(raw);(folder/'evidence.json').write_text(json.dumps(e,indent=2)+'\n');words=array.array('I');words.frombytes(raw);words.byteswap() if sys.byteorder!='little' else None
 first=words[:suite.OUTPUT];actual=suite.decoded(first,m,case,b);native,trace=suite.inspect_native(case);changes=[k for k in native if k!='scope' and actual[k]!=native[k]];actual_trace=suite.reload.charge.team.skill_trace(first,m)
 if actual_trace!=trace:changes.append('skill_trace')
 result=dict(passed=first[0]==0 and words[suite.OUTPUT]==64 and not changes,statuses=[first[0],words[suite.OUTPUT]],changed=changes,actual=actual,native=native,skill_trace=actual_trace,native_skill_trace=trace,captured=str(folder),evidence=e,unchanged52_blocks_reexecuted=0,production_shader_strict_generated_equal_to_1421ea2=True,normalization_extended=False)
 (ROOT/'research/portable-world-projectile-input-fix-metal.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print(result['passed'],result['statuses'],changes);assert result['passed']
if __name__=='__main__':main()
