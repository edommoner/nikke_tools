"""Compare compiled resource identities with live-name scan on either GPU."""
from portable_control_verifier import verify_control
if __name__=='__main__':
    verify_control('gpu/benchmark_reference_scan.slang','portable-hit-references',__file__)
