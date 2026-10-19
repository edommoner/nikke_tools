"""Verify indexed staged selection against every-definition scanning on either GPU."""
from portable_control_verifier import verify_control
if __name__=='__main__':
    verify_control('gpu/benchmark_staged_full_scan.slang','portable-staged-index',__file__)
