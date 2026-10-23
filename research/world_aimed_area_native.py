"""Compose full returned-packet observation with actual native finish accounting."""
from unittest.mock import patch
import world_focus_aim_native as focus
from world_parts_skill_native import observe as accounting_observe
from world_aimed_packet_native import observe as packet_observe


def observe(case):
    with patch.object(focus,'plain_observe',accounting_observe):return packet_observe(case)
