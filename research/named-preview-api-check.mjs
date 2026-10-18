import {readFileSync,writeFileSync} from 'node:fs';
import assert from 'node:assert/strict';
const rows=[];
for(const {name,evaluation} of JSON.parse(readFileSync('research/named-magnitude-api-fixtures.json','utf8'))) {
 const response=await fetch('http://127.0.0.1:4333/api/jobs',{method:'POST',headers:{'content-type':'application/json'},body:JSON.stringify({kind:'compare',evaluation})});assert.ok(response.ok);
 let job=await response.json();
 for(let i=0;i<1800;i++) {
  job=await (await fetch('http://127.0.0.1:4333/api/jobs/'+job.id)).json();
  assert.notEqual(job.status,'failed',job.error);
  if(job.status==='complete')break;
  await new Promise(r=>setTimeout(r,100));
 }
 assert.equal(job.status,'complete');
 for(const {result} of job.results){assert.equal(result.compute.backend,'cuda_detail');assert.equal(result.compute.cpu_verification.matched,true);assert.equal(result.compute.workspace_bytes,1090576);}
 rows.push({name,passed:true,total:job.results[0].result.total_damage,workspace_bytes:1090576});
}
writeFileSync('research/named-magnitude-preview-api.json',JSON.stringify({passed:true,port:4333,cases:rows},null,2)+'\n');console.log(JSON.stringify(rows));
