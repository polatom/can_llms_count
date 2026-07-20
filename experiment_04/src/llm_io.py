"""Shared I/O helpers for the exp_04 LLM harness: .env, prompt assembly, parsing.

Adapted from experiment_01/src/llm_io.py. Differences: (a) prompt files carry a
leading `#` comment header (design provenance) — it sits before `### SYSTEM` and
is dropped by the section split, but the sha is computed over the SECTIONS only,
so editing comments does not change the recorded prompt identity; (b) the answer
schema is `{"pairs": [...], "has_violation": bool}` — nested, so extraction uses
a balanced-brace scanner and takes the LAST parseable object with the expected
keys (R2 emits an enumeration scratchpad before the JSON). Stdlib only.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
from functools import lru_cache


def load_env(path: str) -> dict[str, str]:
    env: dict[str, str] = {}
    if not os.path.exists(path):
        return env
    for line in open(path, encoding="utf-8"):
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        env[k.strip()] = v.strip().strip('"').strip("'")
    return env


def _split_template(text: str) -> tuple[str, str, str]:
    parts = re.split(r"^### (SYSTEM|FEWSHOT|USER)\s*$", text, flags=re.MULTILINE)
    section = {}
    for i in range(1, len(parts), 2):
        section[parts[i]] = parts[i + 1].strip("\n")
    return section.get("SYSTEM", ""), section.get("FEWSHOT", ""), section.get("USER", "")


@lru_cache(maxsize=None)
def load_template(path: str) -> tuple[str, str, str, str]:
    raw = open(path, encoding="utf-8").read()
    sysm, few, user = _split_template(raw)
    sha = hashlib.sha256(("\n§\n".join([sysm, few, user])).encode("utf-8")).hexdigest()[:16]
    return sysm, few, user, sha


def build_messages(template_path: str, sentence: str) -> tuple[list[dict], str]:
    sysm, few, user_tmpl, sha = load_template(template_path)
    filled = user_tmpl.replace("{SENTENCE}", sentence)
    user_content = (few + "\n\n" + filled).strip() if few else filled
    return ([{"role": "system", "content": sysm},
             {"role": "user", "content": user_content}], sha)


def _json_candidates(text: str):
    """Yield balanced {...} substrings, restarting parse state at each '{'.

    A global left-to-right scan breaks when the surrounding PROSE contains an
    odd number of ASCII double-quotes (e.g. the model echoing „kdo, co?" test
    questions): the string state flips and real JSON braces become invisible.
    Scanning from each '{' with fresh state is immune to prose quoting; invalid
    spans are filtered by json.loads in the caller.
    """
    for start in (i for i, c in enumerate(text) if c == "{"):
        depth = 0
        in_str = False
        esc = False
        for j in range(start, len(text)):
            ch = text[j]
            if in_str:
                if esc:
                    esc = False
                elif ch == "\\":
                    esc = True
                elif ch == '"':
                    in_str = False
                continue
            if ch == '"':
                in_str = True
            elif ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    yield text[start:j + 1]
                    break


def parse_completion(text: str | None) -> dict:
    """Extract the LAST parseable answer object with the expected keys.

    Returns {"parse_status": "ok"|"malformed", "pairs": [...]|None,
             "has_violation": bool|None}. Authoritative scoring re-parses the
    stored completion_text with this same function.
    """
    out: dict = {"parse_status": "malformed", "pairs": None, "has_violation": None}
    if not text:
        return out
    best = None
    for cand in _json_candidates(text):
        try:
            obj = json.loads(cand)
        except (json.JSONDecodeError, ValueError):
            continue
        if isinstance(obj, dict) and ("has_violation" in obj or "pairs" in obj):
            best = obj
    if best is None:
        return out
    pairs = best.get("pairs")
    if not isinstance(pairs, list):
        pairs = None
    out.update({
        "parse_status": "ok" if pairs is not None and "has_violation" in best else "partial",
        "pairs": pairs,
        "has_violation": best.get("has_violation")
        if isinstance(best.get("has_violation"), bool) else None,
    })
    return out
