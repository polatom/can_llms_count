"""Score the harness output against the silver gold and aggregate per condition.

Reads results/runs/*.jsonl (full traces) + the gold eval set, joins on
`uid` (= source_file::sent_id, unique), and computes:

Per generation:
  * format validity (did we get a parseable answer)
  * role identification: subject / predicate word-index match (+ loose form match)
  * distance: signed error, exact / ±1 / ±2, abs error, squared error
Per (model × regime):
  * format-ok rate; exact/±1/±2 rates and MAE/RMSE (among format-ok);
    strict exact rate (malformed = wrong); role accuracies
  * consistency across the 3 runs: zero-variance rate + mean stddev
Regime 2 extra (best-effort, token-granular): recompute distance from the model's
  OWN emitted CoNLL-U to split parse-error from counting-error.

Outputs: results/scored.jsonl, results/metrics_by_condition.csv, console table.
Stdlib only.
"""

from __future__ import annotations

import argparse
import csv
import glob
import json
import math
import os
import re
import statistics
from collections import defaultdict


def to_int(x):
    if isinstance(x, bool):
        return None
    if isinstance(x, int):
        return x
    if isinstance(x, float):
        return int(x) if x == int(x) else None
    if isinstance(x, str):
        m = re.search(r"-?\d+", x)
        return int(m.group()) if m else None
    return None


def norm_form(s) -> str:
    return re.sub(r"[^\w]", "", str(s or "").lower(), flags=re.UNICODE)


