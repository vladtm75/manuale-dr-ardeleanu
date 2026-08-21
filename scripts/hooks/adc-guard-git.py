#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Hook PreToolUse(Bash): oprește comenzile git care amestecă sesiunile paralele.

Repo-ul e deschis simultan de mai multe sesiuni Claude (checkout principal + worktree-uri).
Comenzile de mai jos au produs deja incidente reale (muncă necomisă a unei sesiuni comisă de
alta, numere de revizie dublate, commit-uri direct pe main), așa că sunt blocate aici, nu
lăsate pe seama memoriei fiecărei sesiuni.

Ieșire: cod 2 = blocat, mesajul de pe stderr ajunge la Claude. Orice altceva = permis.
"""
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

    if cmd in ("commit", "push") and br in ("main", "master"):
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
