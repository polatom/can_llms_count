"""Build the frozen eval set (METHODOLOGY.md §4.1) and the audit-gate report.

Uniform random sample of N sentences from unfiltered KUK 1.0 (UD layer).
No linguistic filtering, no stratification. Technical exclusions only, logged:
  - empty / whitespace-only text
  - exact duplicates after whitespace normalization (first occurrence kept)
  - sentences longer than MAX_WORDS whitespace words

Two passes: (1) enumerate all sentences (uid, text, n_words, dedup); sample;
(2) re-read only the sampled files to capture raw CoNLL-U blocks.

Outputs (all committed):
  data/eval/eval_640.jsonl     one record per sampled sentence, incl. raw conllu
  data/eval/silver_pairs.jsonl parser-arm extraction on the sample (silver)
  data/eval/sampling_stats.json population + exclusion accounting
  docs/AUDIT_eval640.md        audit-gate report (§4.1) + metric family (§4.3)

Usage: python3 sample_eval_set.py [--kuk-root PATH] [--n 640] [--seed 20260717]
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from collections import Counter, defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from conllu_utils import assign_word_indices, iter_conllu  # noqa: E402
from extract_pairs import T_LIMIT, extract, extraction_to_dict  # noqa: E402

DEFAULT_KUK_ROOT = os.path.normpath(
    os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "..", "..", "data", "raw", "KUK_1.0", "KUK_1.0", "data",
    )
)
MAX_WORDS = 200
# §4.1 decision 2026-07-20: population = the ESO sub-corpus only (single-source:
# ombudsman statements, 844k of KUK's 910k sentences). Override with --subcorpus "".
DEFAULT_SUBCORPUS = "ESO"


def find_conllu_files(root: str) -> list[str]:
    out = []
    for dirpath, _dirnames, filenames in os.walk(root):
        for fn in filenames:
            if fn.endswith(".conllu"):
                out.append(os.path.join(dirpath, fn))
    return sorted(out)


def norm_text(text: str) -> str:
    return " ".join(text.split())


def enumerate_sentences(files: list[str], root: str, only_subcorpus: str = ""):
    """Pass 1: light enumeration with dedup + exclusions accounting."""
    kept = []  # dicts: uid, rel, sent_index, sent_id, subcorpus, text, n_words
    stats = Counter()
    seen: set[str] = set()
    per_subcorpus = Counter()

    for path in files:
        rel = os.path.relpath(path, root)
        subcorpus = rel.split(os.sep)[0]
        for idx, sent in enumerate(iter_conllu(path)):
            stats["total_sentences"] += 1
            per_subcorpus[subcorpus] += 1
            if only_subcorpus and subcorpus != only_subcorpus:
                stats["excluded_other_subcorpus"] += 1
                continue
            text = sent.text or ""
            key = norm_text(text)
            if not key:
                stats["excluded_empty"] += 1
                continue
            _tw, n_words = assign_word_indices(sent)
            if n_words > MAX_WORDS:
                stats["excluded_over_max_words"] += 1
                continue
            if key in seen:
                stats["excluded_duplicate"] += 1
                continue
            seen.add(key)
            kept.append(
                {
                    "uid": f"{rel}::{idx}",
                    "rel": rel,
                    "sent_index": idx,
                    "sent_id": sent.sent_id,
                    "subcorpus": subcorpus,
                    "text": text,
                    "n_words": n_words,
                }
            )
    stats["population_after_exclusions"] = len(kept)
    return kept, stats, per_subcorpus


def collect_raw_blocks(root: str, sampled: list[dict]) -> dict[str, str]:
    """Pass 2: raw CoNLL-U blocks for the sampled sentences, keyed by uid."""
    wanted_by_rel: dict[str, dict[int, str]] = defaultdict(dict)
    for rec in sampled:
        wanted_by_rel[rec["rel"]][rec["sent_index"]] = rec["uid"]

    blocks: dict[str, str] = {}
    for rel, wanted in wanted_by_rel.items():
        path = os.path.join(root, rel)
        cur: list[str] = []
        idx = 0
        with open(path, encoding="utf-8", errors="replace") as fh:
            for line in fh:
                line = line.rstrip("\n")
                if line == "":
                    if any(l and not l.startswith("#") for l in cur):
                        if idx in wanted:
                            blocks[wanted[idx]] = "\n".join(cur)
                        idx += 1
                    cur = []
                    continue
                cur.append(line)
            if any(l and not l.startswith("#") for l in cur) and idx in wanted:
                blocks[wanted[idx]] = "\n".join(cur)
    return blocks


def bucket(value: int, edges: list[int]) -> str:
    lo = 1
    for e in edges:
        if value <= e:
            return f"{lo}-{e}"
        lo = e + 1
    return f"{edges[-1] + 1}+"


def pct(part: int, whole: int) -> str:
    return f"{100.0 * part / whole:.1f}%" if whole else "n/a"


def write_audit(out_md: str, n: int, seed: int, stats: Counter, per_subcorpus: Counter,
                sample: list[dict], extractions: list[dict],
                only_subcorpus: str = "", gold_random_n: int = 200) -> None:
    lines: list[str] = []
    w = lines.append
    w("# Audit gate — eval-%d (METHODOLOGY §4.1) " % n)
    w("")
    w(f"Seed {seed}, uniform random over the deduplicated unfiltered population"
      f"{f' (restricted to the {only_subcorpus} sub-corpus — §4.1 decision 2026-07-20)' if only_subcorpus else ''}. "
      f"Generated by `src/sample_eval_set.py`; frozen at `data/eval/eval_{n}.jsonl`.")
    w("")
    w("## Population and exclusions")
    w("")
    w("| quantity | count |")
    w("|---|--:|")
    w(f"| sentences in KUK UD layer | {stats['total_sentences']} |")
    w(f"| excluded: empty text | {stats['excluded_empty']} |")
    w(f"| excluded: > {MAX_WORDS} words | {stats['excluded_over_max_words']} |")
    w(f"| excluded: exact duplicate (normalized) | {stats['excluded_duplicate']} |")
    if stats.get("excluded_other_subcorpus"):
        w(f"| excluded: other sub-corpus (population = {only_subcorpus}) "
          f"| {stats['excluded_other_subcorpus']} |")
    w(f"| population after exclusions | {stats['population_after_exclusions']} |")
    w(f"| sampled | {len(sample)} |")
    w("")
    w("Population by sub-corpus (before exclusions): "
      + ", ".join(f"{k} {v}" for k, v in sorted(per_subcorpus.items())))
    w("")

    sub = Counter(r["subcorpus"] for r in sample)
    w("## Sample composition")
    w("")
    w("| sub-corpus | sampled | share |")
    w("|---|--:|--:|")
    for k in sorted(sub):
        w(f"| {k} | {sub[k]} | {pct(sub[k], len(sample))} |")
    w("")

    lens = Counter(bucket(r["n_words"], [10, 25, 45]) for r in sample)
    w("Length buckets (words): "
      + ", ".join(f"{b}: {lens[b]}" for b in ["1-10", "11-25", "26-45", "46+"] if b in lens))
    w("")

    # --- extraction-derived stats
    n_sent = len(extractions)
    clause_dist = Counter(min(e["finite_clause_count"], 3) for e in extractions)
    frag = sum(1 for e in extractions if e["is_fragment"])
    pro_drop_sent = sum(1 for e in extractions if e["pro_drop_clause_count"] > 0)
    n_pairs = sum(len(e["pairs"]) for e in extractions)
    pair_dist = Counter()
    flags = Counter()
    for e in extractions:
        for p in e["pairs"]:
            pair_dist[bucket(p["distance"] + 1, [2, 5, 10])] += 1  # d 0-1 / 2-4 / 5-9 / 10+
            if p["pred_is_cop"]:
                flags["copular_pairs"] += 1
            if p["pred_mood_cnd"]:
                flags["conditional_pairs"] += 1
            if p["pred_in_mwt"]:
                flags["pred_in_mwt_pairs (aby/kdyby)"] += 1
            if p["vs_order"]:
                flags["vs_order_pairs"] += 1
            if p["subj_is_pass"]:
                flags["passive_subj_pairs"] += 1
    verdicts = sum(1 for e in extractions if e["verdict"])
    near = sum(
        1 for e in extractions
        if any(4 <= p["distance"] <= 9 for p in e["pairs"])
    )
    nonverbal = sum(e["nonverbal_nsubj_excluded"] for e in extractions)
    nonverbal_upos = Counter(u for e in extractions for u in e["nonverbal_head_upos"])
    csubj = sum(e["csubj_count"] for e in extractions)
    anom = Counter(a.split(":")[0] for e in extractions
                   for a in e["anomalies"] + [x for p in e["pairs"] for x in p["anomalies"]])

    w("## Phenomena (silver, parser-arm extraction)")
    w("")
    w("| quantity | count | share |")
    w("|---|--:|--:|")
    w(f"| sentences | {n_sent} | |")
    w(f"| fragments (no finite clause) | {frag} | {pct(frag, n_sent)} |")
    w(f"| sentences with ≥1 pro-drop clause | {pro_drop_sent} | {pct(pro_drop_sent, n_sent)} |")
    for k, label in [(0, "0 finite clauses"), (1, "1 finite clause"),
                     (2, "2 finite clauses"), (3, "3+ finite clauses")]:
        w(f"| {label} | {clause_dist.get(k, 0)} | {pct(clause_dist.get(k, 0), n_sent)} |")
    w(f"| subject–predicate pairs total | {n_pairs} | {n_pairs / n_sent:.2f}/sentence |")
    for k in sorted(flags):
        w(f"| {k} | {flags[k]} | {pct(flags[k], n_pairs)} of pairs |")
    w(f"| csubj (excluded, counted) | {csubj} | |")
    w(f"| nsubj dropped: non-verbal head, no cop/aux | {nonverbal} | "
      f"UPOS: {dict(nonverbal_upos)} |")
    w(f"| extraction anomalies | {sum(anom.values())} | {dict(anom)} |")
    w("")
    w("Pair distance buckets (d): "
      + ", ".join(f"{b}: {pair_dist[b]}" for b in ["1-2", "3-5", "6-10", "11+"] if b in pair_dist)
      + "  *(bucket labels are d+1 bands: 0–1 / 2–4 / 5–9 / 10+)*")
    w("")
    w("## Verdict prevalence (§4.1 power check)")
    w("")
    w(f"- sentences flagged (any pair d > {T_LIMIT}): **{verdicts} ({pct(verdicts, n_sent)})**")
    w(f"- sentences with a near-threshold pair (d ∈ [4, 9]): {near} ({pct(near, n_sent)})")
    expg = round(verdicts / n_sent * gold_random_n) if n_sent else 0
    w(f"- expected positives in the random gold-{gold_random_n}: **≈ {expg}** "
      "(if < ~15, enlarge the random gold slice per §4.1)")
    w("")

    # --- §4.3 metric family
    import statistics as st

    def col(key):
        vals = [e["family"][key] for e in extractions if e["family"][key] is not None]
        if not vals:
            return "—", "—", "—"
        return (f"{st.mean(vals):.1f}", f"{st.median(vals):.0f}",
                f"{sorted(vals)[int(0.9 * (len(vals) - 1))]}")

    w("## Metric family (§4.3, silver) — mean / median / p90 per sentence")
    w("")
    w("| metric | mean | median | p90 |")
    w("|---|--:|--:|--:|")
    for key, label in [
        ("n_words", "sentence length (words)"),
        ("tree_depth", "dependency tree depth"),
        ("subordinate_clauses", "subordinate clauses (advcl/acl/ccomp/csubj)"),
        ("coordinations", "coordinations (conj)"),
        ("passives", "passive markers (nsubj:pass/aux:pass)"),
        ("max_pair_distance", "max subject–predicate distance"),
    ]:
        m, md, p90 = col(key)
        w(f"| {label} | {m} | {md} | {p90} |")
    w("")
    w("**Gate decision:** *(fill in after review — proceed with N=640 / extend sample)*")
    w("")

    with open(out_md, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--kuk-root", default=DEFAULT_KUK_ROOT)
    ap.add_argument("--n", type=int, default=640)
    ap.add_argument("--seed", type=int, default=20260717)
    ap.add_argument("--subcorpus", default=DEFAULT_SUBCORPUS,
                    help="restrict the population to one sub-corpus ('' = all of KUK)")
    ap.add_argument("--gold-random-n", type=int, default=200,
                    help="planned size of the random gold slice (audit power check)")
    args = ap.parse_args()

    base = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
    eval_dir = os.path.join(base, "data", "eval")
    docs_dir = os.path.join(base, "docs")
    os.makedirs(eval_dir, exist_ok=True)
    os.makedirs(docs_dir, exist_ok=True)

    files = find_conllu_files(args.kuk_root)
    print(f"[1/4] enumerating {len(files)} conllu files …", flush=True)
    kept, stats, per_subcorpus = enumerate_sentences(files, args.kuk_root, args.subcorpus)
    print(f"      population after exclusions: {len(kept)} "
          f"(of {stats['total_sentences']} total)", flush=True)

    rng = random.Random(args.seed)
    sample = rng.sample(kept, args.n)
    sample.sort(key=lambda r: r["uid"])

    print("[2/4] collecting raw conllu blocks for the sample …", flush=True)
    blocks = collect_raw_blocks(args.kuk_root, sample)
    missing = [r["uid"] for r in sample if r["uid"] not in blocks]
    if missing:
        raise RuntimeError(f"raw block missing for {len(missing)} uids, e.g. {missing[:3]}")

    print("[3/4] running parser-arm extraction (silver) …", flush=True)
    extractions = []
    with open(os.path.join(eval_dir, f"eval_{args.n}.jsonl"), "w", encoding="utf-8") as ev, \
         open(os.path.join(eval_dir, "silver_pairs.jsonl"), "w", encoding="utf-8") as sp:
        for rec in sample:
            block = blocks[rec["uid"]]
            ev.write(json.dumps({**{k: rec[k] for k in
                                    ("uid", "subcorpus", "sent_id", "text", "n_words")},
                                 "conllu": block}, ensure_ascii=False) + "\n")
            # parse the block back through iter_conllu via a temp round-trip in memory
            import io
            from conllu_utils import Sentence, Token, MWT  # noqa: F401
            sents = list(_iter_conllu_string(block))
            assert len(sents) == 1, rec["uid"]
            ext = extract(sents[0])
            extractions.append(extraction_to_dict(rec["uid"], rec["subcorpus"], ext))
            sp.write(json.dumps(extractions[-1], ensure_ascii=False) + "\n")

    with open(os.path.join(eval_dir, "sampling_stats.json"), "w", encoding="utf-8") as fh:
        json.dump({"seed": args.seed, "n": args.n, "max_words": MAX_WORDS,
                   "kuk_root": args.kuk_root, "subcorpus": args.subcorpus or "ALL",
                   "stats": dict(stats), "per_subcorpus": dict(per_subcorpus)},
                  fh, ensure_ascii=False, indent=2)

    print("[4/4] writing audit report …", flush=True)
    write_audit(os.path.join(docs_dir, f"AUDIT_eval{args.n}.md"),
                args.n, args.seed, stats, per_subcorpus, sample, extractions,
                only_subcorpus=args.subcorpus, gold_random_n=args.gold_random_n)
    print("done.")


def _iter_conllu_string(block: str):
    """iter_conllu over an in-memory block (single sentence expected)."""
    import tempfile

    with tempfile.NamedTemporaryFile("w", suffix=".conllu", delete=False,
                                     encoding="utf-8") as tf:
        tf.write(block + "\n\n")
        tmp = tf.name
    try:
        yield from iter_conllu(tmp)
    finally:
        os.unlink(tmp)


if __name__ == "__main__":
    main()
