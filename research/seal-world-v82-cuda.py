"""Frozen Metal208 versus one actual bounded CUDA208 execution."""
from portable_cuda_proof_audit import audit
if __name__=='__main__':
 r=audit(version=82,source='db8f4c87c54c29b9c1fbf0e5764ded5fdbfe6a86',expected_file='portable-world-charge-hold-expected.json',native_cases=125,rejected_cases=34,case_counts=[9,26,35,29,26],cpu_tests=11)
 print('CUDA208 sealed:one GPU execution;all Metal fingerprints match;CPU11;normal4682 not rerun')
