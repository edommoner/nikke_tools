import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {runInNewContext} from 'node:vm';
import {run} from '../server.mjs';

const squad=['a','b','c','d','e'];
function job(){return {kind:'optimize',selectionBackend:'metal',teamCount:1,pool:[squad],groups:[[0]],evaluation:{compute_backend:'metal_detail'},cases:[{value:1,evaluation:{squad,compute_backend:'metal_detail'}}],index:0,results:[]};}
for(const failure of [null,'combat_prefilter','select'])test(`Metal optimizer routes both stages and records failure: ${failure}`,async()=>{
 const j=job(),calls=[];
 const worker=async body=>{
  calls.push(body);
  assert.equal(body.backend,'metal');
  if(body.action===failure)throw Error('Metal explicit failure');
  if(body.action==='combat_prefilter')return {backend:'metal',device:'M5',model:'combat-prefilter-metal-f32-v1',scores:[{index:0,squad,damage:999999}]};
  assert.equal(body.action,'select');assert.equal(body.candidates[0].damage,123);
  return {backend:'metal',device:'M5',model:'disjoint-beam-metal-u64-v1',recommendation:{damage:123,teams:[{squad,damage:123}]}};
 };
 const evaluator={isCached:()=>false,many:async bodies=>bodies.map(b=>{
  assert.equal(b.compute_backend,'metal_detail');return {result:{members:squad.map(name=>({name})),total_damage:123}};
 })};
 await run(j,{worker,evaluator});
 assert.deepEqual(calls.map(b=>b.action),['combat_prefilter','select']);
 assert.equal(j.status,'complete');
 for(const [action,field] of [['combat_prefilter','combatAcceleration'],['select','acceleration']]){
  assert.equal(j[field].backend,action===failure?'cpu':'metal');
  if(action===failure){assert.equal(j[field].requested,'metal');assert.match(j[field].reason,/Metal explicit failure/);}
 }
 if(failure!=='select')assert.equal(j.incumbent.damage,123);
 assert.equal(j.results[0].result.total_damage,123);
});

test('UI enables Metal search independently of legacy CUDA and labels its device',async()=>{
 const source=readFileSync(new URL('../web/app.js',import.meta.url),'utf8').split('\n');
 const helper=source.find(l=>l.startsWith('function defaultDetailBackend('));
 const init=source.find(l=>l.startsWith("guarded(async()=>{const hardware=await api('/api/hardware')"));
 for(const available of [false,true]){
  const nodes=new Map(),pending=[];
  const $=id=>{if(!nodes.has(id))nodes.set(id,{querySelector:s=>$(id+'/'+s)});return nodes.get(id);};
  const hardware={available:false,metal:{available:true},metal_search:{available,device:'Apple M5',model:'combat-prefilter-metal-f32-v1'}};
  runInNewContext(helper+'\n'+init,{$,api:async()=>hardware,guarded:fn=>()=>{pending.push(fn());}});
  await Promise.all(pending);
  assert.equal($('selection-backend/[value="cuda"]').disabled,!available);
  assert.equal($('selection-backend').value,available?'metal':'cpu');
  if(available){assert.match($('gpu-status').textContent,/Apple M5 \/ Metal/);assert.match($('gpu-status').textContent,/概算で除いた候補の順位は保証できません/);}
 }
});

test('server accepts only named search backends and dispatches Metal in separate worker',()=>{
 const s=readFileSync(new URL('../server.mjs',import.meta.url),'utf8');
 assert.match(s,/\['cuda','metal','cpu'\]\.includes\(b.selectionBackend\)/);
 assert.match(s,/body.backend==='metal'&&\['combat_prefilter','select'\]\.includes\(body.action\)\|\|body.action==='metal_search_probe'/);
 assert.match(s,/const script='app\/metal_search.py'/);
 assert.match(s,/metal_search:metalSearch/);
});

test('HTTP validation accepts exactly cpu/cuda/metal without starting a worker',async()=>{
 const {server}=await import('../server.mjs');
 const request=body=>new Promise(resolve=>{
  const req={method:'POST',url:'/api/jobs',headers:{host:'127.0.0.1:4317'},async *[Symbol.asyncIterator](){yield Buffer.from(JSON.stringify(body));}};
  const res={writeHead(){},end(text){resolve(JSON.parse(text));}};
  server.emit('request',req,res);
 });
 for(const selectionBackend of ['metal','cuda','cpu',undefined]){
  const response=await request({kind:'unknown',selectionBackend});
  assert.equal(response.error,'Unknown job kind');
 }
 for(const selectionBackend of ['gpu','Metal','',null,false,true,1]){
  const response=await request({kind:'unknown',selectionBackend});
  assert.match(response.error,/GPU\/CPU/);
 }
});

for(const backend of ['metal','cuda'])test(`${backend} job retains preparation failures and their counts`,async()=>{
 const first=['a','b','c','d','e'],second=['f','g','h','i','j'];
 const j={kind:'optimize',selectionBackend:backend,teamCount:1,pool:[first,second],groups:[[0],[1]],evaluation:{compute_backend:'metal_detail'},cases:[{value:1},{value:2}],index:0,results:[]};
 const worker=async body=>body.action==='combat_prefilter'?{backend,scores:[{index:0,squad:first,damage:999}],prepared_candidates:1,scored_candidates:1,unscored_candidates:1,unscored_indices:[1],errors:[{index:1,squad:second,error:'preparation failed'}]}:{backend,recommendation:null};
 const evaluator={isCached:()=>false,many:async bodies=>bodies.map(body=>({result:{members:body.squad.map(name=>({name})),total_damage:123}}))};
 await run(j,{worker,evaluator});
 assert.equal(j.status,'complete');assert.equal(j.results.length,2);
 assert.deepEqual(j.pool,[first,second]);assert.equal(j.combatAcceleration.unscored_candidates,1);
 assert.equal(j.combatAcceleration.errors[0].error,'preparation failed');
 assert.deepEqual(j.results[1].result.members.map(m=>m.name),second);
});
