---
name: sesiune-noua
description: Pornește corect o sesiune de lucru pe manuale când mai multe sesiuni Claude rulează în paralel pe același repo — worktree izolat, ramură din origin/main la zi, număr de revizie rezervat. Folosește la începutul oricărei sarcini de editare (conținut, design, procedură nouă), înainte de prima modificare de fișier.
---

# Pornirea unei sesiuni de lucru izolate

Repo-ul e deschis simultan de mai multe sesiuni Claude. Fără izolare, alta îți poate schimba
ramura sub picioare, îți poate comite fișierele necomise sau poate consuma același număr de revizie.

## 1. Vezi cine mai lucrează aici

```
python3 scripts/adc.py status
```

Reține: worktree-urile active (= sesiunile paralele), fișierele modificate necomise (nu sunt neapărat
ale tale) și, pentru fiecare document, ultima revizie din `origin/main` plus reviziile deja „în lucru”
pe alte ramuri.

## 2. Creează-ți spațiul propriu

```
python3 scripts/adc.py new-session vlad <subiect-scurt>
```

Creează un `git worktree` separat (în scratchpad-ul sesiunii, dacă `CLAUDE_SCRATCHPAD` e setat) și
ramura `edit/vlad-<subiect-scurt>` din `origin/main` la zi. Lucrează **numai** în calea afișată.

Nu lucra în checkout-ul principal (`~/Desktop/Manaule Dr.Ardeleanu`) când `status` arată alte
worktree-uri active — acolo modificările tale se amestecă cu ale altei sesiuni.

## 3. Rezervă numărul de revizie ÎNAINTE de a-l scrie în document

```
python3 scripts/adc.py claim <asistenti|medici|registratori|roi|proc-ben|proc-reg>
```

Rezervarea e vizibilă tuturor sesiunilor locale (fișier în directorul git comun), deci două sesiuni
nu mai pot lua același număr. Scrie în registrul documentului exact numărul rezervat.

Dacă renunți la sarcină: `python3 scripts/adc.py release <doc>`.

## 4. Regulile care rămân valabile

Conținutul, stilul manual-proză, registrul de modificări și paritatea de design sunt descrise în
CLAUDE.md — acest skill nu le înlocuiește, doar asigură că munca ta nu se ciocnește de altă sesiune.
La final rulează skill-ul `pr-manuale`.
