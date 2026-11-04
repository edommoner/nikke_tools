import test from 'node:test';
import assert from 'node:assert/strict';
import {searchCases} from '../server.mjs';
import {readFileSync,mkdtempSync,writeFileSync,rmSync} from 'node:fs';
import {tmpdir} from 'node:os';
import path from 'node:path';
test('independent batch jobs preserve overlapping rosters and all per-request conditions',async()=>{
 const {batchCases,boardCases}=await import('../server.mjs');
 const first={squad:['a','b','c','d','e'],profile:{chars:{a:{skill_levels:3}}},compute_backend:'metal_detail'};
 const second={...structuredClone(first),compute_backend:'cuda_shared_detail',stat_deltas:{a:{atk:5}}};
 const saved=structuredClone([first,second]),cases=batchCases([first,second]);
 assert.deepEqual(cases.map(c=>c.value),[1,2]);assert.deepEqual(cases.map(c=>c.evaluation),saved);
 cases[0].evaluation.profile.chars.a.skill_levels=10;
 assert.deepEqual([first,second],saved);assert.equal(cases[1].evaluation.profile.chars.a.skill_levels,3);
 assert.throws(()=>boardCases([{index:0,evaluation:first},{index:1,evaluation:second}]),/同じキャラ/);
 for(const bad of [null,{},[],Array(33).fill(first),[null],[[]],[1]])assert.throws(()=>batchCases(bad));
 assert.equal(batchCases(Array(32).fill(first)).length,32);
});
test('search preserves original input and all unrelated scenario fields',()=>{
  const body={evaluation:{squad:['a'],profile:{chars:{a:{skill_levels:{'1':7,'2':6,'3':5}}}},patches:{a:{skill_levels:{'1':8}}},stat_deltas:{a:{hp:300}}},target:100,variable:{character:'a',kind:'burst',min:7,max:10,step:1}};
  const copy=structuredClone(body),cases=searchCases(body);
  assert.deepEqual(body,copy);assert.equal(cases.length,4);
  assert.equal(cases[0].evaluation.patches.a.skill_levels['3'],7);
  assert.equal(cases[3].evaluation.patches.a.skill_levels['1'],8);
  assert.equal(cases[3].evaluation.stat_deltas.a.hp,300);
  cases[0].evaluation.patches.a.skill_levels['1']=1;
  assert.equal(cases[1].evaluation.patches.a.skill_levels['1'],8);
});
test('bounded exhaustive search rejects invalid ranges and unowned targets',()=>{
  const b={evaluation:{squad:['a']},target:100,variable:{character:'a',kind:'atk',min:0,max:50000,step:1}};
  assert.throws(()=>searchCases(b),/32/);
  b.variable.max=100;b.variable.step=0;assert.throws(()=>searchCases(b));
  b.variable.step=1;b.variable.character='b';assert.throws(()=>searchCases(b),/キャラ/);
});
test('automatic alternatives enumerate each field separately without mutating other stats',()=>{
  const body={evaluation:{squad:['a'],profile:{chars:{a:{skill_levels:{'1':1,'2':1,'3':1}}}},patches:{a:{skill_levels:{'2':8}}},stat_deltas:{a:{atk:500}}},target:100,variable:{character:'a',kind:'auto'}};
  const saved=structuredClone(body),cases=searchCases(body);
  assert.deepEqual(body,saved);assert.equal(cases.length,35);
  assert.equal(cases.filter(c=>c.field==='skill2').length,3);
  assert.deepEqual(cases.filter(c=>c.field==='atk').map(c=>c.value),[500,5500,10500,20500]);
  assert.equal(cases.filter(c=>c.field==='hp')[1].evaluation.stat_deltas.a.atk,500);
});
test('UTF-8 roster data remains intact across arbitrary network chunk boundaries',async()=>{
  const {readJSONBody}=await import('../server.mjs');
  const original={chars:{'히메노':{name:'ラピ：レッドフード'}},note:'育成データ'};
  const bytes=Buffer.from(JSON.stringify(original));
  async function* oneByteChunks(){for(const byte of bytes)yield Buffer.from([byte]);}
  assert.deepEqual(await readJSONBody(oneByteChunks()),original);
});
test('decimal overload ranges retain exact displayed values',()=>{
  const cases=searchCases({evaluation:{squad:['a']},target:100,variable:{character:'a',kind:'atk_pct',min:22.22,max:22.42,step:0.1}});
  assert.deepEqual(cases.map(c=>c.value),[22.22,22.32,22.42]);
});
test('alternative skill representations preserve unrelated skill levels',()=>{
  const body={evaluation:{squad:['a'],profile:{chars:{a:{skill_levels:[1,2,3]}}},patches:{a:{skill_levels:[7,8,9]}}},target:100,variable:{character:'a',kind:'auto'}};
  const cases=searchCases(body);assert.deepEqual(cases.filter(c=>c.field==='skill2').map(c=>c.value),[8,9,10]);
  const burst=cases.find(c=>c.field==='burst'&&c.value===10);
  assert.deepEqual(burst.evaluation.patches.a.skill_levels,{'1':7,'2':8,'3':10});
});

 test('portable Metal HTTP deadline covers source generation, compilation and GPU bounds',async()=>{
  const {workerTimeoutSeconds}=await import('../server.mjs');
  assert.ok(workerTimeoutSeconds({action:'evaluate_portable_events',backend:'metal'}) > 2*90+300+600);
  assert.equal(workerTimeoutSeconds({action:'evaluate_portable_events'}),1110);
  assert.equal(workerTimeoutSeconds({action:'evaluate_portable_detail_batch'}),1110);
});
 test('CUDA and ordinary CPU worker deadlines remain bounded at 120 seconds',async()=>{
  const {workerTimeoutSeconds}=await import('../server.mjs');
  assert.equal(workerTimeoutSeconds({action:'evaluate_portable_events',backend:'cuda'}),120);
  assert.equal(workerTimeoutSeconds({action:'evaluate',backend:'metal'}),120);
  assert.equal(workerTimeoutSeconds({action:'evaluate_portable_detail_batch',evaluations:[{compute_backend:'cuda_shared_detail'}]}),120);
});
test('shared CUDA configuration requires real directories and is independent of legacy probe',async()=>{
 const {sharedCudaConfigured}=await import('../server.mjs');
 const root=mkdtempSync(path.join(tmpdir(),'nikke-cache-config-'));
 try{
  const env={NIKKE_SLANG_GENERATION_CACHE:root,NIKKE_CUDA_COMPILE_CACHE:root};
  assert.equal(sharedCudaConfigured('win32',env),true);
  assert.equal(sharedCudaConfigured('darwin',env),false);
  assert.equal(sharedCudaConfigured('win32',{}),false);
  assert.equal(sharedCudaConfigured('win32',{...env,NIKKE_CUDA_COMPILE_CACHE:'relative'}),false);
  const file=path.join(root,'file');writeFileSync(file,'not a directory');
  assert.equal(sharedCudaConfigured('win32',{...env,NIKKE_CUDA_COMPILE_CACHE:file}),false);
 }finally{rmSync(root,{recursive:true,force:true});}
});

