#!/bin/bash
cd "$(dirname "$0")"
python3 run_llm.py --formulations r4 --models gemma-27b --workers 3
python3 run_llm.py --formulations r5 --models qwen-72b --workers 3
python3 run_llm.py --formulations r4 --models gemma-27b --workers 2
python3 run_llm.py --formulations r5 --models qwen-72b --workers 2
echo ALL-SWEEPS-DONE
