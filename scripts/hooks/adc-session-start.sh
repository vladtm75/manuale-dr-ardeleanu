#!/bin/sh
# Hook SessionStart: pune în context starea reală a repo-ului (ramură, worktree-uri ale altor
# sesiuni, revizii libere), ca sesiunea să nu presupună că e singura care lucrează aici.
ROOT=$(git rev-parse --show-toplevel 2>/dev/null) || exit 0
[ -f "$ROOT/scripts/adc.py" ] || exit 0
echo "=== Starea repo-ului manuale (sesiuni paralele) ==="
python3 "$ROOT/scripts/adc.py" status 2>/dev/null
echo "Protocol: lucrează într-un worktree propriu (scripts/adc.py new-session), rezervă numărul de"
echo "revizie (scripts/adc.py claim <doc>) și rulează scripts/adc.py preflight înainte de Pull Request."