test('shared CUDA saved images require explicit configuration plus a warm generation directory',async()=>{
 const {sharedCudaConfigured}=await import('../server.mjs');
 const root=mkdtempSync(path.join(tmpdir(),'nikke-saved-config-')),file=path.join(root,'programs.json');
 try{
  const env={NIKKE_SLANG_GENERATION_CACHE:root,NIKKE_SHARED_CUDA_ARTIFACTS:file};
  assert.equal(sharedCudaConfigured('win32',env),false);
  writeFileSync(file,JSON.stringify({schema:1,programs:{'gpu/product_battle_entry.slang':{battle_package:root,request:{package:root,capture:root}}}}));
  assert.equal(sharedCudaConfigured('win32',env),true);
  const registry=JSON.parse(readFileSync(new URL('../data/portable-product-programs.json',import.meta.url),'utf8'));
  for(const program of Object.values(registry.programs)){
    const configured={schema:1,programs:{[program.source]:{battle_package:root,request:{package:root,capture:root}}}};
    writeFileSync(file,JSON.stringify(configured));assert.equal(sharedCudaConfigured('win32',env),true);
    configured.programs['gpu/unregistered_product.slang']=configured.programs[program.source];
    writeFileSync(file,JSON.stringify(configured));assert.equal(sharedCudaConfigured('win32',env),false);
  }
  assert.equal(sharedCudaConfigured('win32',{...env,NIKKE_SLANG_GENERATION_CACHE:''}),false);
  assert.equal(sharedCudaConfigured('darwin',env),false);
  const history={capture:root,observation_sha256:'a'.repeat(64),disposition:'retained-failure',missing_identities:[{pid:71,path:'c:/tools/node.exe',creation_filetime_ticks:'133700000000000007'}]};
  const document={schema:1,programs:{'gpu/product_battle_entry.slang':{battle_package:root,request:{package:root,capture:root,historical_link_observation:history}}}};
  writeFileSync(file,JSON.stringify(document));assert.equal(sharedCudaConfigured('win32',env),true);
  for(const edits of [{capture:path.dirname(root)},{missing_identities:[]},{missing_identities:[history.missing_identities[0],history.missing_identities[0]]},{missing_identities:[{...history.missing_identities[0],path:'C:/TOOLS/NODE.EXE'}]},{missing_identities:[{...history.missing_identities[0],pid:73},history.missing_identities[0]]}]){
    const changed=structuredClone(document);Object.assign(changed.programs['gpu/product_battle_entry.slang'].request.historical_link_observation,edits);
    writeFileSync(file,JSON.stringify(changed));assert.equal(sharedCudaConfigured('win32',env),false);
  }
  history.missing_identities[0].creation_filetime_ticks=133700000000000007;
  writeFileSync(file,JSON.stringify(document));assert.equal(sharedCudaConfigured('win32',env),false);
  writeFileSync(file,JSON.stringify({schema:1,programs:[]}));
  assert.equal(sharedCudaConfigured('win32',env),false);
  writeFileSync(file,'invalid');assert.equal(sharedCudaConfigured('win32',env),false);
 }finally{rmSync(root,{recursive:true,force:true});}
});

