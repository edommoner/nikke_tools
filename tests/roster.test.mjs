import test from 'node:test';
import assert from 'node:assert/strict';
import {manufacturerLabels,manufacturerIconUrl,elementIconUrl,burstIconUrl,matchesRosterFilters,sortRoster,rosterValue,visibleTeams,validPreset} from '../web/roster-model.mjs';
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

const noFilters=()=>({manufacturer:new Set(),element:new Set(),burst:new Set(),weapon:new Set()});
const nikke={manufacturer:'엘리시온',element:'수냉',burst:'2',weapon:'AR'};
test('empty roster filters allow all characters, including missing metadata',()=>{
 assert.ok(matchesRosterFilters(nikke,noFilters()));
 assert.ok(matchesRosterFilters({},noFilters()));
 assert.ok(matchesRosterFilters(undefined,noFilters()));
});
test('roster filters use OR within every category and AND across categories',()=>{
 const filters={manufacturer:new Set(['미실리스','엘리시온']),element:new Set(['전격','수냉']),burst:new Set(['1','2']),weapon:new Set(['SMG','AR'])};
 assert.ok(matchesRosterFilters(nikke,filters));
 assert.ok(matchesRosterFilters({manufacturer:'미실리스',element:'전격',burst:'1',weapon:'SMG'},filters));
 for(const [category,value] of Object.entries({manufacturer:'테트라',element:'작열',burst:'3',weapon:'RL'})){
  assert.equal(matchesRosterFilters({...nikke,[category]:value},filters),false,category);
 }
});
test('any-stage burst matches every selected stage but still obeys other categories',()=>{
 for(const stage of ['1','2','3']){
  const filters={...noFilters(),burst:new Set([stage])};
  assert.ok(matchesRosterFilters({...nikke,burst:'A'},filters));
  assert.ok(matchesRosterFilters({...nikke,burst:'A'},{...filters,burst:new Set(['1','3'])}));
  assert.equal(matchesRosterFilters({...nikke,burst:'A'},{...filters,weapon:new Set(['RL'])}),false);
 }
});
test('unknown or missing roster values never match a restricted category',()=>{
 for(const category of ['manufacturer','element','burst','weapon']){
  const filters={...noFilters(),[category]:new Set([nikke[category]])};
  for(const value of [undefined,null,'','unknown','toString']){
   assert.equal(matchesRosterFilters({...nikke,[category]:value},filters),false,`${category}: ${value}`);
   assert.equal(matchesRosterFilters({...nikke,[category]:value},{...filters,[category]:new Set([value])}),false);
  }
 }
});
test('roster icons use the exact asset path and white manufacturer variants',()=>{
 const base='https://www.blablalink.com/assets/nikke/version/default/shiftysassets/images/';
 const manufacturers={'엘리시온':'elysion','미실리스':'missilis','테트라':'tetra','필그림':'pilgrim','어브노말':'abnormal'};
 assert.deepEqual(Object.values(manufacturerLabels),['エリシオン','ミシリス','テトラ','ピルグリム','アブノーマル']);
 for(const [value,file] of Object.entries(manufacturers))assert.equal(manufacturerIconUrl(value),`${base}icon-manufacturer-${file}--white.png`);
 for(const [value,file] of Object.entries({'풍압':'wind','수냉':'water','작열':'fire','전격':'electric','철갑':'iron'}))assert.equal(elementIconUrl(value),`${base}icon-code-${file}.png`);
 for(const stage of ['1','2','3'])assert.equal(burstIconUrl(stage),`${base}icon-burst-${stage}.png`);
 for(const helper of [manufacturerIconUrl,elementIconUrl,burstIconUrl]){
  for(const value of [undefined,null,'','unknown','toString','__proto__','A'])assert.equal(helper(value),null);
 }
});
