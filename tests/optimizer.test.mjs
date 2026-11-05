import test from 'node:test';
import assert from 'node:assert/strict';
import {candidatePool,bestDisjoint} from '../app/optimizer.mjs';
test('candidate sets are complete, owned and contain no duplicate members',()=>{
  const chars=Array.from({length:40},(_,i)=>({name:String(i),potential:100-i,burst:i<8?'1':i<16?'2':'3'}));
  const {pool,groups}=candidatePool(chars,5,80);
  assert.ok(groups.length);assert.ok(pool.length<=80);
  for(const group of groups)assert.equal(new Set(group.flatMap(i=>pool[i])).size,25);
  for(const squad of pool){assert.equal(squad.length,5);assert.equal(new Set(squad).size,5);}
});
test('global selection avoids choosing strongest first when it blocks the total',()=>{
  const teams=[['a','b'],['a','c'],['b','d'],['e','f']],scores=[100,90,90,1];
  const results=teams.map((s,i)=>({result:{members:s.map(name=>({name})),total_damage:scores[i]}}));
  const best=bestDisjoint(results,2);
  assert.equal(best.damage,180);assert.equal(new Set(best.teams.flatMap(t=>t.squad)).size,4);
});
test('failed evaluations are excluded without changing original candidate indices',()=>{
  const results=[{error:'bad'}, {result:{members:[{name:'a'}],total_damage:10}},{result:{members:[{name:'b'}],total_damage:20}}];
  assert.equal(bestDisjoint(results,2,[[1,2]]).damage,30);
  assert.equal(bestDisjoint(results,3,[[0,1,2]]),null);
});

test('GPU estimates only reorder candidates and preserve a feasible group for final CPU scoring',async()=>{
  const {rankCombatPool}=await import('../app/optimizer.mjs');
  const pool=Array.from({length:8},(_,i)=>Array.from({length:5},(_,j)=>`${i}:${j}`));
  const groups=[[0,1,2,3,4],[2,3,4,5,6]];
  const scores=pool.map((squad,index)=>({squad,index,damage:index*100}));
  const order=rankCombatPool(pool,groups,scores);
  assert.deepEqual(order.slice(0,5),groups[1]);assert.equal(new Set(order).size,8);
  assert.deepEqual(order.slice(5),[7,1,0]);
  assert.throws(()=>rankCombatPool(pool,groups,[{squad:pool[0],index:3,damage:5}]),/validation/);
  assert.throws(()=>rankCombatPool(pool,groups,[scores[0],scores[0]]),/validation/);
});

test('unscored candidates retain original order after scored rows; empty scores retain every candidate',async()=>{
 const {rankCombatPool}=await import('../app/optimizer.mjs');
 const pool=Array.from({length:6},(_,i)=>[String(i)]);
 const scores=[{index:2,squad:pool[2],damage:20},{index:0,squad:pool[0],damage:10}];
 assert.deepEqual(rankCombatPool(pool,[],scores),[2,0,1,3,4,5]);
 assert.deepEqual(rankCombatPool(pool,[[2,5],[0,1]],[]),[0,1,2,3,4,5]);
 const order=rankCombatPool(pool,[[0,1],[2,3]],scores);
 assert.deepEqual(order.slice(0,2),[2,3]);
 assert.deepEqual(new Set(order),new Set([0,1,2,3,4,5]));
 // No fully-scored group exists, but an intact partial group still fits the
 // shortlist, and missing members receive detailed scores there.
 const results=order.slice(0,2).map(i=>({result:{members:pool[i].map(name=>({name})),total_damage:100+i}}));
 assert.equal(bestDisjoint(results,2).damage,205);
});

import {swapCandidates} from '../app/optimizer.mjs';
const swapSquad=['i','ii','iii','extra1','extra2'];
const swapScored=[...swapSquad.map((name,i)=>({name,burst:['1','2','3','3','3'][i],potential:0})),
  {name:'one',burst:'1',potential:10},{name:'two',burst:'2',potential:20},
  {name:'three',burst:'3',potential:30},{name:'wild',burst:'A',potential:40}];
test('swap preserves required stages but allows a different stage when coverage remains',()=>{
  assert.deepEqual(swapCandidates(swapScored,swapSquad,1).names,['wild','two']);
  assert.deepEqual(swapCandidates(swapScored,swapSquad,3).names,['wild','three','two','one']);
});
test('each A fills only one missing stage, and incomplete squads may improve or retain coverage',()=>{
  const scored=[...swapScored,{name:'a',burst:'A',potential:0}];
  assert.deepEqual(swapCandidates(scored,['i','a','iii','extra1','extra2'],0).names,['wild','two','one','ii']);
  const incomplete=['i','iii','extra1','extra2','three'];
  assert.deepEqual(swapCandidates(scored,incomplete,0).names,['wild','two','one','a','ii']);
  assert.ok(!swapCandidates(scored,['i','a','iii','extra1','extra2'],0).names.includes('three'));
});
test('same stage accepts A on either side',()=>{
  assert.deepEqual(swapCandidates(swapScored,swapSquad,3,{sameStage:true}).names,['wild','three']);
  const squad=['i','wild','iii','extra1','extra2'];
  assert.deepEqual(swapCandidates(swapScored,squad,1,{sameStage:true}).names,['two','ii']);
});
test('potential and synergy interleave, dedupe, filter and paginate after skipping',()=>{
  const scored=[...swapScored,{name:'tie',burst:'3',potential:30}];
  const options={synergyOrder:['one','unknown','one','wild','two'],limit:4};
  assert.deepEqual(swapCandidates(scored,swapSquad,3,options),{names:['wild','one','three','tie'],total:5});
  assert.deepEqual(swapCandidates(scored,swapSquad,3,{...options,skip:['wild','three']}),{names:['tie','one','two'],total:3});
});
test('swap rejects invalid and empty slots',()=>{
  for(const slot of [-1,5,1.5,'1'])assert.throws(()=>swapCandidates(swapScored,swapSquad,slot));
  assert.throws(()=>swapCandidates(swapScored,['',...swapSquad.slice(1)],0));
});

test('swap batches default to 20 and skip already calculated candidates',()=>{
  const scored=[...swapScored,...Array.from({length:42},(_,i)=>({name:`candidate${i}`,burst:'3',potential:100+i}))];
  const first=swapCandidates(scored,swapSquad,3),second=swapCandidates(scored,swapSquad,3,{skip:first.names});
  assert.equal(first.names.length,20);assert.equal(first.total,46);
  assert.equal(second.names.length,20);assert.equal(second.total,26);
  assert.equal(new Set([...first.names,...second.names]).size,40);
});
