import test from 'node:test';
import assert from 'node:assert/strict';
import {damageGroups,activeEffects,effectValue,teamDamageGroups,providesGroup,damageValue} from '../web/damage-groups.mjs';
import {matchesRosterFilters} from '../web/roster-model.mjs';
const effect=(extra={})=>({group:'2',stat:'atk_pct',scope:'ally',name:'buff',source:'스킬1',favorite:null,values:{'1':2,'5':5,'10':10},max_stack:1,...extra});
test('favorite stages select whole slots and retain ordinary slots',()=>{
 const effects=[effect(),effect({favorite:1}),effect({source:'스킬2',favorite:2}),effect({source:'스킬2'}),effect({source:'스킬3'}),effect({source:'스킬3',favorite:3})];
 const profile={favorite_slots:[1,2],effects};
 assert.deepEqual(activeEffects(profile,0),[effects[0],effects[3],effects[4]]);
 assert.deepEqual(activeEffects(profile,1),[effects[1],effects[3],effects[4]]);
 assert.deepEqual(activeEffects(profile,3),[effects[1],effects[2],effects[4]]);
 assert.deepEqual(activeEffects(profile),activeEffects(profile,3));
 assert.deepEqual(activeEffects(profile,-1),activeEffects(profile,0));
 assert.deepEqual(activeEffects(profile,99),activeEffects(profile,3));
 assert.deepEqual(activeEffects(profile,'bad'),activeEffects(profile,3));
 assert.deepEqual(activeEffects({effects},0),effects);
});
test('values clamp levels, stack, fixed and unknown',()=>{
 assert.equal(effectValue(effect({max_stack:3}),5),15);
 assert.equal(effectValue(effect(),-1),2);assert.equal(effectValue(effect(),100),10);
 assert.equal(effectValue(effect()),10);assert.equal(effectValue(effect(),'invalid'),10);
 assert.equal(effectValue({fixed:-4,max_stack:2},1),8);
 assert.equal(effectValue({fixed:3,max_stack:0}),3);
 assert.equal(effectValue({}),null);assert.equal(effectValue(effect(),4),null);
});
test('team groups are ordered, deduped only within characters and retain unknowns',()=>{
 const profile={effects:[effect(),effect(),effect({group:'6',stat:'received_dmg_pct',scope:'enemy',name:'debuff',fixed:-4,values:undefined}),effect({group:'count',stat:'infinite_ammo',name:'ammo',values:undefined}),effect({group:'1',stat:'normal_atk_dmg_pct',name:'normal',scope:'self',fixed:2,values:undefined})]};
 const data=teamDamageGroups([{name:'a',profile,skillLevels:{'1':5}},{name:'b',profile}]);
 assert.deepEqual(data.groups.map(g=>g.id),damageGroups.map(g=>g.id));
 assert.equal(data.groups[1].total,15);assert.equal(data.groups[1].entries.length,2);
 assert.equal(data.groups[5].total,8);assert.equal(data.groups[0].total,0);
 assert.equal(data.count.entries.length,2);assert.equal(data.unknown.length,2);
 assert.equal(data.count.entries[0].value,null);
});
test('provides group respects scope and favorite version',()=>{
 const profile={favorite_slots:[1],effects:[effect({scope:'self'}),effect({group:'6',scope:'enemy',favorite:1})]};
 assert.equal(providesGroup(profile,['2'],{favoriteStage:0}),false);
 assert.equal(providesGroup(profile,['2'],{includeSelf:true,favoriteStage:0}),true);
 assert.equal(providesGroup(profile,['6']),true);
 assert.equal(providesGroup(profile,['6'],{favoriteStage:0}),false);
 assert.equal(providesGroup({effects:[effect({group:'count'})]},new Set(['count'])),true);
 assert.equal(providesGroup(null,['1']),false);
 assert.equal(matchesRosterFilters({weapon:'AR'},{group:new Set(['2']),weapon:new Set(['AR'])}),true);
 assert.equal(matchesRosterFilters({weapon:'SG'},{group:new Set(['2']),weapon:new Set(['AR'])}),false);
});

test('shared scope selection excludes self totals, count and unknown entries by default',()=>{
 const members=[{name:'a',profile:{effects:[effect(),effect({scope:'enemy',name:'enemy'}),
   effect({scope:'self',name:'self',max_stack:40}),
   effect({scope:'self',name:'ammo',group:'count',stat:'max_ammo_flat',fixed:3,values:undefined}),
   effect({scope:'self',name:'unknown',values:undefined})]}}];
 const defaults=teamDamageGroups(members),included=teamDamageGroups(members,{includeSelf:true});
 assert.equal(defaults.groups[1].total,20);assert.equal(included.groups[1].total,420);
 assert.equal(defaults.count.entries.length,0);assert.equal(included.count.entries.length,1);
 assert.equal(defaults.unknown.length,0);assert.equal(included.unknown.length,1);
 for(const includeSelf of [false,true]){
   assert.equal(providesGroup(members[0].profile,['count'],{includeSelf}),teamDamageGroups(members,{includeSelf}).count.entries.length>0);
 }
});
test('damage values preserve flat count units and percent units',()=>{
 for(const stat of ['max_ammo_flat','ammo_charge_flat','pellet_count'])assert.equal(damageValue({stat,value:3}),'+3');
 assert.equal(damageValue({stat:'max_ammo_pct',value:3}),'+3.0%');
 assert.equal(damageValue({stat:'max_ammo_flat',value:null}),'値なし');
});
