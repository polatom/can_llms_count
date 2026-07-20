"""Verification sheet for Katka (METHODOLOGY §4.1 step 2).

Stratified sample of CLTT-derived gold pairs for human verification:
ALL pairs of the rare constructions (conditional, aby/kdyby, past copular,
analytic aux) + N random pairs of the common types (finite verb, present
copula, passives), seeded. Rendered like the worked examples: windowed
numbered words, the pair, the distance, ✓/oprava checkbox — in Czech.

Output: docs/VERIFICATION_SHEET_katka.md
Usage:  python3 make_verification_sheet.py [--n-common 80] [--seed 20260720]

Regenerate after any rule change (gold re-derivation) — the sheet embeds the
current pairs. Do not send until K6-K8 / worked-examples answers are in.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from conllu_utils import iter_conllu  # noqa: E402
from derive_cltt_gold import numbered_words  # noqa: E402

BASE = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
DEFAULT_CLTT = os.path.normpath(os.path.join(BASE, "..", "data", "raw", "cs_cltt"))

RARE_KINDS = {
    "conditional (by)", "aby/kdyby (absorbed by)",
    "copular — past copula (byla)", "analytic — aux (jsem/bude …)",
}


def classify(p: dict) -> str:
    if p["pred_in_mwt"]:
        return "aby/kdyby (absorbed by)"
    if p["pred_mood_cnd"]:
        return "conditional (by)"
    if p["pred_is_cop"]:
        return ("copular — past copula (byla)" if p["pred_verbform"] == "Part"
                else "copular — finite copula (je)")
    if p["pred_is_aux"] and p["subj_is_pass"]:
        return ("passive — past aux (byla vydána)" if p["pred_verbform"] == "Part"
                else "passive — finite aux (je/bude vydána)")
    if p["pred_is_aux"]:
        return "analytic — aux (jsem/bude …)"
    return "finite verb / l-participle"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--cltt-dir", default=DEFAULT_CLTT)
    ap.add_argument("--n-common", type=int, default=80)
    ap.add_argument("--seed", type=int, default=20260720)
    args = ap.parse_args()

    texts: dict[str, str] = {}
    for fn in sorted(os.listdir(args.cltt_dir)):
        if fn.endswith(".conllu"):
            for idx, sent in enumerate(iter_conllu(os.path.join(args.cltt_dir, fn))):
                texts[f"cs_cltt/{fn}::{idx}"] = sent.text or ""

    rare, common = [], []
    for line in open(os.path.join(BASE, "data", "cltt_gold_pairs.jsonl"), encoding="utf-8"):
        s = json.loads(line)
        for p in s["pairs"]:
            item = (s["uid"], classify(p), p)
            (rare if item[1] in RARE_KINDS else common).append(item)

    rng = random.Random(args.seed)
    sample = rare + rng.sample(common, min(args.n_common, len(common)))
    order = {"conditional (by)": 0, "aby/kdyby (absorbed by)": 1,
             "copular — past copula (byla)": 2, "analytic — aux (jsem/bude …)": 3}
    sample.sort(key=lambda it: (order.get(it[1], 9), it[0]))

    kinds = Counter(k for _u, k, _p in sample)
    L = []
    w = L.append
    w("# Kontrolní list — odvozený zlatý standard (experiment_04, §4.1 krok 2)")
    w("")
    w(f"Vzorek {len(sample)} párů z {len(rare) + len(common)} odvozených: **všechny páry")
    w(f"vzácných konstrukcí ({len(rare)})** + {len(sample) - len(rare)} náhodných z běžných")
    w(f"typů (seed {args.seed}). U každého: věta s očíslovanými slovy (dlouhé věty zkráceně,")
    w("(…) = vynechaný text), pár podmět↔přísudek a vzdálenost (počet slov ostře mezi nimi).")
    w("**U každého prosím ✓, nebo oprava.** Věta může obsahovat i jiné páry — kontroluješ")
    w("jen ten uvedený.")
    w("")
    w("Složení: " + ", ".join(f"{k}: {v}" for k, v in kinds.most_common()))
    w("")
    cur = None
    for i, (uid, kind, p) in enumerate(sample, 1):
        if kind != cur:
            cur = kind
            w(f"## {kind}")
            w("")
        w(f"**{i}.** `{uid}`")
        w(f"- {numbered_words(texts[uid], focus=[p['subj_word_idx'], p['pred_word_idx']])}")
        w(f"- pár: **{p['subj_form']}** (slovo {p['subj_word_idx']}) ↔ "
          f"**{p['pred_word_form']}** (slovo {p['pred_word_idx']}) → vzdálenost "
          f"**{p['distance']}**")
        w("- [ ] ✓ / oprava: ")
        w("")

    out = os.path.join(BASE, "docs", "VERIFICATION_SHEET_katka.md")
    with open(out, "w", encoding="utf-8") as fh:
        fh.write("\n".join(L))
    print(f"{len(sample)} pairs ({len(rare)} rare + {len(sample)-len(rare)} common) -> {out}")


if __name__ == "__main__":
    main()
