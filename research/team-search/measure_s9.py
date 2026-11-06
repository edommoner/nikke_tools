"""S9 surrogate research. Standard library only; native failures never use CPU fallback."""
import argparse, collections, contextlib, functools, heapq, json, math, os
from pathlib import Path
import random, shlex, shutil, statistics, subprocess, sys, tempfile, time
sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
SCRATCH = ROOT.parent/'proofs/claude-product-standard-phase0-v1-20261102/team-search-v1/s9'
sys.path.insert(0, str(ROOT/'app'))
import measure_s1 as s1
INPUT = json.loads((HERE/'s1-inputs.json').read_text())
CHARS = {c['name']:c for c in INPUT['characters']['characters']}
NAMES = list(CHARS)
INDEX = {n:i for i,n in enumerate(NAMES)}


def read(path):
    return [json.loads(line) for line in path.read_text().splitlines()] if path.exists() else []


def save(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False)+'\n')


def preflight(label):
    SCRATCH.mkdir(parents=True, exist_ok=True)
    budget = 2*1024**3  # copied warm caches <1 GiB, bounded captures, models and JSON
    free = shutil.disk_usage(ROOT).free
    if free < 20*1024**3+budget:
        raise RuntimeError('Need 20 GiB reserve plus 2 GiB peak additional budget')
    r = subprocess.run([sys.executable,str(ROOT/'scripts/nikke_storage.py'),'storage-check',
                        '--path',str(ROOT),'--required-bytes',str(budget)],capture_output=True,text=True)
    if r.returncode: raise RuntimeError(r.stdout+r.stderr)
    save(SCRATCH/(label+'-storage.json'),dict(free_bytes=free,budget_bytes=budget,check=r.stdout))


def generate(count, seed, excluded):
    rng=random.Random(seed); seen=set(excluded); out=[]
    while len(out)<count:
        squad=tuple(rng.sample(NAMES,5))
        if squad in seen or not s1.covered(squad,CHARS): continue
        seen.add(squad); out.append(squad)
    return out


class CacheRoot:
    """Keep source reads at ROOT and all adapter cache writes in owned scratch."""
    def __fspath__(self): return str(ROOT)
    def __truediv__(self, part):
        if str(part).startswith('research/portable-build'):
            return SCRATCH/'cache'/Path(part).relative_to('research/portable-build')
        return ROOT/part


def native_setup():
    import portable_backend, portable_detail, portable_native
    os.environ.update(s1.node(dict(action='env')))
    cache=SCRATCH/'cache';cache.mkdir(exist_ok=True)
    # Preserve warm-cache behavior while restricting every write to allowed scratch.
    for name in ('cpp','native'):
        if not (cache/name).exists():
            shutil.copytree(ROOT/'research/portable-build'/name,cache/name)
    portable_backend.ROOT=CacheRoot()
    portable_native.HOST_THREADS.set(10)
    # Fail closed if a future adapter accidentally attempts reference evaluation.
    def forbidden(*a,**kw): raise RuntimeError('S9 forbids CPU reference/fallback')
    portable_detail._cpu_fallback=forbidden
    portable_detail.cpu_fallback_portable_detail=forbidden
    body=json.loads(Path(INPUT['benchmark']).read_text())[0]
    body.update(INPUT['settings'])
    return portable_detail,portable_native,body


def evaluate(rows, path):
    pd,pn,body=native_setup(); done={r['id']:r for r in read(path)}
    for row in rows:
        if row['id'] in done and list(row['members']) != done[row['id']]['members']:
            raise ValueError('Resume identity mismatch')
    pending=[r for r in rows if r['id'] not in done]
    for offset in range(0,len(pending),32):
        batch=pending[offset:offset+32]; started=time.perf_counter(); timers=collections.defaultdict(float)
        diagnostic=path.name=='s9-dataset.jsonl' and all(r['id']<320 for r in batch)
        def timed(obj,name,label):
            original=getattr(obj,name)
            @functools.wraps(original)
            def call(*a,**kw):
                t=time.perf_counter()
                try: return original(*a,**kw)
                finally: timers[label]+=time.perf_counter()-t
            return call
        with contextlib.ExitStack() as stack:
            if diagnostic:
                from unittest.mock import patch
                for obj,name,label in ((pd,'prepare','prepare'),(pd,'compile_product','compile'),
                                       (pd,'decode_payload','decode'),(pd,'execute','dispatch'),
                                       (pn,'run_host','host_process')):
                    call=timed(obj,name,label)
                    stack.enter_context(patch.object(obj,name,call))
            capture=tempfile.TemporaryDirectory(prefix='capture-',dir=SCRATCH)
            previous=os.environ.get('NIKKE_DETAIL_CAPTURE_ROOT')
            os.environ['NIKKE_DETAIL_CAPTURE_ROOT']=capture.name
            try:
                results=pd.evaluate_many([dict(body,squad=r['members']) for r in batch],verification='deferred')
                # Kernel host seconds are per physical transport, counted once.
                host_seconds=0.
                for ev in Path(capture.name).glob('**/evidence.json'):
                    evidence=json.loads(ev.read_text())
                    if ev.parent.name.startswith('batch-') or not (ev.parent/'batch-member.json').exists():
                        host_seconds+=evidence['transport']['host_seconds']
                for row,result in zip(batch,results):
                    p=result.get('result',{}); marker=p.get('cpu_fallback_pending') or {};compute=p.get('compute',{})
                    row.update(total_damage=p.get('total_damage'),backend=compute.get('backend','native_failed'),
                               fallback_reason=marker.get('reason') or compute.get('fallback_reason'),
                               error=result.get('error'),unsupported=marker.get('unsupported'))
            finally:
                if previous is None: os.environ.pop('NIKKE_DETAIL_CAPTURE_ROOT',None)
                else: os.environ['NIKKE_DETAIL_CAPTURE_ROOT']=previous
                t=time.perf_counter();capture.cleanup();timers['cleanup']=time.perf_counter()-t
        elapsed=time.perf_counter()-started
        with path.open('a') as f:
            for row in batch:
                row['batch_elapsed_seconds']=elapsed
                if diagnostic: row['diagnostic']=dict(timers,kernel=host_seconds,batch_n=len(batch))
                f.write(json.dumps(row,ensure_ascii=False)+'\n')
            f.flush();os.fsync(f.fileno())
        print(f'{path.name} {len(done)+offset+len(batch)}/{len(rows)} batch {elapsed:.2f}s',flush=True)


