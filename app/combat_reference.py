"""Python binary64 transcription of combat.cu, not the pinned detail engine.

Keep expression grouping, event order, truncating casts and ties-to-even damage
rounding aligned with that source. Python pow is the host libm; CUDA libdevice
pow and compiler contraction are not claimed bit-exact without device evidence.
"""
from gpu_combat import CS, ES, NS, ME


def hit(c, b, env, coeff, normal, full, charged, flags):
    attack = max(c[0]*(1+b[0]/100)+b[1]-max(env[1]*(1+b[2]/100)+b[3], 0)*(1-b[4]/100), 0)
    crit = min(.15+(b[5]+(b[22] if normal else 0))/100, 1)*max(.5+(b[6]+(b[23] if normal else 0))/100, 0)
    core = min(1, pow(env[2]/max(c[13]*(1-.00908*b[21]), 1), 2.55)) if normal and env[2] > 0 else 0
    bonus = 1+crit+(.5 if full else 0)+(.3 if normal and c[14] > .5 else 0)+core*((c[12]-100+b[7])/100)
    charge = c[9]/100*(1+b[9]/100)+b[8]/100 if charged else 1
    extra = b[10]+(b[13] if flags & 1 else 0)+(b[14] if flags & 2 else 0)+(b[15] if flags & 4 else 0)+(b[16] if flags & 8 else 0)
    damage = coeff*(1+b[11]/100 if normal else 1)/100*attack*bonus*charge*(1+extra/100)*(1+b[12]/100)*(1.1+b[17]/100 if c[15] > .5 else 1)
    return float(max(round(damage), 1))


def combat_reference(model):
    c, e, env = model['chars'], model['effects'], model['enemy']
    stacks, expires = [0.0]*ME, [-1.0]*ME
    period = [q[5] for q in e]
    totals, ready, shots, warm = [0.0]*5, [0.0]*5, [0.0]*5, [0.0]*5
    next_shot = [c[i*CS+7] for i in range(5)]
    ammo = [c[i*CS+2] for i in range(5)]
    totalshots = cycles = castmask = 0
    fbend, burstnext = -1.0, 3.0

    def buffs(t, who):
        b = list(c[who*CS+20:(who+1)*CS])
        for j, q in enumerate(e):
            if int(q[3]) == 0 and stacks[j] > 0 and expires[j] > t-1e-8 and int(q[1]) & (1 << who):
                b[int(q[2])] += q[6]*stacks[j]
        return b

    def apply(j, q, t, full):
        if int(q[9]) == 1 and not full or int(q[9]) == 2 and full:
            return
        if int(q[3]) == 0:
            stacks[j] = min(stacks[j]+1, q[8])
            expires[j] = 1e30 if q[7] < 0 else t+q[7]
        elif int(q[3]) == 1:
            owner = int(q[0])
            totals[owner] += hit(c[owner*CS:(owner+1)*CS], buffs(t, owner), env, q[6], False, full, False, int(q[10]))*q[11]

    def event(t, ev, who, count, full):
        for j, q in enumerate(e):
            owner, timing = int(q[0]), int(q[4])
            if timing != ev or ev not in (0, 1, 2, 3, 10) and owner != who:
                continue
            if ev == 3 and not castmask & (1 << owner):
                continue
            if ev in (5, 6, 10) and (count <= 0 or count % int(q[5])):
                continue
            apply(j, q, t, full)

    event(0, 0, 0, 0, False)
    for i in range(5):
        ammo[i] = int(max(1, c[i*CS+2]*(1+buffs(0, i)[18]/100)))
    for frame in range(int(env[0]*60+.00001)):
        t = frame/60.0
        full = t < fbend
        if not full and fbend >= 0:
            event(t, 2, 0, 0, False)
            fbend = -1
        if not full and t+1e-8 >= burstnext:
            chosen = [-1]*3
            for stage in range(1, 4):
                for i in range(5):
                    if int(c[i*CS+16]) == stage and ready[i] <= t+1e-8:
                        if env[4] == i+1 and (cycles+1) % 3 != 0:
                            continue
                        chosen[stage-1] = i
                        break
            if all(i >= 0 for i in chosen):
                cycles += 1
                castmask = 0
                for i in chosen:
                    castmask |= 1 << i
                    ready[i] = t+c[i*CS+17]
                event(t, 3, 0, 0, False)
                for q in e:
                    if int(q[3]) == 2 and (int(q[4]) == 1 or int(q[4]) == 3 and castmask & (1 << int(q[0]))):
                        for i in range(5):
                            if int(q[1]) & (1 << i):
                                ready[i] -= q[6]
                fbend, full = t+10, True
                burstnext = fbend+2
                event(t, 1, 0, 0, full)
        for j, q in enumerate(e):
            if int(q[4]) == 4 and t+1e-8 >= period[j]:
                apply(j, q, t, full)
                period[j] += q[5]
        for i in range(5):
            if next_shot[i] > t+1e-8:
                continue
            a, b = c[i*CS:(i+1)*CS], buffs(t, i)
            cap = int(max(1, a[2]*(1+b[18]/100)))
            if ammo[i] <= 0:
                ammo[i], warm[i] = cap, 0
                event(t, 8, i, 0, full)
            totals[i] += hit(a, b, env, a[1]/a[10], True, full, a[7] > 0, 0)*a[10]*a[11]
            ammo[i] -= 1
            shots[i] += 1
            totalshots += 1
            warm[i] += 1
            event(t, 5, i, int(shots[i]), full)
            event(t, 6, i, int(shots[i]*a[10]*a[11]), full)
            event(t, 10, i, totalshots, full)
            if a[7] > 0:
                event(t, 9, i, 0, full)
            interval = max(a[19], a[7]*max(1-b[20]/100, .01)+a[8]) if a[7] > 0 else 1/max(a[4]+(a[5]-a[4])*min(warm[i]/max(a[6], 1), 1), .01)
            if ammo[i] <= 0:
                event(t, 7, i, 0, full)
                interval += max(a[3]*(1-b[19]/100), .05)
            next_shot[i] = t+interval
    return {'squad': model['names'], 'damage': int(sum(totals)), 'members': [int(v) for v in totals], 'shots': totalshots, 'cycles': cycles}
