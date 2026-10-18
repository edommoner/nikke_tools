/** Reusable live-preview check for new raw roster fixtures. */
import {readFileSync,writeFileSync,readdirSync} from 'node:fs';
import {createHash} from 'node:crypto';
import assert from 'node:assert/strict';
const fixture=process.argv[2],output=process.argv[3],port=Number(process.argv[4]||4333);
assert.ok(fixture&&output,'Usage: node check-preview-gpu.mjs fixture.json output.json [port]');
assert.ok(Number.isInteger(port)&&port>0&&port<65536);
const stateBytes=Number(readFileSync('app/detail_effects.ptx','utf8').match(/detail_state_bytes_v\d+\s*=\s*(\d+);/)[1]);
const abi=JSON.parse(readFileSync('app/detail_effects-sm86.json','utf8')).abi;
const files=['scripts/check-preview-gpu.mjs',fixture,'server.mjs',...readdirSync('app').filter(f=>f.endsWith('.py')||f.startsWith('detail_effects')).map(f=>'app/'+f)];
const hashes=()=>Object.fromEntries(files.map(f=>[f,createHash('sha256').update(readFileSync(f)).digest('hex')]));
const source_sha256=hashes();const rows=[];
for(const {name,evaluation} of JSON.parse(readFileSync(fixture,'utf8'))) {
 const response=await fetch(`http://127.0.0.1:${port}/api/jobs`,{method:'POST',headers:{'content-type':'application/json'},body:JSON.stringify({kind:'compare',evaluation:{...evaluation,compute_backend:'cuda_detail',verify_detail:true}})});assert.ok(response.ok);
 let job=await response.json();
 for(let i=0;i<1800;i++) {
  job=await (await fetch(`http://127.0.0.1:${port}/api/jobs/${job.id}`)).json();
  assert.notEqual(job.status,'failed',job.error);if(job.status==='complete')break;
  await new Promise(r=>setTimeout(r,100));
 }
 assert.equal(job.status,'complete');assert.ok(job.results.length);
 for(const {result} of job.results){assert.equal(result.compute.backend,'cuda_detail');assert.equal(result.compute.cpu_verification.matched,true);assert.equal(result.compute.workspace_bytes,stateBytes);}
 rows.push({name,passed:true,total:job.results[0].result.total_damage,workspace_bytes:stateBytes});
}
assert.deepEqual(hashes(),source_sha256);
writeFileSync(output,JSON.stringify({passed:true,port,abi,cases:rows,source_sha256},null,2)+'\n');console.log(JSON.stringify(rows));
