"""Prompting harness — run the 3 regimes × N models × R runs over the eval set.

Design decisions (docs/IMPLEMENTATION.md §8):
  * ONE sentence per call, never batched.
  * Full-trace persistence: one append-only JSONL record per generation, exact
    request + unedited response_raw (incl. usage.cost), raw kept apart from parsed.
  * cell_id keyed → resumable (completed cells are skipped on re-run).
  * provider + quantization pinned per model; usage:{include:true} for real cost.

Modes:
  --dry-run     assemble + print prompts, count calls, DO NOT hit the API
  --limit N     only the first N eval sentences (smoke testing)
  --models a,b  only these model_ids;  --regimes raw_text,...  only these regimes

Usage:
  python src/run_llm.py --config experiment_01/config/experiment.json \
    --eval experiment_01/data/processed/eval_set.jsonl \
    --prompts-dir experiment_01/src/prompts \
    --kuk-root experiment_01/data/raw/KUK_1.0/KUK_1.0/data \
    --out-dir experiment_01/results/runs [--dry-run] [--limit 1]
"""

from __future__ import annotations

import argparse
import glob
import json
import os
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone

import requests

from llm_io import build_messages, conllu_block, load_env, parse_completion

REGIMES = {
    "raw_text": "raw_text.txt",
    "raw_to_conllu": "raw_to_conllu.txt",
    "conllu_input": "conllu_input.txt",
}


def build_request_body(model: dict, messages: list[dict], cfg: dict) -> dict:
    body = {
        "model": model["slug"],
        "messages": messages,
        "temperature": cfg["temperature"],
        "max_tokens": cfg["max_tokens"],
        "usage": {"include": True},
    }
    prov = {}
    if model.get("provider"):
        order = model["provider"] if isinstance(model["provider"], list) else [model["provider"]]
        prov["order"] = order
        prov["allow_fallbacks"] = False
    if model.get("quantization"):
        q = model["quantization"]
        prov["quantizations"] = q if isinstance(q, list) else [q]
    if prov:
        body["provider"] = prov
    return body


def messages_for(regime: str, prompts_dir: str, rec: dict, kuk_root: str) -> tuple[list, str]:
    tmpl = os.path.join(prompts_dir, REGIMES[regime])
    if regime == "conllu_input":
        block = conllu_block(kuk_root, rec["source_file"], rec["sent_id"])
        return build_messages(tmpl, conllu=block)
    return build_messages(tmpl, sentence=rec["text"])


def call_with_retry(session, endpoint, headers, body, cfg) -> dict:
    last_err = None
    for attempt in range(cfg["max_retries"]):
        try:
            resp = session.post(endpoint, headers=headers, json=body, timeout=120)
            if resp.status_code == 200:
                return {"ok": True, "json": resp.json()}
            if resp.status_code in (429,) or resp.status_code >= 500:
                last_err = f"HTTP {resp.status_code}: {resp.text[:200]}"
                time.sleep(cfg["retry_base_seconds"] * (2 ** attempt))
                continue
            return {"ok": False, "error": f"HTTP {resp.status_code}: {resp.text[:300]}"}
        except requests.RequestException as e:
            last_err = str(e)
            time.sleep(cfg["retry_base_seconds"] * (2 ** attempt))
    return {"ok": False, "error": f"exhausted retries: {last_err}"}


