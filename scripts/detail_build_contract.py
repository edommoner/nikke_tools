"""Fail before costly compilation if the detailed kernel and host ABI differ."""
import re

def checked_detail_abi(cuda_source,host_source):
    kernels=re.findall(rb'extern\s+"C"\s+__global__\s+void\s+(detail_[A-Za-z0-9_]+)\s*\(',cuda_source)
    exports=re.findall(rb'''(?m)^DETAIL_ABI\s*=\s*['"](detail_[A-Za-z0-9_]+)['"]\s*$''',host_source)
    if len(kernels)!=1 or len(exports)!=1:
        raise ValueError('Detailed build requires exactly one kernel and one host ABI export')
    if kernels[0]!=exports[0]:
        raise ValueError('Detailed CUDA kernel and host ABI do not match')
    return kernels[0].decode('ascii')
