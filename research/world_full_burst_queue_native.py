"""Reuse the actual full-burst and part-packet observers without replay."""
from world_frame_native import roster_names
from world_full_burst_landing_native import capture
from world_parts_skill_native import observe as plain

def observe(case):
    with capture(roster_names(case)) as o:n,t=plain(case)
    o['packets']=t;n['full_burst_queue']=o;return n,t
