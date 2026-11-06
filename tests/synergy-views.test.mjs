import test from 'node:test';
import assert from 'node:assert/strict';
import {receivedEffects,receiveSummary,synergyMatrix,synergyPoints,teamViewConditions} from '../web/synergy-views.mjs';
const effect = (extra={}) => ({name:'buff',stat:'atk_pct',group:'2',scope:'ally',
  source:'스킬1',selector:{kind:'all'},values:{'1':2,'10':12.3},...extra});
const member = (name, effects=[], extra={}) => ({name,element:'수냉',weapon:'SG',burst:'3',
  synergy:{provides:[],conditions:[],traits:[]},damage_groups:{effects},...extra});
const provide = (selector={kind:'weapon',value:'SG'},extra={}) => ({tier:'A',selector,stat:'atk_pct',...extra});

test('reach follows selectors, excludes self, shares enemy effects, and dedupes per giver',()=>{
  const a=member('a',[effect(),effect(),effect({name:'water',selector:{kind:'element',value:'수냉',excl_self:true}}),
    effect({name:'enemy',scope:'enemy',selector:undefined,group:'6',stat:'received_dmg_pct'}),
    effect({name:'name',selector:{kind:'name',value:'c'}})]);
  const b=member('b',[],{element:'작열'}),c=member('c');
  const {receivers,dynamic}=receivedEffects([a,b,c]);
  assert.deepEqual(receivers.map(entries=>entries.length),[2,2,4]);
  assert.ok(receivers[0].some(entry=>entry.scope==='enemy'));
  assert.equal(receivers[2][0].value,12.3);
  assert.deepEqual(dynamic,[[],[],[]]);
  const before=structuredClone([a,b,c]);receivedEffects([a,b,c]);assert.deepEqual([a,b,c],before);
});

test('self requires includeSelf; only dynamic kinds are unassigned, runtime traits reach matching members',()=>{
  const a=member('Alice',[effect({scope:'self',selector:undefined}),
    effect({name:'dynamic',selector:{kind:'dynamic'}}),
    effect({name:'runtime',group:'4',stat:'charge_dmg_pct',
      selector:{kind:'trait',value:'charge',rule:'allies_top_atk'}})]);
  const helm=member('Helm');helm.synergy.traits=['charge'];
  const members=[a,helm,member('non-charge')];
  const {receivers,dynamic}=receivedEffects(members);
  assert.deepEqual(receivers.map(entries=>entries.length),[0,1,0]);
  assert.equal(receivers[1][0].conditional,true);
  assert.equal(receivers[1][0].dynamic,false);
  const data=receivedEffects(members,{includeSelf:true});
  assert.deepEqual(data.receivers.map(entries=>entries.length),[1,1,0]);
  assert.equal(data.receivers[0][0].conditional,false);
  assert.equal(dynamic[0].length,1);assert.ok(dynamic[0].every(entry=>entry.dynamic));
  const matrix=synergyMatrix(members);
  assert.deepEqual([...matrix.cells[0][1].groups],['4']);
  assert.equal(matrix.cells[0][1].entries[0].conditional,true);
  assert.equal(matrix.dynamic[0].length,1);
  const summary=receiveSummary(members);
  assert.equal(summary[1].groups['4'].total,12.3);
  assert.deepEqual(summary[1].groups['4'].from,['Alice']);
  assert.equal(summary[1].dynamic.length,1);
});

test('growth selects favorite stage, level, stack, fixed and unknown values',()=>{
  const a=member('a',[effect({favorite:null}),effect({favorite:1,values:{'1':7},max_stack:3}),
    effect({name:'fixed',values:undefined,fixed:-5}),effect({name:'unknown',values:undefined})],
    {favoriteStage:1,skillLevels:{'1':1}});
  a.damage_groups.favorite_slots=[1];
  const {receivers}=receivedEffects([a]);
  assert.deepEqual(receivers[0].map(entry=>entry.value),[21]);
  a.favoriteStage=0;
  assert.deepEqual(receivedEffects([a]).receivers[0].map(entry=>entry.value),[2,5,null]);
});

test('summaries sum each group, dedupe givers and count stats, and expose uncertain buffs',()=>{
  const a=member('a',[effect(),effect({name:'second'}),effect({name:'count',group:'count',stat:'attack_speed_pct'}),
    effect({name:'dynamic',selector:{kind:'dynamic'}})]);
  const b=member('b',[effect({group:'count',stat:'attack_speed_pct'}),effect({name:'self',scope:'self'})]);
  const summary=receiveSummary([a,b]);
  assert.equal(summary[1].groups['2'].total,24.6);
  assert.deepEqual(summary[1].groups['2'].from,['a']);
  assert.deepEqual(summary[1].count,['attack_speed_pct']);
  assert.equal(summary[1].dynamic.length,1);
  assert.ok(Math.abs(receiveSummary([a,b],{includeSelf:true})[1].groups['2'].total-36.9)<1e-9);
});

