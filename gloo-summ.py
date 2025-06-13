#!/usr/bin/env python3

import argparse
from pathlib import Path

ap = argparse.ArgumentParser(
    description='Analyze the results from a GLOO experiment',
    formatter_class=argparse.ArgumentDefaultsHelpFormatter,
)
ap.add_argument('--loo_pattern',
                help='Template for GLOO eval files',
                default='eval.RUNTAG')
ap.add_argument('--loo_path',
                help='Path to GLOO eval files',
                type=Path,
                default='.')
ap.add_argument('--official_pattern',
                help='Template for official eval files',
                default='summary.RUNTAG')
ap.add_argument('--official_path',
                help='Path to official eval files',
                type=Path,
                default='.')
ap.add_argument('annotated_qrels',
                help='Annnotated qrels file, giving runs and pids')
args = ap.parse_args()

runs_by_pid = {}
with open(args.annotated_qrels, 'r') as fp:
    for line in fp:
        _, _, pid, runtag, _, _, _ = line.strip().split()