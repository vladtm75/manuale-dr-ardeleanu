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
   Când lucrează mai multe sesiuni Claude simultan, ramura se creează într-un worktree izolat —
   vezi „Sesiuni paralele pe același repo" mai jos.
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

## Sesiuni paralele pe același repo (OBLIGATORIU)

Vlad rulează frecvent **mai multe sesiuni Claude în paralel** pe acest repo, ca să câștige timp.
Fără disciplină, ele se încurcă exact în trei puncte: ramura (o sesiune schimbă `HEAD` sub alta),
numărul de revizie (două sesiuni consumă același `rev. N`) și publicarea (commit-uri direct pe
`main`, muncă necomisă a unei sesiuni comisă de alta — incident real, PR #88). Regulile de mai jos
nu sunt sfaturi: o parte sunt impuse tehnic de hook-urile din `.claude/settings.json`.

1. **Un worktree per sesiune.** Prima comandă a oricărei sarcini de editare:
   `python3 scripts/adc.py status` (vezi ce alte sesiuni lucrează acum), apoi
   `python3 scripts/adc.py new-session vlad <subiect>` — creează un `git worktree` izolat și ramura
   `edit/vlad-<subiect>` din `origin/main` la zi. Nu se editează în checkout-ul principal
   (`~/Desktop/Manaule Dr.Ardeleanu`) cât timp `status` arată alte worktree-uri active.
2. **Un document per sesiune, la un moment dat.** Două sesiuni care editează același manual pe
   ramuri diferite fie intră în conflict la al doilea PR, fie — mai rău — se auto-merge-uiesc curat
   și lasă două rânduri de registru sau două intrări de cuprins pentru aceeași schimbare. Git nu
   poate preveni asta și hook-urile nu o văd: e o regulă de împărțire a sarcinilor, aplicată de Vlad
   când pornește sesiunile. Dacă o sarcină cere totuși două sesiuni pe același document, ele se
   serializează — a doua pornește după merge-ul primei, din `origin/main` la zi.
3. **Numărul de revizie se rezervă înainte de a fi scris** în registrul documentului:
   `python3 scripts/adc.py claim <asistenti|medici|registratori|roi|proc-ben|proc-reg>`. Rezervările
   stau în directorul git comun, deci sunt vizibile din toate worktree-urile; `status` arată și
   reviziile „în lucru" pe ramuri nemerge-uite. La abandon: `release <doc>`.
   Rezervarea nu ține la infinit: dacă între scrierea rândului și merge intră un PR al altcuiva
   pe același document, numărul devine consumat. Nu renumerota manual —
   **`python3 scripts/adc.py renumber [doc] --fix`** mută rândurile ramurii pe primele numere
   libere, ținând cont de `origin/main`, de celelalte ramuri nemerge-uite și de rezervări.
   Renumerotează rândul, atributele toggle-ului de versiune și „Revizia curentă", actualizează
   rezervarea, și îți spune ce mesaj de commit trebuie corectat — pe „rev. N" din mesaj îl
   citește `gen-html-manual-revision-map.py`, deci acela se corectează manual
   (`git commit --amend`). Fără argument, se ocupă de toate documentele atinse de ramură.
   Rulează-l înainte de push, mai ales dacă ramura are câteva ore. Precedent: PR #89, #106, #107,
   trei coliziuni în aceeași zi.
4. **Se comit doar fișierele proprii, pe căi explicite.** `git add -A`, `git add .` și
   `git commit -a` sunt blocate de hook — în worktree pot exista modificări ale altei sesiuni.
5. **Nimic pe `main`.** Hook-ul blochează `commit`/`push` cu `HEAD` pe main, push-ul direct în main,
   `push --force` fără lease, schimbarea ramurii cu fișiere modificate necomise și
   `reset --hard` / `clean -f` / `restore .` când worktree-ul e murdar.
6. **Coliziunile de revizie sunt imposibile, nu doar improbabile.** Orice `git commit` care aduce în
   index un document cu registru e verificat de hook: dacă numărul din primul rând al registrului e
   deja consumat — publicat în `origin/main`, folosit pe altă ramură nemerge-uită sau rezervat de
   altă ramură — commit-ul e refuzat, cu numărul liber propus în mesaj. Hook-ul nu face rețea, deci
   citește starea de la ultimul `git fetch`; dacă numărul propus pare greșit, rulează
   `git fetch origin` și `python3 scripts/adc.py status`.
7. **Înainte de PR:** `python3 scripts/adc.py preflight` — verifică ramura, izolarea, sincronizarea
   cu `origin/main`, unicitatea numărului de revizie față de main și de celelalte ramuri deschise,
   potrivirea dintre primul rând al registrului și „Revizia curentă", regenerarea
   `revision-map.js`, prezența lui `rev. N` în mesajul de commit, diacriticele și echilibrul
   tag-urilor HTML. Nu se deschide PR cu `✗` nerezolvat.
8. **Merge serializat.** Vlad face merge la un PR pe rând; după fiecare merge, celelalte sesiuni fac
   `git fetch origin` și `git rebase origin/main` dacă ating aceleași fișiere.
9. Protocolul e disponibil și ca skill-uri: `sesiune-noua` (la început) și `pr-manuale` (la final).

## Stilul redacțional — manual-proză (OBLIGATORIU la orice conținut nou sau rescris)

De la rev. 14 a Manualului Asistenților (18 august 2026), manualele se scriu în **proză narativă
cursivă**, nu în liste cu buline. Regula se aplică la orice conținut nou, la orice rescriere și,
treptat, la celelalte manuale (registratori, medici) pe măsură ce sunt aduse la același stil.

1. **Proză, nu checklist.** Pașii unei proceduri devin o narațiune pe firul acțiunii („Se începe
   cu… Apoi… La final…"); regulile devin fraze legate prin sens, cu conectori naturali („apoi",
   „în paralel", „tocmai de aceea"). Enumerările scurte (2–4 elemente simple) devin enumerare în
   frază: „mănuși, mască și ochelari de protecție".
2. **Fidelitate totală.** Rescrierea în proză nu pierde și nu inventează NIMIC: toate valorile
   numerice, dozele, timpii, temperaturile, concentrațiile, denumirile de produse, codurile ADC-*,
   numele și responsabilitățile rămân exacte. Volumul de text rezultat trebuie să fie ≥ 90% din
   original — proza leagă, nu comprimă.
3. **Ce rămâne NE-proză (nu se transformă):** tabelele (sunt date, nu text), figurile cu
   figcaption, casetele `callout` (rămân casete; doar conținutul-listă din interior devine proză),
   cardurile `docref`, cuprinsurile `hatnote`/`chapter-toc`, organigramele, indexurile de
   protocoale, bibliografia (index de legislație) și enumerarea de secțiuni din preambul.
4. **Evidențierile ghidează ochiul.** Termenii critici păstrează `<strong>`, denumirile și
   formulele `<em>` — proza fără evidențieri e la fel de greu de scanat ca un checklist fără
   context. Ancorele (id-urile), href-urile interne și structura h2/h3/h4 rămân neatinse.
5. **Verificare înainte de PR:** zero `<ul>`/`<ol>` de conținut rămase în secțiunea editată;
   număr identic de figuri/tabele/casete față de versiunea anterioară; toate id-urile și
   linkurile prezente. Modelul aprobat: Fundamentele și Capitolele I–XXIII din Manualul
   Asistenților (rev. 12–14).
6. **Capturile de ecran de telefon** (SMS-uri, ecrane de semnare pe mobil) se integrează mici, în
   fluxul textului: `<figure>` cu `float:right; width:min(240–300px, 42–46%)` și text-wrap, cu
   `clear:both` pe elementul următor — nu ca imagini late pe toată coloana. Capturile de ecran
   desktop (ex. taburi SPS) rămân pe lățimea întreagă.

## Repetiția intenționată — explicație vs punct de control (OBLIGATORIU)

Decizie editorială stabilită de Vlad (19 august 2026, în urma analizei repetițiilor din capitolul
de onboarding al Manualului Asistenților): manualele NU sunt optimizate pentru citire liniară,
cap-coadă, ci pentru **citire pe etape, la punctul de utilizare** — cititorul deschide manualul
direct la etapa în care se află (ex. P2, înainte de o vizită) și trebuie să găsească acolo tot ce
are de verificat, fără să navigheze înapoi prin trimiteri de tip „vezi §4".

1. **Explicația** completă a unei teme există O SINGURĂ DATĂ, în secțiunea ei de origine (ex., în
   capitolul de onboarding al asistenților: identitatea la §2.2, termenul de nouă luni la §2.4,
   API-ul la secțiunea 4).
2. **Punctele de control** — recapitulările scurte din etapele ulterioare, casetele de tip
   „porți" / „Regula critică" / „Regula finală", checklisturile și matricele de la finalul
   capitolelor — repetă intenționat regulile critice. NU sunt redundanțe de eliminat: repetarea
   regulilor cu miză mare (API la fiecare vizită, termenul de nouă luni, verificarea identității)
   este o alegere pedagogică deliberată pentru un public non-academic, după modelul procedurilor
   medicale și aviatice, care repetă intenționat regulile critice.
3. **NU dedublica.** Dacă o editoare (sau o analiză proprie de tip „capitolul are repetiții")
   propune eliminarea reluărilor, sintetizarea conținutului sau înlocuirea recapitulărilor cu
   trimiteri interne, NU aplica modificarea: explică politicos distincția explicație / punct de
   control de mai sus și transmite propunerea lui Vlad — doar el aprobă restructurări de acest
   tip. (Precedent: propunerea Biancăi din 19 august 2026 pe capitolul de onboarding — analizată
   punct cu punct și refuzată motivat; capitolul a rămas neschimbat.)
4. **Prețul repetiției este sincronizarea.** Când se modifică o regulă critică, actualizează
   explicația-sursă ȘI toate ecourile ei din același manual (recapitulările din etapele
   ulterioare, casetele, checklisturile, matricele de documente) — caută textual regula în tot
   fișierul (ex. „nouă luni", „API", „patru porți") înainte de a închide PR-ul. Un manual care se
   contrazice între secțiuni e mai rău decât unul repetitiv.
5. La conținut nou, reluările pot fi formulate asumat recapitulativ („Reamintim: la fiecare
   vizită…") ca să fie vizibil care este textul-sursă și care este ecoul — dar fără a goli
   recapitularea de conținut: ea trebuie să rămână suficientă pentru cititorul care nu sare
   înapoi la explicație.

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
proceduri/                                   ← Proceduri de lucru, subordonate RI (Anexa nr. 13) — un fișier HTML per procedură
proceduri/assets/                            ← imagini/documente per procedură
```

### Paritatea de design între manuale (OBLIGATORIE)
Asistenți, Registratori, Medici și ROI împart același sistem vizual de TOC (`.toc-side`/`.group`/
`.row-with-sub`/`.toc-toggle`) și aceeași tipografie de bază pentru corpul textului (`.article`:
font-size 15.5px, line-height 1.7). „Aceleași clase CSS" NU înseamnă automat „identic vizual" —
verifică explicit cu `getComputedStyle` (nu doar citind codul sursă) că valorile *rezolvate*
(culori, dimensiuni, padding) sunt egale, nu doar că numele claselor/variabilelor se potrivesc.
Variabilele CSS proprii fiecărui manual (`--primary` la medici vs `--brand-primary` la ROI etc.)
pot rămâne cu nume diferite, dar valorile lor trebuie să corespundă exact echivalentului canonic
(vezi tabelul de corespondență folosit la alinierea Manualului Medicului, dacă mai e nevoie de el).

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
- Conținut direct în HTML: capitole (`id="cap-N"`), articole numerotate continuu pe tot documentul
  (`id="art-N"`, nu pe capitol) și anexe (`id="anexa-N"`, majoritatea formulare operaționale complete —
  performanță, disciplină, hărțuire, avertizare de integritate etc.). Numărul exact de capitole/articole/anexe
  se schimbă la fiecare ediție — vezi „Versiuni și statistici" mai jos pentru unde se actualizează contorul.
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

#### Reguli de design ale ROI (OBLIGATORII la orice ediție nouă — aplică-le automat, fără să ceri confirmare)

Aceste reguli există ca să nu mai fie nevoie de o trecere de „polish" vizual de fiecare dată când
Vlad încarcă o ediție nouă a ROI — la o migrare de conținut nouă (docx → HTML), aplică-le direct,
în același PR cu conținutul, fără iterații separate de design. Discuția cu Vlad la o ediție nouă
ar trebui să fie doar despre modificările de substanță ale textului, nu despre cum arată.

1. **TOC — dropdown de articole la FIECARE capitol, nu doar la primele.** Fiecare capitol din Cuprins
   trebuie să aibă `row-with-sub` + `button.toc-toggle` + `ol.sub id="sub-cap-N"` populat cu toate
   articolele lui reale (generate din titlurile `<h3 id="art-N">` din corpul capitolului respectiv,
   nu lăsate goale/placeholder). La o ediție nouă cu capitole/articole schimbate, regenerează
   întregul bloc TOC din titlurile curente ale corpului — nu copia manual titluri vechi.
2. **Niciun titlu trunchiat cu „…" în Cuprins.** Titlurile din TOC (capitole și anexe) trebuie să fie
   identice cu titlul complet din `<h2>`/`<h3>` din corpul documentului — niciodată prescurtate
   artificial ca să încapă pe un rând (bara laterală face wrap automat, nu are nevoie de trunchiere).
3. **Coloana etichetă din formularele tip etichetă/valoare — lățime minimă, ca eticheta să nu se
   rupă în mijlocul cuvântului.** Regula CSS există deja și se aplică automat prin selector
   (`.article table:not(:has(thead)) tr td:first-child:not(:last-child):not(:has(br)):not(:has(.sig-field))`,
   `width:34%;min-width:150px`) — orice tabel nou din anexe cu acest tipar (2 coloane, fără
   `<thead>`, prima celulă simplă `<td>` fără `<br>`/`.sig-field`) o primește automat, fără nimic de
   adăugat manual. Excepție intenționată: celulele cu `<br>` sau `.sig-field` (blocuri de semnătură
   — vezi punctul 4) și tabelele cu `<thead>` (date de referință, nu formulare de completat). Dacă
   adaugi vreodată un alt tipar de celulă cu conținut multi-linie care NU e etichetă/valoare
   simplă, exclude-l explicit din selector (după modelul `:not(:has(...))`), altfel primește din
   greșeală `width:34%` și strică lățimile coloanelor (verificat cu `getBoundingClientRect` — a fost
   exact regresia produsă când am introdus `.sig-field`, până am adăugat excepția).
4. **Blocul de semnătură din formulare — câmpurile pe rânduri separate, aliniate la marginea din
   dreapta.** Fiecare câmp e o linie flex (`.sig-field`) cu eticheta la stânga și o linie de completat
   (`.sig-line`, `border-bottom`, `flex:1`) care se întinde automat până la marginea din dreapta a
   celulei — identic indiferent dacă blocul are 2 sau 3 coloane (verificat cu `getBoundingClientRect`:
   toate liniile se termină la exact același pixel). Formatul canonic, într-o singură celulă de tabel:
   ```html
   <strong>Rol</strong><div class="sig-field"><span>Nume:</span><span class="sig-line"></span></div><div class="sig-field"><span>Funcție:</span><span class="sig-line"></span></div><div class="sig-field"><span>Data:</span><span class="sig-line"></span></div><div class="sig-field"><span>Semnătura:</span><span class="sig-line"></span></div>
   ```
   NU folosi underscore-uri (`___`) pentru linia de completat — nu se pot alinia consistent la
   marginea dreaptă în font proporțional și la lățimi de celulă diferite (2 vs 3 coloane); CSS-ul
   de mai sus rezolvă asta corect, automat.
5. **Valorile de completat din formulare (celula-valoare dintr-un rând etichetă/valoare) — linie
   CSS, NU underscore-uri.** Un `<td>` a cărui valoare e „de completat de mână" (nu are text real)
   nu se scrie ca `<td>__________</td>` — underscore-urile lungi trec pe mai multe rânduri urât la
   lățimi de celulă mai mici, cu tăietura de wrapping în mijlocul liniei. În loc de asta:
   - **O singură linie de completat:** `<td class="value-line"></td>` (clasa pune `border-bottom`
     direct pe celulă — nicio altă marcă în interior).
   - **Spațiu de scris pe mai multe rânduri** (câmpuri narative lungi — descrieri, motivări,
     sinteze): `<td><div class="value-lines"><span class="vline"></span><span class="vline"></span>…</div></td>`,
     cu câte un `<span class="vline">` pentru fiecare rând dorit (de obicei 2–4, după cât spațiu
     de scris are nevoie câmpul respectiv — nu după numărul de caractere din vechiul underscore).
   - **Blancurile scurte, inline, cu format fix** (zi/lună/an, numere de decizie, ex. „Nr. ___ din
     ___ / ___ / ____") RĂMÂN underscore-uri simple în text — nu sunt „valoare de completat"
     în sensul de mai sus, ci câmpuri de lățime fixă; nu li se aplică `.value-line`.

### Proceduri de lucru (`proceduri/`)
- Documente subordonate RI, câte unul per procedură (ex. `proceduri/ADC-BEN-01_Procedura_Beneficii.html`),
  administrate prin Registrul din Anexa nr. 13 a RI. Folosesc **exact același template** (CSS, topbar,
  hero, TOC, gate script, footer, script-urile de platformă) ca ROI — la o procedură nouă, copiază
  structura unei proceduri existente în loc să reinventezi.
- **Hub central:** `proceduri/index.html` listează toate procedurile (publicate + „în pregătire") într-un
  card grid (`.proto-index`/`.proto-grid`/`.proto-card`). Cardul „Proceduri de lucru" de pe homepage
  indică mereu spre acest hub, **nu** spre o procedură anume — așa nu trebuie schimbat la fiecare
  procedură nouă, doar hub-ul se actualizează.
- **Bară de taburi între proceduri:** fiecare pagină de procedură are, sub topbar și deasupra hero-ului,
  un `<nav class="proc-tabs">` cu un tab per procedură (publicate = link `.proc-tab`, în pregătire =
  `.proc-tab.soon` fără link) plus un tab final spre hub (`.proc-tab.hub`). **La orice procedură nouă
  adăugată sau publicată, actualizează acest bloc identic în TOATE paginile din `proceduri/`** (inclusiv
  hub-ul, care nu are tab-bar propriu dar trebuie să reflecte aceeași listă în `.proto-grid`) — altfel
  taburile ies desincronizate între pagini.
- Adăugarea tab-bar-ului împinge conținutul sub el cu ~44px (~36px pe mobil) — la o pagină de procedură
  nouă, pornește de la CSS-ul unei proceduri existente (nu de la ROI direct), ca să moștenești automat
  offset-urile corecte (`.toc-side{top:122px}`, `scroll-margin-top:122px` pe `h2`/`h3`, sertarul mobil
  la `top:96px`) — altfel linkurile de ancoră aterizează sub taburi.
- Fiecare procedură are cheie de acces proprie (`localStorage` `adcAuthBEN` etc.) și buton „Partajează",
  la fel ca manualele — adaugă intrarea corespunzătoare în obiectul `SHARE` din `index.html`. Hub-ul are
  și el propria cheie (`adcAuthPROC`) **și** acceptă cheia oricărei proceduri publicate (lista `PROC_KEYS`
  din gate-ul hub-ului) — la o procedură nouă cu cheie proprie, adaugă intrarea și acolo.
- Nu are încă o editoare desemnată; Vlad administrează direct conținutul până va desemna pe cineva.
- Sursa fiecărei proceduri: primită de la Vlad ca PDF, convertit direct în HTML (extragere de text +
  tabele) — nu presupune că fișierul PDF original rămâne în repo.

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
