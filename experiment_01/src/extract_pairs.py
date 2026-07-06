"""Extract (subject, predicate, word-distance) gold from KUK 1.0 silver CoNLL-U.

Implements the task definition in docs/METHODOLOGY.md §2:
  * subject   = the single ``nsubj``/``nsubj:pass`` dependent of the sentence root
  * predicate = head of that subject == the root (whatever its POS; copular
                clauses therefore measure to the nominal predicate, with the
                copula index logged separately)
  * distance  = |p - q| - 1 counted in **whitespace-words** (MWT-collapsed)

Filtering (self-consistent from UDPipe's own parse, since we have no gold here):
exactly one root, exactly one root-attached nsubj, no clausal-only subject,
word-length within [--min-words, --max-words]. Every exclusion is counted and
reported — the exclusion breakdown is itself a reported descriptive statistic.

Usage:
    python src/extract_pairs.py \
        --kuk-root experiment_01/data/raw/KUK_1.0/KUK_1.0/data \
        --out-dir  experiment_01/data/processed

Stdlib only.
"""

from __future__ import annotations

import argparse
import glob
import json
import os
from collections import Counter

from conllu_utils import Sentence, assign_word_indices, iter_conllu, tree_depth

SUBJECT_DEPRELS = {"nsubj"}  # base form; covers nsubj and nsubj:pass
CLAUSE_DEPRELS = {"csubj", "ccomp", "xcomp", "advcl", "acl", "parataxis"}


def subcorpus_of(path: str, kuk_root: str) -> tuple[str, str]:
    """Return (subcorpus, variant) from a file path under the KUK data root."""
    rel = os.path.relpath(path, kuk_root)
    parts = rel.split(os.sep)
    subcorpus = parts[0] if parts else "?"
    # variant = the directory between subcorpus and the UD/ folder, if any
    variant = ""
    if "UD" in parts:
        ud_idx = parts.index("UD")
        if ud_idx >= 2:
            variant = parts[ud_idx - 1]
    return subcorpus, variant


