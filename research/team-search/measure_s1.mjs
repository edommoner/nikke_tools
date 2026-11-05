import fs from 'node:fs';
import {candidatePool,bestDisjoint} from '../../app/optimizer.mjs';
import {sharedToolEnv} from '../../app/tool-roots.mjs';
import {fileURLToPath} from 'node:url';
const input=JSON.parse(fs.readFileSync(0,'utf8'));
if(input.action==='env') console.log(JSON.stringify(sharedToolEnv(fileURLToPath(new URL('../../',import.meta.url)))));
else if(input.action==='pool') console.log(JSON.stringify(candidatePool(input.characters,5,160,41,input.templates)));
else console.log(JSON.stringify(bestDisjoint(input.results,5,input.groups)));
