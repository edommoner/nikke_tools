// Claude: WebAssembly entry for the unmodified Slang -target cpp product kernel (777dcaf3 base).
#include <cstdlib>
#include <cstring>
#include KERNEL_FILE
extern "C" {
__attribute__((export_name("alloc"))) void* alloc(size_t n){return std::malloc(n);}
__attribute__((export_name("release"))) void release(void* p){std::free(p);}
__attribute__((export_name("run"))) int run(uint32_t* in,uint32_t inWords,uint32_t* out,uint32_t outWords){
  if(inWords==0||in[0]!=1) return 3;
  auto runtime=(Runtime_0*)std::calloc(1,sizeof(Runtime_0)); if(!runtime) return 4;
  std::memset(out,0,size_t(outWords)*4);
  GlobalParams_0 p{{in,inWords},{out,outWords},{runtime,1}};
  ComputeThreadVaryingInput v={};
  portableEvents_Thread(&v,nullptr,&p);
  std::free(runtime); return 0;
}
}