test('matrix preserves giver/receiver direction, group sets, count and diagonal options',()=>{
  const a=member('a',[effect(),effect({name:'enemy',scope:'enemy',group:'6'}),effect({name:'self',scope:'self'}),
    effect({name:'count',group:'count'}),effect({name:'dynamic',selector:{kind:'dynamic'}})]),b=member('b');
  const {cells,dynamic}=synergyMatrix([a,b]);
  assert.equal(cells.length,2);assert.equal(cells[0].length,2);
  assert.deepEqual([...cells[0][1].groups],['2','6','count']);
  assert.equal(cells[1][0].entries.length,0);assert.equal(cells[0][0].entries.length,0);
  assert.equal(dynamic[0].length,1);
  assert.equal(synergyMatrix([a,b],{includeSelf:true}).cells[0][0].entries.length,4);
});

test('opposite conditions show only the holding Red Hood branch, including absent ally',()=>{
  const owner=member('Red Hood');
  owner.synergy.conditions=[{kind:'has_burst',value:'1',negate:false},{kind:'has_burst',value:'1',negate:true}];
  for(const burst of ['1','3']){
    const points=synergyPoints([owner,member('other',[],{burst})]);
    assert.deepEqual(points.map(item=>item.kind),['condition-ok']);
    assert.equal(points[0].condition.negate,burst!=='1');
  }
  assert.equal(synergyPoints([owner])[0].condition.negate,true);
  owner.synergy.conditions=[{kind:'has_burst',value:'1',negate:true}];
  assert.equal(synergyPoints([owner,member('other',[],{burst:'1'})])[0].kind,'condition-broken');
});

test('points group wasted selectors, retain all stats with damage first, and order warnings before links',()=>{
  const a=member('a',[effect()]),b=member('b'),c=member('c');
  const missing={kind:'element',value:'작열'};
  a.synergy.provides=[provide(missing,{stat:'heal_hp_pct'}),provide(missing),provide(missing),
    provide({kind:'trait',value:'charge'},{tier:'B'}),provide({kind:'all'},{tier:'C'})];
  b.synergy.traits=['charge'];c.synergy.provides=[provide()];
  a.synergy.conditions=[{kind:'has_burst',value:'1'}];
  b.synergy.conditions=[{kind:'has_burst',value:'3',negate:true}];
  const points=synergyPoints([a,b,c]);
  assert.deepEqual(points.map(item=>item.kind),['wasted','condition-missing','condition-broken','link','link','link','info']);
  assert.deepEqual(points[0].stats,['atk_pct','heal_hp_pct']);
  assert.deepEqual(points.filter(item=>item.kind==='link').map(item=>item.tier),['A','A','B']);
  assert.match(points.find(item=>item.tier==='B').reasons[0],/チャージ武器/);
  assert.equal(points.at(-1).count,1);
  assert.deepEqual(synergyPoints([]),[]);
});

test('shared team conditions pair by owner and kind/value, retain only the holding branch, and keep real failures',()=>{
  const a=member('a'),b=member('b',[],{burst:'1'});
  const positive={kind:'has_burst',value:'1',negate:false,source:'스킬1'};
  const negative={...positive,negate:true,source:'스킬2'};
  a.synergy.conditions=[negative,positive,{kind:'has_burst',value:'2'},
    {kind:'has_class',value:'지원형',negate:true}];
  b.synergy.conditions=[{...negative}];
  const members=[a,b],before=structuredClone(members),conditions=teamViewConditions(members);
  assert.deepEqual(conditions.map(({owner,condition,effect,paired})=>
    [owner.name,condition.kind,condition.value,condition.negate??false,effect,paired]),[
    ['a','has_burst','1',false,'satisfied',true],
    ['a','has_burst','2',false,'unmet',false],
    ['a','has_class','지원형',true,'satisfied',false],
    ['b','has_burst','1',true,'satisfied',false],
  ]);
  assert.equal(conditions[0].condition.source,'스킬1');
  assert.deepEqual(members,before);
  b.burst='3';
  assert.equal(teamViewConditions(members)[0].condition,negative);
  assert.equal(teamViewConditions(members)[0].effect,'satisfied');
  a.synergy.conditions=[negative];b.burst='1';
  assert.equal(teamViewConditions(members)[0].effect,'broken');
  assert.deepEqual(teamViewConditions([]),[]);
});
