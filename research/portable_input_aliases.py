"""Share one GPU input while preserving every independent native comparison."""
import array,hashlib


def group_entries(entries):
    rows=[];groups={}
    for name,words,domain in entries:
        if domain is None:
            rows.append((name,words,None));continue
        key=hashlib.sha256(array.array('I',words).tobytes()).digest()
        if key not in groups:
            groups[key]=len(rows);rows.append((name,words,(*domain,(domain,))))
        else:
            index=groups[key];prior,packed,combined=rows[index]
            if words!=packed:raise ValueError('Input digest collision')
            rows[index]=(prior,packed,(*combined[:3],(*combined[3],domain)))
    return rows


def domains(group):return group[3]


def compare_aliases(group,compare):
    answers=[compare(domain) for domain in domains(group)]
    if any(answer!=answers[0] for answer in answers[1:]):
        raise ValueError('Same GPU input has different native alias results')
    return answers[0]