def dataset():
    preflight('B')
    squads=generate(12000,44,{tuple(r['members']) for r in read(HERE/'s1-results.jsonl')})
    evaluate([dict(id=i,members=list(s)) for i,s in enumerate(squads)],HERE/'s9-dataset.jsonl')


def valid(rows):
    return [r for r in rows if r['backend']=='native_detail' and r.get('total_damage',0)>0]


def dot(a,b): return sum(x*y for x,y in zip(a,b))


def ridge(xs,ys,lam):
    """Centered ridge, unpenalized intercept; matrix-free conjugate gradients."""
    p=1+max((i for x in xs for i,v in x),default=-1); n=len(xs)
    means=[0.]*p; rhs=[0.]*p; ym=statistics.mean(ys)
    diag=[lam]*p
    for x,y in zip(xs,ys):
        for i,v in x: means[i]+=v/n;rhs[i]+=v*(y-ym);diag[i]+=v*v
    diag=[max(1e-9,d-n*m*m) for d,m in zip(diag,means)]
    def mv(w):
        z=[lam*v for v in w]; shift=dot(means,w)
        for x in xs:
            val=sum(w[i]*v for i,v in x)
            for i,v in x: z[i]+=v*val
        return [v-n*m*shift for v,m in zip(z,means)]
    w=[0.]*p;r=rhs[:];z=[v/d for v,d in zip(r,diag)];direction=z[:];rz=dot(r,z)
    base=max(dot(rhs,rhs),1e-30)
    for step in range(250):
        if dot(r,r)/base<1e-14: break
        ap=mv(direction);den=dot(direction,ap)
        if den<=0:break
        alpha=rz/den;w=[v+alpha*d for v,d in zip(w,direction)]
        r=[v-alpha*a for v,a in zip(r,ap)];z=[v/d for v,d in zip(r,diag)]
        next_rz=dot(r,z);beta=next_rz/rz;direction=[v+beta*d for v,d in zip(z,direction)];rz=next_rz
    return dict(kind='ridge',weights=w,intercept=ym-dot(means,w),lam=lam,iterations=step+1,relative_squared_residual=dot(r,r)/base)


def linear_predict(model,x):
    w=model['weights'];return model['intercept']+sum(w[i]*v for i,v in x if i<len(w))


def membership(squad): return [(INDEX[n],1.) for n in squad]


def slot(squad):
    x=membership(squad);counts=collections.Counter()
    for n in squad:
        stage=CHARS[n]['burst'];rank=counts[stage];counts[stage]+=1
        x.append((len(NAMES)+5*INDEX[n]+rank,1.))
    return x


def attributes():
    import engine_worker as ew
    body=json.loads(Path(INPUT['benchmark']).read_text())[0]
    metadata=ew.META;cats=['burst_stage','element_code','weapon_type','class','manufacturer']
    keys=[(k,v) for k in cats for v in sorted({str(metadata[n].get(k,'')) for n in NAMES})]
    raw=[];numeric=None
    for n in NAMES:
        growth=ew.normalize_growth(n,body['profile']['chars'][n]);growth['level']=400
        no_cube=growth['cube']['name']=='__none__'
        if no_cube:growth['cube']={'name':next(iter(ew.spec.CUBES)),'level':1}
        profile={'base':'ungrown','_account':body['profile'].get('_account',{}),'chars':{n:growth}}
        char=ew.spec.build_char(n,no_layer=True,profile=ew.spec.load_profile(profile))
        stats=ew.base_stat.calc_base_stats(char)
        if no_cube:
            for k in ('atk','def','hp'):stats[k]-=ew.base_stat._CUBE['_stats']['1'][k]
        if numeric is None:numeric=sorted(k for k,v in stats.items() if isinstance(v,(int,float)))
        raw.append([float(str(metadata[n].get(k,''))==v) for k,v in keys]+[float(stats[k]) for k in numeric])
    scales=[max(abs(r[j]) for r in raw) or 1 for j in range(len(raw[0]))]
    raw=[[v/s for v,s in zip(r,scales)] for r in raw]
    labels=[f'{k}={v}' for k,v in keys]+numeric
    def feature(squad):
        sums=[sum(raw[INDEX[n]][j] for n in squad) for j in range(len(labels))]
        values=sums+[sums[i]*sums[j] for i in range(len(sums)) for j in range(i,len(sums))]
        return [(i,v) for i,v in enumerate(values) if v]
    return feature,dict(labels=labels,scales=scales,character_values=raw)


