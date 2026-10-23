"""Real all-definition preparation for the private physical projectile entry."""
from portable_world_roster_input import compile_world_battle,INPUT_WORDS,OUTPUT_WORDS
from portable_specs import LIMITS as L
from portable_projectile_specs import ABI,MODE,finalize_program
SOURCE='gpu/world_projectile_entry.slang'

def compile_projectile_battle(prepared, *, trace='burst', allow_physical_interrupt=False):
    words,metadata=compile_world_battle(prepared,trace=trace,allow_physical_interrupt=allow_physical_interrupt)
    finalize_program(words)
    metadata['real_prepared_input']['projectile_modifiers_connected']=True
    return words,metadata
