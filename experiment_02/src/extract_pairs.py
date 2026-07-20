"""Parser-arm extractor: METHODOLOGY.md §3 applied to a UD parse.

For one sentence, produce the set of subject–predicate pairs of finite clauses
with an overt nominal subject, the distance for each pair (whitespace words,
§3.4), the sentence verdict (violation ⇔ any d > T, T = 6, §3.5), plus the
phenomenon flags and metric-family statistics used by the audit gate (§4.1,
§4.3) and the post-hoc breakdowns (§7).

Definition recap (§3.1, Katka-signed):
- pair anchor = every ``nsubj``/``nsubj:pass`` edge (subject token -> clause
  head). Shared-subject predicate coordination therefore yields ONE pair
  (K6 provisional: only the first conjunct bears nsubj).
- measured predicate = the FINITE ELEMENT of the clause head's predicate
  complex: the aux/aux:pass/cop child with VerbForm=Fin if present (conditional
  Mood=Cnd preferred if — anomalously — several finite elements exist), else
  the clause head itself (finite verb or bare l-participle).
- aby/kdyby: the absorbed conditional ``by`` is a syntactic token inside a
  multiword token; word indices collapse it onto the surface conjunction word.
- csubj: no pair; counted. Non-verbal nsubj heads without copula/aux
  ("verbless clauses", e.g. headings like "Vstup zakázán" if parsed nominal):
  no pair; counted + logged for the annotation guidelines.

Stdlib-only.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from conllu_utils import Sentence, Token, assign_word_indices, tree_depth

T_LIMIT = 6  # §3.5: violation ⇔ d > T_LIMIT

_FIN = "VerbForm=Fin"
_PART = "VerbForm=Part"
_CONV = "VerbForm=Conv"
_CND = "Mood=Cnd"


@dataclass
class Pair:
    subj_tok_id: int
    subj_form: str
    subj_word_idx: int  # 1-based whitespace-word position
    pred_tok_id: int
    pred_form: str  # form of the measured predicate TOKEN (e.g. "by")
    pred_word_form: str  # surface word carrying it (e.g. "aby")
    pred_word_idx: int  # 1-based
    head_tok_id: int  # clause head the nsubj attaches to
    distance: int  # words strictly between, §3.4
    pred_is_cop: bool
    pred_is_aux: bool
    pred_mood_cnd: bool
    pred_in_mwt: bool  # measured predicate absorbed in a multiword token (aby/kdyby)
    subj_is_pass: bool  # nsubj:pass
    vs_order: bool  # predicate word precedes subject word
    anomalies: list[str] = field(default_factory=list)


@dataclass
class SentenceExtraction:
    pairs: list[Pair]
    verdict: bool  # any pair with distance > T_LIMIT
    n_words: int
    finite_clause_count: int  # candidate finite predicate complexes (silver approx.)
    pro_drop_clause_count: int  # finite complexes with no overt nsubj
    csubj_count: int
    nonverbal_nsubj_excluded: int  # nsubj edges dropped: non-verbal head, no aux/cop
    nonverbal_head_upos: list[str]  # UPOS of those dropped heads (audit)
    is_fragment: bool  # no finite predicate complex at all
    anomalies: list[str]
    family: dict  # §4.3 metric-family stats


def _children(sentence: Sentence) -> dict[int, list[Token]]:
    ch: dict[int, list[Token]] = {}
    for t in sentence.tokens:
        ch.setdefault(t.head, []).append(t)
    return ch


def _base(deprel: str) -> str:
    return deprel.split(":")[0]


def _finite_element(head: Token, kids: list[Token]) -> tuple[Token, bool, list[str]]:
    """The measured predicate token for a clause head (§3.1 mechanical rule).

    Returns (token, head_is_fallback, anomalies).
    """
    fins = [
        c for c in kids
        if _base(c.deprel) in ("aux", "cop") and _FIN in c.feats
    ]
    if not fins:
        return head, True, []
    if len(fins) == 1:
        return fins[0], False, []
    # Anomalous: >1 finite aux/cop. Prefer the conditional; log it.
    anomaly = [f"multiple_finite_aux:{'+'.join(c.form for c in fins)}"]
    cnd = [c for c in fins if _CND in c.feats]
    pick = cnd[0] if cnd else min(fins, key=lambda c: c.id)
    return pick, False, anomaly


def _is_finite_complex(head: Token, kids: list[Token]) -> bool:
    """Is this head a finite predicate complex (§3: 'finite clause')?

    True if it has a finite aux/cop child, or is itself a finite verb or a bare
    l-participle (3rd-person past). Converbs and bare infinitives are not.
    """
    if any(_base(c.deprel) in ("aux", "cop") and _FIN in c.feats for c in kids):
        return True
    if head.upos == "VERB" and (_FIN in head.feats or _PART in head.feats) and _CONV not in head.feats:
        return True
    return False


def _mwt_membership(sentence: Sentence) -> dict[int, str]:
    """token id -> surface form of the MWT it belongs to (if any)."""
    out: dict[int, str] = {}
    for m in sentence.mwts:
        for tid in range(m.start, m.end + 1):
            out[tid] = m.form
    return out


def extract(sentence: Sentence) -> SentenceExtraction:
    tok_by_id = {t.id: t for t in sentence.tokens}
    kids = _children(sentence)
    token_word, n_words = assign_word_indices(sentence)
    in_mwt = _mwt_membership(sentence)
    anomalies: list[str] = []

    # --- candidate finite predicate complexes (for clause counts / pro-drop / fragments)
    finite_heads: list[Token] = []
    for t in sentence.tokens:
        if _base(t.deprel) == "xcomp":
            continue  # controlled complement, shares the matrix subject
        if _is_finite_complex(t, kids.get(t.id, [])):
            finite_heads.append(t)

    # --- pairs: one per nsubj/nsubj:pass edge with a verbal/finite head complex
    pairs: list[Pair] = []
    csubj_count = 0
    nonverbal_excluded = 0
    nonverbal_upos: list[str] = []

    for t in sentence.tokens:
        b = _base(t.deprel)
        if b == "csubj":
            csubj_count += 1
            continue
        if b != "nsubj":
            continue
        head = tok_by_id.get(t.head)
        if head is None:
            anomalies.append(f"nsubj_head_missing:{t.id}")
            continue
        hkids = kids.get(head.id, [])
        has_fin_child = any(
            _base(c.deprel) in ("aux", "cop") and _FIN in c.feats for c in hkids
        )
        head_verbal = head.upos == "VERB" and _CONV not in head.feats
        if not has_fin_child and not head_verbal:
            # nominal/adjectival head without copula -> verbless clause, no pair (§3.3 note)
            nonverbal_excluded += 1
            nonverbal_upos.append(head.upos)
            continue

        pred, is_fallback, an = _finite_element(head, hkids)
        p_anoms = list(an)

        sw = token_word.get(t.id)
        pw = token_word.get(pred.id)
        if sw is None or pw is None:
            anomalies.append(f"word_index_missing:pair@{t.id}")
            continue
        if sw == pw:
            # subject and predicate share one surface word (should not happen)
            p_anoms.append("same_word_index")
            d = 0
        else:
            d = abs(sw - pw) - 1

        pred_word_form = in_mwt.get(pred.id, pred.form)
        pairs.append(
            Pair(
                subj_tok_id=t.id,
                subj_form=t.form,
                subj_word_idx=sw + 1,
                pred_tok_id=pred.id,
                pred_form=pred.form,
                pred_word_form=pred_word_form,
                pred_word_idx=pw + 1,
                head_tok_id=head.id,
                distance=d,
                pred_is_cop=(not is_fallback) and _base(pred.deprel) == "cop",
                pred_is_aux=(not is_fallback) and _base(pred.deprel) == "aux",
                pred_mood_cnd=_CND in pred.feats,
                pred_in_mwt=pred.id in in_mwt,
                subj_is_pass=t.deprel.startswith("nsubj:pass"),
                vs_order=pw < sw,
                anomalies=p_anoms,
            )
        )

    subj_head_ids = {p.head_tok_id for p in pairs}
    pro_drop = sum(1 for h in finite_heads if h.id not in subj_head_ids
                   and not any(_base(c.deprel) == "csubj" for c in kids.get(h.id, [])))

    # --- §4.3 metric family (silver, per sentence)
    family = {
        "n_words": n_words,
        "tree_depth": tree_depth(sentence),
        "subordinate_clauses": sum(
            1 for t in sentence.tokens if _base(t.deprel) in ("advcl", "acl", "ccomp", "csubj")
        ),
        "coordinations": sum(1 for t in sentence.tokens if _base(t.deprel) == "conj"),
        "passives": sum(
            1 for t in sentence.tokens
            if t.deprel.startswith("nsubj:pass") or t.deprel.startswith("aux:pass")
        ),
        "max_pair_distance": max((p.distance for p in pairs), default=None),
    }

    return SentenceExtraction(
        pairs=pairs,
        verdict=any(p.distance > T_LIMIT for p in pairs),
        n_words=n_words,
        finite_clause_count=len(finite_heads),
        pro_drop_clause_count=pro_drop,
        csubj_count=csubj_count,
        nonverbal_nsubj_excluded=nonverbal_excluded,
        nonverbal_head_upos=nonverbal_upos,
        is_fragment=len(finite_heads) == 0,
        anomalies=anomalies,
        family=family,
    )


def extraction_to_dict(uid: str, subcorpus: str, ext: SentenceExtraction) -> dict:
    """JSON-serializable record for silver_pairs.jsonl."""
    return {
        "uid": uid,
        "subcorpus": subcorpus,
        "verdict": ext.verdict,
        "n_words": ext.n_words,
        "finite_clause_count": ext.finite_clause_count,
        "pro_drop_clause_count": ext.pro_drop_clause_count,
        "csubj_count": ext.csubj_count,
        "nonverbal_nsubj_excluded": ext.nonverbal_nsubj_excluded,
        "nonverbal_head_upos": ext.nonverbal_head_upos,
        "is_fragment": ext.is_fragment,
        "anomalies": ext.anomalies,
        "family": ext.family,
        "pairs": [
            {
                "subj_form": p.subj_form,
                "subj_word_idx": p.subj_word_idx,
                "pred_form": p.pred_form,
                "pred_word_form": p.pred_word_form,
                "pred_word_idx": p.pred_word_idx,
                "distance": p.distance,
                "pred_is_cop": p.pred_is_cop,
                "pred_is_aux": p.pred_is_aux,
                "pred_mood_cnd": p.pred_mood_cnd,
                "pred_in_mwt": p.pred_in_mwt,
                "subj_is_pass": p.subj_is_pass,
                "vs_order": p.vs_order,
                "anomalies": p.anomalies,
            }
            for p in ext.pairs
        ],
    }