def fm_fit(xs,ys,k,reg,epochs=35):
    rng=random.Random(47);mean=statistics.mean(ys);w=[0.]*len(NAMES)
    factors=[[rng.gauss(0,.04) for _ in range(k)] for i in NAMES];order=list(range(len(xs)))
    for epoch in range(epochs):
        rng.shuffle(order);lr=.015/(1+.06*epoch)
        for ix in order:
            ids=xs[ix];vs=[factors[i] for i in ids];sums=[sum(v[f] for v in vs) for f in range(k)]
            pred=mean+sum(w[i] for i in ids)+.5*sum(sums[f]**2-sum(v[f]**2 for v in vs) for f in range(k))
            err=max(-5.,min(5.,pred-ys[ix]))
            for i in ids:
                w[i]-=lr*(err+reg*w[i]);v=factors[i]
                for f in range(k):v[f]-=lr*(err*(sums[f]-v[f])+reg*v[f])
    return dict(kind='fm',intercept=mean,weights=w,factors=factors,k=k,reg=reg,epochs=epochs)


def fm_predict(model,ids):
    vs=[model['factors'][i] for i in ids]
    return model['intercept']+sum(model['weights'][i] for i in ids)+sum(dot(vs[i],vs[j]) for i in range(5) for j in range(i))


