import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {enemyScope,groupPresets,normalizeDeclaredScenario,normalizeDeclaredTeams,applyDeclaredScenario,declaredScenarioLabel} from '../web/enemy-model.mjs';
const records=JSON.parse(readFileSync(new URL('../data/raid-presets.json',import.meta.url),'utf8')).presets;
test('enemy contexts are separate for single, solo, and union',()=>{
 assert.equal(enemyScope(true,5),'single');assert.equal(enemyScope(false,5),'solo');assert.equal(enemyScope(false,1),'union');
 const solo=groupPresets(records,'solo'),union=groupPresets(records,'union');
 assert.ok(solo.every(g=>g.members.every(p=>p.mode==='solo')));assert.ok(union.every(g=>g.members.every(p=>p.mode==='union')));
 assert.equal(solo.flatMap(g=>g.members).length,42);assert.equal(union.flatMap(g=>g.members).length,300);
});
test('grouping identical numeric settings preserves all source occurrences',()=>{
 const grouped=groupPresets(records,'single');assert.ok(grouped.length<records.length);
 assert.equal(grouped.flatMap(g=>g.members).length,records.length);
 const keys=grouped.map(g=>JSON.stringify(g.settings));assert.equal(new Set(keys).size,keys.length);
 for(const g of grouped)for(const row of g.members)assert.deepEqual(row.settings,g.settings);
 const one=records.find(p=>p.mode==='solo'),different=structuredClone(one);different.settings.core=10;
 assert.equal(groupPresets([one,different],'solo').length,2);
});

test('declared scenario preserves authored enemy actions without changing growth or another request',()=>{
 const original={squad:['a','b','c','d','e'],profile:{chars:{a:{level:400}}},enemy:{def:31784,parts:[],patterns:[{id:'old',kind:'idle'}]},duration:30,seed:42};
 assert.equal(applyDeclaredScenario(original),original);
 assert.equal(applyDeclaredScenario(original,{}),original);
 const declaration={reference_models:{enemy_movement:{coord:{auto_aim:[0,0]},logical_geometry:[],motion:{actors:[]}}},enemy:{patterns:[{id:'wave',kind:'add',hp:100,after:['start']}]}};
 const before=structuredClone(original),authored=structuredClone(declaration),result=applyDeclaredScenario(original,declaration);
 assert.deepEqual(original,before);assert.deepEqual(declaration,authored);
 assert.deepEqual(result.profile,original.profile);assert.deepEqual(result.squad,original.squad);assert.equal(result.seed,42);assert.equal(result.duration,30);assert.equal(result.enemy.def,31784);
 assert.deepEqual(result.enemy.patterns,authored.enemy.patterns);assert.deepEqual(result.reference_models,authored.reference_models);
 result.reference_models.enemy_movement.motion.actors.push({label:'changed'});result.enemy.patterns[0].hp=1;
 assert.deepEqual(declaration,authored);assert.equal(original.enemy.patterns[0].id,'old');
 const withoutOverride=applyDeclaredScenario(original,{reference_models:{lock_on:{owner:'a'}}});assert.deepEqual(withoutOverride.enemy,original.enemy);
});
test('declaration import cannot override growth, roster or scalar battle settings or hide invalid numeric data',()=>{
 const model={reference_models:{lock_on:{owner:'a'}}};
 for(const invalid of [null,[],{profile:{}},{...model,squad:['a']},{...model,duration:1},{...model,enemy:{def:1}},{...model,enemy:{patterns:[],distance:1}},{enemy:{patterns:[]}},{reference_models:{unknown:{}}},{reference_models:[]},{reference_models:{lock_on:{x:Infinity}}},{reference_models:{lock_on:{x:NaN}}},{...model,enemy:{patterns:[{kind:'move',distance:Infinity}]}}])assert.throws(()=>normalizeDeclaredScenario(invalid));
 let deep={};for(let i=0;i<35;i++)deep={nested:deep};assert.throws(()=>normalizeDeclaredScenario({reference_models:{lock_on:deep}}));
 assert.throws(()=>normalizeDeclaredScenario({reference_models:{lock_on:{text:'a'.repeat(1048576)}}}));
 assert.deepEqual(normalizeDeclaredScenario({reference_models:{}}),{});
});
test('session round trip keeps per-team models isolated and supports older sessions',()=>{
 assert.deepEqual(normalizeDeclaredTeams(),{});
 const imported={'0':{reference_models:{lock_on:{owner:'a'}}},'3':{reference_models:{named_range:{rules:[{effect:'original skill',base_count:2}]}}},'4':{}};
 const roundTrip=normalizeDeclaredTeams(JSON.parse(JSON.stringify(imported)));
 assert.deepEqual(Object.keys(roundTrip),['0','3']);assert.equal(declaredScenarioLabel(roundTrip[0]),'Lock On');assert.equal(declaredScenarioLabel(roundTrip[3]),'範囲・対象数');
 roundTrip[0].reference_models.lock_on.owner='new';assert.equal(imported[0].reference_models.lock_on.owner,'a');assert.equal(roundTrip[3].reference_models.named_range.rules[0].base_count,2);
 for(const invalid of [[],null,{'5':{}},{'-1':{}},{'01':{}},{'0':{profile:{}}}])assert.throws(()=>normalizeDeclaredTeams(invalid));
});
