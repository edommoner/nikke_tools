"""Compare event candidate masks with a full-scan control on either GPU."""
from portable_control_verifier import verify_control

if __name__=='__main__':
    verify_control('gpu/benchmark_event_scan.slang','portable-event-index',__file__)
