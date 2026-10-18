import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import vm from 'node:vm';
const source=readFileSync(new URL('../web/exporter.js',import.meta.url),'utf8');
test('profile bookmark decodes current BlaBlaLink URLs and transfers no credentials',async()=>{
 const id='29080-1234567890123456789',requests=[];let download,blob,asked=false;
 class LocalURL extends URL{static createObjectURL(value){blob=value;return 'blob:local';}static revokeObjectURL(){}}
 const element=()=>({style:{},click(){download=true;},remove(){}});
 const context={URL:LocalURL,Blob,Map,Number,Error,Promise,decodeURIComponent,atob,location:{hostname:'www.blablalink.com',href:'https://www.blablalink.com/user?openid='+encodeURIComponent(btoa(id))},crypto:{randomUUID:()=> 'random-test-nonce'},prompt:()=>{asked=true;},alert:message=>{throw Error(message);},window:{open:()=>null,addEventListener(){},removeEventListener(){}},document:{createElement:element,body:{append(){}}},setTimeout(){},fetch:async(url,init)=>{
   const body=JSON.parse(init.body);requests.push({url,body});
   const data=url.endsWith('GetUserCharacters')?{characters:[{name_code:1,grade:2,core:0}]}:url.endsWith('GetUserCharacterDetails')?{character_details:[{name_code:1,skill1_lv:7}],state_effects:[]}:{outpost_info:{synchro_level:400}};
   return {ok:true,json:async()=>({code:0,data})};
 }};
 await vm.runInNewContext(source,context);
 assert.equal(asked,false);assert.ok(download);assert.equal(requests.length,3);
 for(const request of requests)assert.equal(request.body.intl_open_id,id.split('-')[1]);
 const saved=JSON.parse(await blob.text());assert.equal(saved.characters.length,1);assert.equal(saved.details.length,1);
 assert.ok(!/token|cookie|openid/i.test(JSON.stringify(saved)));
});
