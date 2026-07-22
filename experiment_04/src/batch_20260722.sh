#!/bin/bash
cd "$(dirname "$0")"
python3 run_llm.py --models qwen3-235b --formulations r4 --workers 5 &
P1=$!
python3 run_llm.py --models gpt5-mini --formulations r4 --workers 5 &
P2=$!
python3 run_llm.py --models frontier --formulations r4 --eval ../data/eval_problem.jsonl --runs 1 --workers 4 --out-dir ../results/probe_frontier_off &
P3=$!
python3 run_llm.py --models qwen-72b --formulations r4 --eval ../../experiment_02/data/eval/eval_640.jsonl --workers 4 --out-dir ../results/runs_kuk640 &
P4=$!
wait $P1 $P2 $P3 $P4
# straggler sweeps
python3 run_llm.py --models qwen3-235b --formulations r4 --workers 2
python3 run_llm.py --models gpt5-mini --formulations r4 --workers 2
python3 run_llm.py --models qwen-72b --formulations r4 --eval ../../experiment_02/data/eval/eval_640.jsonl --workers 2 --out-dir ../results/runs_kuk640
echo BATCH-COMPLETE
