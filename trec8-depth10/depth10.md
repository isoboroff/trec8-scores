# TREC-8 runs, depth-10 reduced-run eval

## Details
collection: TREC-8
pool-runs: all
eval-runs: all

Pool/qrels is depth 10 from all runs.

Eval scores are from trec_eval -J, reduced runs

## commands

### Pooling
```shell
./depth-k-qrels.py annots2 > depth10.qrels
```

### Scoring
```shell
cat all-runs | while read runtag; 
do
    ./trec_eval/trec_eval -J -q -m all_trec depth10.qrels inputs/input.$runtag | \
    sed "s/^/$runtag /"
done > depth10.eval

cat depth10.eval | \
    awk '$2 == "map" && $3 == "all" {print $1, $4}' | \
    sort -k2,2gr > depth10.map
```

### Analysis
```shell
./testcoll-tools/tools/tau.pl official-scores.map depth10.map > depth10.tau
```

Tau: 0.92
