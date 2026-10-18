import test from 'node:test';
import assert from 'node:assert/strict';
import {emptyTeams,placeCharacter,restoreTeams,completeTeams} from '../web/board-model.mjs';
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
