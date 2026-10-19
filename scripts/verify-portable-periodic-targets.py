"""Compare named periodic ownership by common cache or scan on either GPU."""
from portable_control_verifier import verify_control

if __name__=='__main__':
    verify_control('gpu/benchmark_periodic_owner_scan.slang','portable-periodic-targets',__file__)
