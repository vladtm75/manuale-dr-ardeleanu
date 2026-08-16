#!/usr/bin/env python3
"""
Regenerează revision-map.js pentru manualele cu conținut HTML direct în
fișier (Asistenți, Registratori, Medici — toate trei folosesc același
sistem de la migrarea Manualului Medicului la HTML static, rev. 30).

De ce există: paginile nu țin un istoric propriu al textului vechi; toggle-ul
"versiune anterioară" din Registrul de modificări aduce textul „dinainte"
live de pe GitHub (raw.githubusercontent.com), la commit-ul exact dinaintea
reviziei. Acest script identifică acel commit pentru fiecare rând din
Registru, citind convenția din mesajele de commit: „rev. N" (ex. "consemnat
rev. 2 în Registrul de modificări").

Secțiunile sunt identificate generic după `<h2 id="...">`/`<h3 id="...">` —
conținutul unei secțiuni e tot ce stă între ea și următorul heading cu id,
indiferent de nivel. Nu necesită nicio modificare la structura manualului.

Rulează din rădăcina repo-ului, pentru un manual anume:

    python3 scripts/gen-html-manual-revision-map.py asistenti
    python3 scripts/gen-html-manual-revision-map.py registratori

Rescrie complet <manual>/revision-map.js (comite fișierul rezultat).
"""
import json
import re
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

MANUALS = {
    "asistenti": {
        "path": "asistenti/Manualul Asistentului Medical.html",
        "output": "asistenti/revision-map.js",
        "global_var": "ASISTENTI_REVISION_MAP",
    },
    "registratori": {
        "path": "registratori/Manualul Registratorului Medical.html",
        "output": "registratori/revision-map.js",
        "global_var": "REGISTRATORI_REVISION_MAP",
    },
    "medici": {
        "path": "medici/Manualul Medicului.html",
        "output": "medici/revision-map.js",
        "global_var": "MEDICI_REVISION_MAP",
    },
}

HEADING_RE = re.compile(r'<h[23][^>]*\sid="([a-zA-Z0-9\-]+)"[^>]*>(.*?)</h[23]>', re.DOTALL)
REV_TAG_RE = re.compile(r"rev\.\s*(\d+)")

# secțiuni care nu sunt "conținut" propriu-zis — se schimbă mecanic la fiecare
# revizie (tabelul de registru crește un rând) sau nu au sens comparate izolat.
EXCLUDE_IDS = {"registru"}


def git(*args):
    result = subprocess.run(
        ["git", "-C", str(REPO_ROOT)] + list(args),
        capture_output=True, text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)} failed: {result.stderr}")
    return result.stdout


def load_file_at(commit, path):
    return git("show", f"{commit}:{path}")


def extract_sections(html_text):
    matches = list(HEADING_RE.finditer(html_text))
    sections = {}
    for i, m in enumerate(matches):
        sec_id = m.group(1)
        title = re.sub(r"<[^>]+>", "", m.group(2)).strip()
        title = re.sub(r"^(\d+(?:\.\d+)?\.)(?=\S)", r"\1 ", title)
        content_start = m.end()
        content_end = matches[i + 1].start() if i + 1 < len(matches) else len(html_text)
        # dacă același id apare de două ori (nu ar trebui), păstrăm prima apariție
        sections.setdefault(sec_id, {"title": title, "html": html_text[content_start:content_end]})
    return sections


def find_revisions_for_commit(message):
    matches = list(REV_TAG_RE.finditer(message))
    if not matches:
        return []
    last_line = message[:matches[-1].end()].splitlines()[-1]
    if " și rev" in last_line or "și rev." in last_line:
        nums = REV_TAG_RE.findall(last_line)
        return sorted(set(int(n) for n in nums))
    return [int(matches[-1].group(1))]


def main():
    if len(sys.argv) != 2 or sys.argv[1] not in MANUALS:
        print(f"Utilizare: python3 {sys.argv[0]} <{'|'.join(MANUALS)}>", file=sys.stderr)
        sys.exit(1)
    cfg = MANUALS[sys.argv[1]]
    path = cfg["path"]
    output_path = REPO_ROOT / cfg["output"]

    commit_hashes = git("log", "--follow", "--format=%H", "--", path).split()
    if not commit_hashes:
        print(f"Niciun commit găsit pentru {path} — abandonez.", file=sys.stderr)
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
    missing = []

    for rev in range(2, max_rev + 1):
        commit = rev_to_commit.get(rev)
        if not commit:
            missing.append(rev)
            continue
        parent = git("rev-parse", f"{commit}^").strip()
        try:
            cur_text = load_file_at(commit, path)
            prev_text = load_file_at(parent, path)
        except Exception as exc:
            print(f"  ! rev {rev}: eroare la citire ({exc}) — sar peste", file=sys.stderr)
            missing.append(rev)
            continue
        cur = extract_sections(cur_text)
        prev = extract_sections(prev_text)
        changed = []
        for sec_id in sorted(set(cur) | set(prev)):
            if sec_id in EXCLUDE_IDS:
                continue
            cur_html = cur.get(sec_id, {}).get("html")
            prev_html = prev.get(sec_id, {}).get("html")
            if cur_html != prev_html:
                title = (prev.get(sec_id) or cur.get(sec_id) or {}).get("title", "")
                changed.append({"id": sec_id, "title": title})
        if not changed:
            print(f"  ! rev {rev}: nicio secțiune schimbată detectată (commit {commit[:7]}) — sar peste", file=sys.stderr)
            missing.append(rev)
            continue
        entries[str(rev)] = {"commit": commit, "before": parent, "sections": changed}

    js = (
        "// Generat automat de scripts/gen-html-manual-revision-map.py — NU edita manual.\n"
        f"// Regenerează după orice PR care adaugă un rând nou în Registrul de modificări:\n"
        f"//   python3 scripts/gen-html-manual-revision-map.py {sys.argv[1]}\n"
        f"window.{cfg['global_var']} = "
        + json.dumps(entries, ensure_ascii=False, indent=2)
        + ";\n"
    )
    output_path.write_text(js, encoding="utf-8")

    print(f"Scris {output_path} cu {len(entries)} revizii mapate.")
    if missing:
        print(f"ATENȚIE — fără mapare (verifică manual): {sorted(missing)}", file=sys.stderr)


if __name__ == "__main__":
    main()
