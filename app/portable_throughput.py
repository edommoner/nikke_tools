"""CPU transport budgets; no numerical or verification policy."""
def split_threads(counts,cpus):
    if not counts:return []
    # If groups outnumber CPUs the pool queues groups; each owns one thread.
    cpus=max(1,cpus)
    if len(counts)>=cpus:return [1]*len(counts)
    budgets=[1]*len(counts)
    for _ in range(cpus-len(counts)):
        i=max(range(len(counts)),key=lambda i:counts[i]/budgets[i])
        budgets[i]+=1
    return budgets
