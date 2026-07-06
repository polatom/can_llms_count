"""CoNLL-U reading utilities for the subject-predicate distance experiment.

Stdlib-only. The one non-trivial piece is `assign_word_indices`, which maps each
syntactic token to a **whitespace-word** index (the unit the distance metric is
defined in — see docs/METHODOLOGY.md §2), collapsing Czech multiword tokens
(e.g. ``aby`` -> ``aby`` + ``by``) into a single surface word.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterator


@dataclass
class Token:
    id: int
    form: str
    lemma: str
    upos: str
    xpos: str
    feats: str
    head: int
    deprel: str
    deps: str
    misc: str


@dataclass
class MWT:
    """A multiword-token surface span (CoNLL-U id ``start-end``)."""

    start: int
    end: int
    form: str
    misc: str


@dataclass
class Sentence:
    sent_id: str
    text: str
    tokens: list[Token] = field(default_factory=list)  # syntactic words only
    mwts: list[MWT] = field(default_factory=list)
    source_file: str = ""

    @property
    def deprel_base(self) -> dict[int, str]:
        # deprel without subtype, e.g. "nsubj:pass" -> "nsubj"
        return {t.id: t.deprel.split(":")[0] for t in self.tokens}


def _no_space_after(misc: str) -> bool:
    """True if this surface unit is glued to the next (no whitespace follows).

    In these corpora whitespace is signalled by ``SpaceAfter=No`` (glued) vs.
    the default / a ``SpacesAfter=...`` value (which always encodes real
    whitespace). So "glued" reduces to the presence of ``SpaceAfter=No``.
    """
    return "SpaceAfter=No" in (misc or "")


def iter_conllu(path: str) -> Iterator[Sentence]:
    """Yield `Sentence` objects from a .conllu file."""
    sent_id = ""
    text = ""
    tokens: list[Token] = []
    mwts: list[MWT] = []

    def flush() -> Sentence | None:
        if not tokens:
            return None
        return Sentence(sent_id=sent_id, text=text, tokens=tokens, mwts=mwts, source_file=path)

    with open(path, encoding="utf-8", errors="replace") as fh:
        for line in fh:
            line = line.rstrip("\n")
            if line == "":
                s = flush()
                if s is not None:
                    yield s
                sent_id, text, tokens, mwts = "", "", [], []
                continue
            if line.startswith("#"):
                if line.startswith("# sent_id"):
                    sent_id = line.split("=", 1)[1].strip() if "=" in line else ""
                elif line.startswith("# text"):
                    text = line.split("=", 1)[1].strip() if "=" in line else ""
                continue
            cols = line.split("\t")
            if len(cols) != 10:
                continue
            tid = cols[0]
            if "-" in tid:  # multiword-token range line
                start, end = tid.split("-")
                mwts.append(MWT(start=int(start), end=int(end), form=cols[1], misc=cols[9]))
                continue
            if "." in tid:  # empty node (enhanced UD) — none in KUK, skip defensively
                continue
            try:
                head = int(cols[6])
            except ValueError:
                head = -1
            tokens.append(
                Token(
                    id=int(tid),
                    form=cols[1],
                    lemma=cols[2],
                    upos=cols[3],
                    xpos=cols[4],
                    feats=cols[5],
                    head=head,
                    deprel=cols[7],
                    deps=cols[8],
                    misc=cols[9],
                )
            )

    s = flush()
    if s is not None:
        yield s


def assign_word_indices(sentence: Sentence) -> tuple[dict[int, int], int]:
    """Map each syntactic token id -> 0-based whitespace-word index.

    Returns ``(token_id -> word_index, n_words)``. Multiword tokens collapse to
    one word; internal syntactic words of an MWT share its word index.
    """
    tok_by_id = {t.id: t for t in sentence.tokens}
    ids = sorted(tok_by_id)
    mwt_by_start = {m.start: m for m in sentence.mwts}
    idset = set(ids)

    # Ordered list of surface units: (misc, [member syntactic ids]).
    units: list[tuple[str, list[int]]] = []
    k = 0
    while k < len(ids):
        tid = ids[k]
        mwt = mwt_by_start.get(tid)
        if mwt is not None:
            members = [j for j in range(mwt.start, mwt.end + 1) if j in idset]
            if members:
                units.append((mwt.misc, members))
                k += len(members)
                continue
        units.append((tok_by_id[tid].misc, [tid]))
        k += 1

    token_word: dict[int, int] = {}
    w = 0
    for u_idx, (misc, members) in enumerate(units):
        for mid in members:
            token_word[mid] = w
        if u_idx < len(units) - 1 and not _no_space_after(misc):
            w += 1
    n_words = (w + 1) if units else 0
    return token_word, n_words


def tree_depth(sentence: Sentence) -> int:
    """Max root-to-token depth of the dependency tree (cheap difficulty proxy)."""
    head = {t.id: t.head for t in sentence.tokens}
    best = 0
    for tid in head:
        d, cur, seen = 0, tid, set()
        while cur and cur != 0 and cur not in seen:
            seen.add(cur)
            cur = head.get(cur, 0)
            d += 1
            if d > 200:  # cycle guard
                break
        best = max(best, d)
    return best
