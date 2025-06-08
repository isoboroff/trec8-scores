#!/usr/bin/env python3

from pathlib import Path
import collections

root = Path('/Users/soboroff/trec/trec8-scores')
pool_runs_desc = root / 'runs-list'
full_qrels = root / 'trec8.qrels'

runs_table = root / 'runs_table.adhoc'

topics = [str(x) for x in range(401, 451)]
depth = 100

pool_runs = {}
groups = set()
group_runs = collections.defaultdict(set)
run_group = {}
qrel = collections.defaultdict(dict)

with open(runs_table, 'r') as runs_table_fp:
    for line in runs_table_fp:
        (run, pid, _, track, _, _, task) = line.strip().split(':', maxsplit=6)
        if track != 'adhoc':
            continue
        groups.add(pid)
        group_runs[pid].add(run)
        run_group[run] = pid

with open(full_qrels, 'r') as qrels_fp:
    for line in qrels_fp:
        (topic, _, docid, rel) = line.strip().split()
        qrel[topic][docid] = int(rel)

with open(pool_runs_desc, 'r') as pool_runs_desc_fp:
    pool_runs = {line.strip(): 100 for line in pool_runs_desc_fp}
    
for topic in topics:
    for run in pool_runs:
        sims = {}
        with open(root / 'results' / run / f't{topic}', 'r') as tfile:
            for line in tfile:
                (top, _, docid, rank, sim, _) = line.strip().split()
                sims[docid] = float(sim)
        docs_in_order = sorted(sims.keys(), key=lambda x: -sims[x])[:pool_runs[run]]
        for i, d in enumerate(docs_in_order):
            print(topic, d, run, run_group[run], i+1, sims[d], qrel[topic].get(d, -1))