# ---- regime-2: recompute distance from the model's own emitted CoNLL-U -------
def distance_from_model_conllu(conllu_text: str):
    """Best-effort token-granular distance between nsubj and its head in the
    model's OWN parse. Returns (token_distance | None, nsubj_found: bool).

    NOTE: token-granular (CoNLL-U rows), not whitespace-words — so it is an
    approximate check of 'counting given own parse', not directly comparable to
    the word-distance gold. Tolerant to 5-col or 10-col output.
    """
    if not conllu_text:
        return None, False
    rows = []
    for line in conllu_text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        cols = line.split("\t") if "\t" in line else line.split()
        if len(cols) < 5:
            continue
        if not re.match(r"^\d+$", cols[0]):
            continue
        rows.append(cols)
    # find nsubj row + its head; find root
    nsubj = None
    for c in rows:
        joined = "\t".join(c).lower()
        if "nsubj" in joined:
            nsubj = c
            break
    if nsubj is None:
        return None, False
    # head is the numeric field that is a valid row id (heuristic: 5-col -> col[3],
    # 10-col -> col[6]); try both.
    head_id = None
    for idx in (6, 3):
        if idx < len(nsubj) and re.match(r"^\d+$", nsubj[idx]):
            head_id = int(nsubj[idx])
            break
    nsubj_id = int(nsubj[0])
    if head_id is None or head_id == 0:
        return None, True
    return abs(nsubj_id - head_id) - 1, True


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--runs-dir", required=True)
    ap.add_argument("--eval", required=True)
    ap.add_argument("--out-dir", required=True)
    args = ap.parse_args()

    gold = {}
    for line in open(args.eval, encoding="utf-8"):
        r = json.loads(line)
        uid = f"{r['source_file']}::{r['sent_id']}"
        gold[uid] = r

    os.makedirs(args.out_dir, exist_ok=True)
    scored_path = os.path.join(args.out_dir, "scored.jsonl")
    scored = []

    files = [f for f in glob.glob(os.path.join(args.runs_dir, "*.jsonl")) if "failures" not in f]
    for f in files:
        for line in open(f, encoding="utf-8"):
            rec = json.loads(line)
            uid = rec.get("uid") or f"{rec['source_file']}::{rec['sent_id']}"
            g = gold.get(uid)
            if g is None:
                continue
            p = rec.get("parsed", {}) or {}
            dist_pred = to_int(p.get("vzdalenost"))
            subj_idx = to_int(p.get("podmet_index"))
            pred_idx = to_int(p.get("prisudek_index"))
            format_ok = p.get("parse_status") == "ok" and dist_pred is not None

            row = {
                "uid": uid, "model_id": rec["model_id"], "regime": rec["regime"],
                "run_index": rec["run_index"], "subcorpus": rec.get("subcorpus"),
                "dist_gold": g["distance"], "dist_pred": dist_pred,
                "n_words": g["n_words"], "gold_distance_bucket": g.get("distance_bucket"),
                "gold_length_bucket": g.get("length_bucket"),
                "format_ok": format_ok,
                "subj_idx_match": (subj_idx == g["subj_word"] + 1) if subj_idx is not None else False,
                "pred_idx_match": (pred_idx == g["pred_word"] + 1) if pred_idx is not None else False,
                "subj_form_match": norm_form(p.get("podmet")) == norm_form(g["subj_form"]),
                "pred_form_match": norm_form(p.get("prisudek")) == norm_form(g["pred_form"]),
            }
            row["both_roles"] = row["subj_idx_match"] and row["pred_idx_match"]
            if format_ok:
                err = dist_pred - g["distance"]
                row.update(signed_err=err, abs_err=abs(err), sq_err=err * err,
                           exact=(err == 0), within1=(abs(err) <= 1), within2=(abs(err) <= 2))
            if rec["regime"] == "raw_to_conllu":
                td, found = distance_from_model_conllu(p.get("conllu_emitted", ""))
                row["r2_nsubj_found"] = found
                row["r2_token_dist"] = td
                if td is not None and dist_pred is not None:
                    row["r2_count_matches_own_parse"] = (td == dist_pred)
            scored.append(row)

    with open(scored_path, "w", encoding="utf-8") as fh:
        for r in scored:
            fh.write(json.dumps(r, ensure_ascii=False) + "\n")

    # ---- aggregate per (model, regime) ----
    groups = defaultdict(list)
    for r in scored:
        groups[(r["model_id"], r["regime"])].append(r)

    def rate(rows, key):
        vals = [r[key] for r in rows if key in r]
        return round(sum(vals) / len(vals), 4) if vals else None

    table = []
    for (model_id, regime), rows in sorted(groups.items()):
        ok = [r for r in rows if r["format_ok"]]
        # consistency: per uid, the runs' predicted distance
        by_uid = defaultdict(list)
        for r in rows:
            if r["format_ok"]:
                by_uid[r["uid"]].append(r["dist_pred"])
        complete = [v for v in by_uid.values() if len(v) >= 2]
        zero_var = sum(1 for v in complete if len(set(v)) == 1)
        stddevs = [statistics.pstdev(v) for v in complete if len(v) >= 2]
        rec = {
            "model_id": model_id, "regime": regime, "n": len(rows),
            "format_ok_rate": rate(rows, "format_ok"),
            "exact_among_ok": rate(ok, "exact"),
            "exact_strict": round(sum(1 for r in rows if r.get("exact")) / len(rows), 4) if rows else None,
            "within1": rate(ok, "within1"),
            "within2": rate(ok, "within2"),
            "mae": round(statistics.mean([r["abs_err"] for r in ok]), 3) if ok else None,
            "rmse": round(math.sqrt(statistics.mean([r["sq_err"] for r in ok])), 3) if ok else None,
            "subj_acc": rate(rows, "subj_idx_match"),
            "pred_acc": rate(rows, "pred_idx_match"),
            "both_roles_acc": rate(rows, "both_roles"),
            "consistency_zero_var_rate": round(zero_var / len(complete), 4) if complete else None,
            "mean_run_stddev": round(statistics.mean(stddevs), 3) if stddevs else None,
        }
        if regime == "raw_to_conllu":
            rec["r2_count_matches_own_parse"] = rate(rows, "r2_count_matches_own_parse")
        table.append(rec)

    cols = ["model_id", "regime", "n", "format_ok_rate", "exact_among_ok", "exact_strict",
            "within1", "within2", "mae", "rmse", "subj_acc", "pred_acc", "both_roles_acc",
            "consistency_zero_var_rate", "mean_run_stddev", "r2_count_matches_own_parse"]
    csv_path = os.path.join(args.out_dir, "metrics_by_condition.csv")
    with open(csv_path, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=cols)
        w.writeheader()
        for r in table:
            w.writerow({c: r.get(c, "") for c in cols})

    # ---- console ----
    print(f"Scored {len(scored):,} generations from {len(files)} model files.\n")
    hdr = f"{'model':10s} {'regime':14s} {'n':>5s} {'fmt%':>6s} {'exact':>6s} {'strict':>7s} " \
          f"{'±1':>6s} {'±2':>6s} {'MAE':>6s} {'both':>6s} {'zeroVar':>8s}"
    print(hdr)
    print("-" * len(hdr))
    for r in table:
        def pct(x): return f"{x*100:.1f}" if isinstance(x, (int, float)) else "-"
        print(f"{r['model_id']:10s} {r['regime']:14s} {r['n']:>5d} "
              f"{pct(r['format_ok_rate']):>6s} {pct(r['exact_among_ok']):>6s} "
              f"{pct(r['exact_strict']):>7s} {pct(r['within1']):>6s} {pct(r['within2']):>6s} "
              f"{str(r['mae']):>6s} {pct(r['both_roles_acc']):>6s} "
              f"{pct(r['consistency_zero_var_rate']):>8s}")
    print(f"\nWrote {scored_path}")
    print(f"Wrote {csv_path}")


if __name__ == "__main__":
    main()
