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

test('manual cover declarations survive request and session projection without changing another team',()=>{
 const original={squad:['a','b','c','d','e'],profile:{chars:{a:{level:400}}},enemy:{def:1000},duration:30};
 const declaration={reference_models:{cover_defense:[{name:'a',base_defense:1000}]},manual_cover_sequences:{a:[{action:'cover',t:7.4,duration:.25}]}};
 const authored=structuredClone(declaration),result=applyDeclaredScenario(original,declaration);
 assert.deepEqual(result.manual_cover_sequences,authored.manual_cover_sequences);
 assert.deepEqual(result.profile,original.profile);assert.equal(result.duration,30);
 assert.equal(declaredScenarioLabel(declaration),'遮蔽DEF・手動遮蔽');
 const restored=normalizeDeclaredTeams(JSON.parse(JSON.stringify({'0':declaration,'2':{reference_models:{lock_on:{owner:'c'}}}})));
 assert.deepEqual(restored[0],authored);assert.equal(restored[2].manual_cover_sequences,undefined);
 result.manual_cover_sequences.a[0].t=8;restored[0].manual_cover_sequences.a[0].duration=1;
 assert.deepEqual(declaration,authored);assert.equal(original.manual_cover_sequences,undefined);
 assert.throws(()=>applyDeclaredScenario({...original,squad:['b','c','d','e','f']},declaration),/現在の部隊/);
});
test('manual cover import rejects invalid literals instead of discarding them',()=>{
 const models={cover_defense:[]},op={action:'cover',t:1,duration:.5};
 const invalid=[{},[],{a:[]},{a:Array(9).fill(op)},{a:[{...op,action:'shoot'}]},{a:[{...op,t:true}]},{a:[{...op,t:-1}]},{a:[{...op,duration:181}]},{a:[{...op,duration:Infinity}]},{a:[{...op,profile:{}}]},{a:[{...op,t:2},op]},{'':[op]}];
 for(const manual_cover_sequences of invalid)assert.throws(()=>normalizeDeclaredScenario({reference_models:models,manual_cover_sequences}));
 assert.throws(()=>normalizeDeclaredScenario({manual_cover_sequences:{a:[op]}}));
 assert.deepEqual(normalizeDeclaredScenario({reference_models:models,manual_cover_sequences:{a:[op]}}).manual_cover_sequences,{a:[op]});
});
test('actual score and frozen baseline keys change when only manual cover timing changes',async()=>{
 const {runInNewContext}=await import('node:vm');
 const source=readFileSync(new URL('../web/app.js',import.meta.url),'utf8');
 const code=source.split('\n').filter(line=>line.startsWith('function key(request)')||line.startsWith('const battleKey=')).join('\n');
 const evaluation={squad:['a'],profile:{chars:{a:{level:400}},_account:{}},patches:{},stat_deltas:{},duration:30,level:400,enemy:{def:1000},reference_models:{cover_defense:[]},manual_cover_sequences:{a:[{action:'cover',t:1,duration:.5}]}};
 const changed=structuredClone(evaluation);changed.manual_cover_sequences.a[0].t=2;
 const keys=runInNewContext(code+'\nrequests.map(r=>[key(r),battleKey(r)])',{requests:[evaluation,changed],merge:(a,b)=>({...a,...b})});
 assert.notEqual(keys[0][0],keys[1][0]);assert.notEqual(keys[0][1],keys[1][1]);
});

test('actual UI application rejects a foreign manual-cover owner before mutating saved conditions',async()=>{
 const {runInNewContext}=await import('node:vm');
 const source=readFileSync(new URL('../web/app.js',import.meta.url),'utf8');
 const start=source.indexOf('function setDeclaredScenario(value)');const end=source.indexOf('\nfunction burst(',start);
 assert.ok(start>=0&&end>start);
 const prior={reference_models:{cover_defense:[]}},state={activeTeam:0,teams:[['a','b','c','d','e']],declaredScenarios:{0:prior}},calls=[];
 const context={state,normalizeDeclaredScenario,applyDeclaredScenario,requireEditable(){},enemyScope,
 $(){return {dataset:{}}},rememberEnemy(){calls.push('remember')},renderAll(){calls.push('render')},renderReference(){calls.push('reference')},notice(){calls.push('notice')},
 candidate:{reference_models:{cover_defense:[]},manual_cover_sequences:{foreign:[{action:'cover',t:1,duration:.5}]}}};
 const code=source.slice(start,end)+'\nsetDeclaredScenario(candidate);';
 assert.throws(()=>runInNewContext(code,context),/現在の部隊/);
 assert.equal(state.declaredScenarios[0],prior);assert.deepEqual(calls,[]);
 context.candidate.manual_cover_sequences={a:[{action:'cover',t:1,duration:.5}]};
 runInNewContext(code,context);assert.deepEqual(state.declaredScenarios[0].manual_cover_sequences,context.candidate.manual_cover_sequences);assert.ok(calls.length>0);
});
