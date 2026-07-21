#!/bin/bash
# R4 grid, resilient sequence (2026-07-21): qwen first (its endpoint healthy),
# gemma delayed (DeepInfra gemma temporarily rate-limited upstream) at low
# concurrency, then a final low-concurrency sweep of any stragglers.
cd "$(dirname "$0")"
python3 run_llm.py --formulations r4 --models qwen-72b --workers 5
sleep 600
python3 run_llm.py --formulations r4 --models gemma-27b --workers 3
python3 run_llm.py --formulations r4 --workers 2
echo "R4 SEQUENCE COMPLETE"
