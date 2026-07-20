"""CLTT-derived gold + worked examples for Katka (METHODOLOGY §4.2).

Applies the §3 extraction rule to the human-annotated `cs_cltt` UD treebank:
because the trees are human gold, the §3 rule applied to them *defines* the
CLTT-derived gold pairs (no parser involved). Also emits the worked-examples
review sheet: 2–3 short examples per §3.1 construction type, formatted for
Katka to confirm or correct, plus the open verbless-clause category (K7).

Outputs:
  data/cltt_gold_pairs.jsonl
  docs/WORKED_EXAMPLES_katka.md

Usage: python3 derive_cltt_gold.py [--cltt-dir PATH] [--kuk-silver PATH]
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from conllu_utils import assign_word_indices, iter_conllu  # noqa: E402
from extract_pairs import extract, extraction_to_dict  # noqa: E402

DEFAULT_CLTT = os.path.normpath(os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "..", "..", "data", "raw", "cs_cltt"))


def classify_pair(p) -> str:
    if p.pred_in_mwt:
        return "aby/kdyby (absorbed by)"
    if p.pred_mood_cnd:
        return "conditional (by)"
    if p.pred_is_cop:
        return ("copular — past copula (byla)" if p.pred_verbform == "Part"
                else "copular — finite copula (je)")
    if p.pred_is_aux and p.subj_is_pass:
        return ("passive — past aux (byla vydána)" if p.pred_verbform == "Part"
                else "passive — finite aux (je/bude vydána)")
    if p.pred_is_aux:
        return "analytic — aux (jsem/bude …)"
    # fallback = clause head itself
    return "finite verb / l-participle"


def numbered_words(text: str) -> str:
    return " ".join(f"{i+1}:{w}" for i, w in enumerate(text.split()))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--cltt-dir", default=DEFAULT_CLTT)
    args = ap.parse_args()

    base = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
    out_gold = os.path.join(base, "data", "cltt_gold_pairs.jsonl")
    out_md = os.path.join(base, "docs", "WORKED_EXAMPLES_katka.md")

    files = sorted(
        os.path.join(args.cltt_dir, f) for f in os.listdir(args.cltt_dir)
        if f.endswith(".conllu")
    )
    kinds = Counter()
    examples: dict[str, list] = {}
    verbless_examples = []
    n_sent = n_pairs = 0

    with open(out_gold, "w", encoding="utf-8") as fh:
        for path in files:
            rel = os.path.basename(path)
            for idx, sent in enumerate(iter_conllu(path)):
                ext = extract(sent)
                n_sent += 1
                n_pairs += len(ext.pairs)
                uid = f"cs_cltt/{rel}::{idx}"
                fh.write(json.dumps(
                    extraction_to_dict(uid, "cs_cltt", ext), ensure_ascii=False) + "\n")

                text = sent.text or ""
                nw = len(text.split())
                for p in ext.pairs:
                    kind = classify_pair(p)
                    kinds[kind] += 1
                    # short, clean examples only
                    if 4 <= nw <= 22 and not p.anomalies:
                        examples.setdefault(kind, [])
                        if len(examples[kind]) < 3:
                            examples[kind].append((text, p, uid))
                if ext.nonverbal_nsubj_excluded and nw <= 20 and len(verbless_examples) < 4:
                    verbless_examples.append((text, uid))

    lines = []
    w = lines.append
    w("# Worked examples for Katka — §3 extraction rule on CLTT gold trees")
    w("")
    w("Purpose (METHODOLOGY §4.2): confirm that the mechanical rule (predicate = finite element")
    w("of the predicate complex; subject = nsubj head word) matches your definition, per")
    w("construction type. All examples below come from human-annotated `cs_cltt` trees, so any")
    w("error is in OUR rule, not in a parser. For each: numbered words, the extracted pair,")
    w("the distance (words strictly between). **Please mark each ✓ or correct it.**")
    w("")
    w(f"Derivation over the whole treebank: {n_sent} sentences → {n_pairs} pairs. "
      f"Distribution: " + ", ".join(f"{k}: {v}" for k, v in kinds.most_common()))
    w("")
    for kind in [
        "finite verb / l-participle",
        "copular — finite copula (je)", "copular — past copula (byla)",
        "conditional (by)", "aby/kdyby (absorbed by)",
        "passive — finite aux (je/bude vydána)", "passive — past aux (byla vydána)",
        "analytic — aux (jsem/bude …)",
    ]:
        w(f"## {kind}  ({kinds.get(kind, 0)} pairs in CLTT)")
        w("")
        for text, p, uid in examples.get(kind, []):
            w(f"- `{uid}`")
            w(f"  - {numbered_words(text)}")
            w(f"  - pair: **{p.subj_form}** (word {p.subj_word_idx}) ↔ "
              f"**{p.pred_word_form}** (word {p.pred_word_idx}"
              f"{'' if p.pred_word_form == p.pred_form else f', measured token: {p.pred_form}'}) "
              f"→ distance **{p.distance}**")
            w("  - [ ] ✓ / correction: ")
            w("")
        if not examples.get(kind):
            w("*(no clean short example found in CLTT — will supply one from KUK)*")
            w("")
    w("## Open category — verbless clauses (new question, K7)")
    w("")
    w("UD sometimes attaches an overt subject to a **non-verbal head with no copula**")
    w("(typically a short-form adjective/participle: *„Vstup zakázán“*-type, or elliptical")
    w("constructions). Our current rule **excludes** these (no finite element to measure to)")
    w("and logs them — they are ~8% of subject edges in the KUK sample (mostly ADJ heads).")
    w("Question: exclude (current), or measure to the non-verbal head itself?")
    w("")
    for text, uid in verbless_examples:
        w(f"- `{uid}`: {text}")
    w("")
    w("- [ ] exclude (current rule)   [ ] measure to the head   [ ] other: ")
    w("")

    with open(out_md, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines))

    print(f"CLTT: {n_sent} sentences, {n_pairs} gold pairs -> {out_gold}")
    print("kinds:", dict(kinds))
    print(f"worked examples -> {out_md}")


if __name__ == "__main__":
    main()
