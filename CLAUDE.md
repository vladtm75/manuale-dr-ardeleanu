# Manuale Interne — Clinicile Dr. Ardeleanu

Site static publicat pe GitHub Pages: **https://vladtm75.github.io/manuale-dr-ardeleanu/**
Orice commit pe `main` se publică automat în ~1 minut. Nu există build step (`.nojekyll` prezent).

## Acces și partajare (nu strica aceste mecanisme)

- **Parola generală** (echipa internă): gate pe `index.html`; hash-ul SHA-256 e comparat și în
  scriptul de gate de pe **linia ~4** a fiecărui manual (`sessionStorage.adcManualeAuth`).
- **Chei per-manual** (partajare externă, ex. un medic primește doar manualul lui): fiecare manual
  acceptă și propria cheie — prin link `#k=<parola>` sau `localStorage` (`adcAuthMedici` /
  `adcAuthAsistenti` / `adcAuthRegistratori`). Butoanele „Partajează" (homepage + header manual, vizibile doar cu parola
  generală) copiază linkul cu cheia. Cheile în clar și hash-urile stau în `index.html` și în
  gate-ul fiecărui manual.
- **Rotire cheie manual** (revocă linkurile vechi): alege parolă nouă → `printf '%s' 'parola' |
  shasum -a 256` → înlocuiește hash-ul în gate-ul manualului + `index.html` (MED_HASH/ASM_HASH/REG_HASH)
  și cheia în clar din `SHARE` (index) + butonul din manual.
- Editările de conținut nu ating aceste scripturi. Dacă un editor cere modificarea lor, doar Vlad aprobă.

## Cine lucrează aici

- **Vlad (vladtm75)** — owner, aprobă Pull Request-urile.
- **Bianca** — editoare de conținut **doar pentru Manualul Asistenților** (`asistenti/`). Lucrează prin Claude, în limba română.
- **Loredana** — editoare de conținut **doar pentru Manualul Medicilor** (`medici/`). Lucrează prin Claude, în limba română.
- **Alexandra** — editoare de conținut **doar pentru Manualul Registratorilor** (`registratori/`). Lucrează prin Claude, în limba română.

Manualul ROI (`roi/`) nu are încă o editoare desemnată — nu apare mai jos la Bianca, Loredana sau
Alexandra. Vlad administrează direct conținutul lui, până când va desemna pe cineva.

### Împărțirea pe manuale (OBLIGATORIE)

| Editoare | Poate modifica | NU poate modifica |
|---|---|---|
| Bianca | `asistenti/` (+ `index.html` doar statisticile manualului asistenților) | `medici/`, `registratori/` |
| Loredana | `medici/` (+ `index.html` doar statisticile manualului medicilor) | `asistenti/`, `registratori/` |
| Alexandra | `registratori/` (+ `index.html` doar statisticile manualului registratorilor) | `asistenti/`, `medici/` |

Dacă o editoare cere o modificare în alt manual decât al ei,
**refuză politicos** și explică-i că acel manual e în responsabilitatea colegei sale —
modificarea trebuie cerută de aceasta sau aprobată explicit de Vlad.

## Reguli de lucru (OBLIGATORII)

1. **Nu se lucrează niciodată direct pe `main`.** Orice modificare se face pe un branch nou
   (`edit/<nume>-<subiect-scurt>`, ex. `edit/bianca-sterilizare`) și se deschide un Pull Request către `main`.
