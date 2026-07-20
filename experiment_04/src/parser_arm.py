"""Parser arm (METHODOLOGY §5.1): UDPipe on raw CLTT sentence units, scored vs gold.

For every `cs_cltt` gold sentence unit:
1. parse the RAW TEXT with UDPipe 2 (`czech-pdt-ud-2.15-241121`, the same model
   as the KUK silver) via the LINDAT API — responses cached to
   `data/parser_arm/udpipe_cache.jsonl` (keyed by uid), so reruns are offline;
2. UDPipe may re-segment the unit into several sentences (~60% expected):
   extract pairs from EVERY sub-sentence (§3 rule) and union them, mapping
   word indices onto the WHOLE unit via cumulative offsets. A sub-sentence
   boundary that falls inside a whitespace word (previous unit glued,
   SpaceAfter=No) merges the adjacent word indices. Invariant checked per
   unit: reconstructed word count == len(text.split()); mismatches logged;
3. score against `data/cltt_gold_pairs.jsonl`: verdict confusion (accuracy /
   P / R / F1), pair-level P/R/F1 (index-exact and form-based), distance
   exact/±1/MAE on matched pairs, segmentation stats.

Outputs:
  data/parser_arm/udpipe_cache.jsonl   (raw parses; committed — makes reruns offline)
  data/parser_arm/parser_pairs.jsonl   (extracted pairs + verdict per unit)
  docs/PARSER_ARM_RESULTS.md           (PRELIMINARY until K6-K9 are settled)

Usage: python3 parser_arm.py [--cltt-dir PATH] [--workers 4] [--offline]
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.parse
import urllib.request
from collections import Counter
from concurrent.futures import ThreadPoolExecutor

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from conllu_utils import Sentence, assign_word_indices, iter_conllu  # noqa: E402
from extract_pairs import T_LIMIT, extract  # noqa: E402

UDPIPE_URL = "https://lindat.mff.cuni.cz/services/udpipe/api/process"
UDPIPE_MODEL = "czech-pdt-ud-2.15-241121"

DEFAULT_CLTT = os.path.normpath(os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "data", "raw", "cs_cltt"))
BASE = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))


def udpipe(text: str) -> str:
    data = urllib.parse.urlencode({
        "tokenizer": "", "tagger": "", "parser": "", "model": UDPIPE_MODEL,
        "output": "conllu", "data": text,
    }).encode()
    for attempt in range(5):
        try:
            r = urllib.request.urlopen(UDPIPE_URL, data=data, timeout=120)
            return json.load(r)["result"]
        except Exception:
            if attempt == 4:
                raise
    return ""


def parse_conllu_string(text: str) -> list[Sentence]:
    import tempfile

    with tempfile.NamedTemporaryFile("w", suffix=".conllu", delete=False,
                                     encoding="utf-8") as tf:
        tf.write(text + "\n\n")
        tmp = tf.name
    try:
        return list(iter_conllu(tmp))
    finally:
        os.unlink(tmp)


def _last_unit_glued(sent: Sentence) -> bool:
    """Does the unit's final surface unit carry SpaceAfter=No (glued to what follows)?"""
    if not sent.tokens:
        return False
    last_id = max(t.id for t in sent.tokens)
    for m in sent.mwts:
        if m.start <= last_id <= m.end:
            return "SpaceAfter=No" in (m.misc or "")
    tok = next(t for t in sent.tokens if t.id == last_id)
    return "SpaceAfter=No" in (tok.misc or "")


def extract_unit(conllu_text: str, unit_text: str):
    """Union extraction over UDPipe's sub-sentences with unit-level word offsets."""
    subs = parse_conllu_string(conllu_text)
    pairs = []
    anomalies = []
    offset = 0
    for k, sub in enumerate(subs):
        ext = extract(sub)
        _tw, n_words = assign_word_indices(sub)
        for p in ext.pairs:
            pairs.append({
                "subj_form": p.subj_form, "subj_word_idx": p.subj_word_idx + offset,
                "pred_form": p.pred_form, "pred_word_form": p.pred_word_form,
                "pred_word_idx": p.pred_word_idx + offset,
                "distance": p.distance, "pred_is_cop": p.pred_is_cop,
                "pred_is_aux": p.pred_is_aux, "pred_verbform": p.pred_verbform,
                "subj_is_rel": p.subj_is_rel,
            })
        # cumulative offset; a glued boundary merges the adjacent word indices
        offset += n_words - (1 if (_last_unit_glued(sub) and k < len(subs) - 1) else 0)
    expected = len(unit_text.split())
    if offset != expected:
        anomalies.append(f"word_count_mismatch:{offset}!={expected}")
    verdict = any(p["distance"] > T_LIMIT for p in pairs)
    return pairs, verdict, len(subs), anomalies


