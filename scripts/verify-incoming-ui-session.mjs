/** Validate the review fixture with the real UI parsers; no browser claim. */
import assert from 'node:assert/strict';
import {readFileSync,writeFileSync} from 'node:fs';
import {createHash} from 'node:crypto';
import {validPreset} from '../web/roster-model.mjs';
import {restoreTeams} from '../web/board-model.mjs';
import {normalizePatterns} from '../web/phase-model.mjs';
import {normalizeParts} from '../web/parts-model.mjs';
const path='research/detail-incoming-ui-fixture.json',session=JSON.parse(readFileSync(path,'utf8'));
const evaluation=JSON.parse(readFileSync('research/detail-incoming-api-fixture.json','utf8'));
assert.equal(session.format,'nikke-tools-session-v1');assert.equal(session.snapshot.is_demo,true);assert.equal(session.singleMode,true);
assert.equal(session.settings['detail-backend'],'cuda_verified');assert.equal(session.job,null);assert.equal(session.comparison,null);
assert.deepEqual(session.profile,evaluation.profile);assert.deepEqual(session.deltas,evaluation.stat_deltas);
assert.deepEqual(restoreTeams(session.teams,new Set(Object.keys(session.profile.chars)))[0],evaluation.squad);
assert.equal(session.customPresets.length,1);assert.ok(validPreset(session.customPresets[0]));
assert.deepEqual(normalizePatterns(session.enemyPatterns),session.customPresets[0].patterns);
assert.equal(session.enemyPatterns.length,3);assert.equal(session.enemyPatterns.filter(p=>p.kind==='buff').length,1);
assert.deepEqual(normalizeParts(session.enemyParts),evaluation.enemy.parts||[]);
for(let i=0;i<session.enemyPatterns.length;i++){
 const {note,...actual}=session.enemyPatterns[i],{note:_,...expected}=evaluation.enemy.patterns[i];assert.deepEqual(actual,expected);
}
const files=[path,'research/detail-incoming-api-fixture.json','scripts/verify-incoming-ui-session.mjs','web/app.js','web/roster-model.mjs','web/board-model.mjs','web/phase-model.mjs','web/parts-model.mjs'];
const report={generated_at:new Date().toISOString(),passed:true,scope:'The fictional saved session uses the production UI parsers and the API smoke input profile, deltas and boss conditions; API execution is verified separately.',browser_interaction_verified:false,source_sha256:Object.fromEntries(files.map(f=>[f,createHash('sha256').update(readFileSync(f)).digest('hex')]))};
writeFileSync('research/detail-incoming-ui-session-verification.json',JSON.stringify(report,null,2)+'\n');console.log(JSON.stringify({passed:true,patterns:3,fictional:true,browser_interaction_verified:false}));
