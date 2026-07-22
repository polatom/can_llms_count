"""LLM-arm harness (METHODOLOGY §5.2, §6): formulations × models × passes over CLTT.

Ported from experiment_01/src/run_llm.py. Exp_04 specifics:
  * eval items = CLTT gold sentence units (data/eval_units.jsonl: uid, text);
  * formulations r1/r2 (config map -> src/prompts/*.txt), {SENTENCE} substitution;
  * ANTI-CACHING protocol (§6): runs are executed as SEQUENTIAL FULL PASSES
    (pass 1 over all items completes before pass 2 starts), item order SHUFFLED
    per pass (seed = pass index), latency + provider/generation metadata logged;
  * per-model `reasoning` config passthrough (OpenRouter `reasoning` body param);
  * one sentence per call; append-only full traces; cell_id-resumable;
    provider + quantization pinned, allow_fallbacks=false, usage.cost captured.

Usage:
  python3 run_llm.py [--dry-run] [--limit N] [--models a,b] [--formulations r1,r2]
                     [--runs N] [--out-dir ../results/runs]
"""

from __future__ import annotations

import argparse
import json
import os
import random
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone

import requests

from llm_io import build_messages, load_env, parse_completion

BASE = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
PROMPTS_DIR = os.path.join(BASE, "src", "prompts")


def build_request_body(model: dict, messages: list[dict], cfg: dict) -> dict:
    body = {
        "model": model["slug"],
        "messages": messages,
        "temperature": cfg["temperature"],
        # reasoning models need far larger budgets (probe v1 lesson: 76/104
        # truncated at 6k with reasoning consuming ~5.4k) -> per-model override
        "max_tokens": model.get("max_tokens", cfg["max_tokens"]),
        "usage": {"include": True},
    }
    if model.get("reasoning") is not None:
        body["reasoning"] = model["reasoning"]
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