2. Mesajele de commit și descrierile de PR se scriu **în română**, descriind ce s-a schimbat și de ce.
3. **Nu modifica designul, CSS-ul sau JavaScript-ul** decât dacă utilizatorul cere explicit asta.
   Editările normale sunt de conținut (text, tabele, liste, capitole, imagini — vezi „Imagini și fotografii").
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
   - Medici: în `medici/Manualul Medicului.html`, secțiunea `id="registru"`.
   - Registratori: în `registratori/Manualul Registratorului Medical.html`, înainte de `</article>`.
   Numerotarea reviziilor e per-manual și crește mereu cu 1; nu se rescriu rândurile vechi.

## Imagini și fotografii (permise editoarelor)

Editoarele (Bianca, Loredana, Alexandra) pot adăuga fotografii/imagini în manualul lor, pe branch-ul lor,
prin PR — la fel ca orice modificare de conținut. Nu refuza cererile de adăugare de imagini.

- Salvează fișierul în folderul `assets/` al manualului respectiv (`asistenti/assets/`, `medici/assets/`, `registratori/assets/`).
- Nume de fișier: kebab-case, fără diacritice și fără spații (ex. `pozitionare-senzor-rx.jpg`).
- Formate: JPG / PNG / WebP. Peste ~1,5 MB sau ~1600px lățime: redimensionează/recomprimă înainte de commit (ex. Python + PIL).
- Inserarea în conținut:
  - **Asistenți / Registratori:** `<img>` sau `<figure>` direct în HTML, cu `src="assets/<fisier>"`, `alt` descriptiv
    în română și stilul/clasele elementelor vecine.
  - **Medici:** `<img>` sau `<figure>` direct în HTML, cu `src="assets/<fisier>"`, `alt` descriptiv
    în română și stilul/clasele elementelor vecine — la fel ca la Asistenți/Registratori.
- **Confidențialitate (OBLIGATORIU):** nu se publică imagini cu fețe identificabile de pacienți sau cu date
  personale vizibile (nume, CNP, fișe, ecrane ERP). Dacă o poză trimisă încalcă regula, exclude-o și explică
  editoarei de ce; excepțiile le aprobă doar Vlad. Pozele cu angajați — doar cu acordul persoanei.
- Dacă imaginile atașate în conversație **nu sunt accesibile** în mediul de lucru, spune-i editoarei explicit
  (nu inventa/nu genera fișiere-substitut) și oferă alternative: urcarea pozei prin interfața GitHub direct pe
  branch-ul PR-ului (Add file → Upload files în folderul `assets/` al manualului), sau trimiterea pozei la Vlad.
- Imaginile adăugate se menționează în rândul din Registrul de modificări al PR-ului, ca orice modificare.

## Structura repo-ului

```
index.html                                  ← homepage (cardurile manualelor + statistici)
asistenti/Manualul Asistentului Medical.html ← TOT manualul asistenților, un singur fișier (~10k linii)
asistenti/assets/                            ← imagini, consimțăminte, documente onboarding
medici/Manualul Medicului.html               ← TOT manualul medicilor, un singur fișier
medici/assets/                               ← imagini
registratori/Manualul Registratorului Medical.html ← TOT manualul registratorilor, un singur fișier
registratori/assets/                         ← imagini (+ .docx-ul sursă al manualului)
roi/Regulamentul de Organizare Interna.html  ← Regulamentul de Organizare Internă (ROI), un singur fișier
roi/assets/                                  ← imagini/documente (gol momentan)
```

### Manualul Asistenților (ADC-ASM-03)
- Conținutul e direct în HTML, organizat în secțiuni cu `id="cap-N"` (capitol) și `id="cap-N-M"` (subcapitol).
- Ca să găsești un subiect: caută textul în fișier sau caută ancora capitolului (ex. `id="cap-14"`).
- Are versiune mobilă (<=640px) cu reguli CSS speciale — nu strica clasele existente.

### Manualul Registratorilor (ADC-REC-01)
- Aceeași structură ca manualul asistenților: conținut direct în HTML, secțiuni `id="cap-N"` (1–9).
- Construit pe scheletul manualului asistenților — beneficiază de aceleași facilități (mobil, căutare, partajare).

### Manualul Medicilor (ADC-MED-01)
- De la migrarea la HTML static (rev. 30, august 2026), aceeași structură ca celelalte manuale: conținutul
  e direct în HTML, secțiuni cu `id="cap-N"` (capitol, N=1–3) și `id="cap-N-M"` (subcapitol) — nu mai
  există un fișier de date separat (`manual-data.js` a fost eliminat).
- Are un nivel suplimentar de grupare în Cuprins (grupuri de subcapitole în cadrul unui capitol, ex.
  „Onboarding-ul medicului" în capitolul Operațional) — marcat cu `<li class="sub-group-label">` în TOC
  și `<div class="group-divider">` în conținut, o extensie peste sistemul comun de TOC (`.toc-side`).

### Toggle „versiune anterioară" în Registrul de modificări (asistenți, registratori, medici)
Fiecare rând din Registru (cu excepția reviziei de origine și a reorganizărilor structurale fără diff
de text) are un switch care aduce live, de pe `raw.githubusercontent.com`, textul secțiunii așa cum era
înainte de acea revizie — necesită internet, nu funcționează offline. Datele vin din `<manual>/revision-map.js`
(generat automat, NU se editează manual), pe baza `id`-urilor `<h2>`/`<h3>` din pagină. **După orice PR
care adaugă un rând nou în Registrul de modificări al oricăruia dintre aceste trei manuale, rulează din
rădăcina repo-ului:**
`python3 scripts/gen-html-manual-revision-map.py <asistenti|registratori|medici>` — și comite fișierul
`revision-map.js` rezultat, alături de restul modificării. Scriptul citește convenția „rev. N" din
mesajele de commit ca să identifice automat commit-ul fiecărei revizii. Manualul Registratorilor e
încă la rev. 1 (originea) — nu are coloana „Versiune"/toggle până la rev. 2. Manualul Medicului are
reviziile 1–30 marcate fără toggle (`rev-na`) — ele precedă structura HTML actuală sau documentează
schimbări structurale fără diff de text; prima cu toggle real va fi rev. 31+.

### Regulament Intern / ROI (ADC-RI-02, ediția V2)
- De la 15 august 2026: **document-șablon (model-cadru) multi-entitate**, nu regulament unic — a înlocuit
  integral fostul ADC-ROI-01 (Ediția 2026). Fiecare societate care operează sub marca Dr. Ardeleanu
  adoptă separat modelul, își completează datele în Anexa nr. 1 și îl comunică propriilor salariați.
- Conținut direct în HTML: 17 capitole (`id="cap-N"`, N=1–17), **131 de articole numerotate continuu**
  (`id="art-N"`, N=1–131, nu pe capitol) și **13 anexe** (`id="anexa-N"`, N=1–13, majoritatea formulare
  operaționale complete — performanță, disciplină, hărțuire, avertizare de integritate etc.).
- **Conține deliberat câmpuri necompletate** (denumirea legală a angajatorului, sediu, CUI, numărul
  deciziei de adoptare, data intrării în vigoare) — la cererea lui Vlad, NU se înlocuiesc cu presupuneri
  despre ce societate din grup s-ar aplica. Se completează doar când Vlad decide asta explicit.
- Document HR/legal, nu manual clinic — nu are încă o editoare desemnată; Vlad îl administrează direct
  până va desemna pe cineva pentru acest manual.
- Are cheie de acces proprie și buton „Partajează" (`adcAuthROI`, ca la celelalte manuale) —
  partajarea funcționează la fel ca pentru medici/asistenți/registratori.
- Include o secțiune finală „Modificări față de Ediția 2026 (ADC-ROI-01)" (`id="modificari"`), înainte de
  Registrul de modificări — actualizeaz-o doar dacă apare o ediție nouă a regulamentului, nu la corecturi mici.
- Sursa ediției V2: primită de la Vlad ca document Word (`.docx`), convertit programatic (paragrafe +
  tabele extrase din XML, în lipsa pandoc/LibreOffice local) — nu presupune că fișierul `.docx` original
  rămâne în repo; conversia e un instantaneu, nu o legătură vie.

## Versiuni și statistici (de actualizat împreună)

La orice ediție nouă sau schimbare de structură, sincronizează:

| Loc | Ce conține |
|---|---|
| `index.html` (~linia 217–218) | Ediția + capitole Manualul Medicului (`V1.0 · 2026`, `3 · 46 subcap.`) |
| `index.html` (~linia 234–235) | Ediția + capitole Manualul Asistenților (`V3.0 · Mai 2026`, `22`) |
| `asistenti/...html` | Stringul de versiune apare în MAI MULTE locuri (title, header, secțiunea Noutăți, footer) — caută `V3.` și actualizează-le pe toate |
| `medici/Manualul Medicului.html` | Caută `V1.` (title, header, hero, footer) |
| `index.html` (cardul registratori) | Ediția + capitole Manualul Registratorilor (`V4.1 · Mai 2025`, `9`) |
| `registratori/...html` | Caută `V4.` (title, header, hero, footer) |
| `index.html` (cardul ROI) | Ediția + capitole ROI (`V2`, `17 · 13 anexe`) |
| `roi/...html` | Caută `V2` / `ADC-RI-02` (title, header, hero, footer) |

Modificările mici de conținut (corecturi, paragrafe noi) **nu** cer schimbarea versiunii — versiunea
se schimbă doar când Vlad anunță o ediție nouă.

## Verificare înainte de PR

1. Deschide fișierul modificat local în browser (sau verifică vizual diff-ul) — fără tag-uri rupte.
2. Confirmă că n-au apărut caractere stricate (diacritice corupte, `&amp;` dublat etc.).

## Ghid pentru editoare

Ghidul pas-cu-pas în română pentru Bianca și Loredana: [GHID-EDITARE.md](GHID-EDITARE.md).
