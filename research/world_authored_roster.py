"""Literal skill levels shared by native observers and GPU input compilers.

No coefficient is evaluated here. Default cases retain their original level10;
explicit cases must supply all three levels for all five roster slots.
"""
import copy

def skill_levels(case):
    levels=case.get('skill_levels')
    if levels is None:
        if 'skill_levels' in case:raise ValueError('Five explicit skill-level maps required')
        return [{'1':10,'2':10,'3':10} for _ in range(5)]
    if not isinstance(levels,list) or len(levels)!=5:raise ValueError('Five explicit skill-level maps required')
    if any(not isinstance(row,dict) or set(row)!={'1','2','3'} or any(type(value) is not int or not 1<=value<=10 for value in row.values()) for row in levels):
        raise ValueError('Skill levels must have keys 1/2/3 and integer values 1..10')
    return copy.deepcopy(levels)