def greedy_match(gold: list[dict], pred: list[dict], by_index: bool):
    """Greedy 1:1 matching; returns list of (g, p) matches."""
    used = set()
    matches = []
    for g in gold:
        best = None
        for j, p in enumerate(pred):
            if j in used:
                continue
            if by_index:
                ok = (p["subj_word_idx"] == g["subj_word_idx"]
                      and p["pred_word_idx"] == g["pred_word_idx"])
            else:
                ok = (p["subj_form"] == g["subj_form"]
                      and p["pred_word_form"] == g["pred_word_form"])
            if ok:
                cost = abs(p["subj_word_idx"] - g["subj_word_idx"])
                if best is None or cost < best[0]:
                    best = (cost, j)
        if best is not None:
            used.add(best[1])
            matches.append((g, pred[best[1]]))
    return matches


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--cltt-dir", default=DEFAULT_CLTT)
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--offline", action="store_true",
                    help="use the cache only; fail on cache misses")
    args = ap.parse_args()

    out_dir = os.path.join(BASE, "data", "parser_arm")
    os.makedirs(out_dir, exist_ok=True)
    cache_path = os.path.join(out_dir, "udpipe_cache.jsonl")

    # units from the treebank (uid -> raw text)
    units = []
    for fn in sorted(os.listdir(args.cltt_dir)):
        if not fn.endswith(".conllu"):
            continue
        for idx, sent in enumerate(iter_conllu(os.path.join(args.cltt_dir, fn))):
            units.append({"uid": f"cs_cltt/{fn}::{idx}", "text": sent.text or ""})

    cache: dict[str, str] = {}
    if os.path.exists(cache_path):
        for line in open(cache_path, encoding="utf-8"):
            r = json.loads(line)
            cache[r["uid"]] = r["conllu"]

    todo = [u for u in units if u["uid"] not in cache]
    if todo and args.offline:
        raise SystemExit(f"offline mode but {len(todo)} cache misses")
    if todo:
        print(f"parsing {len(todo)} units via LINDAT UDPipe ({UDPIPE_MODEL}) …", flush=True)
        with open(cache_path, "a", encoding="utf-8") as cf, \
             ThreadPoolExecutor(max_workers=args.workers) as ex:
            for uid, conllu in zip(
                [u["uid"] for u in todo],
                ex.map(lambda u: udpipe(u["text"]), todo),
            ):
                cf.write(json.dumps({"uid": uid, "conllu": conllu},
                                    ensure_ascii=False) + "\n")
                cache[uid] = conllu
        print("parsing done.", flush=True)

    # gold
    gold = {json.loads(l)["uid"]: json.loads(l)
            for l in open(os.path.join(BASE, "data", "cltt_gold_pairs.jsonl"),
                          encoding="utf-8")}

    # extraction + scoring
    seg_dist = Counter()
    mism = 0
    cm = Counter()  # verdict confusion
    gold_pairs_n = pred_pairs_n = 0
    m_idx = m_form = 0
    dist_exact = dist_w1 = 0
    abs_err = []
    out_records = []

    for u in units:
        uid = u["uid"]
        pairs, verdict, n_subs, anomalies = extract_unit(cache[uid], u["text"])
        seg_dist[min(n_subs, 3)] += 1
        if any(a.startswith("word_count_mismatch") for a in anomalies):
            mism += 1
        g = gold[uid]
        gv, pv = g["verdict"], verdict
        cm[(gv, pv)] += 1
        gold_pairs_n += len(g["pairs"])
        pred_pairs_n += len(pairs)
        mi = greedy_match(g["pairs"], pairs, by_index=True)
        mf = greedy_match(g["pairs"], pairs, by_index=False)
        m_idx += len(mi)
        m_form += len(mf)
        for gp, pp in mf:
            d = abs(pp["distance"] - gp["distance"])
            abs_err.append(d)
            dist_exact += d == 0
            dist_w1 += d <= 1
        out_records.append({"uid": uid, "n_subsentences": n_subs,
                            "anomalies": anomalies, "verdict": verdict,
                            "pairs": pairs})

    with open(os.path.join(out_dir, "parser_pairs.jsonl"), "w", encoding="utf-8") as fh:
        for r in out_records:
            fh.write(json.dumps(r, ensure_ascii=False) + "\n")

    n = len(units)
    tp = cm[(True, True)]; fp = cm[(False, True)]
    fn = cm[(True, False)]; tn = cm[(False, False)]
    acc = (tp + tn) / n
    prec = tp / (tp + fp) if tp + fp else 0.0
    rec = tp / (tp + fn) if tp + fn else 0.0
    f1 = 2 * prec * rec / (prec + rec) if prec + rec else 0.0
    pair_p = m_form / pred_pairs_n if pred_pairs_n else 0.0
    pair_r = m_form / gold_pairs_n if gold_pairs_n else 0.0
    pair_f = 2 * pair_p * pair_r / (pair_p + pair_r) if pair_p + pair_r else 0.0

    L = []
    w = L.append
    w("# Parser arm — results vs. CLTT gold (PRELIMINARY: pending K6–K9 sign-off)")
    w("")
    w(f"UDPipe 2 `{UDPIPE_MODEL}` (LINDAT API) on the raw text of all {n} gold sentence")
    w("units; §3 extraction with sub-sentence union and word-offset mapping (§5.1).")
    w("Gold may shift when Katka's K6–K9 answers land; rescoring is deterministic and cheap.")
    w("")
    w("## Verdict (violation ⇔ any pair d > 6) — the deployment metric")
    w("")
    w("| metric | value |")
    w("|---|--:|")
    w(f"| accuracy | **{100*acc:.1f}%** |")
    w(f"| precision | {100*prec:.1f}% |")
    w(f"| recall | {100*rec:.1f}% |")
    w(f"| F1 | {100*f1:.1f}% |")
    w(f"| confusion (gold→pred) | TP {tp} · FP {fp} · FN {fn} · TN {tn} |")
    w("")
    w("## Pair extraction")
    w("")
    w(f"- gold pairs {gold_pairs_n}, predicted {pred_pairs_n}")
    w(f"- form-matched: {m_form} → precision {100*pair_p:.1f}%, recall {100*pair_r:.1f}%, "
      f"F1 {100*pair_f:.1f}%")
    w(f"- index-exact matched: {m_idx} ({100*m_idx/gold_pairs_n:.1f}% of gold)")
    if abs_err:
        w(f"- distance on form-matched pairs: exact {100*dist_exact/len(abs_err):.1f}%, "
          f"±1 {100*dist_w1/len(abs_err):.1f}%, MAE {sum(abs_err)/len(abs_err):.2f}")
    w("")
    w("## Segmentation (the known upstream error)")
    w("")
    w(f"- units kept as one sentence by UDPipe: {seg_dist[1]} ({100*seg_dist[1]/n:.1f}%)")
    w(f"- split into 2: {seg_dist[2]} ({100*seg_dist[2]/n:.1f}%); into 3+: {seg_dist[3]} "
      f"({100*seg_dist[3]/n:.1f}%)")
    w(f"- word-count mismatches after union mapping: {mism}")
    w("")
    with open(os.path.join(BASE, "docs", "PARSER_ARM_RESULTS.md"), "w",
              encoding="utf-8") as fh:
        fh.write("\n".join(L))

    print(f"verdict acc {100*acc:.1f}%  P {100*prec:.1f}  R {100*rec:.1f}  F1 {100*f1:.1f}")
    print(f"pairs: form-F1 {100*pair_f:.1f}  dist-exact {100*dist_exact/max(1,len(abs_err)):.1f}%")
    print(f"segmentation: 1={seg_dist[1]} 2={seg_dist[2]} 3+={seg_dist[3]}  mismatches={mism}")
    print("-> docs/PARSER_ARM_RESULTS.md")


if __name__ == "__main__":
    main()
