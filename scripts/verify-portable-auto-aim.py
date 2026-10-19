"""Compare automatic add aim with shared cached or rebuilt spawn basis on either GPU."""
from portable_control_verifier import verify_control

if __name__=='__main__':
    verify_control('gpu/benchmark_spawn_scan.slang','portable-auto-aim',__file__)
