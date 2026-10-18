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