test('CPU and GPU worker text streams retain split UTF-8 payloads and diagnostics',async()=>{
 const {workerTextStreams}=await import('../server.mjs');
 const {PassThrough}=await import('node:stream');
 const {once}=await import('node:events');
 const expected={spec:{text:'기본 스펙(3단계)보다 딜이 낮게 나오는 게 정상이다. 日本語と絵文字🎯'},members:[{name:'얀'}]};
 const lines=JSON.stringify(expected)+'\n'+JSON.stringify({id:'two',result:expected})+'\n';
 const diagnostic='計算終了: 정상 — 🎯';
 const child={stdout:new PassThrough(),stderr:new PassThrough()};
 assert.equal(workerTextStreams(child),child);
 let output='',error='';child.stdout.on('data',chunk=>output+=chunk);child.stderr.on('data',chunk=>error+=chunk);
 const done=Promise.all([once(child.stdout,'end'),once(child.stderr,'end')]);
 for(const byte of Buffer.from(lines,'utf8'))child.stdout.write(Buffer.from([byte]));
 for(const byte of Buffer.from(diagnostic,'utf8'))child.stderr.write(Buffer.from([byte]));
 child.stdout.end();child.stderr.end();await done;
 const rows=output.trimEnd().split('\n').map(line=>JSON.parse(line));
 assert.deepEqual(rows,[expected,{id:'two',result:expected}]);assert.equal(error,diagnostic);
});

test('Metal detail worker budget covers every compatible or separate source group',async()=>{
 const {workerTimeoutSeconds}=await import('../server.mjs');
 // Enumerate all ordered partitions: preparation can produce any grouping of 8 cases.
 const partitions=n=>n===0?[[]]:Array.from({length:n},(_,i)=>i+1).flatMap(k=>partitions(n-k).map(rest=>[k,...rest]));
 for(let n=1;n<=8;n++){
  const outer=workerTimeoutSeconds({action:'evaluate_portable_detail_batch',evaluations:Array.from({length:n},()=>({compute_backend:'metal_detail'}))});
  assert.equal(outer,1110*n);
  for(const groups of partitions(n))assert.ok(outer>groups.reduce((sum,k)=>sum+180+300+Math.min(4800,600*k),0));
 }
 assert.equal(workerTimeoutSeconds({action:'evaluate_portable_detail_batch',evaluations:Array(100).fill({compute_backend:'metal_detail'})}),8880);
});

test('server budget uses the Python Metal deadline policy',async()=>{
 const {spawnSync}=await import('node:child_process');
 const {workerTimeoutSeconds}=await import('../server.mjs');
 const {resolvePython}=await import('../app/python-runtime.mjs');
 const result=spawnSync(resolvePython(),['-c',"import sys,json;sys.path.insert(0,'app');import portable_backend as b;print(json.dumps([b.METAL_COMPILE_TIMEOUT_SECONDS,*[b.metal_gpu_timeout_seconds(n) for n in range(1,9)]]))"],{encoding:'utf8'});
 assert.equal(result.status,0,result.stderr);
 const [compile,...gpu]=JSON.parse(result.stdout);
 for(let n=1;n<=8;n++)assert.ok(workerTimeoutSeconds({action:'evaluate_portable_detail_batch',evaluations:Array(n).fill({compute_backend:'metal_detail'})})>n*(180+compile)+gpu[n-1]);
});

test('other Metal transport consumers fit the calibrated guard and command counts',async()=>{
 const {workerTimeoutSeconds}=await import('../server.mjs');
 const command=180+300+4800;
 assert.ok(workerTimeoutSeconds({action:'combat_prefilter',backend:'metal'})>command);
 assert.ok(workerTimeoutSeconds({action:'select',backend:'metal',teamCount:1})>command);
 assert.ok(workerTimeoutSeconds({action:'select',backend:'metal',teamCount:5})>5*command);
 assert.equal(workerTimeoutSeconds({action:'metal_search_probe'}),630);
});
