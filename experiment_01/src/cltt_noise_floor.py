"""Parser noise-floor: UDPipe (the model that made KUK silver) vs. cs_cltt gold.

Estimates how much to trust the silver standard on legal Czech for OUR task.
For each cs_cltt gold sentence that passes our single-main-nsubj filter, we
re-parse the raw text with the SAME UDPipe model (czech-pdt-ud-2.15-241121) and
compare the extracted (subject-word, predicate-word, word-distance) against gold.

Distances are in whitespace-words (robust to UD tokenization differences), so
gold and UDPipe word indices are directly comparable on the identical raw text.

Reports: coverage (does UDPipe also yield a clean single pair?), role-word
agreement, distance exact/±1, MAE. This is the ceiling the silver-based LLM
numbers should be read against.

Usage:
  python src/cltt_noise_floor.py --cltt-dir experiment_01/data/raw/cs_cltt \
     --out experiment_01/results/cltt_noise_floor.json
Stdlib only.
"""

from __future__ import annotations

import argparse
import glob
import json
import os
import statistics
import sys
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed

sys.path.insert(0, os.path.dirname(__file__))
from conllu_utils import MWT, Sentence, Token, assign_word_indices, iter_conllu  # noqa: E402

UDPIPE_URL = "https://lindat.mff.cuni.cz/services/udpipe/api/process"
UDPIPE_MODEL = "czech-pdt-ud-2.15-241121"


def extract_pair(sent: Sentence):
    """(subj_word, pred_word, distance) for a single-main-nsubj sentence, else None."""
    toks = sent.tokens
    if not toks:
        return None
    base = sent.deprel_base
    roots = [t for t in toks if t.head == 0]
    if len(roots) != 1:
        return None
    root = roots[0]
    subs = [t for t in toks if t.head == root.id and base[t.id] == "nsubj"]
    if len(subs) != 1:
        return None
    tw, nw = assign_word_indices(sent)
    sw, pw = tw.get(subs[0].id), tw.get(root.id)
    if sw is None or pw is None or sw == pw or not (5 <= nw <= 80):
        return None
    return sw, pw, abs(sw - pw) - 1


def parse_conllu_string(text: str):
    """Yield Sentence objects from a CoNLL-U string (mirror of iter_conllu)."""
    sid, txt, toks, mwts = "", "", [], []
    for line in text.splitlines():
        if line == "":
            if toks:
                yield Sentence(sid, txt, toks, mwts)
            sid, txt, toks, mwts = "", "", [], []
            continue
        if line.startswith("#"):
            if line.startswith("# sent_id") and "=" in line:
                sid = line.split("=", 1)[1].strip()
            elif line.startswith("# text") and "=" in line:
                txt = line.split("=", 1)[1].strip()
            continue
        c = line.split("\t")
        if len(c) != 10:
            continue
        if "-" in c[0]:
            s, e = c[0].split("-")
            mwts.append(MWT(int(s), int(e), c[1], c[9]))
            continue
        if "." in c[0]:
            continue
        try:
            head = int(c[6])
        except ValueError:
            head = -1
        toks.append(Token(int(c[0]), c[1], c[2], c[3], c[4], c[5], head, c[7], c[8], c[9]))
    if toks:
        yield Sentence(sid, txt, toks, mwts)


def udpipe(text: str) -> str:
    data = urllib.parse.urlencode({
        "tokenizer": "", "tagger": "", "parser": "", "model": UDPIPE_MODEL,
        "output": "conllu", "data": text,
    }).encode()
    for attempt in range(4):
        try:
            r = urllib.request.urlopen(UDPIPE_URL, data=data, timeout=90)
            return json.load(r)["result"]
        except Exception:
            if attempt == 3:
                raise
    return ""


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--cltt-dir", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--workers", type=int, default=4)
    args = ap.parse_args()

    gold = []
    for f in sorted(glob.glob(os.path.join(args.cltt_dir, "*.conllu"))):
        for s in iter_conllu(f):
            p = extract_pair(s)
            if p and s.text:
                gold.append({"text": s.text, "subj_word": p[0], "pred_word": p[1], "distance": p[2]})
    print(f"cs_cltt gold sentences passing filter: {len(gold)}")

    def work(item):
        try:
            out = udpipe(item["text"])
        except Exception as e:
            return item, None, f"udpipe_error:{e}"
        sents = list(parse_conllu_string(out))
        if len(sents) != 1:
            return item, None, f"udpipe_segmented_{len(sents)}"
        up = extract_pair(sents[0])
        if up is None:
            return item, None, "udpipe_no_clean_pair"
        return item, up, "ok"

    results = []
    with ThreadPoolExecutor(max_workers=args.workers) as ex:
        futs = [ex.submit(work, g) for g in gold]
        for i, fut in enumerate(as_completed(futs), 1):
            results.append(fut.result())
            if i % 100 == 0:
                print(f"  {i}/{len(gold)}")

    both = [(g, up) for g, up, st in results if st == "ok"]
    reasons = {}
    for _, _, st in results:
        if st != "ok":
            reasons[st.split(":")[0]] = reasons.get(st.split(":")[0], 0) + 1

    subj_match = sum(1 for g, up in both if g["subj_word"] == up[0])
    pred_match = sum(1 for g, up in both if g["pred_word"] == up[1])
    both_match = sum(1 for g, up in both if g["subj_word"] == up[0] and g["pred_word"] == up[1])
    dist_exact = sum(1 for g, up in both if g["distance"] == up[2])
    dist_w1 = sum(1 for g, up in both if abs(g["distance"] - up[2]) <= 1)
    abs_errs = [abs(g["distance"] - up[2]) for g, up in both]
    n = len(both)

    summary = {
        "udpipe_model": UDPIPE_MODEL,
        "gold_passing": len(gold),
        "udpipe_also_clean_pair": n,
        "coverage": round(n / len(gold), 4) if gold else None,
        "no_pair_reasons": reasons,
        "on_shared_pairs": {
            "subject_word_agreement": round(subj_match / n, 4) if n else None,
            "predicate_word_agreement": round(pred_match / n, 4) if n else None,
            "both_roles_agreement": round(both_match / n, 4) if n else None,
            "distance_exact_agreement": round(dist_exact / n, 4) if n else None,
            "distance_within1_agreement": round(dist_w1 / n, 4) if n else None,
            "distance_mae": round(statistics.mean(abs_errs), 3) if abs_errs else None,
        },
    }
    with open(args.out, "w", encoding="utf-8") as fh:
        json.dump(summary, fh, ensure_ascii=False, indent=2)

    print(json.dumps(summary, ensure_ascii=False, indent=2))
    print(f"\nWrote {args.out}")


if __name__ == "__main__":
    main()
