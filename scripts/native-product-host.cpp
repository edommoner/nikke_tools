#include <algorithm>
#include <atomic>
#include <chrono>
#include <cstdint>
#include <cstdio>
#include <exception>
#include <fstream>
#include <iostream>
#include <limits>
#include <memory>
#include <mutex>
#include <stdexcept>
#include <string>
#include <thread>
#include <vector>
#ifdef __APPLE__
#include <sys/sysctl.h>
#endif
#include KERNEL_FILE

static size_t positive(const char* text) {
    std::string s(text);size_t end=0;
    if(s.empty() || s.find_first_not_of("0123456789")!=std::string::npos)throw std::runtime_error("invalid positive integer");
    auto n=std::stoull(s,&end);
    if(!n || n>std::numeric_limits<size_t>::max()/4)throw std::runtime_error("dimension out of range");
    return size_t(n);
}
static std::string brand() {
#ifdef __APPLE__
    char name[256]={};size_t size=sizeof(name);
    if(!sysctlbyname("machdep.cpu.brand_string",name,&size,nullptr,0))return name;
#endif
    std::ifstream cpu("/proc/cpuinfo");std::string line;
    while(std::getline(cpu,line))if(line.rfind("model name",0)==0)return line.substr(line.find(':')+2);
    return "CPU";
}
static std::string jsonString(const std::string& s) {
    std::string out="\"";const char hex[]="0123456789abcdef";
    for(unsigned char c:s) {
        if(c=='"'||c=='\\'){out+='\\';out+=char(c);}
        else if(c<32){out+="\\u00";out+=hex[c>>4];out+=hex[c&15];}
        else out+=char(c);
    }
    return out+'"';
}
int main(int argc,char** argv) {
    try {
        if(argc!=6)throw std::runtime_error("usage: host input.bin output.bin input_words output_words threads");
        const size_t iw=positive(argv[3]),ow=positive(argv[4]),threads=positive(argv[5]);
        std::ifstream file(argv[1],std::ios::binary|std::ios::ate);
        if(!file)throw std::runtime_error("cannot open input");
        auto bytes=file.tellg();if(bytes<4 || bytes%4)throw std::runtime_error("invalid input length");
        std::vector<uint32_t> input(size_t(bytes)/4);file.seekg(0);
        if(!file.read(reinterpret_cast<char*>(input.data()),bytes))throw std::runtime_error("short input read");
        const size_t count=input[0];
        if(!count || count>65536 || threads>count || iw>(input.size()-1)/count || input.size()!=1+count*iw
            || ow>std::numeric_limits<size_t>::max()/4/count)throw std::runtime_error("invalid wire dimensions");
        std::vector<uint32_t> output(count*ow,0);std::atomic<size_t> next{0};
        std::exception_ptr failure;std::mutex mutex;
        auto work=[&] {
            try {
                for(size_t i;(i=next.fetch_add(1))<count;) {
                    std::vector<uint32_t> single(1+iw);single[0]=1;
                    std::copy_n(input.data()+1+i*iw,iw,single.data()+1);
                    auto runtime=std::make_unique<Runtime_0>();
                    GlobalParams_0 params{{single.data(),single.size()},{output.data()+i*ow,ow},{runtime.get(),1}};
                    ComputeThreadVaryingInput varying={};portableEvents_Thread(&varying,nullptr,&params);
                }
            }catch(...){std::lock_guard<std::mutex> guard(mutex);failure=std::current_exception();next.store(count);}
        };
        std::vector<std::thread> pool;pool.reserve(threads);
        auto start=std::chrono::steady_clock::now();
        try {for(size_t i=0;i<threads;i++)pool.emplace_back(work);}
        catch(...){next.store(count);for(auto& t:pool)t.join();throw;}
        for(auto& t:pool)t.join();
        double seconds=std::chrono::duration<double>(std::chrono::steady_clock::now()-start).count();
        if(failure)std::rethrow_exception(failure);
        std::ofstream result(argv[2],std::ios::binary|std::ios::trunc);
        if(!result || !result.write(reinterpret_cast<const char*>(output.data()),output.size()*4))throw std::runtime_error("output write failed");
        result.close();if(!result)throw std::runtime_error("output close failed");
        std::cout.precision(12);
        std::cout<<"{\"cases\":"<<count<<",\"threads\":"<<threads<<",\"host_seconds\":"<<seconds
          <<",\"input_bytes\":"<<size_t(bytes)<<",\"output_bytes\":"<<output.size()*4
          <<",\"command_status\":\"completed\",\"device\":"<<jsonString("cpu:"+brand()+" x"+std::to_string(threads))<<"}\n";
    }catch(const std::exception& e){std::cerr<<e.what()<<'\n';return 1;}
}
