import {ownNativeProcessGroup} from './app/native-worker-process.mjs';
import {verifyOptimizer,verificationView,recommendationForView} from './app/optimizer-verification.mjs';
import {attachBrowser,cancelBrowser,acceptBrowserResults,browserWasm} from './app/browser-transport.mjs';
import {createEvaluator,advanceCases} from './app/evaluation-queue.mjs';
import {resolvePython} from './app/python-runtime.mjs';
import {sharedToolEnv} from './app/tool-roots.mjs';
import {portableEventRequest} from './app/portable_http_policy.mjs';
import {candidatePool,swapCandidates} from './app/optimizer.mjs';
import http from 'node:http';
import {spawn} from 'node:child_process';
import {readFileSync, existsSync, statSync, lstatSync} from 'node:fs';
import {createHash, randomUUID} from 'node:crypto';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
const root = path.dirname(fileURLToPath(import.meta.url));
const port = Number(process.env.PORT || 4317);
const python = resolvePython();
const toolEnv = sharedToolEnv(root);
const jobs = new Map(), cache = new Map();
const fingerprint = createHash('sha256').update(readFileSync(path.join(root, 'app/engine_worker.py'))).update(readFileSync(path.join(root, 'app/synergy_profile.py'))).update(readFileSync(path.join(root, 'app/engine_revision.py'))).update(readFileSync(path.join(root, 'data/engine-revisions.json'))).update(readFileSync(path.join(root, 'app/engine_gpu_admission.py'))).update(readFileSync(path.join(root, 'app/engine_compat.py'))).update(readFileSync(path.join(root, 'app/survival_compat.py'))).update(readFileSync(path.join(root, 'app/survival_scaling_compat.py'))).update(readFileSync(path.join(root, 'app/detail_gpu.py'))).update(readFileSync(path.join(root, 'app/detail_world.py'))).update(readFileSync(path.join(root, 'app/detail_boss.py'))).update(readFileSync(path.join(root,'app/portable_detail.py'))).update(readFileSync(path.join(root,'app/portable_product_healing.py'))).update(readFileSync(path.join(root,'app/portable_product_weighted.py'))).update(readFileSync(path.join(root,'app/portable_product_ammo.py'))).update(readFileSync(path.join(root,'app/enemy_ammo_model.py'))).update(readFileSync(path.join(root,'app/portable_resource_decode.py'))).update(readFileSync(path.join(root,'app/portable_enemy_ammo_readback.py'))).update(readFileSync(path.join(root,'app/portable_product_world_contract.py'))).update(readFileSync(path.join(root,'app/portable_product_cover.py'))).update(readFileSync(path.join(root,'app/cover_defense_battle_model.py'))).update(readFileSync(path.join(root,'app/portable_declared_manual_sequences.py'))).update(readFileSync(path.join(root,'app/weighted_incoming_battle_model.py'))).update(readFileSync(path.join(root,'app/product_reference_models.py'))).update(readFileSync(path.join(root,'app/product_lock_model.py'))).update(readFileSync(path.join(root,'app/portable_product_locks.py'))).update(readFileSync(path.join(root,'app/portable_product_coordinate_lock.py'))).update(readFileSync(path.join(root,'app/portable_product_typed_lock.py'))).update(readFileSync(path.join(root,'app/portable_product_fixed.py'))).update(readFileSync(path.join(root,'app/product_movement_model.py'))).update(readFileSync(path.join(root,'app/product_coordinate_model.py'))).update(readFileSync(path.join(root,'app/product_typed_model.py'))).update(readFileSync(path.join(root,'app/portable_product_typed.py'))).update(readFileSync(path.join(root,'app/product_named_range_model.py'))).update(readFileSync(path.join(root,'app/portable_product_coordinate.py'))).update(readFileSync(path.join(root,'app/portable_product_named_carriers.py'))).update(readFileSync(path.join(root,'app/portable_product_named_range.py'))).update(readFileSync(path.join(root,'app/named_range_battle.py'))).update(readFileSync(path.join(root,'app/effect_range_policy.py'))).update(readFileSync(path.join(root,'app/effect_target_count_policy.py'))).update(readFileSync(path.join(root,'app/portable_product_movement.py'))).update(readFileSync(path.join(root,'app/enemy_movement_model.py'))).update(readFileSync(path.join(root,'app/coordinate_logical_actor_geometry.py'))).update(readFileSync(path.join(root,'app/portable_coordinate_sample_v1.py'))).update(readFileSync(path.join(root,'research/coordinate_geometry_reference.py'))).update(readFileSync(path.join(root,'research/portable_coordinate_math_cases.py'))).update(readFileSync(path.join(root,'app/enemy_healing_model.py'))).update(readFileSync(path.join(root,'app/portable_world_result.py'))).update(readFileSync(path.join(root,'app/portable_product_add_attack.py'))).update(readFileSync(path.join(root,'app/portable_detail_service.py'))).update(readFileSync(path.join(root,'app/portable_backend.py'))).update(readFileSync(path.join(root,'app/portable_native.py'))).update(readFileSync(path.join(root,'app/portable_wasm.py'))).update(readFileSync(path.join(root,'scripts/wasm-product-host.cpp'))).update(readFileSync(path.join(root,'scripts/wasm-platform.h'))).update(readFileSync(path.join(root,'app/portable_slang_generation.py'))).update(readFileSync(path.join(root,'scripts/native-product-host.cpp'))).update(readFileSync(path.join(root,'app/portable_runtime.py'))).update(readFileSync(path.join(root,'data/portable-product-programs.json'))).update(readFileSync(path.join(root, 'data/import-mappings.json'))).update(readFileSync(path.join(root, 'data/engine-effect-overrides.json'))).update(readFileSync(path.join(root, 'research/engine-probe-results.json'))).digest('hex');
export function nativeHardware(module='portable_native') {
  return new Promise(resolve=>{
    const child=spawn(python,['-c',`import json; from pathlib import Path; from ${module} import availability; print(json.dumps(availability(Path.cwd())))`],{cwd:root,env:{...process.env,...toolEnv,PYTHONPATH:path.join(root,'app')},windowsHide:true});
    let output='';const fail=reason=>resolve({available:false,device:'',reason});
    const timer=setTimeout(()=>{child.kill();fail('CPU高速計算の環境確認が制限時間を超えました。');},10000);
    child.stdout.on('data',data=>{output+=data;});child.stderr.on('data',()=>{});
    child.on('error',error=>{clearTimeout(timer);fail(error.message);});
    child.on('close',code=>{clearTimeout(timer);try{if(code!==0)throw Error('CPU高速計算の環境を確認できません。');resolve(JSON.parse(output));}catch(error){fail(error.message);}});
  });
}
const clone = v => structuredClone(v);
const stable = v => v && typeof v === 'object' ? Array.isArray(v) ? v.map(stable) : Object.fromEntries(Object.keys(v).sort().map(k => [k, stable(v[k])])) : v;
export function workerTextStreams(child) {
  child.stdout.setEncoding('utf8');child.stderr.setEncoding('utf8');
  return child;
}
export function workerTimeoutSeconds(body) {
  if(['evaluate_portable_detail_batch','prepare_browser_wires','finish_browser'].includes(body.action))return 1110*Math.min(32,Math.max(1,body.evaluations?.length||1));
  return 120;
}
function worker(body, job) {
  return new Promise((resolve,reject) => {
    const script=['evaluate_portable_detail_batch','prepare_browser_wires','finish_browser','verify_portable_detail','cpu_fallback_portable_detail'].includes(body.action)?'app/portable_detail_service.py':'app/engine_worker.py';
    const nativeGroup=body.action==='evaluate_portable_detail_batch'&&body.evaluations?.[0]?.compute_backend==='native_detail'&&process.platform!=='win32';
    const child = workerTextStreams(spawn(python, [path.join(root,script)], {cwd:root, detached:nativeGroup, windowsHide:true, env:{...process.env,...toolEnv,PYTHONIOENCODING:'utf-8',PYTHONUTF8:'1'}}));
    ownNativeProcessGroup(child,nativeGroup);
    if (job) {job.child=child;(job.children ||= new Set()).add(child);}
    let out='', err='';
    // Cover every possible source group, compilation and bounded execution phase.
    const timeoutSeconds = workerTimeoutSeconds(body);
    const timer=setTimeout(()=>{child.kill();reject(Error(`計算が${timeoutSeconds}秒を超えました。`));},timeoutSeconds*1000);
    child.stdout.on('data',b=>out+=b); child.stderr.on('data',b=>err+=b);
    child.on('error',e=>{clearTimeout(timer);reject(e);});
    child.on('close',code=>{
      clearTimeout(timer); if(job){if(job.child===child)job.child=null;job.children?.delete(child);}
      try {const value=JSON.parse(out); if(code || value.error) reject(Error(value.error || err || '計算に失敗しました。')); else resolve(value);}
      catch(e){reject(Error(err || e.message));}
    });
    child.stdin.on('error',()=>{}); child.stdin.end(JSON.stringify(body));
  });
}
const evaluator=createEvaluator({worker,cache,keyOf:body=>createHash('sha256').update(fingerprint+JSON.stringify(stable(body))).digest('hex')});
const evaluate=evaluator.one;
function integer(v,lo,hi,label){if(!Number.isInteger(v)||v<lo||v>hi)throw Error(`${label}: ${lo}〜${hi}の整数を指定してください。`);return v;}
function skillDict(value){if(value===undefined)return {};if(typeof value==='number')return {'1':value,'2':value,'3':value};if(typeof value==='string')value=value.split('/').map(Number);if(Array.isArray(value))return Object.fromEntries(value.map((v,i)=>[String(i+1),v]));return {...value};}
function rangedNumber(v,lo,hi,label){if(typeof v!=='number'||!Number.isFinite(v)||v<lo||v>hi)throw Error(`${label}: ${lo}〜${hi}の数値を指定してください。`);return v;}
export function searchCases(body) {
  const {variable} = body;
  if(!variable || !body.evaluation.squad.includes(variable.character))throw Error('探索するキャラを編成から選んでください。');
  const kind=variable.kind;
  if(kind==='auto'){
    const n=variable.character,entry=body.evaluation.profile.chars[n],patch=body.evaluation.patches?.[n]||{};
    const cases=[];
    for(const [field,slot]of [['skill1','1'],['skill2','2'],['burst','3']]){
      const current=skillDict(patch.skill_levels)[slot]??skillDict(entry.skill_levels)[slot];
      if(!Number.isInteger(current))throw Error('項目比較にはスキルLvの入力が必要です。');
      cases.push(...searchCases({...body,variable:{...variable,kind:field,min:current,max:10,step:1}}).map(c=>({...c,field})));
    }
    for(const field of ['atk','hp','def']){
      const current=body.evaluation.stat_deltas?.[n]?.[field]||0;
      for(const offset of [0,5000,10000,20000])cases.push(...searchCases({...body,variable:{...variable,kind:field,min:current+offset,max:current+offset,step:1}}).map(c=>({...c,field})));
    }
    return cases;
  }
  if(!['skill1','skill2','burst','atk','hp','def','element_bonus','atk_pct','charge_speed_pct','max_ammo_pct'].includes(kind))throw Error('未対応の探索項目です。');
  const min=rangedNumber(variable.min,0,10000000,'開始値'), max=rangedNumber(variable.max,min,10000000,'終了値'), step=rangedNumber(variable.step,0.000001,10000000,'刻み幅');
  if(['skill1','skill2','burst'].includes(kind)&&(![min,max,step].every(Number.isInteger)||min<1||max>10))throw Error('スキルLvは1〜10の整数です。');
  const count=Math.floor((max-min)/step+1e-7)+1;
  if(count>32)throw Error('試作では探索候補を32件以内にしてください。');
  if(!Number.isFinite(body.target)||body.target<=0)throw Error('目標ダメージを指定してください。');
  return Array.from({length:count},(_,i)=>{
    const value=Number((min+i*step).toFixed(8)),evaluation=clone(body.evaluation),name=variable.character;
    if(['atk','hp','def'].includes(kind)) {
      evaluation.stat_deltas ||= {};evaluation.stat_deltas[name] ||= {};evaluation.stat_deltas[name][kind]=value;
    } else {
      evaluation.patches ||= {};evaluation.patches[name] ||= {};
      if(['skill1','skill2','burst'].includes(kind)) {
        const slot={skill1:'1',skill2:'2',burst:'3'}[kind];
        evaluation.patches[name].skill_levels=skillDict(evaluation.patches[name].skill_levels);evaluation.patches[name].skill_levels[slot]=value;
      } else {
        evaluation.patches[name].equip_skills ||= {};evaluation.patches[name].equip_skills[kind]=value;
      }
    }
    return {value,evaluation};
  });
}
export function batchCases(evaluations){
  if(!Array.isArray(evaluations)||evaluations.length<1||evaluations.length>32)throw Error('独立した計算要求を1〜32件指定してください。');
  return evaluations.map((evaluation,index)=>{
    if(!evaluation||typeof evaluation!=='object'||Array.isArray(evaluation))throw Error('各計算要求はオブジェクトで指定してください。');
    return {value:index+1,evaluation:structuredClone(evaluation)};
  });
}
export function boardCases(teams){
  if(!Array.isArray(teams)||teams.length<1||teams.length>5)throw Error('計算する部隊を1〜5部隊指定してください。');
  const used=new Set(),indices=new Set();
  return teams.map(t=>{
    if(!Number.isInteger(t.index)||t.index<0||t.index>4||indices.has(t.index)||!Array.isArray(t.evaluation?.squad)||t.evaluation.squad.length!==5)throw Error('部隊の指定が正しくありません。');
    indices.add(t.index);
    for(const name of t.evaluation.squad){if(typeof name!=='string'||!name||used.has(name))throw Error('同じキャラを複数の部隊に編成できません。');used.add(name);}
    return {value:t.index+1,evaluation:structuredClone(t.evaluation)};
  });
}
function validateSwap(body){
  const squad=body.evaluation?.squad;
  if(!Array.isArray(squad)||squad.length!==5||!squad.every(n=>typeof n==='string'&&n.trim())||new Set(squad).size!==5)throw Error('入れ替えには異なる5人の部隊を指定してください。');
  integer(body.slot,0,4,'入れ替える枠');
}
export function swapCases(body,scored){
  validateSwap(body);
  const {squad}=body.evaluation,{slot}=body;
  const {names,total}=swapCandidates(scored.characters,squad,slot,{synergyOrder:body.synergyOrder,sameStage:body.sameStage,skip:body.skip});
  const cases=body.includeBaseline?[{value:'現在',evaluation:clone(body.evaluation)}]:[];
  for(const name of names){
    const evaluation=clone(body.evaluation);evaluation.squad[slot]=name;
    evaluation.stat_deltas=Object.fromEntries(Object.entries(evaluation.stat_deltas||{}).filter(([n])=>evaluation.squad.includes(n)));
    cases.push({value:name,evaluation});
  }
  return {cases,swap:{slot,outgoing:squad[slot],remaining:total-names.length,names,bursts:Object.fromEntries(scored.characters.map(c=>[c.name,c.burst]))},skipped:scored.skipped};
}
const optimizerWorker=worker,optimizerEvaluator=evaluator;
export function cancelJob(job){
  job.status='cancelled';cancelBrowser(job);
  for(const child of new Set([...(job.children||[]),job.child].filter(Boolean)))child.kill();
}
export async function run(job,{worker=optimizerWorker,evaluator=optimizerEvaluator}={}) {
  if(job.running)return;
  attachBrowser(job);
  job.running=true;job.status='running';
  try {
    if(job.kind==='swap'){
      while(job.index<job.cases.length&&job.status==='running'){
        const item=job.cases[job.index];let row;
        const evaluation={...item.evaluation,stat_deltas:Object.fromEntries(Object.entries(item.evaluation.stat_deltas||{}).filter(([n])=>item.evaluation.squad.includes(n)))};
        try{row={value:item.value,result:await evaluator.one(evaluation,job)};}
        catch(error){row={value:item.value,error:error.message};}
        if(job.status==='cancelled')break;
        job.results.push(row);job.index++;job.updatedAt=Date.now();
        if(job.pauseRequested){job.status='paused';break;}
      }
    }else await advanceCases(job,evaluator);
    if(job.index===job.cases.length && job.status==='running'){
      await verifyOptimizer(job,evaluator);
      if(job.status==='running')job.status=job.pauseRequested?'paused':'complete';
    }else if(job.kind==='optimize'&&job.status==='paused'){
      job.status='running';await verifyOptimizer(job,evaluator);
      if(job.status==='running')job.status='paused';
    }
  } catch(e){if(job.status!=='cancelled'){job.status='failed';job.error=e.message;}}
  finally {job.running=false;}
}
export function view(job) {
  const feasible=job.results.filter(r=>r.meets);
  return {verification:verificationView(job),browser_request:job.awaitingBrowser,id:job.id,status:job.status,kind:job.kind,index:job.index,total:job.cases.length,results:job.results,error:job.error,
    target:job.target,strict:job.strict,best:feasible[0]||null,complete:job.status==='complete',updatedAt:job.updatedAt,
    combatAcceleration:job.combatAcceleration,selectionBackend:job.selectionBackend,phase:job.phase,acceleration:job.acceleration,recommendation:recommendationForView(job),poolSize:job.pool?.length,swap:job.swap,skipped:job.skipped,mode:job.mode,searchKind:job.searchKind,bestByField:Object.fromEntries([...new Set(feasible.map(r=>r.field).filter(Boolean))].map(f=>[f,feasible.find(r=>r.field===f)]))};
}
function json(res,value,code=200){res.writeHead(code,{'Content-Type':'application/json; charset=utf-8','Cache-Control':'no-store'});res.end(JSON.stringify(value));}
async function body(req){let size=0;const chunks=[];for await(const chunk of req){size+=chunk.length;if(size>12*1024*1024)throw Error('JSONは12MB以内にしてください。');chunks.push(chunk);}return JSON.parse(Buffer.concat(chunks).toString('utf8'));}
const assets = {'/synergy-views.mjs':'synergy-views.mjs','/damage-groups.mjs':'damage-groups.mjs','/browser-worker.js':'browser-worker.js','/growth-model.mjs':'growth-model.mjs','/':'index.html','/app.js':'app.js','/style.css':'style.css','/exporter.js':'exporter.js','/board-model.mjs':'board-model.mjs','/roster-model.mjs':'roster-model.mjs','/enemy-model.mjs':'enemy-model.mjs','/parts-model.mjs':'parts-model.mjs','/phase-model.mjs':'phase-model.mjs','/synergy-model.mjs':'synergy-model.mjs','/synergy-labels.mjs':'synergy-labels.mjs'};
const server=http.createServer(async(req,res)=>{
  try {
    const url=new URL(req.url,`http://127.0.0.1:${port}`);
    if(!['127.0.0.1','localhost'].includes((req.headers.host||'').split(':')[0]))return json(res,{error:'Host rejected'},403);
    if(req.headers.origin && ![`http://127.0.0.1:${port}`,`http://localhost:${port}`].includes(req.headers.origin))return json(res,{error:'Origin rejected'},403);
    if(req.method==='GET' && assets[url.pathname]) {
      const file=assets[url.pathname];res.writeHead(200,{'Content-Type':(/\.m?js$/.test(file))?'text/javascript; charset=utf-8':file.endsWith('.css')?'text/css; charset=utf-8':'text/html; charset=utf-8','X-Content-Type-Options':'nosniff','Content-Security-Policy':"default-src 'self'; script-src 'self' 'wasm-unsafe-eval'; worker-src 'self'; style-src 'self'; connect-src 'self'; img-src 'self' data: https://sg-tools-cdn.blablalink.com https://www.blablalink.com/assets/nikke/version/default/shiftysassets/images/; object-src 'none'; base-uri 'none'; frame-ancestors 'none'"});res.end(readFileSync(path.join(root,'web',file)));return;
    }
    if(req.method==='GET' && url.pathname==='/api/hardware')return json(res,{native:await nativeHardware(),browser:await nativeHardware('portable_wasm')});
    if(req.method==='GET' && url.pathname.startsWith('/api/browser-wasm/')){
      try{const raw=browserWasm(root,url.pathname.slice('/api/browser-wasm/'.length));res.writeHead(200,{'Content-Type':'application/wasm','X-Content-Type-Options':'nosniff','Cache-Control':'private, max-age=31536000, immutable'});res.end(raw);return;}
      catch{return json(res,{error:'ブラウザ計算のWASMが見つかりません。'},404);}
    }
    if(req.method==='GET' && url.pathname==='/api/catalog')return json(res,await worker({action:'catalog'}));
    if(req.method==='GET' && url.pathname==='/api/demo')return json(res,await worker({action:'demo',expanded:url.searchParams.get('expanded')==='true',detail:url.searchParams.get('detail')==='true'}));
    if(req.method==='POST' && url.pathname==='/api/portable-events')return json(res,await worker(portableEventRequest(await body(req))));
    if(req.method==='POST' && url.pathname==='/api/import'){const data=await body(req);return json(res,await worker({action:'import',data}));}
    if(req.method==='POST' && url.pathname==='/api/jobs') {
      const b=await body(req);
      if(b.selectionBackend!==undefined&&b.selectionBackend!=='cpu')throw Error('候補選択方法の指定が正しくありません。');
      if([...jobs.values()].some(j=>j.running))throw Error('実行中の計算を一時停止または終了してから開始してください。');
      if(jobs.size>=30){const old=[...jobs.values()].find(j=>!j.running&&j.status!=='paused');if(!old)throw Error('保持できる計算が上限です。');jobs.delete(old.id);}
      let cases;
      let pool,groups,skipped,teamCount,swap;
      if(b.kind==='optimize'){
        teamCount=b.teamCount===1?1:5;
        const scored=await worker({action:'candidates',evaluation:b.evaluation,excluded:b.excluded||[]});
        ({pool,groups}=candidatePool(scored.characters,teamCount,160,41,scored.templates));skipped=scored.skipped;
        const limit={fast:20,detail:80,long:160}[b.mode];if(!limit)throw Error('探索モードを選択してください。');
        cases=pool.slice(0,limit).map((squad,i)=>({value:i+1,evaluation:{...clone(b.evaluation),squad,stat_deltas:Object.fromEntries(Object.entries(b.evaluation.stat_deltas||{}).filter(([n])=>squad.includes(n)))}}));
      }
      else if(b.kind==='swap'){
        validateSwap(b);
        const scored=await worker({action:'candidates',evaluation:b.evaluation,excluded:b.excluded||[]});
        const missingMembers=b.evaluation.squad.filter(n=>!scored.characters.some(c=>c.name===n));
        if(missingMembers.length){
          const catalog=await worker({action:'catalog'});
          scored.characters.push(...catalog.characters.filter(c=>missingMembers.includes(c.name)).map(c=>({name:c.name,burst:c.burst,potential:0})));
        }
        ({cases,swap,skipped}=swapCases(b,scored));
      }
      else if(b.kind==='search')cases=searchCases(b);
      else if(b.kind==='board')cases=boardCases(b.teams);
      else if(b.kind==='batch')cases=batchCases(b.evaluations);
      else if(b.kind==='compare')cases=[{value:'原本',evaluation:{...clone(b.evaluation),patches:{},stat_deltas:{}}},{value:'検討案',evaluation:clone(b.evaluation)}];
      else throw Error('Unknown job kind');
      const job={id:randomUUID(),kind:b.kind,cases,index:0,results:[],target:b.target,strict:!!b.strict,status:'queued',updatedAt:Date.now(),pool,groups,skipped,teamCount,swap,selectionBackend:b.selectionBackend||'cpu',mode:b.mode,searchKind:b.variable?.kind,evaluation:clone(b.evaluation)};jobs.set(job.id,job);void run(job);return json(res,view(job),202);
    }
    const match=url.pathname.match(/^\/api\/jobs\/([\w-]+)(?:\/(pause|resume|cancel|extend|browser-results))?$/);
    if(match){const job=jobs.get(match[1]);if(!job)return json(res,{error:'計算情報がありません。サーバー再起動後は新しく実行してください。'},404);
      if(req.method==='POST'){
        const op=match[2];
        if(op==='browser-results'){acceptBrowserResults(job,await body(req),req.headers['user-agent']||'Browser');return json(res,{accepted:true});}
        if(op==='extend'){
          if(job.kind!=='optimize'||job.running)throw Error('探索が停止または完了してから続けてください。');
          if([...jobs.values()].some(j=>j.running))throw Error('別の計算が実行中です。');
          const b=await body(req),limit={detail:80,long:160}[b.mode];if(!limit)throw Error('詳細または長時間を選択してください。');
          if(limit<=job.cases.length||job.cases.length===job.pool.length)throw Error('この候補群はすでに計算済みです。');
          job.cases=job.pool.slice(0,limit).map((squad,i)=>({value:i+1,evaluation:{...clone(job.evaluation),squad,stat_deltas:Object.fromEntries(Object.entries(job.evaluation.stat_deltas||{}).filter(([n])=>squad.includes(n)))}}));
          job.mode=b.mode;job.pauseRequested=false;void run(job);return json(res,view(job));
        }
        if(op==='pause'&&job.status==='running')job.pauseRequested=true;
        else if(op==='resume'&&job.status==='paused'){
          if([...jobs.values()].some(j=>j.running))throw Error('別の計算が実行中です。');
          job.pauseRequested=false;void run(job);
        }else if(op==='cancel'){cancelJob(job);}
        else throw Error('現在の状態では操作できません。');
      }else if(req.method!=='GET')return json(res,{error:'Method not allowed'},405);
      return json(res,view(job));
    }
    json(res,{error:'Not found'},404);
  }catch(e){json(res,{error:e.message},400);}
});
if(process.argv[1]===fileURLToPath(import.meta.url))server.listen(port,'127.0.0.1',()=>console.log(`NIKKE TOOLS http://127.0.0.1:${port}`));
export {server,body as readJSONBody};
