from pathlib import Path
p=Path(__file__).resolve().parent/'save-boss-buffs-checkpoint.py';s=p.read_text(encoding='utf-8')
for old,new in [('boss_buff_cases=38','boss_buff_cases=len(full["cases"])'),('long_native_180_second_battles=5','long_native_180_second_battles=len(long["cases"])'),('python_focused_tests_passed=75','python_focused_tests_passed=normal["tests_run"]')]:
 assert old in s,old;s=s.replace(old,new)
p.write_text(s,encoding='utf-8')