def rank_metrics(x,y):
    rx,ry=s1.ranks(x),s1.ranks(y);mx=statistics.mean(rx);my=statistics.mean(ry)
    den=math.sqrt(sum((v-mx)**2 for v in rx)*sum((v-my)**2 for v in ry))
    spearman=sum((a-mx)*(b-my) for a,b in zip(rx,ry))/den if den else None
    # Fenwick counts compare only strictly different x groups; tie corrections
    # include ties in both coordinates, as required by Kendall tau-b.
    yindex={v:i+1 for i,v in enumerate(sorted(set(y)))};tree=[0]*(len(yindex)+1)
    def prefix(i):
        result=0
        while i:result+=tree[i];i-=i&-i
        return result
    order=sorted(range(len(x)),key=lambda i:x[i]);score=seen=0;offset=0
    while offset<len(order):
        end=offset+1
        while end<len(order) and x[order[end]]==x[order[offset]]:end+=1
        for i in order[offset:end]:
            j=yindex[y[i]];score+=prefix(j-1)-(seen-prefix(j))
        for i in order[offset:end]:
            j=yindex[y[i]]
            while j<len(tree):tree[j]+=1;j+=j&-j
            seen+=1
        offset=end
    pairs=len(x)*(len(x)-1)//2
    ties=lambda values:sum(v*(v-1)//2 for v in collections.Counter(values).values())
    kd=math.sqrt((pairs-ties(x))*(pairs-ties(y)))
    return dict(n=len(x),spearman=spearman,kendall_tau_b=score/kd if kd else None)


def metrics(rows,pred):
    ys=[math.log(r['total_damage']) for r in rows]
    corr=rank_metrics(pred,ys)
    corr['rmse_log']=math.sqrt(statistics.mean((a-b)**2 for a,b in zip(ys,pred)))
    truth=sorted(range(len(rows)),key=lambda i:(-ys[i],rows[i]['id']))
    order=sorted(range(len(rows)),key=lambda i:(-pred[i],rows[i]['id']))
    corr['recall']={str(n):{str(k):len(set(truth[:n])&set(order[:math.ceil(k*len(rows))]))/min(n,len(rows))
                                 for k in (.01,.05,.1,.2)} for n in (20,100)}
    return corr


def sufficient_stats(xs,ys,p):
    stats=dict(n=len(xs),sum_y=sum(ys),sum_x=[0.]*p,rhs=[0.]*p,gram=[[0.]*(i+1) for i in range(p)])
    for x,y in zip(xs,ys):
        # Feature construction already yields increasing indices.
        for offset,(i,v) in enumerate(x):
            stats['sum_x'][i]+=v;stats['rhs'][i]+=v*y;row=stats['gram'][i]
            for j,u in x[:offset+1]:row[j]+=v*u
    return stats


def combine_stats(parts,signs):
    p=len(parts[0]['sum_x'])
    return dict(n=sum(sign*a['n'] for a,sign in zip(parts,signs)),
        sum_y=sum(sign*a['sum_y'] for a,sign in zip(parts,signs)),
        sum_x=[sum(sign*a['sum_x'][i] for a,sign in zip(parts,signs)) for i in range(p)],
        rhs=[sum(sign*a['rhs'][i] for a,sign in zip(parts,signs)) for i in range(p)],
        gram=[[sum(sign*a['gram'][i][j] for a,sign in zip(parts,signs)) for j in range(i+1)] for i in range(p)])


def ridge_cholesky(stats,lam):
    n=stats['n'];sx=stats['sum_x'];p=len(sx);ym=stats['sum_y']/n
    rhs=[v-x*ym for v,x in zip(stats['rhs'],sx)]
    lower=[[v-sx[i]*sx[j]/n+(lam if i==j else 0.) for j,v in enumerate(row)] for i,row in enumerate(stats['gram'])]
    for i in range(p):
        row=lower[i]
        for j in range(i+1):
            other=lower[j];value=row[j]-sum(row[k]*other[k] for k in range(j))
            row[j]=math.sqrt(value) if i==j else value/other[j]
    z=[]
    for i in range(p):z.append((rhs[i]-sum(lower[i][j]*z[j] for j in range(i)))/lower[i][i])
    w=[0.]*p
    for i in range(p-1,-1,-1):w[i]=(z[i]-sum(lower[j][i]*w[j] for j in range(i+1,p)))/lower[i][i]
    return dict(kind='ridge',weights=w,intercept=ym-dot(sx,w)/n,lam=lam,solver='centered Cholesky')


def choose_attribute_ridge(xs,ys):
    p=1+max(i for x in xs for i,v in x)
    folds=[sufficient_stats([x for i,x in enumerate(xs) if i%5==f],[y for i,y in enumerate(ys) if i%5==f],p) for f in range(5)]
    full=combine_stats(folds,[1]*5);training=[combine_stats([full,fold],[1,-1]) for fold in folds];candidates=[]
    for lam in (.1,1.,10.,100.):
        losses=[]
        for f in range(5):
            m=ridge_cholesky(training[f],lam)
            losses.extend((linear_predict(m,x)-y)**2 for i,(x,y) in enumerate(zip(xs,ys)) if i%5==f)
        candidates.append(dict(lam=lam,mse=statistics.mean(losses)))
    best=min(candidates,key=lambda a:a['mse'])['lam']
    return ridge_cholesky(full,best),candidates


def choose_ridge(xs,ys):
    candidates=[]
    # Split train deterministically into five interleaved folds; no holdout use.
    for lam in (.1,1.,10.,100.):
        losses=[]
        for fold in range(5):
            model=ridge([x for i,x in enumerate(xs) if i%5!=fold],[y for i,y in enumerate(ys) if i%5!=fold],lam)
            losses.extend((linear_predict(model,x)-y)**2 for i,(x,y) in enumerate(zip(xs,ys)) if i%5==fold)
        candidates.append(dict(lam=lam,mse=statistics.mean(losses)))
    best=min(candidates,key=lambda a:a['mse'])['lam']
    return ridge(xs,ys,best),candidates


def models():
    started=time.perf_counter();rows=valid(read(HERE/'s9-dataset.jsonl'))
    if len(read(HERE/'s9-dataset.jsonl'))!=12000:raise ValueError('Part B incomplete')
    random.Random(45).shuffle(rows)
    # Keep 10,000 successful training rows; native failures reduce holdout.
    train=rows[:10000];holdout=rows[10000:12000]
    if len(train)<5000:raise ValueError('Too few native successes')
    ys=[math.log(r['total_damage']) for r in train];attr,attrmeta=attributes()
    features={'M1':membership,'M2':slot,'M4':attr}; fitted={}; selection={};times={}
    for name,feature in features.items():
        t=time.perf_counter();xs=[feature(r['members']) for r in train]
        fitted[name],selection[name]=(choose_attribute_ridge if name=='M4' else choose_ridge)(xs,ys);times[name]=time.perf_counter()-t
        print(name,'fit seconds',times[name],flush=True)
    ids=[[INDEX[n] for n in r['members']] for r in train];t=time.perf_counter();vsize=max(1,len(train)//5)
    choices=[]
    for k in (4,8,16):
        for reg in (.001,.01,.1):
            model=fm_fit(ids[vsize:],ys[vsize:],k,reg)
            mse=statistics.mean((fm_predict(model,x)-y)**2 for x,y in zip(ids[:vsize],ys[:vsize]))
            choices.append(dict(k=k,reg=reg,mse=mse));print('FM',choices[-1],flush=True)
    best=min(choices,key=lambda a:a['mse']);fitted['M3']=fm_fit(ids,ys,best['k'],best['reg']);times['M3']=time.perf_counter()-t;selection['M3']=choices
    # M0 remains unfitted: log(simple score) for RMSE, preserving S1 ranking.
    def predict(name,rs):
        if name=='M0':return [math.log(sum(CHARS[n]['potential'] for n in r['members'])) for r in rs]
        if name=='M3':return [fm_predict(fitted[name],[INDEX[n] for n in r['members']]) for r in rs]
        return [linear_predict(fitted[name],features[name](r['members'])) for r in rs]
    external=valid(read(HERE/'s1-results.jsonl'));sets={'holdout':holdout,'S1-external':external}
    sets.update({f'S1-{c}':[r for r in external if r['cohort']==c] for c in 'ABC'})
    scores={name:{label:metrics(rs,predict(name,rs)) for label,rs in sets.items()} for name in ('M0','M1','M2','M3','M4')}
    winner=max(scores,key=lambda name:scores[name]['holdout']['recall']['100']['0.05'])
    curves={}
    for size in (1000,2500,5000,10000):
        actual=min(size,len(train));t=time.perf_counter()
        # Reuse the train-selected hyperparameters; curve subsets never tune on holdout.
        m1=ridge([membership(r['members']) for r in train[:actual]],ys[:actual],fitted['M1']['lam'])
        m3=fm_fit(ids[:actual],ys[:actual],best['k'],best['reg'])
        curves[str(size)]=dict(actual_train=actual,M1=metrics(holdout,[linear_predict(m1,membership(r['members'])) for r in holdout]),
            M3=metrics(holdout,[fm_predict(m3,[INDEX[n] for n in r['members']]) for r in holdout]),wall_seconds=time.perf_counter()-t)
    result=dict(train_n=len(train),holdout_n=len(holdout),native_n=len(rows),split='seed45 shuffle successful rows; first 10000 train, remaining holdout',
                train_ids=[r['id'] for r in train],holdout_ids=[r['id'] for r in holdout],selection=selection,fit_seconds=times,
                scores=scores,learning_curves=curves,winner=winner,wall_seconds=time.perf_counter()-started)
    save(SCRATCH/'models.json',dict(fitted=fitted,attributes=attrmeta))
    save(SCRATCH/'part-c.json',result)
    print('Part C winner',winner,flush=True)


def scorer(name,model,attrmeta):
    if name=='M0':return lambda s:math.log(sum(CHARS[n]['potential'] for n in s))
    if name=='M3':return lambda s:fm_predict(model,[INDEX[n] for n in s])
    if name in ('M1','M2'):
        feature=membership if name=='M1' else slot
        return lambda s:linear_predict(model,feature(s))
    raw=attrmeta['character_values'];d=len(raw[0])
    def score(s):
        sums=[sum(raw[INDEX[n]][j] for n in s) for j in range(d)]
        values=sums+[sums[i]*sums[j] for i in range(d) for j in range(i,d)]
        return model['intercept']+dot(model['weights'],values)
    return score


def search():
    preflight('D');part=json.loads((SCRATCH/'part-c.json').read_text());bundle=json.loads((SCRATCH/'models.json').read_text())
    name=part['winner'];score=scorer(name,bundle['fitted'].get(name),bundle['attributes'])
    candidates_path=SCRATCH/'search-candidates.json'
    if candidates_path.exists():
        saved=json.loads(candidates_path.read_text())
        if saved['model']!=name:raise ValueError('Saved candidate model mismatch')
    else:
        seen={tuple(r['members']) for f in ('s1-results.jsonl','s9-dataset.jsonl','s9-search.jsonl') for r in read(HERE/f)}
        rng=random.Random(46);heap=[];accepted=0;score_seconds=0.;started=time.perf_counter()
        while accepted<1000000:
            squad=tuple(rng.sample(NAMES,5))
            if squad in seen or not s1.covered(squad,CHARS):continue
            seen.add(squad);t=time.perf_counter();value=score(squad);score_seconds+=time.perf_counter()-t
            item=(value,-accepted,squad)
            if len(heap)<300:heapq.heappush(heap,item)
            elif item>heap[0]:heapq.heapreplace(heap,item)
            accepted+=1
        saved=dict(model=name,count=accepted,score_seconds=score_seconds,generation_and_scoring_seconds=time.perf_counter()-started,
                   candidates=[dict(id=i,members=list(s),model_score=v,candidate_index=-neg) for i,(v,neg,s) in enumerate(sorted(heap,reverse=True))])
        save(candidates_path,saved)
    evaluate(saved['candidates'],HERE/'s9-search.jsonl')
    search_statistics()


def distribution(rows):
    values=sorted(r['total_damage'] for r in rows)
    return dict(n=len(values),max=max(values),top10_mean=statistics.mean(values[-10:]),median=statistics.median(values),
                p99=values[math.ceil(.99*len(values))-1],p90=values[math.ceil(.9*len(values))-1])


def search_statistics():
    candidate_path=SCRATCH/'search-candidates.json'
    if candidate_path.exists():
        candidates=json.loads(candidate_path.read_text())
    else:
        # Ranking statistics come entirely from JSONL. Original timing metadata
        # survives in the allowed summary when an ephemeral scratch is absent.
        previous=json.loads((HERE/'s9-summary.json').read_text())['part_d']
        candidates=dict(model=previous['model'],count=previous['candidate_count'],
            score_seconds=previous['score_seconds_per_million'],
            generation_and_scoring_seconds=previous['generation_and_scoring_seconds'])
    rows=read(HERE/'s9-search.jsonl');good=valid(rows)
    randoms=valid(read(HERE/'s9-dataset.jsonl'))+valid([r for r in read(HERE/'s1-results.jsonl') if r['cohort'] in ('B','C')])
    baseline=distribution(randoms)
    stats=dict(model=candidates['model'],candidate_count=candidates['count'],score_seconds_per_million=candidates['score_seconds'],
               generation_and_scoring_seconds=candidates['generation_and_scoring_seconds'],search=distribution(good),random=baseline,
               beat_random={k:sum(r['total_damage']>baseline[k] for r in good) for k in ('max','p99','p90')},
               metrics=metrics(good,[r['model_score'] for r in good]),counts=counts(rows),
               extrapolated_seconds_2_9e9=candidates['score_seconds']*2900,
               exact_unordered_sets=math.comb(len(NAMES),5),
               extrapolated_seconds_exact=candidates['score_seconds']*math.comb(len(NAMES),5)/1000000)
    save(SCRATCH/'part-d.json',stats)


def counts(rows):
    return dict(generated=len(rows),native_ok=len(valid(rows)),backends=dict(collections.Counter(r['backend'] for r in rows)),
                failed_by_reason=dict(collections.Counter(r.get('fallback_reason') or r.get('error') or 'unknown' for r in rows if r['backend']!='native_detail' or not r.get('total_damage',0))))


def report():
    rows=read(HERE/'s9-dataset.jsonl');c=json.loads((SCRATCH/'part-c.json').read_text());d=json.loads((SCRATCH/'part-d.json').read_text())
    a=collections.defaultdict(float);batches={}
    for r in rows:
        if 'diagnostic' in r:batches[r['id']//32]=r
    for r in batches.values():
        for k,v in r['diagnostic'].items():
            if k!='batch_n':a[k]+=v
        a['end_to_end']+=r['batch_elapsed_seconds']
    n=sum(r['diagnostic']['batch_n'] for r in batches.values())
    a['native_and_adapter_residual']=a['end_to_end']-sum(a[k] for k in ('prepare','compile','decode','cleanup'))
    a['dispatch_outside_host']=a['dispatch']-a['host_process']
    a['host_outside_kernel']=a['host_process']-a['kernel']
    a=dict(n=n,seconds=dict(a),ms_per_squad={k:v/n*1000 for k,v in a.items()})
    summary=dict(part_a=a,part_b=counts(rows),part_c=c,part_d=d)
    save(HERE/'s9-summary.json',summary)
    lines=['# S9: learned surrogate for squad search','',
        'Research only; native detailed rankings are unverified (`verify_detail=false`, deferred verification). No CPU reference or fallback runs.', '',
        '## Method','',
        'S1 benchmark profile and settings are reused unchanged: 206 characters, 180 s, level 400, DEF 31784, wind, 50 px core, 25 m, auto burst, fixed gauge. '
        'The unchanged S1 Node adapter supplies tool environment only; it is not invoked per squad. '
        'Uniform ordered samples use `random.sample(names, 5)` and reject missing burst coverage (the S1 rule), exact ordered duplicates and S1 rows. Dataset seed 44; search seed 46. '
        'Each A-stage member covers one otherwise missing stage. Ordering is sampled uniformly and retained.',
        'Native `portable_detail.evaluate_many` uses batches of 32 (last search batch 12), 10 host threads, deferred verification. '
        'Pending fallbacks are copied to JSONL and excluded; the fallback entry points are guarded against reference execution. '
        'JSONL is append-only and flushed/fsynced per batch; restart checks member identity and skips saved IDs. '
        'Only owned temporary capture directories are removed after result extraction. Warm native caches are copied into scratch to keep adapter writes inside the allowed scope. No throughput optimization was made.', '',
        '## Part A: first 320 squads','',
        'Timers wrap the existing Python preparation, compiler, decoder, native execute and native host calls. Host-reported kernel seconds are counted once per physical dispatch. '
        'Dispatch includes build-cache checks, transport, readback and digests; host process includes launch and host I/O. These nested measurements must not be added twice. '
        'End-to-end includes extraction and cleanup, excluding JSONL output and one-time setup/cache copying. Concurrent dispatch, host-process and kernel timings are summed work durations and overlap. The native-and-adapter residual is elapsed time minus serial preparation, compile, decode and cleanup; it includes transport critical path and remaining Python/I/O. It cannot separate kernel critical-path time from transport overhead without changing the adapter. dispatch_outside_host and host_outside_kernel are differences of summed call durations, not additional elapsed components.', '',
        '| Component | ms/squad |','|---|---:|']
    for k,v in a['ms_per_squad'].items():lines.append(f'| {k} | {v:.4f} |')
    largest=max(('prepare','compile','decode','cleanup','native_and_adapter_residual'),key=lambda k:a['seconds'][k])
    lines += ['',f'Largest elapsed-time component (dispatch and adapter overhead grouped by residual): **{largest}**. Node time in these batches: 0 (one environment lookup occurs before evaluation).', '',
              '## Counts and storage','',f"Dataset: {summary['part_b']['generated']} generated; {summary['part_b']['native_ok']} native successes. Backends: {summary['part_b']['backends']}.",
              f"Train / holdout: **{c['train_n']} / {c['holdout_n']}** successful rows. Native failures make a 10,000/2,000 successful split impossible from exactly 12,000 generated rows; preserve 10,000 train and reduce holdout. Split: {c['split']}.",
              'S1 native successes form a separate external test set, reported both together and by A/B/C. A is template-selected and C lacks the burst constraint, so neither matches the random covered sampling distribution.', '',
              '| Failure reason | Dataset squads |','|---|---:|']
    lines += [f'| {k.replace(chr(10)," ").replace("|","/")} | {v} |' for k,v in summary['part_b']['failed_by_reason'].items()]
    for label in ('B','D'):
        storage=json.loads((SCRATCH/(label+'-storage.json')).read_text())
        lines += ['',f"Before Part {label}: {storage['free_bytes']/1024**3:.3f} GiB free; 2 GiB additional peak budget and 20 GiB reserve passed both shutil.disk_usage and storage-check. No raw captures retained."]
    lines += ['', '## Part C: features, fitting and selection','',
        'Target is natural log damage. M0 is the unchanged unfitted sum potential, mapped through log for RMSE; it has no fitted damage calibration. '
        'M1 uses 206 membership indicators and an unpenalized intercept. '
        'M2 adds `(character, within-stage rank)` indicators: scan the ordered tuple left to right, count preceding members whose literal burst-stage label equals this character’s label, and use ranks 0–4. A is its own stage group; this feature does not expand A into stages 1/2/3. '
        'M1/M2 ridge penalty is λ × sum(weights²); loss is sum squared errors. Choose λ from {0.1,1,10,100} by five interleaved folds of the seed-45 shuffled training rows, minimizing pooled validation log MSE. M1/M2 use matrix-free centered conjugate gradients with relative squared residual <1e-14 or 250 steps. M4 uses centered normal equations and Cholesky; sufficient statistics are collected separately for each training fold.',
        'M3 is an unordered membership factorization machine: intercept + sum character biases + sum pairwise factor dot products. '
        'Seed 47 initializes factors and shuffles SGD. 35 epochs, rate 0.015/(1+0.06×epoch), clipped residual ±5. '
        'Choose rank {4,8,16} and regularization {0.001,0.01,0.1} on the first 20% of training (fit the remaining 80%), minimizing log MSE, then refit all training. Intercept is the training mean; regularization applies to active biases/factors at each update.',
        'M4 contains no character IDs: counts of burst-stage, element, weapon, class and manufacturer, plus sums of numeric base stats derived from the S1 profile by existing static stat calculation. '
        'Aggregate inputs are '+', '.join(json.loads((SCRATCH/'models.json').read_text())['attributes']['labels'])+'. '
        'Numeric fields are divided by the maximum absolute per-character value in the profile (no labels); categorical fields are unscaled. Include all upper-triangle products of these squad sums/counts, including squares. Ridge selection is identical to M1. This feature map can score unseen identities when their attributes are supplied; unseen category values require an expanded schema/refit.',
        'All fitting uses training only; holdout selects the search model by top-100 recall at K=5%, with model order breaking ties. '
        'All top-K sizes are ceil(fraction×evaluated n), ties use stable row ID. Spearman uses average ranks; Kendall is tie-corrected tau-b. '
        'Learning curves use training prefixes and the full-training-selected hyperparameters; they measure data volume with those fixed settings.', '',
        '| Model | Fit + selection wall seconds | Selected settings |','|---|---:|---|']
    bundle=json.loads((SCRATCH/'models.json').read_text())
    for name,t in c['fit_seconds'].items():
        m=bundle['fitted'][name];settings={k:m[k] for k in ('lam','k','reg','epochs') if k in m}
        lines.append(f'| {name} | {t:.3f} | {settings} |')
    lines += ['', '| Model | Set | n | Spearman | Kendall tau-b | log RMSE |', '|---|---|---:|---:|---:|---:|']
    for name,sets in c['scores'].items():
        for label,m in sets.items():lines.append(f"| {name} | {label} | {m['n']} | {m['spearman']:.6f} | {m['kendall_tau_b']:.6f} | {m['rmse_log']:.6f} |")
    def recall_table(title,items):
        lines.extend(['',title,'','| Model / set | True top-N | K=1% | K=5% | K=10% | K=20% |','|---|---:|---:|---:|---:|---:|'])
        for label,m in items:
            for top,values in m['recall'].items():lines.append(f'| {label} | {top} | '+' | '.join(f'{v:.2%}' for v in values.values())+' |')
    recall_table('### Top-N recall',[(name+' / '+label,m) for name,sets in c['scores'].items() for label,m in sets.items()])
    lines += ['', '### Learning curves','', '| Model | Training n | Spearman | Kendall tau-b | log RMSE |', '|---|---:|---:|---:|---:|']
    for size,curve in c['learning_curves'].items():
        for name in ('M1','M3'):
            m=curve[name];lines.append(f"| {name} | {curve['actual_train']} | {m['spearman']:.6f} | {m['kendall_tau_b']:.6f} | {m['rmse_log']:.6f} |")
    recall_table('Learning-curve recall',[(name+' / '+size,curve[name]) for size,curve in c['learning_curves'].items() for name in ('M1','M3')])
    lines += ['', '## Part D: search test','',f"Selected **{c['winner']}** by held-out top-100 recall at K=5%. Scored 1,000,000 fresh ordered covered squads, excluding all evaluated tuples and exact duplicates.",
        f"Scoring only: {d['score_seconds_per_million']:.3f} s/million; generation + coverage + duplicate checks + scoring + top-300 heap: {d['generation_and_scoring_seconds']:.3f} s.",
        f"Top-300 native outcomes: {d['counts']}", '', '| Detailed damage statistic | Search native successes | Random 12,000 + S1 B/C native successes |','|---|---:|---:|']
    for k in ('n','max','top10_mean','median','p99','p90'):lines.append(f"| {k} | {d['search'][k]:,.3f} | {d['random'][k]:,.3f} |")
    lines += ['',f"Search squads beating random dataset best / 99th / 90th percentile: **{d['beat_random']['max']} / {d['beat_random']['p99']} / {d['beat_random']['p90']}**. Percentiles use nearest rank; strict greater-than comparisons.",
        f"Top-end Spearman on {d['metrics']['n']} successful selected squads: **{d['metrics']['spearman']:.6f}** (Kendall {d['metrics']['kendall_tau_b']:.6f}).",'',
        f"Linear extrapolation from scoring-only time to 2.9 billion sets: {d['extrapolated_seconds_2_9e9']/3600:.3f} hours; exact C(206,5)={d['exact_unordered_sets']:,}: {d['extrapolated_seconds_exact']/3600:.3f} hours. This excludes enumeration, constraints, top-K retention and native evaluation. Ordered priority variants multiply the work; an unordered set has up to 120 orders. This is a time projection, not a run.",
        'For additive M1, remaining-character weight maxima give admissible branch-and-bound bounds; M2 also needs bounds over possible stage ranks: each remaining character can use its membership weight plus its largest feasible rank weight as an upper bound. For a fixed membership set, maximizing the model over within-stage orders is a small assignment problem in each stage group. '
        'For M3, precompute pairwise dot products and use remaining bias maxima plus upper bounds on chosen-to-remaining and remaining-to-remaining pair contributions. '
        'M4 admits interval bounds on aggregate attributes and their products. Such bounds can be loose; no pruning performance or global optimum is established here.', '',
        '## Reproduction, commands and wall times','',
        'Run from this worktree with Python 3.12; no packages are installed. `models` retrains and recomputes Part C from saved JSONL without native evaluation. '
        '`search-stats` recomputes Part D statistics from saved search JSONL without evaluation (original timing metadata comes from scratch or the saved summary). `report` assembles the saved results. '
        'Timing fields naturally differ on recomputation; predictions, selections, split IDs and numerical metrics are deterministic.', '', '```sh',
        'python3.12 research/team-search/measure_s9.py --help',
        'python3.12 research/team-search/measure_s9.py dataset',
        'python3.12 research/team-search/measure_s9.py models',
        'python3.12 research/team-search/measure_s9.py search',
        'python3.12 research/team-search/measure_s9.py search-stats',
        'python3.12 research/team-search/measure_s9.py report', '```', '',
        f"Part B summed batch wall: {sum(r['batch_elapsed_seconds'] for r in rows)/32:.3f} s (all batches have 32 rows). Part C total wall: {c['wall_seconds']:.3f} s. Per-model wall above includes selection and final refit; learning-curve timings are in summary JSON.",
        'Exact session commands and measured command wall times are recorded in `$S/s9/commands.jsonl`.', '',
        '## Open issues','',
        'Single profile/scenario, unverified native rankings, finite random sample and native failure exclusions limit generalization. '
        'Holdout is smaller than 2,000 because failed native rows cannot be ranked. No uncertainty intervals or cross-scenario tests were requested. '
        'Search-model selection consumes the holdout; S1 external is untouched by selection. '
        'High average correlation does not establish safe pruning; use the measured top-tail recall and independent top-300 detailed test. '
        'Models M1–M3 use identities and cannot extrapolate to unseen characters; M4 can use supplied known-schema attributes, but no leave-character-out experiment was run. '
        'This S9 run made no product changes, CPU reference runs, GPU work, installs, commit or push. Unrelated edits appeared elsewhere in the worktree during collection and were left untouched.']
    recall=c['scores'][c['winner']]['holdout']['recall']['100']['0.05']
    lines += ['', '## Assessment', '',
        f"The selected model retains {recall:.1%} of the held-out detailed top-100 in a 5% shortlist. "
        + ('This meets a 99% recall threshold on this holdout, but requires independent confirmation.' if recall>=.99 else
           'This does not meet the design memo’s 99% recall goal for safe aggressive pruning.'),
        f"The guided search maximum is {d['search']['max']/d['random']['max']-1:+.1%} relative to the best random-data squad. "
        'This measures candidate discovery in this scenario; it does not establish global coverage or optimality.',
        f"At K=20%, M2 retains {c['scores']['M2']['holdout']['recall']['100']['0.2']:.1%} of the held-out top-100 and {c['scores']['M2']['S1-external']['recall']['100']['0.2']:.1%} externally. A wider shortlist is promising, but held-out recall still falls short of 99%."]
    lines += ['', '### Actual recorded commands', '', '| Command | Wall seconds |', '|---|---:|']
    for command in read(SCRATCH/'commands.jsonl'):
        lines.append(f"| `{shlex.join(command['command'])}` | {command['wall_seconds']:.3f} |")
    lines += ['', 'The initial dataset command wall is approximated from log creation to final batch write; all CLI command walls use perf_counter. The separate analytical/pilot checks did not contribute training data.']
    (HERE/'s9-report.md').write_text('\n'.join(lines)+'\n')


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('part',choices=['dataset','models','search','search-stats','report','all'],help='Separate resumable evaluation and saved-data statistics')
    args=parser.parse_args();SCRATCH.mkdir(parents=True,exist_ok=True);t=time.perf_counter()
    actions={'dataset':dataset,'models':models,'search':search,'search-stats':search_statistics,'report':report}
    for name in (actions if args.part=='all' else [args.part]):actions[name]()
    with (SCRATCH/'commands.jsonl').open('a') as f:f.write(json.dumps(dict(command=[sys.executable,*sys.argv],wall_seconds=time.perf_counter()-t))+'\n')


if __name__=='__main__':main()
