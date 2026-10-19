"""Compare resource notification index with shared scan on either GPU."""
from portable_control_verifier import verify_control
if __name__=='__main__':
    verify_control('gpu/benchmark_resource_scan.slang','portable-resources',__file__)
