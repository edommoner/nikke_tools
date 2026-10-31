import test from 'node:test';
import assert from 'node:assert/strict';
import {emptyTeams,placeCharacter,restoreTeams,completeTeams,serializeSession,SESSION_MAX_BYTES} from '../web/board-model.mjs';
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
test('history export stays lossless and reimportable when indentation alone exceeds the limit',()=>{
 const row={time:1,label:'declared-movement',position:[0,1],segments:[{before:[0,1],after:[2,3],disabled:true}]};
 const session={format:'nikke-tools-session-v1',ui_version:4,teams:emptyTeams(),declaredScenarios:{0:{reference_models:{lock_on:{owner:'a'}}}},job:{results:Array(50000).fill(row)}};
 assert.ok(new TextEncoder().encode(JSON.stringify(session,null,2)).byteLength>SESSION_MAX_BYTES);
 const exported=serializeSession(session);assert.ok(new TextEncoder().encode(exported).byteLength<=SESSION_MAX_BYTES);assert.deepEqual(JSON.parse(exported),session);
});
test('settings-only export is explicit and leaves live history and declarations intact',()=>{
 const session={format:'nikke-tools-session-v1',profile:{chars:{a:{level:400}}},teams:emptyTeams(),declaredScenarios:{0:{reference_models:{lock_on:{owner:'a'}}}},reference:{damage:3},comparison:{damage:4},job:{results:[1,2]}};
 const before=structuredClone(session),exported=JSON.parse(serializeSession(session,false));
 assert.deepEqual(session,before);assert.deepEqual(exported,{...before,reference:null,comparison:null,job:null});
 assert.throws(()=>serializeSession({...session,job:{data:'界'.repeat(SESSION_MAX_BYTES/3)}}),/12MB/);
});
