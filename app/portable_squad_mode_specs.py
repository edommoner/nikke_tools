"""Versioned native character-mode state; no CPU runtime state is packed."""
INPUT_BASE=109656
VERSION=2
MAGIC=0x4d535431
STATE_BASE=1769808
SOURCE='gpu/world_coordinate_squad_mode_entry.slang'

def mark(words):
    result=list(words)
    if len(result)!=109792 or result[INPUT_BASE+1]!=1:raise ValueError('Complete v1 squad input required')
    result[INPUT_BASE+1]=VERSION;result[INPUT_BASE+5]=MAGIC
    return result
