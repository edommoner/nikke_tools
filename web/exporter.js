/* Run this bookmark only in your own signed-in BlaBlaLink page. No credentials are exported. */
(async () => {
  if (!['www.blablalink.com','blablalink.com'].includes(location.hostname)) return alert('自分のBlaBlaLinkプロフィールを開いてから、このブックマークを実行してください。');
  function profileId(input){
    const url=new URL(input);if(!['www.blablalink.com','blablalink.com'].includes(url.hostname)||url.protocol!=='https:')throw Error('BlaBlaLinkのプロフィールURLを指定してください。');
    let id=url.searchParams.get('openid');if(!id)throw Error('プロフィール画面のURL（openid付き）を指定してください。');
    if(!/^\d{5}-\d{9,30}$/.test(id)){try{id=decodeURIComponent(atob(id.replace(/ /g,'+')));}catch{throw Error('プロフィールIDを読み取れませんでした。');}}
    if(!/^29080-\d{9,30}$/.test(id))throw Error('NIKKEのプロフィールIDではありません。');
    return id.split('-')[1];
  }
  let openid;
  try{openid=profileId(location.href);}catch{const entered=prompt('自分のBlaBlaLinkプロフィールURLを貼り付けてください。',location.href);if(!entered)return;try{openid=profileId(entered);}catch(error){return alert(error.message);}}
  const configuredOrigin='__NIKKE_TOOLS_ORIGIN__',toolOrigin=configuredOrigin.startsWith('http://127.0.0.1:')||configuredOrigin.startsWith('http://localhost:')?configuredOrigin:'http://127.0.0.1:4317';
  const nonce=crypto.randomUUID();let ready=false,ack=false;
  const bridge=window.open(toolOrigin+'/?blablalink_import='+encodeURIComponent(nonce),'nikke-tools-import');
  const onMessage=event=>{if(event.origin!==toolOrigin||event.source!==bridge||event.data?.nonce!==nonce)return;if(event.data.type==='nikke-tools-ready')ready=true;if(event.data.type==='nikke-tools-imported')ack=true;};
  window.addEventListener('message',onMessage);
  const common={game_id:'29080',area_id:'global',source:'pc_web',intl_game_id:'29080',language:'ko',env:'prod'};
  const badge=document.createElement('div');badge.textContent='NIKKE TOOLS: 所持一覧を取得中…';
  Object.assign(badge.style,{position:'fixed',right:'20px',bottom:'20px',zIndex:2147483647,background:'#17212c',color:'#fff',padding:'18px',borderRadius:'12px',maxWidth:'480px'});document.body.append(badge);
  const delay=ms=>new Promise(r=>setTimeout(r,ms));
  async function post(route,extra){
    const response=await fetch('https://api.blablalink.com/api/game/proxy/'+route,{method:'POST',credentials:'include',headers:{'Content-Type':'application/json','X-Channel-Type':'2','X-Language':'ko','X-Common-Params':JSON.stringify(common)},body:JSON.stringify({intl_open_id:openid,...extra})});
    if(!response.ok)throw Error('BlaBlaLink HTTP '+response.status);return response.json();
  }
  function download(data){const url=URL.createObjectURL(new Blob([JSON.stringify(data)],{type:'application/json'}));const link=document.createElement('a');link.href=url;link.download='nikke-growth-'+new Date().toISOString().slice(0,10)+'.json';link.click();setTimeout(()=>URL.revokeObjectURL(url),10000);}
  try{
    let characters,area,lastCode;
    for(const value of [83,1,261,219,145,81,82]){const response=await post('Game/GetUserCharacters',{nikke_area_id:value});lastCode=response.code;if(Number(response.code)===0&&response.data?.characters?.length){characters=response.data.characters;area=value;break;}}
    if(!characters)throw Error('所持一覧を取得できません（応答 '+lastCode+'）。ID形式・ログイン状態・公開設定のいずれかを確認する必要があります。応答コードだけでは原因を特定できません。');
    const details=[],effects=new Map();
    for(let i=0;i<characters.length;i+=60){badge.textContent=`NIKKE TOOLS: 育成情報 ${Math.min(i+60,characters.length)} / ${characters.length}`;const response=await post('Game/GetUserCharacterDetails',{nikke_area_id:area,name_codes:characters.slice(i,i+60).map(c=>c.name_code)});if(Number(response.code)!==0||!Array.isArray(response.data?.character_details))throw Error('育成詳細を取得できません（応答 '+response.code+'）。作戦人員の公開設定を確認してください。');details.push(...response.data.character_details);for(const effect of response.data.state_effects||[])effects.set(effect.id,effect);}
    if(details.length!==characters.length)throw Error('育成詳細の一部が未取得です。プロフィールの作戦人員の公開設定を確認してください。');
    const response=await post('Game/GetUserProfileOutpostInfo',{nikke_area_id:area});
    const data={format:'nikke-tools-blablalink-v1',exported_at:new Date().toISOString(),area,characters,details,state_effects:[...effects.values()],outpost:Number(response.code)===0?response.data?.outpost_info||{}:{}};
    if(bridge){for(let i=0;i<20&&!ready;i++){bridge.postMessage({type:'nikke-tools-ping',nonce},toolOrigin);await delay(250);}if(ready){bridge.postMessage({type:'nikke-tools-import',nonce,payload:data},toolOrigin);for(let i=0;i<60&&!ack;i++)await delay(250);}}
    if(ack)badge.textContent='NIKKE TOOLS: 計算ツールへ読み込みました。ツールのタブを確認してください。';else{download(data);badge.textContent='NIKKE TOOLS: JSONを保存しました。計算ツールの「JSONファイルを選択」で読み込んでください。';}
  }catch(error){badge.textContent='NIKKE TOOLS: '+error.message+' 認証情報をコピーする必要はありません。';if(bridge&&ready)bridge.postMessage({type:'nikke-tools-import-error',nonce,message:error.message},toolOrigin);}
  finally{window.removeEventListener('message',onMessage);setTimeout(()=>badge.remove(),30000);}
})();
