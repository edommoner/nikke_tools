/** End-to-end local API smoke test. Starts and closes an isolated test server. */
import {spawn} from 'node:child_process';
import {once} from 'node:events';
import assert from 'node:assert/strict';
const port=4329,url=`http://127.0.0.1:${port}`;
const child=spawn(process.execPath,['server.mjs'],{env:{...process.env,PORT:String(port)},windowsHide:true,stdio:['ignore','pipe','pipe']});
let stderr='';child.stderr.on('data',b=>stderr+=b);
const delay=ms=>new Promise(r=>setTimeout(r,ms));
async function api(route,data){const r=await fetch(url+route,data===undefined?{}:{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(data)});const v=await r.json();assert.ok(r.ok,JSON.stringify(v));return v;}
async function until(id,states=['complete']){for(let i=0;i<500;i++){const j=await api('/api/jobs/'+id);if(states.includes(j.status))return j;if(j.status==='failed')throw Error(j.error);await delay(100);}throw Error('Job timeout');}
try{
  await once(child.stdout,'data');
  const hardware=await api('/api/hardware');
  const catalog=await api('/api/catalog');assert.equal(catalog.enemy_presets.filter(p=>p.mode==='solo').length,42);assert.equal(catalog.enemy_presets.filter(p=>p.mode==='union').length,300);
  const d=await api('/api/demo');
  const evaluation={profile:d.profile,squad:d.squad,duration:8,level:400,enemy:{def:31784,code:'풍압',core_px:0,distance:30},patches:{},stat_deltas:{'앨리스':{atk:5000}}};
  let j=await api('/api/jobs',{kind:'compare',evaluation});j=await until(j.id);
  assert.equal(j.results.length,2);assert.ok(j.results[1].result.total_damage>j.results[0].result.total_damage);
  const damages=j.results.map(r=>r.result.total_damage);
  j=await api('/api/jobs',{kind:'search',evaluation,target:damages[0],strict:true,variable:{character:'앨리스',kind:'atk',min:0,max:1000,step:1000}});j=await until(j.id);
  assert.equal(j.results[0].meets,false);assert.equal(j.results[1].meets,true);assert.equal(j.best.value,1000);
  j=await api('/api/jobs',{kind:'search',evaluation:{...evaluation,stat_deltas:{}},target:damages[0],strict:true,variable:{character:'앨리스',kind:'auto'}});j=await until(j.id);
  assert.equal(j.bestByField.atk.value,5000);assert.ok(j.results.some(r=>r.field==='hp'));
  const expanded=await api('/api/demo?expanded=true');
  const raid={...evaluation,profile:expanded.profile,squad:expanded.squad,stat_deltas:{}};
  j=await api('/api/jobs',{kind:'optimize',selectionBackend:hardware.available?'cuda':'cpu',evaluation:raid,mode:'fast',teamCount:5,excluded:[]});
  await api(`/api/jobs/${j.id}/pause`,{});j=await until(j.id,['paused','complete']);assert.ok(j.index>0||j.combatAcceleration?.backend==='cuda');
  if(j.status==='paused'){await api(`/api/jobs/${j.id}/resume`,{});j=await until(j.id);}
  assert.ok(j.recommendation,'Expected five-squad recommendation');
  if(hardware.available){assert.equal(j.acceleration.backend,'cuda');assert.equal(j.combatAcceleration.backend,'cuda');assert.ok(j.combatAcceleration.approximate);assert.ok(j.combatAcceleration.candidates>=j.total);assert.ok(j.results.every(r=>!r.result||r.result.engine_revision));}
  assert.equal(j.recommendation.teams.length,5);assert.equal(new Set(j.recommendation.teams.flatMap(t=>t.squad)).size,25);
  const firstTwenty=JSON.stringify(j.results),fiveDamage=j.recommendation.damage,exclude=j.recommendation.teams[0].squad;
  const optimizerId=j.id;
  let board=await api('/api/jobs',{kind:'board',teams:j.recommendation.teams.map((t,index)=>({index,evaluation:{...raid,squad:t.squad}}))});
  board=await until(board.id);assert.equal(board.results.length,5);
  assert.equal(board.results.reduce((sum,row)=>sum+row.result.total_damage,0),fiveDamage);
  j=await api('/api/jobs/'+optimizerId);
  await api(`/api/jobs/${j.id}/extend`,{mode:'detail'});await api(`/api/jobs/${j.id}/pause`,{});j=await until(j.id,['paused','complete']);
  assert.equal(JSON.stringify(j.results.slice(0,20)),firstTwenty);assert.ok(j.index>20);assert.ok(j.recommendation.damage>=fiveDamage);const expandedCount=j.index;
  await api(`/api/jobs/${j.id}/cancel`,{});
  j=await api('/api/jobs',{kind:'optimize',evaluation:raid,mode:'fast',teamCount:1,excluded:exclude});j=await until(j.id);
  assert.ok(j.recommendation);assert.ok(j.recommendation.teams[0].squad.every(n=>!exclude.includes(n)));
  const rejected=await fetch(url+'/api/demo',{headers:{Origin:'https://unrelated.example'}});assert.equal(rejected.status,403);
  console.log(JSON.stringify({passed:true,gpu:hardware.available,archive_presets:catalog.enemy_presets.length,comparison:damages,strict_target_search:true,multi_field_search:true,five_squad_damage:fiveDamage,unique_members:25,batch_board:true,pause_resume:true,extended_candidates:expandedCount,prior_results_preserved:true,union_exclusions:true,origin_check:true},null,2));
}catch(error){console.error(error,stderr);process.exitCode=1;}
finally{child.kill();await once(child,'exit');}



