"""Compare source count memoization with full expiry counting on either GPU."""
from portable_control_verifier import verify_control
if __name__=='__main__':
    verify_control('gpu/benchmark_source_count_scan.slang','portable-sources',__file__)
