"""One exact world-node reader for ordinary, actor and original comparisons."""
import struct
from portable_specs import LIMITS as L

def read_nodes(block,count,*,cleanse=False):
    if type(count) is not int or not 0<=count<=32:raise ValueError('World-node count outside wire capacity')
    base=L['WORLD_OVERLAY_STATE_BASE']+32
    if len(block)<base+count*8:raise ValueError('Truncated world-node readback')
    rows=[]
    for index in range(count):
        at=base+index*8
        row=dict(blocked=struct.unpack('<d',struct.pack('<II',*block[at+4:at+6]))[0],opens=block[at])
        if cleanse:
            if block[at+1] not in (0,1):raise ValueError('Invalid world-node dispel flag')
            row.update(dispelled=bool(block[at+1]),dispels=block[at+6])
        rows.append(row)
    return rows
