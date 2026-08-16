// Generat automat de scripts/gen-html-manual-revision-map.py — NU edita manual.
// Regenerează după orice PR care adaugă un rând nou în Registrul de modificări:
//   python3 scripts/gen-html-manual-revision-map.py medici
//
// Gol la migrarea la HTML static (rev. 30): reviziile 1-29 au precedat
// structura pe care acest script o poate diferenția (conținutul era în
// manual-data.js), iar rev. 30 este chiar migrarea — schimbare structurală,
// fără toggle. Prima revizie cu toggle real va fi rev. 31+.
window.MEDICI_REVISION_MAP = {};
