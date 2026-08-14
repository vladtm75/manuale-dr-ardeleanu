#!/usr/bin/env python3
"""
Regenerează medici/revision-map.js — harta „revizie → commit → subcapitole
schimbate" folosită de toggle-urile „versiune anterioară" din Registrul de
modificări al Manualului Medicului.

De ce există: manual-data.js nu ține un istoric propriu al textului vechi;
toggle-ul aduce textul „dinainte" live de pe GitHub (raw.githubusercontent.com),
la commit-ul exact dinaintea reviziei respective. Acest script identifică acel
commit pentru fiecare rând din Registru, citind convenția din mesajele de
commit: „Adaugă rev. N (dată) în Registrul de modificări."

Rulează-l din rădăcina repo-ului, după orice PR care adaugă un rând nou în
Registrul de modificări al Manualului Medicului:

    python3 scripts/gen-medici-revision-map.py

Rescrie complet medici/revision-map.js (commit-uiește fișierul rezultat).
"""
import json
import re
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
MANUAL_DATA_PATH = "medici/manual-data.js"
OUTPUT_PATH = REPO_ROOT / "medici" / "revision-map.js"

# Revizii care nu primesc toggle, deși au commit asociat:
#   - nu au o stare "dinainte" cunoscută (originea manualului), sau
#   - sunt reorganizări structurale (renumerotare) fără diferență reală de text.
# Actualizează manual această listă dacă apare un caz similar cu rev. 28
# (renumerotare de capitole, fără schimbare de conținut de fond).
STRUCTURAL_ONLY_REVISIONS = {28}


def git(*args):
    result = subprocess.run(
        ["git", "-C", str(REPO_ROOT)] + list(args),
        capture_output=True, text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)} failed: {result.stderr}")
    return result.stdout


def load_manual_at(commit):
    raw = git("show", f"{commit}:{MANUAL_DATA_PATH}")
    body = raw[raw.index("=") + 1:].strip()
    if body.endswith(";"):
        body = body[:-1]
    return json.loads(body)


def index_subs(data):
    idx = {}
    for ch in data["chapters"]:
        for sub in ch["subs"]:
            idx[(ch["id"], sub["id"])] = sub
    return idx


REV_TAG_RE = re.compile(r"rev\.\s*(\d+)")


def find_revisions_for_commit(message):
    """Întoarce lista de numere de revizie asociate acestui commit.

    Majoritatea commit-urilor ating o singură revizie — ultima mențiune
    "rev. N" din mesaj e cea corectă (mențiunile anterioare pot fi
    revendicări vechi, dinainte de rezolvarea conflictelor de merge).
    Dacă ultima linie relevantă enumeră explicit mai multe revizii
    ("rev. 26 și rev. 27"), le asociem pe toate acestui commit.
    """
    matches = list(REV_TAG_RE.finditer(message))
    if not matches:
        return []
    last_line = message[:matches[-1].end()].splitlines()[-1]
    if " și rev" in last_line or "și rev." in last_line:
        nums = REV_TAG_RE.findall(last_line)
        return sorted(set(int(n) for n in nums))
    return [int(matches[-1].group(1))]


def main():
    commit_hashes = git("log", "--follow", "--format=%H", "--", MANUAL_DATA_PATH).split()
    if not commit_hashes:
        print("Niciun commit găsit pentru manual-data.js — abandonez.", file=sys.stderr)
        sys.exit(1)

    rev_to_commit = {}
    for h in commit_hashes:
        message = git("log", "-1", "--format=%B", h)
        for rev in find_revisions_for_commit(message):
            rev_to_commit.setdefault(rev, h)

    if not rev_to_commit:
        print("Nicio revizie identificată din mesajele de commit.", file=sys.stderr)
        sys.exit(1)

    max_rev = max(rev_to_commit)
    entries = {}
    skipped = []
    missing = []

    for rev in range(2, max_rev + 1):
        if rev in STRUCTURAL_ONLY_REVISIONS:
            skipped.append(rev)
            continue
        commit = rev_to_commit.get(rev)
        if not commit:
            missing.append(rev)
            continue
        parent = git("rev-parse", f"{commit}^").strip()
        try:
            cur = load_manual_at(commit)
            prev = load_manual_at(parent)
        except Exception as exc:
            print(f"  ! rev {rev}: eroare la citirea manual-data.js ({exc}) — sar peste", file=sys.stderr)
            missing.append(rev)
            continue
        cur_idx = index_subs(cur)
        prev_idx = index_subs(prev)
        changed = []
        for key in sorted(set(cur_idx) | set(prev_idx)):
            cur_sub = cur_idx.get(key)
            prev_sub = prev_idx.get(key)
            if (cur_sub or {}).get("html") != (prev_sub or {}).get("html"):
                changed.append({
                    "chapter": key[0],
                    "id": key[1],
                    "title": (prev_sub or cur_sub or {}).get("t", ""),
                })
        if not changed:
            print(f"  ! rev {rev}: niciun subcapitol schimbat detectat (commit {commit[:7]}) — sar peste", file=sys.stderr)
            missing.append(rev)
            continue
        entries[str(rev)] = {
            "commit": commit,
            "before": parent,
            "subs": changed,
        }

    js = (
        "// Generat automat de scripts/gen-medici-revision-map.py — NU edita manual.\n"
        "// Regenerează după orice PR care adaugă un rând nou în Registrul de modificări:\n"
        "//   python3 scripts/gen-medici-revision-map.py\n"
        "window.MEDICI_REVISION_MAP = "
        + json.dumps(entries, ensure_ascii=False, indent=2)
        + ";\n"
    )
    OUTPUT_PATH.write_text(js, encoding="utf-8")

    print(f"Scris {OUTPUT_PATH} cu {len(entries)} revizii mapate.")
    if skipped:
        print(f"Excluse explicit (structurale, fără toggle): {sorted(skipped)}")
    if missing:
        print(f"ATENȚIE — fără mapare (verifică manual): {sorted(missing)}", file=sys.stderr)


if __name__ == "__main__":
    main()
