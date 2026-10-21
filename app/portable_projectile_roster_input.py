"""Real all-definition preparation for the private physical projectile entry."""
from portable_world_roster_input import compile_world_battle,INPUT_WORDS,OUTPUT_WORDS
from portable_specs import LIMITS as L
from portable_projectile_specs import ABI,MODE
SOURCE='gpu/world_projectile_entry.slang'

def compile_projectile_battle(prepared, *, trace='burst'):
    words,metadata=compile_world_battle(prepared,trace=trace)
    words[0]=ABI
    words[L['TARGET_COUNTER_INPUT_BASE']+6]=MODE
    metadata['real_prepared_input']['projectile_modifiers_connected']=True
    return words,metadata
