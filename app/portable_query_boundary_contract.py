"""Check the current query helpers retain their explicit compiler boundaries."""
import re
from pathlib import Path

BOUNDARIES={
    'gpu/world_actor_fields.slang':('actorFieldCommand',),
    'gpu/world_actor_state.slang':('actorNamedQueryCommand',),
    'gpu/world_actor_pools.slang':('actorPoolCommand',),
    'gpu/quantity_runtime.slang':('plainQuantity',),
    'gpu/ammo_instant_runtime.slang':('hasInfiniteAmmo','ammoInstantCapacity'),
}

def verify(root, *, sources=None):
    root=Path(root);sources=sources or {};names=[]
    for path,functions in BOUNDARIES.items():
        source=sources.get(path,(root/path).read_text())
        for name in functions:
            pattern=r'(?m)^\[noinline\]\n(?:bool|uint|uint64_t) '+re.escape(name)+r'\('
            assert len(re.findall(pattern,source))==1,'Query boundary missing or duplicated: '+name
            names.append(name)
    return dict(verified=True,functions=names,files=len(BOUNDARIES),gpu_calls=0)
