import test from 'node:test';
import assert from 'node:assert/strict';
import {sortRoster,rosterValue,visibleTeams,validPreset} from '../web/roster-model.mjs';
test('observed power sorting keeps missing values last in both directions',()=>{
 const entries={a:{_observed_combat_power:0},b:{},c:{_observed_combat_power:200}};
 const args={field:'power',entry:n=>entries[n],label:n=>n};
 assert.deepEqual(sortRoster(['a','b','c'],{...args,direction:'desc'}),['c','a','b']);
 assert.deepEqual(sortRoster(['a','b','c'],{...args,direction:'asc'}),['a','c','b']);
 assert.equal(rosterValue({_observed_combat_power:'200'},'power'),null);
});
test('limit break includes core enhancement and incomplete skills are unknown',()=>{
 assert.equal(rosterValue({breakthrough:3,core_enhancement:4},'limit'),7);
 assert.equal(rosterValue({skill_levels:'7/8/9'},'skill'),24);
 assert.equal(rosterValue({skill_levels:{1:7,2:8}},'skill'),null);
 assert.equal(rosterValue({skill_levels:{3:9,1:7,2:8}},'burst'),9);
});
test('single-squad view retains the selected squad index',()=>{
 assert.deepEqual(visibleTeams(true,3,5),[3]);assert.deepEqual(visibleTeams(false,3,5),[0,1,2,3,4]);
});
test('enemy preset rejects missing fields, invalid values, and unknown element',()=>{
 const p={label:'My boss',settings:{'enemy-def':31784,'enemy-code':'풍압',level:400,duration:180,core:0,distance:30}};
 assert.ok(validPreset(p));assert.ok(!validPreset({...p,settings:{...p.settings,duration:0}}));
 assert.ok(!validPreset({...p,settings:{...p.settings,level:400.5}}));assert.ok(!validPreset({...p,settings:{...p.settings,'enemy-code':'unknown'}}));
});
