# Manuale Interne — Clinicile Dr. Ardeleanu

Site static publicat pe GitHub Pages: **https://vladtm75.github.io/manuale-dr-ardeleanu/**
Orice commit pe `main` se publică automat în ~1 minut. Nu există build step (`.nojekyll` prezent).

## Acces și partajare (nu strica aceste mecanisme)

- **Parola generală** (echipa internă): gate pe `index.html`; hash-ul SHA-256 e comparat și în
  scriptul de gate de pe **linia ~4** a fiecărui manual (`sessionStorage.adcManualeAuth`).
- **Chei per-manual** (partajare externă, ex. un medic primește doar manualul lui): fiecare manual
  acceptă și propria cheie — prin link `#k=<parola>` sau `localStorage` (`adcAuthMedici` /
  `adcAuthAsistenti`). Butoanele „Partajează" (homepage + header manual, vizibile doar cu parola
  generală) copiază linkul cu cheia. Cheile în clar și hash-urile stau în `index.html` și în
  gate-ul fiecărui manual.
- **Rotire cheie manual** (revocă linkurile vechi): alege parolă nouă → `printf '%s' 'parola' |
  shasum -a 256` → înlocuiește hash-ul în gate-ul manualului + `index.html` (MED_HASH/ASM_HASH)
  și cheia în clar din `SHARE` (index) + butonul din manual.
- Editările de conținut nu ating aceste scripturi. Dacă un editor cere modificarea lor, doar Vlad aprobă.

## Cine lucrează aici

- **Vlad (vladtm75)** — owner, aprobă Pull Request-urile.
- **Bianca** — editoare de conținut **doar pentru Manualul Asistenților** (`asistenti/`). Lucrează prin Claude, în limba română.
- **Loredana** — editoare de conținut **doar pentru Manualul Medicilor** (`medici/`). Lucrează prin Claude, în limba română.

### Împărțirea pe manuale (OBLIGATORIE)

| Editoare | Poate modifica | NU poate modifica |
|---|---|---|
| Bianca | `asistenti/` (+ `index.html` doar statisticile manualului asistenților) | `medici/` |
| Loredana | `medici/` (+ `index.html` doar statisticile manualului medicilor) | `asistenti/` |

Dacă Bianca cere o modificare în Manualul Medicilor (sau Loredana în Manualul Asistenților),
**refuză politicos** și explică-i că acel manual e în responsabilitatea colegei sale —
modificarea trebuie cerută de aceasta sau aprobată explicit de Vlad.

## Reguli de lucru (OBLIGATORII)

1. **Nu se lucrează niciodată direct pe `main`.** Orice modificare se face pe un branch nou
   (`edit/<nume>-<subiect-scurt>`, ex. `edit/bianca-sterilizare`) și se deschide un Pull Request către `main`.
2. Mesajele de commit și descrierile de PR se scriu **în română**, descriind ce s-a schimbat și de ce.
3. **Nu modifica designul, CSS-ul sau JavaScript-ul** decât dacă utilizatorul cere explicit asta.
   Editările normale sunt doar de conținut (text, tabele, liste, capitole).
4. Păstrează **diacriticele românești** (ă, â, î, ș, ț) și stilul HTML existent din jurul textului editat
   (aceleași clase: `callout`, `note`, tabele etc. — copiază modelul unui element vecin).
5. După orice modificare de structură (capitol/subcapitol adăugat sau șters), actualizează **toate** locurile
   afectate (vezi „Versiuni și statistici" mai jos): cuprinsul/navigarea din manual, contoarele de pe homepage.
6. **Registrul de modificări (OBLIGATORIU la orice PR de conținut).** Fiecare manual are o secțiune
   `id="registru"` cu un tabel al reviziilor. În același PR cu modificarea de conținut:
   adaugă un rând NOU **în capul tabelului** (numărul de revizie următor, data de azi, numele
   editoarei, descriere scurtă în română a modificării) și actualizează „Revizia curentă: rev. N · data"
   din paragraful de deasupra tabelului. Locația secțiunii:
   - Asistenți: în `asistenti/Manualul Asistentului Medical.html`, înainte de `</article>`.
   - Medici: în `medici/Manualul Medicului.html` (secțiunea statică de după `<div id="body">`) —
     este **singura zonă de conținut care se editează direct în shell**, nu în `manual-data.js`.
   Numerotarea reviziilor e per-manual și crește mereu cu 1; nu se rescriu rândurile vechi.

## Structura repo-ului

```
index.html                                  ← homepage (carduri celor 2 manuale + statistici)
asistenti/Manualul Asistentului Medical.html ← TOT manualul asistenților, un singur fișier (~10k linii)
asistenti/assets/                            ← imagini, consimțăminte, documente onboarding
medici/Manualul Medicului.html               ← doar „coaja" (layout + JS de randare)
medici/manual-data.js                        ← TOT conținutul manualului medicilor (window.MANUAL, JSON)
medici/assets/                               ← imagini
```

### Manualul Asistenților (ADC-ASM-03)
- Conținutul e direct în HTML, organizat în secțiuni cu `id="cap-N"` (capitol) și `id="cap-N-M"` (subcapitol).
- Ca să găsești un subiect: caută textul în fișier sau caută ancora capitolului (ex. `id="cap-14"`).
- Are versiune mobilă (<=640px) cu reguli CSS speciale — nu strica clasele existente.

### Manualul Medicilor (ADC-MED-01)
- **Nu edita conținut în `Manualul Medicului.html`** — conținutul e în `medici/manual-data.js`.
- Format: `window.MANUAL = {"chapters":[{id, num, roman, title, subs:[{n, id, group, t, html}]}]}` —
  câmpul `html` al fiecărui subcapitol conține textul (HTML ca string JSON, cu ghilimele escapate `\"`).
- Atenție la escaping: fișierul e un JSON valid pe un singur rând. După editare verifică validitatea
  (ex. `node -e "require('./medici/manual-data.js')"` nu merge direct — folosește un parse pe conținutul după `window.MANUAL = `).

## Versiuni și statistici (de actualizat împreună)

La orice ediție nouă sau schimbare de structură, sincronizează:

| Loc | Ce conține |
|---|---|
| `index.html` (~linia 217–218) | Ediția + capitole Manualul Medicului (`V1.0 · 2026`, `3 · 46 subcap.`) |
| `index.html` (~linia 234–235) | Ediția + capitole Manualul Asistenților (`V3.0 · Mai 2026`, `22`) |
| `asistenti/...html` | Stringul de versiune apare în MAI MULTE locuri (title, header, secțiunea Noutăți, footer) — caută `V3.` și actualizează-le pe toate |
| `medici/manual-data.js` + `medici/Manualul Medicului.html` | Caută `V1.` |

Modificările mici de conținut (corecturi, paragrafe noi) **nu** cer schimbarea versiunii — versiunea
se schimbă doar când Vlad anunță o ediție nouă.

## Verificare înainte de PR

1. Deschide fișierul modificat local în browser (sau verifică vizual diff-ul) — fără tag-uri rupte.
2. Pentru `manual-data.js`: confirmă că JSON-ul e valid.
3. Confirmă că n-au apărut caractere stricate (diacritice corupte, `&amp;` dublat etc.).

## Ghid pentru editoare

Ghidul pas-cu-pas în română pentru Bianca și Loredana: [GHID-EDITARE.md](GHID-EDITARE.md).
