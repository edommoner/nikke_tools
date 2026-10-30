import {createEvaluator,advanceCases} from './app/evaluation-queue.mjs';
import {resolvePython} from './app/python-runtime.mjs';
import {portableEventRequest} from './app/portable_http_policy.mjs';
import {candidatePool,bestDisjoint,rankCombatPool} from './app/optimizer.mjs';
import http from 'node:http';
import {spawn} from 'node:child_process';
import {readFileSync, existsSync, statSync} from 'node:fs';
import {createHash, randomUUID} from 'node:crypto';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
const root = path.dirname(fileURLToPath(import.meta.url));
const port = Number(process.env.PORT || 4317);
const python = resolvePython();
const jobs = new Map(), cache = new Map();
const fingerprint = createHash('sha256').update(readFileSync(path.join(root, 'app/engine_worker.py'))).update(readFileSync(path.join(root, 'app/engine_compat.py'))).update(readFileSync(path.join(root, 'app/survival_compat.py'))).update(readFileSync(path.join(root, 'app/survival_scaling_compat.py'))).update(readFileSync(path.join(root, 'app/detail_gpu.py'))).update(readFileSync(path.join(root, 'app/detail_world.py'))).update(readFileSync(path.join(root, 'app/detail_boss.py'))).update(readFileSync(path.join(root, 'app/detail_effects-build.json'))).update(existsSync(path.join(root,'app/detail_effects-sm86.json'))?readFileSync(path.join(root,'app/detail_effects-sm86.json')):'').update(readFileSync(path.join(root, 'app/gpu_service.py'))).update(readFileSync(path.join(root,'app/portable_detail.py'))).update(readFileSync(path.join(root,'app/portable_detail_service.py'))).update(readFileSync(path.join(root,'app/portable_backend.py'))).update(readFileSync(path.join(root,'app/portable_runtime.py'))).update(readFileSync(path.join(root, 'data/import-mappings.json'))).update(readFileSync(path.join(root, 'data/engine-effect-overrides.json'))).update(readFileSync(path.join(root, 'research/engine-probe-results.json'))).digest('hex');
const clone = v => structuredClone(v);
const stable = v => v && typeof v === 'object' ? Array.isArray(v) ? v.map(stable) : Object.fromEntries(Object.keys(v).sort().map(k => [k, stable(v[k])])) : v;
let gpuProcess=null,gpuOutput='',gpuRequests=new Map();
function gpuWorker(body,job){
  if(!gpuProcess){
    const child=spawn(python,[path.join(root,'app/gpu_service.py')],{cwd:root,windowsHide:true,env:{...process.env,PYTHONIOENCODING:'utf-8',PYTHONUTF8:'1'}});
    gpuProcess=child;gpuOutput='';
    const fail=error=>{if(gpuProcess!==child)return;error.gpuUnavailable=true;gpuProcess=null;for(const pending of gpuRequests.values()){clearTimeout(pending.timer);pending.reject(error);}gpuRequests.clear();};
    child.on('error',fail);child.on('close',()=>fail(Error('GPUワーカーが終了しました。')));child.stderr.on('data',()=>{});
    child.stdin.on('error',fail);
    child.stdout.on('data',chunk=>{gpuOutput+=chunk.toString('utf8');let end;while((end=gpuOutput.indexOf('\n'))>=0){const line=gpuOutput.slice(0,end);gpuOutput=gpuOutput.slice(end+1);try{const response=JSON.parse(line),pending=gpuRequests.get(response.id);if(!pending)continue;gpuRequests.delete(response.id);clearTimeout(pending.timer);if(response.error)pending.reject(Error(response.error));else pending.resolve(response.result);}catch(error){child.kill();fail(error);}}});
  }
  const child=gpuProcess,id=randomUUID();if(job)job.child=child;
  return new Promise((resolve,reject)=>{const timer=setTimeout(()=>{const error=Error('GPU処理が制限時間を超えました。');error.gpuUnavailable=true;gpuRequests.delete(id);reject(error);child.kill();},['evaluate_detail','evaluate_detail_batch'].includes(body.action)?300000:120000);gpuRequests.set(id,{timer,resolve,reject});child.stdin.write(JSON.stringify({id,body})+'\n');}).finally(()=>{if(job?.child===child)job.child=null;});
}
process.on('exit',()=>gpuProcess?.kill());
export function sharedCudaConfigured(platform=process.platform,env=process.env) {
  return platform==='win32'&&['NIKKE_SLANG_GENERATION_CACHE','NIKKE_CUDA_COMPILE_CACHE'].every(k=>{
    try{return Boolean(env[k]&&path.isAbsolute(env[k])&&statSync(env[k]).isDirectory());}catch{return false;}
  });
}
export function workerTimeoutSeconds(body) {
  if(body.action==='evaluate_portable_detail_batch'&&body.evaluations?.[0]?.compute_backend==='cuda_shared_detail')return 120;
  // Match portable_runtime.evaluate's default backend.
  return body.action==='evaluate_portable_detail_batch' || body.action==='evaluate_portable_events' && (body.backend ?? 'metal')==='metal' ? 630 : 120;
}
function worker(body, job) {
  if(body.action==='gpu_probe'||body.action==='evaluate_detail'||body.action==='evaluate_detail_batch'||body.action==='combat_prefilter'||body.action==='select'&&body.backend==='cuda')return gpuWorker(body,job);
  return new Promise((resolve,reject) => {
    const script=body.action==='evaluate_portable_detail_batch'?'app/portable_detail_service.py':'app/engine_worker.py';
    const child = spawn(python, [path.join(root,script)], {cwd:root, windowsHide:true, env:{...process.env,PYTHONIOENCODING:'utf-8',PYTHONUTF8:'1'}});
    if (job) job.child=child;
    let out='', err='';
    // Metal may spend 2*90s generating sources, 300s compiling, then 120s on GPU.
    const timeoutSeconds = workerTimeoutSeconds(body);
    const timer=setTimeout(()=>{child.kill();reject(Error(`計算が${timeoutSeconds}秒を超えました。`));},timeoutSeconds*1000);
    child.stdout.on('data',b=>out+=b); child.stderr.on('data',b=>err+=b);
    child.on('error',e=>{clearTimeout(timer);reject(e);});
    child.on('close',code=>{
      clearTimeout(timer); if(job)job.child=null;
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
async function run(job) {
  if(job.running)return;
  job.running=true;job.status='running';
  try {
    if(job.kind==='optimize'&&job.selectionBackend==='cuda'&&!job.prefilterAttempted){
      job.prefilterAttempted=true;job.phase='GPUで戦闘を概算して候補を絞り込み中';
      try{
        const coarse=await worker({action:'combat_prefilter',evaluation:job.evaluation,squads:job.pool},job);
        if(job.status==='cancelled')return;
        const order=rankCombatPool(job.pool,job.groups,coarse.scores);
        const oldPool=job.pool,reverse=new Map(order.map((old,index)=>[old,index]));
        job.pool=order.map(i=>oldPool[i]);job.groups=job.groups.map(g=>g.map(i=>reverse.get(i)));
        job.cases=job.pool.slice(0,job.cases.length).map((squad,i)=>({value:i+1,evaluation:{...clone(job.evaluation),squad,stat_deltas:Object.fromEntries(Object.entries(job.evaluation.stat_deltas||{}).filter(([n])=>squad.includes(n)))}}));
        job.combatAcceleration={...coarse,scores:undefined};
        job.combatEstimates=new Map(coarse.scores.map(s=>[JSON.stringify(s.squad),s.damage]));
      }catch(error){if(job.status==='cancelled')return;job.combatAcceleration={backend:'cpu',reason:error.message};}
      job.phase=null;
      if(job.pauseRequested){job.status='paused';return;}
    }
    await advanceCases(job,evaluator);
    if(job.index===job.cases.length && job.status==='running'){
      if(job.kind==='optimize'&&job.selectionBackend==='cuda'){
        job.phase='GPUで部隊の組合せを評価中';
        try{
          const candidates=job.results.filter(r=>r.result).map(r=>({squad:r.result.members.map(m=>m.name),damage:r.result.total_damage}));
          const selected=await worker({action:'select',backend:'cuda',width:1024,teamCount:job.teamCount,candidates},job);
          if(job.status!=='cancelled'){
            const found=selected.recommendation;
            if(found){const names=found.teams.flatMap(t=>t.squad);if(found.teams.length!==job.teamCount||new Set(names).size!==job.teamCount*5||found.teams.reduce((n,t)=>n+t.damage,0)!==found.damage||found.teams.some(t=>!candidates.some(c=>JSON.stringify(c)===JSON.stringify(t))))throw Error('GPU result validation failed');
              if(!job.incumbent||found.damage>job.incumbent.damage)job.incumbent=found;}
            job.acceleration={...selected,at_candidates:job.index,recommendation:undefined};
          }
        }catch(error){if(job.status!=='cancelled')job.acceleration={backend:'cpu',requested:'cuda',reason:error.message};}
        job.phase=null;
      }
      if(job.status==='running')job.status='complete';
    }
  } catch(e){if(job.status!=='cancelled'){job.status='failed';job.error=e.message;}}
  finally {job.running=false;}
}
function view(job) {
  if(job.kind==='optimize'&&job.recommendationIndex!==job.index){
    const found=bestDisjoint(job.results,job.teamCount,job.groups);
    if(found&&(!job.incumbent||found.damage>job.incumbent.damage))job.incumbent=found;
    job.recommendationIndex=job.index;
  }
  if(job.combatAcceleration?.backend==='cuda'){
    const errors=job.results.filter(r=>r.result?.total_damage>0).map(r=>{const estimate=job.combatEstimates?.get(JSON.stringify(r.result.members.map(m=>m.name)));return estimate===undefined?null:Math.abs(estimate-r.result.total_damage)/r.result.total_damage;}).filter(v=>v!==null);
    job.combatAcceleration.validation={samples:errors.length,mean_absolute_relative_error:errors.length?errors.reduce((a,b)=>a+b,0)/errors.length:null,max_absolute_relative_error:errors.length?Math.max(...errors):null};
  }
  const feasible=job.results.filter(r=>r.meets);
  return {id:job.id,status:job.status,kind:job.kind,index:job.index,total:job.cases.length,results:job.results,error:job.error,
    target:job.target,strict:job.strict,best:feasible[0]||null,complete:job.status==='complete',updatedAt:job.updatedAt,
    combatAcceleration:job.combatAcceleration,selectionBackend:job.selectionBackend,phase:job.phase,acceleration:job.acceleration,recommendation:job.incumbent||null,poolSize:job.pool?.length,skipped:job.skipped,mode:job.mode,searchKind:job.searchKind,bestByField:Object.fromEntries([...new Set(feasible.map(r=>r.field).filter(Boolean))].map(f=>[f,feasible.find(r=>r.field===f)]))};
}
function json(res,value,code=200){res.writeHead(code,{'Content-Type':'application/json; charset=utf-8','Cache-Control':'no-store'});res.end(JSON.stringify(value));}
async function body(req){let size=0;const chunks=[];for await(const chunk of req){size+=chunk.length;if(size>12*1024*1024)throw Error('JSONは12MB以内にしてください。');chunks.push(chunk);}return JSON.parse(Buffer.concat(chunks).toString('utf8'));}
const assets = {'/':'index.html','/app.js':'app.js','/style.css':'style.css','/exporter.js':'exporter.js','/board-model.mjs':'board-model.mjs','/roster-model.mjs':'roster-model.mjs','/enemy-model.mjs':'enemy-model.mjs','/parts-model.mjs':'parts-model.mjs','/phase-model.mjs':'phase-model.mjs'};
const server=http.createServer(async(req,res)=>{
  try {
    const url=new URL(req.url,`http://127.0.0.1:${port}`);
    if(!['127.0.0.1','localhost'].includes((req.headers.host||'').split(':')[0]))return json(res,{error:'Host rejected'},403);
    if(req.headers.origin && ![`http://127.0.0.1:${port}`,`http://localhost:${port}`].includes(req.headers.origin))return json(res,{error:'Origin rejected'},403);
    if(req.method==='GET' && assets[url.pathname]) {
      const file=assets[url.pathname];res.writeHead(200,{'Content-Type':(/\.m?js$/.test(file))?'text/javascript; charset=utf-8':file.endsWith('.css')?'text/css; charset=utf-8':'text/html; charset=utf-8','X-Content-Type-Options':'nosniff','Content-Security-Policy':"default-src 'self'; script-src 'self'; style-src 'self'; connect-src 'self'; img-src 'self' data: https://sg-tools-cdn.blablalink.com; object-src 'none'; base-uri 'none'; frame-ancestors 'none'"});res.end(readFileSync(path.join(root,'web',file)));return;
    }
    if(req.method==='GET' && url.pathname==='/api/hardware'){const gpu=await worker({action:'gpu_probe'});return json(res,{...gpu,metal:{available:process.platform==='darwin',verification:'per-request'},shared_cuda:{available:sharedCudaConfigured(),verification:'per-request',cold_compilation:false}});}
    if(req.method==='GET' && url.pathname==='/api/catalog')return json(res,await worker({action:'catalog'}));
    if(req.method==='GET' && url.pathname==='/api/demo')return json(res,await worker({action:'demo',expanded:url.searchParams.get('expanded')==='true',gpu_detail:url.searchParams.get('gpu_detail')==='true'}));
    if(req.method==='POST' && url.pathname==='/api/portable-events')return json(res,await worker(portableEventRequest(await body(req))));
    if(req.method==='POST' && url.pathname==='/api/import'){const data=await body(req);return json(res,await worker({action:'import',data}));}
    if(req.method==='POST' && url.pathname==='/api/jobs') {
      const b=await body(req);
      if(b.selectionBackend&&!['cuda','cpu'].includes(b.selectionBackend))throw Error('GPU/CPUの指定が正しくありません。');
      if([...jobs.values()].some(j=>j.running))throw Error('実行中の計算を一時停止または終了してから開始してください。');
      if(jobs.size>=30){const old=[...jobs.values()].find(j=>!j.running&&j.status!=='paused');if(!old)throw Error('保持できる計算が上限です。');jobs.delete(old.id);}
      let cases;
      let pool,groups,skipped,teamCount;
      if(b.kind==='optimize'){
        teamCount=b.teamCount===1?1:5;
        const scored=await worker({action:'candidates',evaluation:b.evaluation,excluded:b.excluded||[]});
        ({pool,groups}=candidatePool(scored.characters,teamCount,b.selectionBackend==='cuda'?800:160,41,scored.templates));skipped=scored.skipped;
        const limit={fast:20,detail:80,long:160}[b.mode];if(!limit)throw Error('探索モードを選択してください。');
        cases=pool.slice(0,limit).map((squad,i)=>({value:i+1,evaluation:{...clone(b.evaluation),squad,stat_deltas:Object.fromEntries(Object.entries(b.evaluation.stat_deltas||{}).filter(([n])=>squad.includes(n)))}}));
      }
      else if(b.kind==='search')cases=searchCases(b);
      else if(b.kind==='board')cases=boardCases(b.teams);
      else if(b.kind==='compare')cases=[{value:'原本',evaluation:{...clone(b.evaluation),patches:{},stat_deltas:{}}},{value:'検討案',evaluation:clone(b.evaluation)}];
      else throw Error('Unknown job kind');
      const job={id:randomUUID(),kind:b.kind,cases,index:0,results:[],target:b.target,strict:!!b.strict,status:'queued',updatedAt:Date.now(),pool,groups,skipped,teamCount,selectionBackend:b.selectionBackend||'cpu',mode:b.mode,searchKind:b.variable?.kind,evaluation:clone(b.evaluation)};jobs.set(job.id,job);void run(job);return json(res,view(job),202);
    }
    const match=url.pathname.match(/^\/api\/jobs\/([\w-]+)(?:\/(pause|resume|cancel|extend))?$/);
    if(match){const job=jobs.get(match[1]);if(!job)return json(res,{error:'計算情報がありません。サーバー再起動後は新しく実行してください。'},404);
      if(req.method==='POST'){
        const op=match[2];
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
        }else if(op==='cancel'){job.status='cancelled';job.child?.kill();}
        else throw Error('現在の状態では操作できません。');
      }else if(req.method!=='GET')return json(res,{error:'Method not allowed'},405);
      return json(res,view(job));
    }
    json(res,{error:'Not found'},404);
  }catch(e){json(res,{error:e.message},400);}
});
if(process.argv[1]===fileURLToPath(import.meta.url))server.listen(port,'127.0.0.1',()=>console.log(`NIKKE TOOLS http://127.0.0.1:${port}`));
export {server,body as readJSONBody};









