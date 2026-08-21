---
name: pr-manuale
description: Închide corect o sarcină pe manuale — verificări obligatorii înainte de Pull Request (ramură, revizii nedublate, revision-map regenerat, igienă HTML), apoi deschiderea PR-ului în română. Folosește când modificarea e gata, înainte de commit final / gh pr create.
---

# Închiderea sarcinii: de la modificare la Pull Request

## 1. Comite doar fișierele tale

Niciodată `git add -A` / `git commit -a` (hook-ul le blochează): în worktree pot exista modificări
ale altei sesiuni. Adaugă explicit căile pe care le-ai editat.

Mesajul de commit, în română, trebuie să conțină `rev. N` pentru documentele cu revision-map
(asistenți, medici, registratori) — generatorul identifică revizia din mesaj.

Dacă hook-ul refuză commit-ul cu „coliziune de număr de revizie", numărul din primul rând al
registrului e deja consumat (publicat în main, folosit pe altă ramură deschisă sau rezervat de altă
sesiune). Treci rândul **și** „Revizia curentă" pe numărul propus în mesaj și comite din nou; nu
ocoli verificarea.

## 2. Regenerează harta reviziilor (asistenți / medici / registratori)

```
python3 scripts/gen-html-manual-revision-map.py <asistenti|medici|registratori>
```

Comite `<manual>/revision-map.js` în același PR. ROI și procedurile nu au revision-map.

## 3. Rulează verificările

```
python3 scripts/adc.py preflight
```

Rezolvă tot ce apare cu `✗` (blocant) și citește `!` / `·`. Verifică, printre altele:
ramura nu e main, rândul nou din registru are numărul mai mare decât în `origin/main` și nu e
folosit de altă ramură deschisă, „Revizia curentă” e sincronizată cu primul rând, revision-map
regenerat, mesajul de commit conține `rev. N`, diacritice necorupte, tag-uri HTML echilibrate.

## 4. Deschide PR-ul

```
git push -u origin <ramura>
gh pr create --base main --title "<titlu în română>" --body "<ce s-a schimbat și de ce>"
```

Apoi eliberează rezervarea numărului de revizie:

```
python3 scripts/adc.py release <doc>
```

Merge-ul îl face Vlad, un PR pe rând. După fiecare merge, celelalte sesiuni fac `git fetch origin`
și, dacă ating aceleași fișiere, `git rebase origin/main`.

## 5. Dacă munca ta s-a amestecat deja cu a altei sesiuni

Comite **numai** partea ta, pe ramură nouă, și lasă restul necomis (preferința lui Vlad).
Verifică ce e al tău cu `git diff -- <cale>` înainte de `git add`.
