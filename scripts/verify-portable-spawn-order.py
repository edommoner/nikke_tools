"""Compare cached enemy spawn order with a rebuilt sequence on either GPU."""
from portable_control_verifier import verify_control

if __name__=='__main__':
    verify_control('gpu/benchmark_spawn_scan.slang','portable-spawn-order',__file__)
