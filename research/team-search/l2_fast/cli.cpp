#include "l2.h"
#include <fstream>
#include <iostream>
#include <vector>
// Binary stdin: uint32 ordered squads. Binary stdout: total then 5 members/row.
// Input is streamed in bounded chunks; table is the single compiler artifact.
int main(int argc,char**argv){
    if(argc!=2){std::cerr<<"usage: l2-cli TABLE < squads.u32 > scores.f64\n";return 2;}
    std::ifstream f(argv[1],std::ios::binary);char magic[8];uint64_t n=0;f.read(magic,8);f.read(reinterpret_cast<char*>(&n),8);
    if(!f||(std::string(magic,8)!="L2FT0001"&&std::string(magic,8)!="L2FT0002")||n>10000000)return 2;
    std::vector<double> words(n);f.read(reinterpret_cast<char*>(words.data()),n*8);if(!f)return 2;
    void*t=l2_create(words.data(),n);if(!t)return 2;
    std::vector<uint32_t> ids(5*4096);std::vector<double> totals(4096),members(5*4096),out(6*4096);
    while(std::cin){std::cin.read(reinterpret_cast<char*>(ids.data()),ids.size()*4);size_t bytes=std::cin.gcount();if(bytes%20)return 2;size_t count=bytes/20;
        if(l2_score_many(t,ids.data(),count,totals.data(),members.data()))return 2;
        for(size_t i=0;i<count;i++){out[i*6]=totals[i];for(int j=0;j<5;j++)out[i*6+1+j]=members[i*5+j];}
        std::cout.write(reinterpret_cast<char*>(out.data()),count*48);
    }l2_destroy(t);
}