def analyze(sentence: Sentence) -> tuple[dict | None, str]:
    """Return (record, reason). record is None iff the sentence is excluded."""
    toks = sentence.tokens
    if not toks:
        return None, "empty"

    base = sentence.deprel_base
    roots = [t for t in toks if t.head == 0]
    if len(roots) == 0:
        return None, "no_root"
    if len(roots) > 1:
        return None, "multiple_roots"
    root = roots[0]

    root_subjects = [t for t in toks if t.head == root.id and base[t.id] == "nsubj"]
    root_csubjs = [t for t in toks if t.head == root.id and base[t.id] == "csubj"]

    if len(root_subjects) == 0:
        return None, "csubj_only" if root_csubjs else "no_subject"
    if len(root_subjects) > 1:
        return None, "multiple_main_subjects"

    subj = root_subjects[0]
    pred = root  # predicate == head of subject == root
    cops = [t for t in toks if t.head == root.id and base[t.id] == "cop"]
    cop = cops[0] if cops else None

    token_word, n_words = assign_word_indices(sentence)
    subj_w = token_word.get(subj.id)
    pred_w = token_word.get(pred.id)
    if subj_w is None or pred_w is None:
        return None, "word_index_error"
    if subj_w == pred_w:
        return None, "subj_pred_same_word"

    distance = abs(subj_w - pred_w) - 1

    lo, hi = min(subj_w, pred_w), max(subj_w, pred_w)
    intervening_clauses = sum(
        1
        for t in toks
        if base[t.id] in CLAUSE_DEPRELS and lo < token_word.get(t.id, -1) < hi
    )

    # Faithfulness check: our MWT-aware word count vs. a naive text.split().
    text_words = len(sentence.text.split()) if sentence.text else n_words
    word_count_check = "ok" if text_words == n_words else "mismatch"

    record = {
        "sent_id": sentence.sent_id,
        "subj_id": subj.id,
        "subj_form": subj.form,
        "subj_deprel": subj.deprel,
        "subj_word": subj_w,
        "pred_id": pred.id,
        "pred_form": pred.form,
        "pred_upos": pred.upos,
        "pred_deprel": pred.deprel,
        "pred_word": pred_w,
        "is_copula": cop is not None,
        "cop_id": cop.id if cop else None,
        "cop_word": token_word.get(cop.id) if cop else None,
        "distance": distance,
        "n_words": n_words,
        "n_ud_tokens": len(toks),
        "tree_depth": tree_depth(sentence),
        "intervening_clauses": intervening_clauses,
        "word_count_check": word_count_check,
        "text": sentence.text,
    }
    return record, "ok"


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--kuk-root", required=True, help="Path to KUK .../data dir")
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--min-words", type=int, default=5)
    ap.add_argument("--max-words", type=int, default=80)
    ap.add_argument(
        "--drop-word-mismatch",
        action="store_true",
        help="Exclude sentences where MWT word count != text.split() count",
    )
    args = ap.parse_args()

    os.makedirs(args.out_dir, exist_ok=True)
    files = sorted(glob.glob(os.path.join(args.kuk_root, "**", "*.conllu"), recursive=True))
    print(f"Found {len(files)} .conllu files under {args.kuk_root}")

    out_path = os.path.join(args.out_dir, "kuk_pairs.jsonl")
    reasons: Counter = Counter()
    by_subcorpus_total: Counter = Counter()
    by_subcorpus_pass: Counter = Counter()
    examples: dict[str, list] = {}
    mismatch = 0
    n_sent = 0
    n_pass = 0

    with open(out_path, "w", encoding="utf-8") as out:
        for path in files:
            subcorpus, variant = subcorpus_of(path, args.kuk_root)
            for sent in iter_conllu(path):
                n_sent += 1
                by_subcorpus_total[subcorpus] += 1
                rec, reason = analyze(sent)

                if rec is not None and rec["word_count_check"] == "mismatch":
                    mismatch += 1
                    if args.drop_word_mismatch:
                        rec, reason = None, "word_count_mismatch"

                # length filter (applied last so length stats reflect real sentences)
                if rec is not None and not (args.min_words <= rec["n_words"] <= args.max_words):
                    rec, reason = None, "length_out_of_bounds"

                if rec is None:
                    reasons[reason] += 1
                    if len(examples.setdefault(reason, [])) < 3:
                        examples[reason].append({"sent_id": sent.sent_id, "text": sent.text[:160]})
                    continue

                rec["subcorpus"] = subcorpus
                rec["variant"] = variant
                rec["source_file"] = os.path.relpath(path, args.kuk_root)
                out.write(json.dumps(rec, ensure_ascii=False) + "\n")
                n_pass += 1
                by_subcorpus_pass[subcorpus] += 1

    summary = {
        "n_files": len(files),
        "n_sentences": n_sent,
        "n_pass": n_pass,
        "pass_rate": round(n_pass / n_sent, 4) if n_sent else 0.0,
        "word_count_mismatch_among_candidates": mismatch,
        "exclusion_reasons": dict(reasons.most_common()),
        "by_subcorpus": {
            sc: {
                "total": by_subcorpus_total[sc],
                "pass": by_subcorpus_pass[sc],
                "pass_rate": round(by_subcorpus_pass[sc] / by_subcorpus_total[sc], 4)
                if by_subcorpus_total[sc]
                else 0.0,
            }
            for sc in sorted(by_subcorpus_total)
        },
        "exclusion_examples": examples,
        "params": {"min_words": args.min_words, "max_words": args.max_words},
    }
    summary_path = os.path.join(args.out_dir, "kuk_exclusions.json")
    with open(summary_path, "w", encoding="utf-8") as fh:
        json.dump(summary, fh, ensure_ascii=False, indent=2)

    print(f"\nSentences: {n_sent:,}  Passed: {n_pass:,}  ({summary['pass_rate']*100:.1f}%)")
    print(f"Word-count mismatches among candidates: {mismatch:,}")
    print("\nExclusion reasons:")
    for r, c in reasons.most_common():
        print(f"  {r:28s} {c:>9,}")
    print("\nBy subcorpus (pass / total):")
    for sc, d in summary["by_subcorpus"].items():
        print(f"  {sc:14s} {d['pass']:>8,} / {d['total']:>8,}  ({d['pass_rate']*100:.1f}%)")
    print(f"\nWrote {out_path}")
    print(f"Wrote {summary_path}")


if __name__ == "__main__":
    main()
