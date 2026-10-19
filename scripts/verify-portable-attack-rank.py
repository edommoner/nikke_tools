"""Compare cached enemy attack ranks with a live-sort control on either GPU."""
from portable_control_verifier import verify_control

if __name__=='__main__':
    verify_control('gpu/benchmark_attack_rank_scan.slang','portable-attack-rank',__file__)