def call_with_retry(session, endpoint, headers, body, cfg) -> dict:
    last_err = None
    for attempt in range(cfg["max_retries"]):
        try:
            t0 = time.monotonic()
            resp = session.post(endpoint, headers=headers, json=body, timeout=300)
            latency = time.monotonic() - t0
            if resp.status_code == 200:
                return {"ok": True, "json": resp.json(), "latency_s": round(latency, 3)}
            if resp.status_code == 429 or resp.status_code >= 500:
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
    ap.add_argument("--config", default=os.path.join(BASE, "config", "experiment.json"))
    ap.add_argument("--eval", default=os.path.join(BASE, "data", "eval_units.jsonl"))
    ap.add_argument("--out-dir", default=os.path.join(BASE, "results", "runs"))
    ap.add_argument("--env", default=os.path.join(BASE, "..", ".env"))
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--models", default=None)
    ap.add_argument("--formulations", default=None)
    ap.add_argument("--runs", type=int, default=None)
    ap.add_argument("--workers", type=int, default=None,
                    help="override config workers (e.g. lower after 429s)")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    cfg = json.load(open(args.config, encoding="utf-8"))
    if args.workers:
        cfg["workers"] = args.workers
    recs = [json.loads(l) for l in open(args.eval, encoding="utf-8")]
    if args.limit:
        recs = recs[: args.limit]

    models = [m for m in cfg["models"] if m.get("enabled", True)]
    if args.models:
        keep = set(args.models.split(","))
        models = [m for m in cfg["models"] if m["model_id"] in keep]
    forms = dict(cfg["formulations"])
    if args.formulations:
        keep = set(args.formulations.split(","))
        forms = {k: v for k, v in forms.items() if k in keep}
    n_runs = args.runs or cfg["n_runs"]

    total = len(recs) * len(forms) * len(models) * n_runs
    if args.dry_run:
        print(f"DRY RUN — {len(recs)} units × {len(forms)} formulations × "
              f"{len(models)} models × {n_runs} runs = {total:,} calls\n")
        for fk, fv in forms.items():
            msgs, sha = build_messages(os.path.join(PROMPTS_DIR, fv), recs[0]["text"])
            print(f"===== formulation={fk} ({fv})  sha={sha} =====")
            for m in msgs:
                print(f"[{m['role']}] {len(m['content'])} chars")
            print(msgs[-1]["content"][-400:], "\n")
        print("Models:", [(m["model_id"], m["slug"], m.get("provider")) for m in models])
        return

    env = load_env(args.env)
    endpoint = env.get("OPENROUTER_UFAL_ENDPOINT")
    apikey = env.get("OPENROUTER_UFAL_APIKEY")
    if not endpoint or not apikey:
        raise SystemExit("Missing OPENROUTER_UFAL_ENDPOINT / OPENROUTER_UFAL_APIKEY in .env")
    headers = {"Authorization": f"Bearer {apikey}", "Content-Type": "application/json",
               "HTTP-Referer": "https://ufal.mff.cuni.cz", "X-Title": "can-llms-count-e04"}

    os.makedirs(args.out_dir, exist_ok=True)

    for model in models:
        out_path = os.path.join(args.out_dir, f"{model['model_id']}.jsonl")
        fail_path = os.path.join(args.out_dir, f"{model['model_id']}.failures.jsonl")
        done = load_done_cells(out_path)
        session = requests.Session()

        def do(task):
            cell_id, rec, fk, run_i = task
            messages, sha = build_messages(os.path.join(PROMPTS_DIR, forms[fk]), rec["text"])
            body = build_request_body(model, messages, cfg)
            res = call_with_retry(session, endpoint, headers, body, cfg)
            base = {
                "cell_id": cell_id, "uid": rec["uid"], "formulation": fk,
                "model_id": model["model_id"], "slug": model["slug"],
                "run_index": run_i,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "prompt_template_sha": sha,
                "request_params": {k: v for k, v in build_request_body(
                    model, [], cfg).items() if k != "messages"},
            }
            if not res["ok"]:
                base["error"] = res["error"]
                return base, False
            raw = res["json"]
            text = (raw.get("choices") or [{}])[0].get("message", {}).get("content")
            base.update({
                "latency_s": res["latency_s"],
                "response_raw": raw,
                "completion_text": text,
                "parsed": parse_completion(text),
            })
            return base, True

        # §6 anti-caching: sequential full passes, order shuffled per pass
        for run_i in range(1, n_runs + 1):
            tasks = []
            for rec in recs:
                for fk in forms:
                    cell_id = f"{rec['uid']}|{fk}|{model['model_id']}|{run_i}"
                    if cell_id not in done:
                        tasks.append((cell_id, rec, fk, run_i))
            if not tasks:
                print(f"[{model['model_id']}] pass {run_i}: complete, skipping")
                continue
            random.Random(run_i).shuffle(tasks)
            print(f"[{model['model_id']}] pass {run_i}: {len(tasks)} calls", flush=True)
            n_ok = n_fail = 0
            with ThreadPoolExecutor(max_workers=cfg["workers"]) as ex, \
                    open(out_path, "a", encoding="utf-8") as ok_f, \
                    open(fail_path, "a", encoding="utf-8") as fail_f:
                futures = [ex.submit(do, t) for t in tasks]
                for i, fut in enumerate(as_completed(futures), 1):
                    rec_out, ok = fut.result()
                    (ok_f if ok else fail_f).write(
                        json.dumps(rec_out, ensure_ascii=False) + "\n")
                    (ok_f if ok else fail_f).flush()
                    n_ok += ok
                    n_fail += (not ok)
                    if i % 250 == 0:
                        print(f"  [{model['model_id']}|p{run_i}] {i}/{len(tasks)} "
                              f"ok={n_ok} fail={n_fail}", flush=True)
            print(f"[{model['model_id']}] pass {run_i} done: ok={n_ok} fail={n_fail}",
                  flush=True)


if __name__ == "__main__":
    main()
