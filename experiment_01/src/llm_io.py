"""Shared I/O helpers for the LLM harness: .env, prompt assembly, response parsing.

Kept separate so `run_llm.py` (calls models) and `score.py` (parses stored raw)
use the *same* parsing logic. Stdlib only.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
from functools import lru_cache


# ---------------------------------------------------------------- .env / config
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


# ---------------------------------------------------------------- prompt assembly
def _split_template(text: str) -> tuple[str, str, str]:
    """Return (system, fewshot, user) from a ### SYSTEM/### FEWSHOT/### USER file."""
    parts = re.split(r"^### (SYSTEM|FEWSHOT|USER)\s*$", text, flags=re.MULTILINE)
    # parts = ['', 'SYSTEM', <sys>, 'FEWSHOT', <few>, 'USER', <user>]
    section = {}
    for i in range(1, len(parts), 2):
        section[parts[i]] = parts[i + 1].strip("\n")
    return section.get("SYSTEM", ""), section.get("FEWSHOT", ""), section.get("USER", "")


@lru_cache(maxsize=None)
def load_template(path: str) -> tuple[str, str, str, str]:
    """Return (system, fewshot, user_template, sha256) for a prompt file."""
    raw = open(path, encoding="utf-8").read()
    sysm, few, user = _split_template(raw)
    sha = hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]
    return sysm, few, user, sha


def build_messages(template_path: str, *, sentence: str | None = None,
                   conllu: str | None = None) -> tuple[list[dict], str]:
    """Assemble chat messages for one item. Few-shot examples ride inline in the
    user turn (robust across the differing per-regime few-shot formats).

    Returns (messages, prompt_template_sha).
    """
    sysm, few, user_tmpl, sha = load_template(template_path)
    filled = user_tmpl
    if sentence is not None:
        filled = filled.replace("{SENTENCE}", sentence)
    if conllu is not None:
        filled = filled.replace("{CONLLU}", conllu)
    user_content = (few + "\n\n" + filled).strip() if few else filled
    messages = [
        {"role": "system", "content": sysm},
        {"role": "user", "content": user_content},
    ]
    return messages, sha


# ---------------------------------------------------------------- conllu blocks
@lru_cache(maxsize=None)
def _file_blocks(path: str) -> dict:
    blocks, sid, buf = {}, None, []
    for line in open(path, encoding="utf-8", errors="replace"):
        if line.strip() == "":
            if sid is not None:
                blocks[sid] = "".join(buf)
            sid, buf = None, []
            continue
        if line.startswith("# sent_id"):
            sid = line.split("=", 1)[1].strip()
        buf.append(line)
    if sid is not None:
        blocks[sid] = "".join(buf)
    return blocks


def conllu_block(kuk_root: str, source_file: str, sent_id: str) -> str:
    return _file_blocks(os.path.join(kuk_root, source_file)).get(sent_id, "")


# ---------------------------------------------------------------- response parsing
_JSON_RE = re.compile(r"\{[^{}]*\}")
_CONLLU_RE = re.compile(r"<conllu>(.*?)</conllu>", re.DOTALL)


def parse_completion(text: str) -> dict:
    """Best-effort extraction of the answer JSON (and CoNLL-U block, if present).

    Authoritative scoring lives in score.py; this is a convenience parse stored
    alongside the raw trace. Returns dict with parse_status.
    """
    out: dict = {"parse_status": "malformed"}
    if text is None:
        return out
    m = _CONLLU_RE.search(text)
    if m:
        out["conllu_emitted"] = m.group(1).strip()
    # take the LAST json-looking object that has 'vzdalenost'
    best = None
    for jm in _JSON_RE.finditer(text):
        try:
            obj = json.loads(jm.group(0))
        except (json.JSONDecodeError, ValueError):
            continue
        if isinstance(obj, dict) and "vzdalenost" in obj:
            best = obj
    if best is not None:
        out.update(
            {
                "podmet": best.get("podmet"),
                "podmet_index": best.get("podmet_index"),
                "prisudek": best.get("prisudek"),
                "prisudek_index": best.get("prisudek_index"),
                "vzdalenost": best.get("vzdalenost"),
                "parse_status": "ok",
            }
        )
    return out
