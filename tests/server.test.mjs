import test from 'node:test';
import assert from 'node:assert/strict';
import {searchCases} from '../server.mjs';
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