def load_done_cells(path: str) -> set[str]:
    done = set()
    if os.path.exists(path):
        for line in open(path, encoding="utf-8"):
            try:
                done.add(json.loads(line)["cell_id"])
            except (json.JSONDecodeError, KeyError):
                continue
    return done


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--config", required=True)
    ap.add_argument("--eval", required=True)
    ap.add_argument("--prompts-dir", required=True)
    ap.add_argument("--kuk-root", required=True)
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--env", default=".env")
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--models", default=None, help="comma-separated model_ids to include")
    ap.add_argument("--regimes", default=None, help="comma-separated regimes to include")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    cfg = json.load(open(args.config, encoding="utf-8"))
    recs = [json.loads(l) for l in open(args.eval, encoding="utf-8")]
    if args.limit:
        recs = recs[: args.limit]

    models = cfg["models"]
    if args.models:
        keep = set(args.models.split(","))
        models = [m for m in models if m["model_id"] in keep]
    regimes = list(REGIMES)
    if args.regimes:
        regimes = [r for r in args.regimes.split(",") if r in REGIMES]

    os.makedirs(args.out_dir, exist_ok=True)

    # ---- dry run: show exact prompts, count calls, no API ----
    if args.dry_run:
        print(f"DRY RUN — {len(recs)} sentences × {len(regimes)} regimes × "
              f"{len(models)} models × {cfg['n_runs']} runs "
              f"= {len(recs)*len(regimes)*len(models)*cfg['n_runs']:,} calls\n")
        for regime in regimes:
            msgs, sha = messages_for(regime, args.prompts_dir, recs[0], args.kuk_root)
            print(f"===== regime={regime}  template_sha={sha} =====")
            for m in msgs:
                print(f"[{m['role']}]\n{m['content']}\n")
            print()
        print("Models:", [m["model_id"] + " -> " + m["slug"] for m in models])
        return

    # ---- live run ----
    env = load_env(args.env)
    endpoint = env.get("OPENROUTER_UFAL_ENDPOINT")
    apikey = env.get("OPENROUTER_UFAL_APIKEY")
    if not endpoint or not apikey:
        raise SystemExit("Missing OPENROUTER_UFAL_ENDPOINT / OPENROUTER_UFAL_APIKEY in .env")
    headers = {"Authorization": f"Bearer {apikey}", "Content-Type": "application/json",
               "HTTP-Referer": "https://ufal.mff.cuni.cz", "X-Title": "can-llms-count"}

    for model in models:
        out_path = os.path.join(args.out_dir, f"{model['model_id']}.jsonl")
        fail_path = os.path.join(args.out_dir, f"{model['model_id']}.failures.jsonl")
        done = load_done_cells(out_path)

        tasks = []
        for rec in recs:
            # sent_id resets per CoNLL-U file, so it is NOT unique across the eval
            # set — the uid must include source_file or cells collide.
            uid = f"{rec['source_file']}::{rec['sent_id']}"
            for regime in regimes:
                for run_i in range(1, cfg["n_runs"] + 1):
                    cell_id = f"{uid}|{regime}|{model['model_id']}|{run_i}"
                    if cell_id in done:
                        continue
                    tasks.append((cell_id, uid, rec, regime, run_i))

        print(f"[{model['model_id']}] {len(tasks)} calls to make "
              f"({len(done)} already done)")
        if not tasks:
            continue

        session = requests.Session()

        def do(task):
            cell_id, uid, rec, regime, run_i = task
            messages, sha = messages_for(regime, args.prompts_dir, rec, args.kuk_root)
            body = build_request_body(model, messages, cfg)
            res = call_with_retry(session, endpoint, headers, body, cfg)
            base = {
                "cell_id": cell_id, "uid": uid, "sent_id": rec["sent_id"],
                "source_file": rec["source_file"], "subcorpus": rec["subcorpus"],
                "regime": regime, "model_id": model["model_id"], "slug": model["slug"],
                "run_index": run_i, "timestamp": datetime.now(timezone.utc).isoformat(),
                "prompt_template_sha": sha,
                "request": {"messages": messages, "params": {k: body[k] for k in body if k != "messages"}},
            }
            if not res["ok"]:
                base["error"] = res["error"]
                return base, False
            raw = res["json"]
            text = (raw.get("choices") or [{}])[0].get("message", {}).get("content")
            base["response_raw"] = raw
            base["completion_text"] = text
            base["parsed"] = parse_completion(text)
            return base, True

        n_ok = n_fail = 0
        with ThreadPoolExecutor(max_workers=cfg["workers"]) as ex, \
                open(out_path, "a", encoding="utf-8") as ok_f, \
                open(fail_path, "a", encoding="utf-8") as fail_f:
            futures = [ex.submit(do, t) for t in tasks]
            for i, fut in enumerate(as_completed(futures), 1):
                rec_out, ok = fut.result()
                if ok:
                    ok_f.write(json.dumps(rec_out, ensure_ascii=False) + "\n")
                    ok_f.flush()
                    n_ok += 1
                else:
                    fail_f.write(json.dumps(rec_out, ensure_ascii=False) + "\n")
                    fail_f.flush()
                    n_fail += 1
                if i % 200 == 0:
                    print(f"  [{model['model_id']}] {i}/{len(tasks)}  ok={n_ok} fail={n_fail}")
        print(f"[{model['model_id']}] done: ok={n_ok} fail={n_fail} "
              f"(failures -> {fail_path})")


if __name__ == "__main__":
    main()
