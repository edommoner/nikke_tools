import test from 'node:test';
import assert from 'node:assert/strict';
import {searchCases} from '../server.mjs';
import {readFileSync,mkdtempSync,writeFileSync,rmSync} from 'node:fs';
import {tmpdir} from 'node:os';
import path from 'node:path';
test('independent batch jobs preserve overlapping rosters and all per-request conditions',async()=>{
 const {batchCases,boardCases}=await import('../server.mjs');
 const first={squad:['a','b','c','d','e'],profile:{chars:{a:{skill_levels:3}}},compute_backend:'native_detail'};
 const second={...structuredClone(first),compute_backend:'browser_detail',stat_deltas:{a:{atk:5}}};
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

import {swapCases} from '../server.mjs';
test('swap cases put baseline first, replace only the slot, filter deltas and preserve inputs',()=>{
  const body={evaluation:{squad:['i','ii','iii','x','y'],profile:{chars:{}},patches:{z:{skill_levels:10}},stat_deltas:{ii:{atk:1},z:{atk:2},i:{hp:3}}},slot:1,includeBaseline:true};
  const scored={characters:['i','ii','iii','x','y','z'].map((name,i)=>({name,burst:['1','2','3','3','3','2'][i],potential:i})),skipped:['missing']};
  const saved=structuredClone({body,scored}),{cases,swap,skipped}=swapCases(body,scored);
  assert.deepEqual({body,scored},saved);assert.equal(cases[0].value,'現在');
  assert.deepEqual(cases[0].evaluation,body.evaluation);
  assert.deepEqual(cases[1].evaluation.squad,['i','z','iii','x','y']);
  assert.deepEqual(cases[1].evaluation.stat_deltas,{z:{atk:2},i:{hp:3}});
  assert.deepEqual(swap,{slot:1,outgoing:'ii',remaining:0,names:['z'],bursts:Object.fromEntries(scored.characters.map(c=>[c.name,c.burst]))});
  assert.deepEqual(skipped,['missing']);
  cases[0].evaluation.patches.z.skill_levels=1;
  assert.equal(cases[1].evaluation.patches.z.skill_levels,10);
  assert.equal(swapCases({...body,includeBaseline:false},scored).cases.length,1);
});
test('swap validates five distinct nonempty members and an integer slot',()=>{
  const scored={characters:[],skipped:[]},evaluation={squad:['a','b','c','d','e']};
  for(const squad of [[],['a','b','c','d',''],['a','a','c','d','e'],['a','b','c','d',' ']])assert.throws(()=>swapCases({evaluation:{squad},slot:0},scored));
  for(const slot of [-1,5,0.5,'0'])assert.throws(()=>swapCases({evaluation,slot},scored));
});
 test('ordinary CPU worker deadlines remain bounded at 120 seconds',async()=>{
  const {workerTimeoutSeconds}=await import('../server.mjs');
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
