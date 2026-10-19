"""Compare reference-scale presence shortcut against shared lookup on either GPU."""
from portable_control_verifier import verify_control
if __name__=='__main__':
    verify_control('gpu/benchmark_reference_scale_lookup.slang','portable-reference-scales',__file__)
