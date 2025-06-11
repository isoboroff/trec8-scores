#!/usr/bin/env python3

import collections
import argparse

ap = argparse.ArgumentParser(
    description='Create a depth-k qrels from the annots2 file',
    formatter_class=argparse.ArgumentDefaultsHelpFormatter
)
ap.add_argument('-k', '--depth',
                help='Depth (1-based)',
                type=int,
                default=10)
ap.add_argument('-l', '--rel_level',
                help='Minimum relevance level',
                default='1')
ap.add_argument('--runs_list',
                help='List of runs allowed (None=all)',
                default=None)
ap.add_argument('--pid_list',
                help='List of pids allowed (None=all)',
                default=None)
ap.add_argument('pool',
                help='Annotated pool file',
                default='annots2')
args = ap.parse_args()

def infinite_defaultdict():
    return collections.defaultdict(infinite_defaultdict)

ok_runs = set()
if args.runs_list:
    with open(args.runs_list, 'r') as fp:
        for line in fp:
            ok_runs.add(line.strip())

ok_pids = set()
if args.pid_list:
    with open(args.pid_list, 'r') as fp:
        for line in fp:
            ok_pids.add(line.strip())
 
qrels = infinite_defaultdict()

with open(args.pool, 'r') as fp:
    for line in fp:
        topic, docid, run, pid, rank, sim, rel = line.strip().split()
        if args.runs_list and not run in ok_runs:
            continue
        if args.pid_list and not pid in ok_pids:
            continue
        if int(rank) > args.depth:
            continue
        qrels[topic][docid] = rel

for topic in sorted(qrels.keys()):
    for docid in sorted(qrels[topic].keys()):
        print(topic, 0, docid, qrels[topic][docid])
