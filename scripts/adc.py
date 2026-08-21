#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""adc.py — unealta de coordonare a sesiunilor paralele pe repo-ul manuale-dr-ardeleanu.

Subcomenzi:
  status                  — cine lucrează pe ce (worktree-uri, ramuri, rezervări de revizie)
  next <doc>              — următorul număr de revizie liber pentru un document
  claim <doc> [--nota T]  — rezervă numărul următor pentru ramura curentă
  release <doc>           — eliberează rezervarea ramurii curente
  preflight               — verificările obligatorii înainte de Pull Request
  new-session <nume> <subiect> — creează worktree + ramură nouă, pornind de la origin/main

Rezervările se scriu în $(git rev-parse --git-common-dir)/adc-rev-claims.json — director
comun tuturor worktree-urilor aceluiași repo, deci vizibil din toate sesiunile locale.
"""
import argparse
import json
import os
import re
import subprocess
import sys
from datetime import date

# key -> (cale, denumire, nume-manual pentru gen-html-manual-revision-map.py sau None)
DOCS = {
    "asistenti":   ("asistenti/Manualul Asistentului Medical.html",          "Manualul Asistentului Medical",   "asistenti"),
    "medici":      ("medici/Manualul Medicului.html",                        "Manualul Medicului",              "medici"),
    "registratori":("registratori/Manualul Registratorului Medical.html",    "Manualul Registratorului Medical","registratori"),
    "roi":         ("roi/Regulamentul de Organizare Interna.html",           "Regulament Intern (ADC-RI)",      None),
    "proc-ben":    ("proceduri/ADC-BEN-01_Procedura_Beneficii.html",         "Procedura Beneficii (ADC-BEN-01)",None),
    "proc-reg":    ("proceduri/ADC-REG-01_Procedura_Registrul_Online.html",  "Procedura Registrul Online (ADC-REG-01)", None),
}
PATH2KEY = {v[0]: k for k, v in DOCS.items()}

C_RED, C_YEL, C_GRN, C_DIM, C_OFF = "\033[31m", "\033[33m", "\033[32m", "\033[2m", "\033[0m"
if not sys.stdout.isatty():
    C_RED = C_YEL = C_GRN = C_DIM = C_OFF = ""

RE_CURENT = re.compile(r"Revizia curent[ăa]:\s*<strong>rev\.\s*(\d+)</strong>")
RE_ROW = re.compile(r"<tr[^>]*>\s*<td>(\d+)</td>\s*<td>")


def sh(args, cwd=None, check=False):
    p = subprocess.run(args, cwd=cwd, capture_output=True, text=True)
    if check and p.returncode:
        raise SystemExit(f"{C_RED}Eroare la {' '.join(args)}:{C_OFF}\n{p.stderr.strip()}")
    return p.returncode, p.stdout, p.stderr


def git(*args, cwd=None, check=False):
    return sh(["git", *args], cwd=cwd, check=check)


def repo_root():
    rc, out, _ = git("rev-parse", "--show-toplevel")
    if rc:
        raise SystemExit("Nu ești într-un repo git.")
    return out.strip()


def common_dir():
    rc, out, _ = git("rev-parse", "--path-format=absolute", "--git-common-dir")
    return out.strip()


def claims_path():
    return os.path.join(common_dir(), "adc-rev-claims.json")


def load_claims():
    try:
        with open(claims_path(), encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def save_claims(data):
    with open(claims_path(), "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=1, sort_keys=True)


def current_branch(cwd=None):
    rc, out, _ = git("symbolic-ref", "--short", "-q", "HEAD", cwd=cwd)
    return out.strip() if rc == 0 else "(detached HEAD)"


def blob(ref, path):
    rc, out, _ = git("show", f"{ref}:{path}")
    return out if rc == 0 else None


def max_rev(text):
    """Cel mai mare număr de revizie găsit într-un document (antet + rândurile tabelului)."""
    if not text:
        return 0
    nums = [int(m.group(1)) for m in RE_CURENT.finditer(text)]
    nums += [int(m.group(1)) for m in RE_ROW.finditer(text)]
    return max(nums) if nums else 0


def top_row_rev(text):
    m = RE_ROW.search(text or "")
    return int(m.group(1)) if m else None


def header_rev(text):
    m = RE_CURENT.search(text or "")
    return int(m.group(1)) if m else None


def unmerged_refs():
    """Ramuri (locale + remote) care nu sunt încă în origin/main — pot conține revizii nepublicate."""
    refs = []
    for scope in (["--no-merged", "origin/main", "--format=%(refname:short)"],):
        for flag in ("-r", "-l"):
            rc, out, _ = git("branch", flag, *scope)
            if rc:
                continue
            for line in out.splitlines():
                name = line.strip()
                if not name or "HEAD" in name or name.endswith("/main"):
                    continue
                refs.append(name)
    return sorted(set(refs))


def used_revs(doc_key, fetch=True):
    """{numar: [unde]} — reviziile deja consumate pentru un document, oriunde în repo."""
    path = DOCS[doc_key][0]
    if fetch:
        git("fetch", "origin", "--prune", "-q")
    used = {}

    def add(n, where):
        if n:
            used.setdefault(n, []).append(where)

    add(max_rev(blob("origin/main", path)), "origin/main")
    for ref in unmerged_refs():
        t = blob(ref, path)
        if t is None:
            continue
        base = blob("origin/main", path)
        n = max_rev(t)
        if n and n > max_rev(base):
            add(n, ref)
    for branch, per_doc in load_claims().items():
        entry = per_doc.get(doc_key)
        if entry:
            add(entry["rev"], f"rezervat de {branch}")
    return used


def next_free(doc_key, fetch=True):
    used = used_revs(doc_key, fetch=fetch)
    return (max(used) + 1 if used else 1), used



# ------------------------------------------------- renumerotarea rândurilor de registru

RE_ATTR = re.compile(r'(data-rev(?:-old|-toggle|-body|-close)?=")(\d+)(")')
RE_REV_OLD = re.compile(r'<tr[^>]*data-rev-old="(\d+)"[^>]*>')


def registru_span(text):
    """Zona Registrului: de la paragraful «Revizia curentă» până la finalul tabelului."""
    m = RE_CURENT.search(text or "")
    if not m:
        return None
    end = text.find("</table>", m.end())
    return None if end == -1 else (m.start(), end + len("</table>"))


def registru_rows(text):
    """Rândurile Registrului, ca {num, body, start, end}.

    `body` e amprenta rândului — conținutul de după celula numărului, cu numerele din
    atribute neutralizate — ca să recunoaștem același rând chiar dacă a fost renumerotat.
    Exact asta lipsește dintr-o comparație pe numere: când două ramuri scriu amândouă
    „rev. N", numărul nu spune nimic despre identitatea rândului.
    `start`/`end` includ, dacă există, rândul-companion «versiune anterioară».
    """
    span = registru_span(text)
    if not span:
        return []
    r0, r1 = span
    region = text[r0:r1]
    rows = []
    for m in RE_ROW.finditer(region):
        num = int(m.group(1))
        row_end = region.find("</tr>", m.end())
        row_end = len(region) if row_end == -1 else row_end + len("</tr>")
        body = region[m.end():row_end]
        end = row_end
        nxt_at = region.find("<tr", row_end)
        if nxt_at != -1:
            nxt = RE_REV_OLD.match(region, nxt_at)
            if nxt and int(nxt.group(1)) == num:
                comp = region.find("</tr>", nxt.end())
                if comp != -1:
                    end = comp + len("</tr>")
        rows.append({"num": num,
                     "body": re.sub(r"\s+", " ", RE_ATTR.sub(
                         lambda x: x.group(1) + "#" + x.group(3), body)).strip(),
                     "start": r0 + m.start(), "end": r0 + end})
    return rows


def renumber_doc(text, targets):
    """Renumerotează exact rândurile date: targets = [(rând, număr_nou)].

    Se lucrează pe poziția rândului, nu pe numărul lui: în ramură pot coexista două
    rânduri cu același număr — al ramurii și unul venit din main — și numai al ramurii
    trebuie schimbat. Se merge de la sfârșit spre început, ca pozițiile să rămână valide.
    """
    for row, new in sorted(targets, key=lambda t: t[0]["start"], reverse=True):
        chunk = text[row["start"]:row["end"]]
        chunk = RE_ROW.sub(lambda m: m.group(0).replace(
            ">" + m.group(1) + "<", ">" + str(new) + "<", 1), chunk, count=1)
        chunk = RE_ATTR.sub(lambda m: m.group(1) + (
            str(new) if int(m.group(2)) == row["num"] else m.group(2)) + m.group(3), chunk)
        text = text[:row["start"]] + chunk + text[row["end"]:]
    nums = [r["num"] for r in registru_rows(text)]
    if nums:
        text = RE_CURENT.sub(
            "Revizia curentă: <strong>rev. %d</strong>" % max(nums), text, count=1)
    return text


def foreign_max(doc_key, branch, fetch):
    """Cea mai mare revizie consumată de altcineva: main, alte ramuri nemerge-uite,
    rezervările altor ramuri. Ce a scris ramura curentă nu se numără — pe acela îl mutăm."""
    mine = {branch, "origin/" + branch, "rezervat de " + branch}
    nums = [n for n, where in used_revs(doc_key, fetch=fetch).items()
            if any(w not in mine for w in where)]
    return max(nums) if nums else 0


def cmd_renumber(args):
    root, branch = repo_root(), current_branch()
    if args.doc:
        keys = [args.doc]
    else:
        rc, out, _ = git("diff", "--name-only", "origin/main")
        keys = [PATH2KEY[p] for p in out.splitlines() if p in PATH2KEY]
    if not keys:
        print(f"{C_DIM}Nicio modificare într-un document cu registru.{C_OFF}")
        return 0

    if not args.no_fetch:
        git("fetch", "origin", "--prune", "-q")

    rc, msgs, _ = git("log", "--format=%h %s", "origin/main..HEAD")
    changed, problems = [], []

    for key in keys:
        path, label, manual = DOCS[key]
        full = os.path.join(root, path)
        text = open(full, encoding="utf-8").read()
        base_rows = registru_rows(blob("origin/main", path) or "")
        rows = registru_rows(text)
        base_bodies = {r["body"] for r in base_rows}
        new_rows = sorted([r for r in rows if r["body"] not in base_bodies],
                          key=lambda r: r["num"])
        if not new_rows:
            print(f"{C_DIM}{label}: ramura nu adaugă rânduri de registru.{C_OFF}")
            continue

        start = foreign_max(key, branch, fetch=False) + 1
        want = list(range(start, start + len(new_rows)))
        have = [r["num"] for r in new_rows]
        print(f"{label}: rânduri noi {have} · consumate de alții până la rev. {start - 1}")
        if have == want:
            print(f"  {C_GRN}✓ numerotarea continuă corect{C_OFF}")
            continue
        print(f"  {C_YEL}✗ de renumerotat: " +
              ", ".join(f"{o} → {n}" for o, n in zip(have, want)) + C_OFF)

        if args.fix:
            open(full, "w", encoding="utf-8").write(
                renumber_doc(text, list(zip(new_rows, want))))
            claims = load_claims()
            if branch in claims and key in claims[branch]:
                claims[branch][key]["rev"] = want[0]
                save_claims(claims)
            changed.append((label, manual, have, want))
            print(f"  {C_GRN}→ scris{C_OFF}")
        else:
            problems.append(f"{label}: rulează `python3 scripts/adc.py renumber {key} --fix` ca să renumerotez")

        for line in msgs.splitlines():
            for old in re.findall(r"rev\.\s*(\d+)", line):
                if int(old) in have:
                    problems.append(
                        f"mesajul de commit „{line}” spune rev. {old}, acum ar trebui "
                        f"rev. {want[have.index(int(old))]} — corectează-l "
                        f"(git commit --amend), gen-html-manual-revision-map.py îl citește")

    for p in problems:
        print(f"{C_YEL}ATENȚIE — {p}{C_OFF}")

    if changed:
        manuals = [m for _, m, _, _ in changed if m]
        if manuals:
            print("Regenerează harta de revizii: " + "; ".join(
                f"python3 scripts/gen-html-manual-revision-map.py {m}" for m in manuals))
        return 0
    return 1 if problems else 0

# ---------------------------------------------------------------- subcomenzi

def cmd_status(args):
    root = repo_root()
    print(f"{C_DIM}repo:{C_OFF} {root}")
    print(f"{C_DIM}ramura curentă:{C_OFF} {current_branch()}")
    rc, out, _ = git("status", "--porcelain", "-uno")
    dirty = [l for l in out.splitlines() if l.strip()]
    if dirty:
        print(f"{C_YEL}modificări necomise în acest worktree ({len(dirty)}):{C_OFF}")
        for l in dirty[:15]:
            print("   " + l)
    else:
        print(f"{C_GRN}worktree curat{C_OFF}")

    print(f"\n{C_DIM}— worktree-uri active (alte sesiuni) —{C_OFF}")
    rc, out, _ = git("worktree", "list", "--porcelain")
    wt, cur = [], {}
    for line in out.splitlines():
        if line.startswith("worktree "):
            if cur:
                wt.append(cur)
            cur = {"path": line[9:]}
        elif line.startswith("branch "):
            cur["branch"] = line[7:].replace("refs/heads/", "")
    if cur:
        wt.append(cur)
    for w in wt:
        here = " <— aici" if os.path.realpath(w["path"]) == os.path.realpath(root) else ""
        rc, o, _ = git("status", "--porcelain", "-uno", cwd=w["path"])
        d = len([l for l in o.splitlines() if l.strip()])
        print(f"   {w.get('branch','(detached)'):<46} {('· ' + str(d) + ' fișiere modificate') if d else '· curat':<28}{here}")
        print(f"   {C_DIM}{w['path']}{C_OFF}")

    print(f"\n{C_DIM}— revizii: în main / următoarea liberă —{C_OFF}")
    git("fetch", "origin", "--prune", "-q")
    for key in DOCS:
        n, used = next_free(key, fetch=False)
        in_main = max_rev(blob("origin/main", DOCS[key][0]))
        extra = {k: v for k, v in used.items() if k > in_main}
        note = ""
        if extra:
            note = f"   {C_YEL}în lucru: " + "; ".join(f"rev. {k} ({', '.join(v)})" for k, v in sorted(extra.items())) + C_OFF
        print(f"   {key:<13} main: rev. {in_main:<4} liber: rev. {n}{note}")
    return 0


def cmd_next(args):
    n, used = next_free(args.doc)
    print(n)
    if args.verbose:
        for k in sorted(used):
            print(f"{C_DIM}rev. {k}: {', '.join(used[k])}{C_OFF}", file=sys.stderr)
    return 0


def cmd_claim(args):
    branch = current_branch()
    if branch in ("main", "master", "(detached HEAD)"):
        print(f"{C_RED}Nu se rezervă revizii de pe {branch}. Creează o ramură edit/... mai întâi.{C_OFF}")
        return 1
    n, _ = next_free(args.doc)
    claims = load_claims()
    entry = claims.setdefault(branch, {})
    if args.doc in entry:
        print(f"{C_YEL}Ramura {branch} are deja rezervat rev. {entry[args.doc]['rev']} pentru {args.doc}.{C_OFF}")
        return 0
    entry[args.doc] = {"rev": n, "data": date.today().isoformat(),
                       "worktree": repo_root(), "nota": args.nota or ""}
    save_claims(claims)
    print(f"{C_GRN}Rezervat rev. {n}{C_OFF} pentru {args.doc} ({DOCS[args.doc][1]}), ramura {branch}.")
    return 0


def cmd_release(args):
    branch = current_branch()
    claims = load_claims()
    if branch in claims and (args.doc is None or args.doc in claims[branch]):
        if args.doc is None:
            del claims[branch]
        else:
            del claims[branch][args.doc]
            if not claims[branch]:
                del claims[branch]
        save_claims(claims)
        print(f"{C_GRN}Rezervare eliberată pentru {branch}.{C_OFF}")
    else:
        print(f"{C_DIM}Nimic de eliberat pentru {branch}.{C_OFF}")
    return 0


def cmd_preflight(args):
    root = repo_root()
    branch = current_branch()
    problems, warnings, notes = [], [], []

    # 1. ramura
    if branch in ("main", "master"):
        problems.append("Ești pe „%s”. Munca de conținut se face pe o ramură edit/<nume>-<subiect>." % branch)
    elif branch == "(detached HEAD)":
        problems.append("HEAD detașat — creează o ramură edit/... înainte de commit.")
    elif not branch.startswith("edit/"):
        warnings.append(f"Ramura „{branch}” nu respectă convenția edit/<nume>-<subiect>.")

    # 2. izolare
    rc, out, _ = git("worktree", "list")
    n_wt = len([l for l in out.splitlines() if l.strip()])
    primary = out.splitlines()[0].split()[0] if out.strip() else ""
    if n_wt > 1 and os.path.realpath(root) == os.path.realpath(primary):
        warnings.append(f"Lucrezi în checkout-ul principal, dar mai există {n_wt - 1} worktree(uri) activ(e) "
                        "— alte sesiuni pot schimba ramura sub tine. Preferă un worktree propriu "
                        "(scripts/adc.py new-session).")

    # 3. curățenie
    rc, out, _ = git("status", "--porcelain")
    dirty = [l for l in out.splitlines() if l.strip()]
    tracked_dirty = [l for l in dirty if not l.startswith("??")]
    if tracked_dirty:
        warnings.append("Modificări necomise (NU intră în PR): " +
                        ", ".join(l[3:] for l in tracked_dirty[:8]) +
                        (" …" if len(tracked_dirty) > 8 else ""))

    # 4. sincronizare cu origin/main
    git("fetch", "origin", "--prune", "-q")
    rc, out, _ = git("rev-list", "--left-right", "--count", f"origin/main...HEAD")
    behind, ahead = (out.split() + ["0", "0"])[:2] if rc == 0 else ("?", "?")
    if ahead == "0":
        problems.append("Ramura nu are niciun commit peste origin/main — nu e nimic de trimis în PR.")
    if behind not in ("0", "?") and int(behind) > 0:
        notes.append(f"origin/main are {behind} commit(uri) noi față de baza ta. "
                     "Dacă PR-ul atinge aceleași fișiere, fă `git rebase origin/main` înainte.")

    # 5. documente atinse: registrul de modificări
    rc, out, _ = git("diff", "--name-only", "origin/main...HEAD")
    changed = [l for l in out.splitlines() if l.strip()]
    docs_touched = [PATH2KEY[p] for p in changed if p in PATH2KEY]
    rc, msgs, _ = git("log", "--format=%s%n%b", "origin/main..HEAD")

    for key in docs_touched:
        path, label, manual = DOCS[key]
        text = open(os.path.join(root, path), encoding="utf-8").read()
        top, head = top_row_rev(text), header_rev(text)
        base_max = max_rev(blob("origin/main", path))
        if top is None or head is None:
            problems.append(f"{label}: nu găsesc registrul de modificări (rândul de sus / „Revizia curentă”).")
            continue
        if top != head:
            problems.append(f"{label}: primul rând din registru e rev. {top}, dar „Revizia curentă” zice rev. {head} — sincronizează-le.")
        if top <= base_max:
            problems.append(f"{label}: rev. {top} nu e mai mare decât ultima din origin/main (rev. {base_max}) — "
                            f"n-ai adăugat un rând nou în registru? Următorul liber: rev. {next_free(key, fetch=False)[0]}.")
        else:
            coliziuni = {k: v for k, v in used_revs(key, fetch=False).items()
                         if k == top and any(w not in ("origin/main",) and branch not in w for w in v)}
            for k, where in coliziuni.items():
                others = [w for w in where if branch not in w and w != "origin/main"]
                if others:
                    problems.append(f"{label}: rev. {k} e folosit și de {', '.join(others)} — "
                                    f"treci pe rev. {next_free(key, fetch=False)[0]} ca să nu se dubleze — "
                                    f"`python3 scripts/adc.py renumber --fix` o face automat.")
        if str(date.today().day) not in text[max(0, text.find(f"<td>{top}</td>")):][:400]:
            notes.append(f"{label}: verifică data din rândul rev. {top} (astăzi e {date.today().strftime('%d.%m.%Y')}).")
        if manual:
            if f"{manual}/revision-map.js" not in changed:
                problems.append(f"{label}: lipsește {manual}/revision-map.js regenerat. Rulează "
                                f"`python3 scripts/gen-html-manual-revision-map.py {manual}` și comite fișierul.")
            if f"rev. {top}" not in msgs:
                problems.append(f"{label}: niciun mesaj de commit nu conține „rev. {top}” — "
                                "generatorul de revision-map identifică revizia din mesajul de commit.")

    # 6. igienă HTML pe fișierele HTML atinse
    for p in [c for c in changed if c.endswith(".html")]:
        fp = os.path.join(root, p)
        if not os.path.exists(fp):
            continue
        t = open(fp, encoding="utf-8").read()
        for bad in ("â€", "Ã¢", "&amp;amp;", "Ãa"):
            if bad in t:
                problems.append(f"{p}: caractere corupte („{bad}”) — verifică diacriticele.")
        counts = {}
        for tag in ("div", "table", "tr", "td", "section", "article", "figure", "p", "ul", "ol", "li"):
            o = len(re.findall(rf"<{tag}[\s>]", t, re.I))
            c = len(re.findall(rf"</{tag}\s*>", t, re.I))
            if tag in ("div", "table", "section", "article", "figure") and o != c:
                counts[tag] = (o, c)
        for tag, (o, c) in counts.items():
            warnings.append(f"{p}: <{tag}> deschis {o}× / închis {c}× — posibil tag rupt (verifică manual).")

    # 7. raport
    print(f"{C_DIM}ramura:{C_OFF} {branch}   {C_DIM}commit-uri peste origin/main:{C_OFF} {ahead}   "
          f"{C_DIM}documente atinse:{C_OFF} {', '.join(docs_touched) or '—'}")
    for p in problems:
        print(f"{C_RED}✗ {p}{C_OFF}")
    for w in warnings:
        print(f"{C_YEL}! {w}{C_OFF}")
    for n in notes:
        print(f"{C_DIM}· {n}{C_OFF}")
    if not problems:
        print(f"{C_GRN}✓ Gata de PR.{C_OFF} `gh pr create --base main --fill` (descriere în română).")
    return 1 if problems else 0


def cmd_new_session(args):
    root = repo_root()
    slug = re.sub(r"[^a-z0-9-]+", "-", f"{args.nume}-{args.subiect}".lower()).strip("-")
    branch = f"edit/{slug}"
    base = os.environ.get("CLAUDE_SCRATCHPAD") or args.dir or os.path.join(root, ".worktrees")
    dest = os.path.join(base, f"wt-{slug}")
    git("fetch", "origin", "--prune", "-q")
    rc, out, err = git("worktree", "add", dest, "-b", branch, "origin/main")
    if rc:
        print(err.strip())
        return rc
    print(f"{C_GRN}Worktree nou:{C_OFF} {dest}\n{C_GRN}Ramura:{C_OFF} {branch} (din origin/main, la zi)")
    print(f"{C_DIM}Când termini: cd „{dest}” && python3 scripts/adc.py preflight{C_OFF}")
    return 0


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("status").set_defaults(fn=cmd_status)
    p = sub.add_parser("next"); p.add_argument("doc", choices=DOCS); p.add_argument("-v", "--verbose", action="store_true"); p.set_defaults(fn=cmd_next)
    p = sub.add_parser("claim"); p.add_argument("doc", choices=DOCS); p.add_argument("--nota"); p.set_defaults(fn=cmd_claim)
    p = sub.add_parser("release"); p.add_argument("doc", nargs="?", choices=list(DOCS)); p.set_defaults(fn=cmd_release)
    sub.add_parser("preflight").set_defaults(fn=cmd_preflight)
    p = sub.add_parser("renumber"); p.add_argument("doc", nargs="?", choices=list(DOCS)); p.add_argument("--fix", action="store_true"); p.add_argument("--no-fetch", action="store_true"); p.set_defaults(fn=cmd_renumber)
    p = sub.add_parser("new-session"); p.add_argument("nume"); p.add_argument("subiect"); p.add_argument("--dir"); p.set_defaults(fn=cmd_new_session)
    args = ap.parse_args()
    sys.exit(args.fn(args))


if __name__ == "__main__":
    main()
