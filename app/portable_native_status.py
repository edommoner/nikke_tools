"""Explicit numerical failure witnesses, never arbitrary battle error admission."""
def expected(adapter,config,domain):
    policy=config.get('native_status_contract')
    if policy is None:return 0
    if policy!='movement-step-overflow-v1' or config.get('source')!='gpu/enemy_movement_math_probe.slang':
        raise ValueError('Unknown native status contract')
    oracle=adapter.native_reference(domain)
    status=oracle.get('status') if isinstance(oracle,dict) else None
    if type(status) is not int or status not in (0,16):raise ValueError('Exact movement numerical status0/16 required')
    return status
