// Each worker owns its WebAssembly memory. No shared memory or isolation headers.
const instances=new Map();
function bytes64(text){return Uint8Array.from(atob(text),c=>c.charCodeAt(0));}
function base64(bytes){let text='';for(let i=0;i<bytes.length;i+=8192)text+=String.fromCharCode(...bytes.subarray(i,i+8192));return btoa(text);}
onmessage=async({data})=>{
  try{
    const {wire,wasm}=data;
    let e=instances.get(wire.wasm_identity);
    if(!e){const {instance}=await WebAssembly.instantiate(wasm,{env:{emscripten_notify_memory_growth(){}}});e=instance.exports;e._initialize();instances.set(wire.wasm_identity,e);}
    const input=new Uint8Array(await new Response(new Blob([bytes64(wire.input_gzip_base64)]).stream().pipeThrough(new DecompressionStream('gzip'))).arrayBuffer());
    if(input.byteLength!==(wire.input_words+1)*4)throw Error('Invalid browser input length');
    const digest=[...new Uint8Array(await crypto.subtle.digest('SHA-256',input))].map(b=>b.toString(16).padStart(2,'0')).join('');
    if(digest!==wire.input_sha256)throw Error('Invalid browser input hash');
    const outBytes=wire.output_words*4,ip=e.alloc(input.byteLength),op=e.alloc(outBytes);
    try{
      if(!ip||!op)throw Error('Browser allocation failed');
      new Uint8Array(e.memory.buffer,ip,input.byteLength).set(input);
      const started=performance.now(),rc=e.run(ip,input.byteLength/4,op,wire.output_words),seconds=(performance.now()-started)/1000;
      if(rc!==0)throw Error('Browser kernel failed: '+rc);
      const output=new Uint8Array(e.memory.buffer,op,outBytes).slice();
      const compressed=new Uint8Array(await new Response(new Blob([output]).stream().pipeThrough(new CompressionStream('gzip'))).arrayBuffer());
      postMessage({result:{input_sha256:digest,readback_gzip_base64:base64(compressed),browser_seconds:seconds}});
    }finally{if(ip)e.release(ip);if(op)e.release(op);}
  }catch(error){postMessage({error:error.message});}
};
