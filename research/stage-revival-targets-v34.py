"""Add exact down-only and count-limited living target descriptors to v34."""
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];stage=ROOT/'research/staging/v34'
def edit(path,changes):
 p=stage/path;s=p.read_text(encoding='utf-8')
 for old,new in changes:
  assert old in s,(path,old[:90]);s=s.replace(old,new)
 p.write_text(s,encoding='utf-8')
edit('app/detail_gpu.py',[
 ("elif target=='self':q[4]=0", "elif isinstance(target,str) and re.fullmatch(r'allies_down_top_atk_excl:[1-5]',target):q[4]=22;q[5]=int(target.rsplit(':',1)[1])\n  elif isinstance(target,str) and re.fullmatch(r'allies_down_class_random:[^:]+:[1-5]',target):\n   _,role,count=target.split(':');q[4]=23;q[5]=int(count);q[48]=sum(1<<i for i,ch in enumerate(chars) if ch['_weapon'].get('class')==role)\n  elif target=='self':q[4]=0"),
 ("kind in (5,6,7,15,16,21)","kind in (5,6,7,15,16,21,22,23,24)"),
 ("parts=target.split(':');selected=list(range(5));prefix=parts[0]","parts=target.split(':');selected=list(range(5));prefix=parts[0];live_limit=None"),
 ("selected=selected[:int(parts[2])] if len(parts)>2 else selected","live_limit=int(parts[2]) if len(parts)>2 else None"),
 ("if prefix=='allies_code_weapon_leftmost':selected=selected[:int(parts[3])]","if prefix=='allies_code_weapon_leftmost':live_limit=int(parts[3])"),
 ("selected.sort(key=lambda i:-chars[i]['_weapon']['charge_time']);selected=selected[:int(parts[1])];q[141]=1", "selected.sort(key=lambda i:-chars[i]['_weapon']['charge_time']);live_limit=int(parts[1]);q[141]=1"),
 ("q[4]=8;q[48]=sum(1<<i for i in selected)\n  elif isinstance(target,str) and not ':' in target:", "q[4]=24 if live_limit is not None else 8;q[5]=min(live_limit,5) if live_limit is not None else 0;q[48]=sum(1<<i for i in selected)\n  elif isinstance(target,str) and not ':' in target:"),
 ("elif kind=='instant' and stat=='enemy_buff_cleanse':q[1]=28", "elif kind=='instant' and stat=='enemy_buff_cleanse':q[1]=28\n   elif kind=='instant' and stat=='revive':q[1]=29"),
 ("if q[1] in (6,7,8,27) and q[4]==4", "if q[1] in (6,7,8,27,29) and q[4]==4"),
 ("if stat=='trigger_count_reduce'", "if stat=='trigger_count_reduce'") if False else ("if q[1] in (16,17,18,19,20,21,22):", "if q[1]==29 and (not isinstance(q[6],(int,float)) or not math.isfinite(q[6]) or q[6]<=0):raise UnsupportedDetail('revive requires a positive HP percentage')\n   if q[1] in (16,17,18,19,20,21,22):")])
edit('app/detail_effects.cu',[
 ('if(lazy_target(q)||kind==20)return -1;', 'if(kind==24){int used=0;if(q[141]>0){for(Order raw=(Order)q[140];raw&&used<arg;raw>>=3){int who=(raw&7)-1;if(who>=0&&who<n&&((int)q[48]&(1<<who))&&!(s->down_mask&(1<<who))){mask|=1<<who;used++;}}}else for(int who=0;who<n&&used<arg;who++)if(((int)q[48]&(1<<who))&&!(s->down_mask&(1<<who))){mask|=1<<who;used++;}return mask;}\n if(lazy_target(q)||kind==20||kind==22||kind==23)return -1;'),
 ('if(s->down_mask&(1<<who))continue;\n  if(q[4]==19)', 'if(q[4]==23){if((s->down_mask&(1<<who))&&((int)q[48]&(1<<who)))pool[n++]=who;continue;}\n  if(s->down_mask&(1<<who))continue;\n  if(q[4]==19)'),
 ('if(q[4]==19||q[4]==20)return random_target', 'if(q[4]==19||q[4]==20||q[4]==23)return random_target'),
 ('if(s->down_mask&(1<<who)||mask&(1<<who)||q[49]>0', 'if((kind==22?!(s->down_mask&(1<<who))||who==owner:bool(s->down_mask&(1<<who)))||mask&(1<<who)||q[49]>0'),
 ('double v=kind==5||kind==15?rank_atk(c,e,ne,s,who,full)', 'double v=kind==5||kind==15||kind==22?rank_atk(c,e,ne,s,who,full)'),
 ('if(mask<0&&(eager||q[4]==20))', 'if(mask<0&&(eager||q[4]==20||q[4]==22||q[4]==23))')])
print('Staged revival descriptors; revival notification FSM remains to be implemented before GPU builds.')
