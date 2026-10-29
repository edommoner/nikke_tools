"""Scoped saved-proof declarations shared by source audit and work routing.

These describe pinned captures, never current-source admission or a live run.
"""


def validation():
    return dict(
        scope='Pinned resident storage proofs; inspect source identity before reuse',
        frames=dict(suite='coordinate-resident-frames',inputs=106,native_cases=63,rejected_cases=43,
            metal_verified=True,independently_audited=True,all_old_entry_fingerprints_preserved=True,
            golden='research/portable-coordinate-resident-frames-short-v2-expected.json',
            evidence='tests/fixtures/resident-append-full106-metal-v1.json',
            evidence_sha256='ab7a2c9a316140085f869bb61380e112057e45cc6bec9dbda62a4504b15dbec2',
            cuda_device_verified=False,full_character_verified=False,public_admission=False),
        appends=dict(suite='resident-append-cache-only',inputs=9,native_contracts=9,canonical_battle_cases=0,
            metal_cuda_fingerprints_equal=True,cuda_calculation_verified=True,
            required_generation_cache_hit=True,required_cubin_cache_hit=True,
            slang_calls=0,nvrtc_calls=0,launch_sync_readback_calls_each=1,
            evidence='tests/fixtures/resident-append-cross-gpu-v1.json',
            evidence_sha256='9f0ad6e5c32b7f87f5a8a463f81eb8d4860d935b67683658dd540a68598e42b2',
            overall_stage_passed=False,environment_preservation_verified=False,
            preservation_status='unverified_service_identification',
            full_resident_battle_verified=False,full_character_verified=False,public_admission=False),
        wire=dict(suite='coordinate-resident-frames',inputs=106,native_reference_cases=63,
            cuda_device_execution_verified=True,shared_metal_wire_equivalence_verified=True,
            evidence='tests/fixtures/resident-current-cuda-v2-summary.json',
            evidence_sha256='7bfa35fef584ae4efdecd22a869f3660f3bf9d424549755c29a6b98a964117ce',
            peer_summary=True,original_cuda_raw_independently_read_on_mac=False,
            pending_independent_native_audit=True,calculation_verified=False,
            environment_preservation_verified=False,overall_stage_passed=False,
            full_character_verified=False,public_admission=False))
