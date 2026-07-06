"""Estimate the token volume and USD cost of the full LLM run.

Grounded in the *actual* eval set: measures the real prompt overhead (system +
few-shot from src/prompts/), the real sentence texts, and the real CoNLL-U
blocks (fetched from the corpus) that regime 3 feeds in / regime 2 emits.

chars -> tokens via a configurable ratio (Czech + CoNLL-U is subword-heavy, so
we default to 3.5 chars/token and also report a 3.0 / 4.0 sensitivity band).
Prices are ILLUSTRATIVE OpenRouter placeholders — verify per chosen model slug.

Usage:
    python src/estimate_cost.py \
        --eval    experiment_01/data/processed/eval_set.jsonl \
        --prompts experiment_01/src/prompts \
        --kuk-root experiment_01/data/raw/KUK_1.0/KUK_1.0/data \
        --out     experiment_01/results/cost_estimate.json
Stdlib only.
"""

from __future__ import annotations

import argparse
import json
import math
import os
from functools import lru_cache

N_RUNS = 3  # repeated generations per (sentence, regime, model) at temp 0

# Illustrative OpenRouter prices, USD per 1M tokens (input, output). VERIFY.
MODELS = [
    {"id": "small-1 (~8B open)", "size": "small", "in": 0.02, "out": 0.03},
    {"id": "small-2 (~7-12B open)", "size": "small", "in": 0.05, "out": 0.10},
    {"id": "large-1 (~70B open)", "size": "large", "in": 0.12, "out": 0.30},
    {"id": "large-2 (frontier)", "size": "large", "in": 2.50, "out": 10.00},
]


def prompt_overhead_chars(prompts_dir: str, name: str) -> int:
    """Chars of the fixed SYSTEM + FEWSHOT part (everything before ### USER)."""
    text = open(os.path.join(prompts_dir, name), encoding="utf-8").read()
    head = text.split("### USER")[0]
    return len(head)


@lru_cache(maxsize=None)
def _file_blocks(path: str) -> dict:
    """Map sent_id -> raw CoNLL-U block (comments + token lines) for one file."""
    blocks: dict[str, str] = {}
    sid, buf = None, []
    for line in open(path, encoding="utf-8", errors="replace"):
        if line.strip() == "":
            if sid is not None:
                blocks[sid] = "".join(buf)
            sid, buf = None, []
            continue
        if line.startswith("# sent_id"):
            sid = line.split("=", 1)[1].strip()
        buf.append(line)
    if sid is not None:
        blocks[sid] = "".join(buf)
    return blocks


def conllu_block(kuk_root: str, source_file: str, sent_id: str) -> str:
    return _file_blocks(os.path.join(kuk_root, source_file)).get(sent_id, "")


def answer_json_chars(r: dict) -> int:
    """Chars of the JSON answer, using the real subject/predicate forms."""
    obj = {
        "podmet": r["subj_form"],
        "podmet_index": r["subj_word"] + 1,
        "prisudek": r["pred_form"],
        "prisudek_index": r["pred_word"] + 1,
        "vzdalenost": r["distance"],
    }
    return len(json.dumps(obj, ensure_ascii=False))


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--eval", required=True)
    ap.add_argument("--prompts", required=True)
    ap.add_argument("--kuk-root", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--cpt", type=float, default=3.5, help="chars per token (central)")
    args = ap.parse_args()

    recs = [json.loads(l) for l in open(args.eval, encoding="utf-8")]
    ov = {
        "raw_text": prompt_overhead_chars(args.prompts, "raw_text.txt"),
        "raw_to_conllu": prompt_overhead_chars(args.prompts, "raw_to_conllu.txt"),
        "conllu_input": prompt_overhead_chars(args.prompts, "conllu_input.txt"),
    }

    # Per-regime char totals across the whole eval set (one generation each).
    in_chars = {"raw_text": 0, "raw_to_conllu": 0, "conllu_input": 0}
    out_chars = {"raw_text": 0, "raw_to_conllu": 0, "conllu_input": 0}

    for r in recs:
        sent = r["text"]
        ans = answer_json_chars(r)
        block = conllu_block(args.kuk_root, r["source_file"], r["sent_id"])

        # regime 1: raw text in, JSON out
        in_chars["raw_text"] += ov["raw_text"] + len("Věta: ") + len(sent)
        out_chars["raw_text"] += ans

        # regime 2: raw text in; out = generated CoNLL-U (~5-col, ~22 ch/token) + JSON
        in_chars["raw_to_conllu"] += ov["raw_to_conllu"] + len("Věta: ") + len(sent)
        out_chars["raw_to_conllu"] += r["n_ud_tokens"] * 22 + len("<conllu>\n</conllu>\n") + ans

        # regime 3: full real CoNLL-U block in, JSON out
        in_chars["conllu_input"] += ov["conllu_input"] + len(block)
        out_chars["conllu_input"] += ans

    def toks(chars: float, cpt: float) -> int:
        return math.ceil(chars / cpt)

    def totals(cpt: float) -> dict:
        tin = sum(toks(in_chars[k], cpt) for k in in_chars) * N_RUNS
        tout = sum(toks(out_chars[k], cpt) for k in out_chars) * N_RUNS
        return {"in": tin, "out": tout}

    central = totals(args.cpt)
    band = {"cpt_3.0": totals(3.0), "cpt_3.5": totals(3.5), "cpt_4.0": totals(4.0)}

    # cost per model (each model runs the SAME per-model token load)
    per_model = []
    total_cost = 0.0
    for m in MODELS:
        cost = central["in"] / 1e6 * m["in"] + central["out"] / 1e6 * m["out"]
        per_model.append({**m, "cost_usd": round(cost, 2)})
        total_cost += cost

    result = {
        "n_sentences": len(recs),
        "n_runs": N_RUNS,
        "n_models": len(MODELS),
        "generations": len(recs) * 3 * len(MODELS) * N_RUNS,
        "cpt_central": args.cpt,
        "prompt_overhead_chars": ov,
        "per_regime_input_chars": in_chars,
        "per_regime_output_chars": out_chars,
        "per_model_token_load_central": central,
        "token_band_over_all_models": {
            k: {"in": v["in"] * len(MODELS), "out": v["out"] * len(MODELS)}
            for k, v in band.items()
        },
        "per_model_cost_usd": per_model,
        "total_cost_usd_central": round(total_cost, 2),
    }

    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as fh:
        json.dump(result, fh, ensure_ascii=False, indent=2)

    # ---- console report ----
    print(f"Eval sentences: {len(recs)}   generations: {result['generations']:,} "
          f"(= {len(recs)} × 3 regimes × {len(MODELS)} models × {N_RUNS} runs)")
    print(f"\nPrompt fixed overhead (chars): {ov}")
    print(f"\nPer-model token load (central cpt={args.cpt}): "
          f"in {central['in']:,}  out {central['out']:,}  "
          f"total {central['in']+central['out']:,}")
    print("Token band across ALL 4 models:")
    for k, v in band.items():
        allin, allout = v["in"] * len(MODELS), v["out"] * len(MODELS)
        print(f"  {k}: in {allin:,}  out {allout:,}  total {allin+allout:,}")
    print("\nPer-model cost (central):")
    for m in per_model:
        print(f"  {m['id']:24s} in ${m['in']:.2f}/M out ${m['out']:.2f}/M  ->  ${m['cost_usd']:,.2f}")
    print(f"\nTOTAL (central, all 4 models, {N_RUNS} runs): ${result['total_cost_usd_central']:,.2f}")
    print(f"\nWrote {args.out}")


if __name__ == "__main__":
    main()
