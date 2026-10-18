/** Normal API acceptance for the growth editor's scalar/list option values. */
import {spawn} from 'node:child_process';
import {readFileSync,writeFileSync} from 'node:fs';
import {createHash} from 'node:crypto';
import {once} from 'node:events';
import assert from 'node:assert/strict';
import {overloadFields,formatOverload,parseOverload} from '../web/roster-model.mjs';
const [fixture='research/detail-heal-charge-api-fixture.json',output='research/detail-owned-api-acceptance.json',expectedWarning]=process.argv.slice(2);

const files=['scripts/smoke-owned-detail.mjs','web/roster-model.mjs','web/app.js','web/index.html','server.mjs',
  fixture,'app/detail_gpu.py','app/named_target_specs.py','app/evaluation-queue.mjs','app/detail_effects.cu',
  'app/detail_effects-sm86.cubin','app/detail_effects-sm86.json','app/detail_effects.ptx',
  'app/engine_worker.py','app/engine_compat.py','app/gpu_service.py'];
files.push('app/weapon_mode_runtime.py','app/effect_spec.py');
const hashes=()=>Object.fromEntries(files.map(f=>[f,createHash('sha256').update(readFileSync(f)).digest('hex')]));
const source_sha256=hashes();
const evaluation=JSON.parse(readFileSync(fixture,'utf8'));
for(const entry of Object.values(evaluation.profile.chars)) {
  const original=structuredClone(entry.equip_skills);
  for(const [,key] of overloadFields) {
    const value=parseOverload(formatOverload(original[key]),original[key]);
    if(value!==undefined)entry.equip_skills[key]=value;
  }
  assert.deepEqual(entry.equip_skills,original);
}
const port=Number(process.env.NIKKE_TEST_PORT||4339),base=`http://127.0.0.1:${port}`;
const child=spawn(process.execPath,['server.mjs'],{env:{...process.env,PORT:String(port)},windowsHide:true,stdio:['ignore','pipe','pipe']});
let errors='';child.stderr.on('data',v=>errors+=v);
const pause=ms=>new Promise(r=>setTimeout(r,ms));
async function api(route,body) {
  const response=await fetch(base+route,body?{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)}:{});
  const data=await response.json();assert.ok(response.ok,JSON.stringify(data));return data;
}
async function job(evaluation) {
  let data=await api('/api/jobs',{kind:'compare',evaluation});
  for(let i=0;i<1800;i++) {
    data=await api(`/api/jobs/${data.id}`);
    if(data.status==='complete')return data.results.map(r=>r.result);
    assert.notEqual(data.status,'failed',data.error);
    await pause(100);
  }
  throw Error('Owned detailed API acceptance timed out');
}
try {
  await once(child.stdout,'data');
  const asset=await fetch(base+'/roster-model.mjs');assert.equal(asset.status,200);
  assert.match(asset.headers.get('content-type'),/javascript/);
  const verified=await job({...evaluation,compute_backend:'cuda_detail',verify_detail:true});
  const pure=await job({...evaluation,compute_backend:'cuda_detail',verify_detail:false});
  const cpu=await job({...evaluation,compute_backend:'cpu',verify_detail:false});
  for(let i=0;i<2;i++) {
    assert.equal(verified[i].compute.backend,'cuda_detail');
    assert.equal(verified[i].compute.cpu_verification.matched,true);
    assert.equal(pure[i].compute.backend,'cuda_detail');
    assert.equal(pure[i].compute.cpu_verification,undefined);
    assert.equal(cpu[i].compute.backend,'cpu');
    if(expectedWarning)for(const result of [verified[i],pure[i],cpu[i]])assert.ok(result.app_warnings.includes(expectedWarning));
    for(const key of ['total_damage','members','base_stats','burst_timeline']) {
      assert.deepEqual(pure[i][key],cpu[i][key],`pure GPU ${i} ${key}`);
      assert.deepEqual(verified[i][key],cpu[i][key],`verified GPU ${i} ${key}`);
    }
  }
  let modePolicyRoundtrip;
  if(evaluation.weapon_mode_swap===true) {
    for(const rows of [pure,verified,cpu])for(const result of rows)assert.equal(result.weapon_mode_swap,true);
    const disabled=await job({...evaluation,weapon_mode_swap:false,compute_backend:'cuda_detail',verify_detail:true});
    for(let i=0;i<2;i++) {
      assert.equal(disabled[i].compute.backend,'cuda_detail');
      assert.equal(disabled[i].compute.cpu_verification.matched,true);
      assert.equal(disabled[i].weapon_mode_swap,false);
      assert.notEqual(disabled[i].total_damage,pure[i].total_damage);
    }
    const restored=await job({...evaluation,compute_backend:'cuda_detail',verify_detail:false});
    for(let i=0;i<2;i++)assert.equal(restored[i].total_damage,pure[i].total_damage);
    modePolicyRoundtrip={passed:true,enabled:pure.map(r=>r.total_damage),disabled:disabled.map(r=>r.total_damage),restored:restored.map(r=>r.total_damage)};
  }
  assert.deepEqual(hashes(),source_sha256);
  const report={generated_at:new Date().toISOString(),passed:true,fictional_owned_data:true,
    live_import_verified:false,scalar_and_list_editor_roundtrip:true,
    pure_gpu_and_verified_and_cpu_equal:true,original_total:pure[0].total_damage,total:pure[1].total_damage,
    members:pure[1].members,burst_timeline:pure[1].burst_timeline,mode_policy_roundtrip:modePolicyRoundtrip,source_sha256};
  writeFileSync(output,JSON.stringify(report,null,2)+'\n');
  console.log(JSON.stringify({passed:true,total:report.total,original_total:report.original_total}));
} finally {
  if(child.exitCode===null){child.kill();await once(child,'exit');}
  if(errors)console.error(errors);
}
