import test from 'node:test';
import assert from 'node:assert/strict';
import {emptyTeams,placeCharacter,restoreTeams,completeTeams,normalizeTeamPreset,normalizeTeamPresets,applyTeamPreset,presetDefaultName} from '../web/board-model.mjs';
import {boardCases} from '../server.mjs';
test('moving a character between squads swaps members without duplication',()=>{
  const original=emptyTeams();original[0][0]='a';original[1][2]='b';
  const next=placeCharacter(original,1,2,'a');
  assert.equal(next[0][0],'b');assert.equal(next[1][2],'a');assert.equal(original[0][0],'a');
  assert.equal(next.flat().filter(n=>n==='a').length,1);
});
test('restoring old sessions filters missing and duplicate members',()=>{
  const teams=restoreTeams([['a','a','unknown','b']],new Set(['a','b']));
  assert.deepEqual(teams[0],['a','','','b','']);assert.equal(teams.length,5);
});
test('only complete squads are sent for batch calculation',()=>{
  const teams=emptyTeams();teams[0]=['a','b','c','d','e'];teams[1][0]='f';
  const result=completeTeams(teams);assert.equal(result.length,1);
  const request=boardCases(result.map(t=>({index:t.index,evaluation:{squad:t.squad}})));
  assert.equal(request[0].value,1);assert.throws(()=>boardCases([{index:0,evaluation:{squad:teams[0]}},{index:1,evaluation:{squad:teams[0]}}]),/複数/);
});

const teamPreset=(changes={})=>({id:'team:one',name:'  編成  ',members:['a','','b','',''],saved_at:'saved',...changes});
test('team preset normalization validates and copies only member data',()=>{
  const raw=teamPreset({patches:{a:{level:1}}}),normalized=normalizeTeamPreset(raw);
  assert.deepEqual(normalized,{id:'team:one',name:'編成',members:['a','','b','',''],saved_at:'saved'});
  assert.notEqual(normalized.members,raw.members);
  assert.equal(normalizeTeamPreset(teamPreset({saved_at:123})).saved_at,'');
  for(const invalid of [null,{},teamPreset({id:1}),teamPreset({id:'user:one'}),teamPreset({name:''}),teamPreset({name:'   '}),teamPreset({name:'a'.repeat(41)}),teamPreset({name:5}),teamPreset({members:['a']}),teamPreset({members:['a','','a','','']}),teamPreset({members:['','','','','']}),teamPreset({members:['a',1,'','','']}),teamPreset({members:Array(5)})])assert.equal(normalizeTeamPreset(invalid),null);
  assert.ok(normalizeTeamPreset(teamPreset({name:'a'.repeat(40)})));
});
test('team preset lists keep first valid unique ids and cap at 50',()=>{
  assert.deepEqual(normalizeTeamPresets(null),[]);
  const list=[teamPreset({name:''}),teamPreset(),teamPreset({name:'duplicate'}),...Array.from({length:60},(_,i)=>teamPreset({id:`team:${i}`}))];
  const result=normalizeTeamPresets(list);
  assert.equal(result.length,50);assert.equal(result[0].name,'編成');assert.equal(result[49].id,'team:48');
});
test('recalling a preset replaces the row, moves other members, and reports missing members',()=>{
  const original=emptyTeams();original[0]=['old','a','','',''];original[1]=['','b','','stay',''];original[3][4]='c';
  const before=structuredClone(original),members=['b','a','unknown','','c'];
  const result=applyTeamPreset(original,0,members,new Set(['a','b','c','old','stay']));
  const expected=emptyTeams();expected[0]=['b','a','','','c'];expected[1][3]='stay';
  assert.deepEqual(result,{teams:expected,moved:[{name:'b',from:1},{name:'c',from:3}],missing:['unknown']});
  assert.deepEqual(original,before);assert.deepEqual(members,['b','a','unknown','','c']);
  assert.notEqual(result.teams,original);for(let t=0;t<5;t++)assert.notEqual(result.teams[t],original[t]);
});
test('recalling into any row preserves slot order and does not mark target members as moved',()=>{
  for(let t=0;t<5;t++){
    const teams=emptyTeams();teams[t]=['a','','b','',''];
    const result=applyTeamPreset(teams,t,['','b','','a',''],new Set(['a','b']));
    assert.deepEqual(result.teams[t],['','b','','a','']);assert.deepEqual(result.moved,[]);assert.deepEqual(result.missing,[]);
  }
  for(const index of [-1,5,1.5,'0',NaN])assert.throws(()=>applyTeamPreset(emptyTeams(),index,['a','','','',''],new Set(['a'])),/Invalid/);
});
test('default preset names use the first two occupied labels and indicate additional members',()=>{
  const labels={a:'アニス：スター',b:'プリカ',c:'ミント'},label=n=>labels[n];
  assert.equal(presetDefaultName(['','a','','b','c'],label),'アニス：スター・プリカ ほか');
  assert.equal(presetDefaultName(['a','','b','',''],label),'アニス：スター・プリカ');
  assert.equal(presetDefaultName(['','','a','',''],label),'アニス：スター');
  assert.equal(presetDefaultName(['','','','',''],label),'');
});
