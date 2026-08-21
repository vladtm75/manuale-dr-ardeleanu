#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Hook PreToolUse(Bash): oprește comenzile git care amestecă sesiunile paralele.

Repo-ul e deschis simultan de mai multe sesiuni Claude (checkout principal + worktree-uri).
Comenzile de mai jos au produs deja incidente reale (muncă necomisă a unei sesiuni comisă de
alta, numere de revizie dublate, commit-uri direct pe main), așa că sunt blocate aici, nu
lăsate pe seama memoriei fiecărei sesiuni.

Ieșire: cod 2 = blocat, mesajul de pe stderr ajunge la Claude. Orice altceva = permis.
"""
import importlib.util
import json
import os
import re
import shlex
import subprocess
import sys

SPLIT = re.compile(r"&&|\|\||;|\n|\|")


def git_out(args, cwd):
    p = subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True)
    return p.stdout.strip() if p.returncode == 0 else ""


def branch_of(cwd):
    return git_out(["symbolic-ref", "--short", "-q", "HEAD"], cwd)


def tracked_dirty(cwd):
    # fără .strip() pe ieșire: primul caracter al fiecărui rând e semnificativ (" M cale")
    p = subprocess.run(["git", "status", "--porcelain", "-uno"], cwd=cwd,
                       capture_output=True, text=True)
    if p.returncode:
        return []
    return [l[3:] for l in p.stdout.splitlines() if l.strip()]


def block(msg):
    print(msg, file=sys.stderr)
    sys.exit(2)


def delete_only_push(flags, pos):
    """True dacă `git push` doar șterge referințe (`--delete ramura` sau `origin :ramura`).

    Un push de ștergere nu publică nimic și nu atinge ramura pe care stă HEAD, deci nu are de ce
    să fie oprit de regula „nimic direct pe main”. Ștergerea lui main/master rămâne blocată mai
    jos, de verificarea țintelor.
    """
    if any(f in ("-d", "--delete") for f in flags):
        return True
    refspecs = pos[1:]  # pos[0] = remote-ul
    return bool(refspecs) and all(r.startswith(":") for r in refspecs)


def check(tokens, cwd):
    # git -C <cale> ...
    i = 1
    while i < len(tokens) - 1 and tokens[i] in ("-C", "--git-dir", "--work-tree"):
        if tokens[i] == "-C":
            cwd = tokens[i + 1] if os.path.isabs(tokens[i + 1]) else os.path.join(cwd, tokens[i + 1])
        i += 2
    rest = tokens[i:]
    if not rest:
        return
    cmd, args = rest[0], rest[1:]
    flags = [a for a in args if a.startswith("-")]
    pos = [a for a in args if not a.startswith("-")]
    br = branch_of(cwd)
    dirty = None  # calculat leneș

    def is_dirty():
        nonlocal dirty
        if dirty is None:
            dirty = tracked_dirty(cwd)
        return dirty

    # ștergerea unei ramuri nu publică nimic: nu intră sub regula „nimic direct pe main”
    delete_push = cmd == "push" and delete_only_push(flags, pos)

    if cmd in ("commit", "push") and br in ("main", "master") and not delete_push:
        block(f"BLOCAT: `git {cmd}` cu HEAD pe „{br}”.\n"
              "Regula repo-ului: nimic direct pe main — mută-te pe o ramură edit/<nume>-<subiect> "
              "(ideal într-un worktree propriu: `python3 scripts/adc.py new-session vlad <subiect>`) "
              "și deschide Pull Request.")

    if cmd == "push":
        targets = " ".join(pos)
        if re.search(r"(^|\s|:)(main|master)(\s|$)", targets):
            block("BLOCAT: push direct în main/master. Publicarea se face doar prin Pull Request "
                  "aprobat de Vlad (`gh pr create --base main`).")
        if any(f in ("-f", "--force") or f.startswith("--force") for f in flags) and "--force-with-lease" not in flags:
            block("BLOCAT: `git push --force`. Pe un repo deschis de mai multe sesiuni forțarea poate "
                  "șterge commit-uri ale altei sesiuni. Folosește `--force-with-lease` și doar pe ramura ta.")

    if cmd == "add" and any(a in ("-A", "--all", "-u", "--update", ".", ":/", "*") for a in args):
        d = is_dirty()
        block("BLOCAT: `git add` în bloc (" + " ".join(a for a in args if a in ("-A", "--all", "-u", "--update", ".", ":/", "*")) + ").\n"
              f"În acest worktree sunt {len(d)} fișiere modificate: " + ", ".join(d[:6]) +
              ("…" if len(d) > 6 else "") + "\n"
              "Unele pot fi ale altei sesiuni Claude care lucrează în paralel (incident real: PR #88). "
              "Adaugă explicit doar fișierele pe care le-ai editat tu: `git add \"cale/fișier.html\"`.")

    if cmd == "commit" and any(a in ("-a", "--all") or (a.startswith("-") and not a.startswith("--") and "a" in a[1:]) for a in args):
        block("BLOCAT: `git commit -a` comite tot ce e modificat în worktree, inclusiv munca altei "
              "sesiuni paralele. Pune în index doar fișierele tale (`git add \"cale\"`) și apoi "
              "`git commit -m \"…\"`.")

    if cmd in ("commit",):
        check_registry(cwd, [a for a in pos if a not in ("--",)])

    if cmd in ("checkout", "switch") and "--" not in args:
        creates = any(f in ("-b", "-B", "-c", "-C") for f in flags)
        if not creates and pos and is_dirty():
            target = pos[0]
            if not os.path.exists(os.path.join(cwd, target)):
                block(f"BLOCAT: `git {cmd} {target}` cu {len(is_dirty())} fișiere modificate necomise "
                      f"({', '.join(is_dirty()[:5])}).\n"
                      "git duce modificările necomise cu el pe ramura nouă — așa a ajuns munca unei sesiuni "
                      "comisă de alta. Fie comiți/`git stash` mai întâi, fie (recomandat) lucrezi în paralel "
                      "cu `python3 scripts/adc.py new-session vlad <subiect>`, care creează un worktree separat.")

    if cmd in ("reset", "clean", "restore") and is_dirty():
        destructive = (cmd == "reset" and "--hard" in flags) or \
                      (cmd == "clean" and any("f" in f for f in flags)) or \
                      (cmd == "restore" and (not pos or pos[0] in (".", ":/")))
        if destructive:
            block(f"BLOCAT: `git {cmd}` distructiv cu {len(is_dirty())} fișiere modificate în worktree "
                  f"({', '.join(is_dirty()[:5])}).\n"
                  "Pot fi modificări nesalvate ale altei sesiuni. Dacă e intenționat, rulează comanda "
                  "manual în terminal, după ce confirmi cu Vlad ce se pierde.")


def repo_root(cwd):
    return git_out(["rev-parse", "--show-toplevel"], cwd)


def load_adc(root):
    """Încarcă scripts/adc.py ca modul, ca să nu dublăm logica registrelor."""
    path = os.path.join(root, "scripts", "adc.py")
    if not os.path.exists(path):
        return None
    spec = importlib.util.spec_from_file_location("adc_lib", path)
    mod = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(mod)
    except Exception:
        return None
    return mod


def staged_docs(cwd, positional, adc):
    """Documentele cu registru care intră în acest commit (index + căi date explicit)."""
    out = git_out(["diff", "--cached", "--name-only"], cwd).splitlines()
    files = {l.strip() for l in out if l.strip()}
    root = repo_root(cwd)
    for a in positional:
        cand = os.path.relpath(os.path.abspath(os.path.join(cwd, a)), root) if root else a
        files.add(cand.replace(os.sep, "/"))
    return [adc.PATH2KEY[f] for f in files if f in adc.PATH2KEY]


def doc_text(root, path):
    """Conținutul care va fi comis: versiunea din index, altfel din worktree."""
    t = git_out(["show", f":{path}"], root)
    if t:
        return t
    try:
        return open(os.path.join(root, path), encoding="utf-8").read()
    except Exception:
        return ""


def check_registry(cwd, positional):
    """Blochează un commit care ar duplica un număr de revizie deja consumat altundeva."""
    root = repo_root(cwd)
    if not root:
        return
    adc = load_adc(root)
    if adc is None:
        return
    try:
        os.chdir(root)  # funcțiile din adc.py rulează în cwd-ul procesului
    except OSError:
        return
    branch = branch_of(root)
    for key in staged_docs(root, positional, adc):
        path, label, _ = adc.DOCS[key]
        text = doc_text(root, path)
        top = adc.top_row_rev(text)
        if not top:
            continue
        # fără fetch: hook-ul nu face rețea. Folosim starea de la ultimul fetch.
        used = adc.used_revs(key, fetch=False)
        others = []
        for where in used.get(top, []):
            if where == "origin/main":
                if top <= adc.max_rev(adc.blob("origin/main", path)):
                    others.append("origin/main (revizie deja publicată)")
            elif branch and branch in where:
                continue  # propria ramură / propria rezervare
            else:
                others.append(where)
        if others:
            libera = adc.next_free(key, fetch=False)[0]
            block(f"BLOCAT: coliziune de număr de revizie în {label}.\n"
                  f"Rândul de sus din registru e rev. {top}, dar rev. {top} e deja consumat de: "
                  f"{', '.join(sorted(set(others)))}.\n"
                  f"Treci rândul (și „Revizia curentă”) pe rev. {libera}, apoi comite din nou. "
                  f"Dacă numărul liber pare greșit, rulează `python3 scripts/adc.py status` "
                  f"(hook-ul nu face fetch — poate fi nevoie de `git fetch origin`).")


def main():
    try:
        data = json.load(sys.stdin)
    except Exception:
        return
    if data.get("tool_name") != "Bash":
        return
    command = (data.get("tool_input") or {}).get("command") or ""
    cwd = data.get("cwd") or os.getcwd()
    for seg in SPLIT.split(command):
        seg = seg.strip()
        if not seg:
            continue
        try:
            tokens = shlex.split(seg)
        except ValueError:
            tokens = seg.split()
        # sări peste prefixe de tip `cd X`, `sudo`, variabile de mediu
        while tokens and (tokens[0] in ("sudo", "time", "nohup") or "=" in tokens[0].split("/")[0] and not tokens[0].startswith("git")):
            tokens = tokens[1:]
        if tokens and tokens[0] == "git":
            check(tokens, cwd)


if __name__ == "__main__":
    main()
