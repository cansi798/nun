# NUN

NUN ist eine wissenschaftliche Open-Access-Plattform für islamische Publikationen in Deutschland, Österreich und der Schweiz. Absolventinnen und Absolventen des Islamologischen Instituts veröffentlichen hier Fachartikel, Abschlussarbeiten, Übersetzungen und Bücher, frei zugänglich für alle.

> Damit wir einander kennen

Wissenschaftlich und journalistisch hochwertige Beiträge zu Religion, Denken und Gesellschaft, in sechs Formen. Quellen, Studie, Essay, Reportage, Gespräch und Vortrag. Die Formen stehen in `content/site.json` unter `formate`, die wissenschaftlichen Arten einer Studie (Fachartikel, Abschlussarbeit, Kurzbeitrag und weitere) unter `arten`.

Vorschau https://cansi798.github.io/nun/

## Technik

- [Astro](https://astro.build) 5 erzeugt eine rein statische Seite. Sie läuft auf jedem Webserver, ohne Datenbank im Betrieb.
- Inhalte kommen heute aus `content/`, später aus [PocketBase](https://pocketbase.io). Umgeschaltet wird mit `NUN_QUELLE=pocketbase`, siehe `pocketbase/README.md`.
- Gestaltung nach dem CI-Handbuch in `design-system/`. `src/styles/tokens.css` wird aus `design-system/tokens.json` erzeugt und nie von Hand geändert.
- Mobile first. Die Grundregeln in `src/styles/site.css` gelten für das Telefon, ab 640 px folgt das Tablet, ab 960 px der Desktop.
- Schriften liegen lokal (DSGVO). Es werden keine fremden Server angefragt.

## Aufbau

| Ordner | Inhalt |
| --- | --- |
| `content/` | `site.json` mit Formaten und Rubriken, `autoren.json`, `ausgaben.json`, `beitraege/*.json` |
| `public/` | Logos aus dem Logopaket, Icons, PDFs der Beiträge |
| `src/lib/` | Datenzugriff (`daten.ts`), Zitate und Links (`hilfen.ts`), Typen |
| `src/components/` | Bausteine aus dem Handbuch, etwa PublicationCard, ArtikelKopf, Zitiervorschlag, ThemenFilter |
| `src/pages/` | alle Seiten, dazu `zitat.bib`, `zitat.ris`, Sitemap und Manifest |
| `pocketbase/` | Schema der Sammlungen und Anleitung |
| `design-system/` | das CI-Handbuch mit Tokens und Komponentenbeschreibungen |
| `site/` | gebaute Fassung für GitHub Pages |

## Arbeiten

Benötigt wird Node 20 oder neuer.

```
npm install
npm run dev          # Vorschau unter http://localhost:4321
npm run build        # baut nach dist/
npm test             # prüft dist/ (Seiten, Links, Metadaten, Tokens, Alternativtexte)
```

### Neuer Beitrag

1. PDF nach `public/pdf/<slug>.pdf` legen.
2. Datei `content/beitraege/<slug>.json` anlegen. Am einfachsten über das Formular unter `/intern/`, das die Datei erzeugt.
3. Pflichtfelder sind slug, format (die Form), rubrik, titel, autoren, datum und abstract_de. Optional ist art, etwa abschlussarbeit. Form, Art und Rubrik müssen in `content/site.json` stehen. Höchstens fünf Schlagworte.
4. `npm run build`. Fehlerhafte Angaben brechen den Bau mit einer klaren Meldung ab.

## Veröffentlichen

**Eigener Server.** `NUN_SITE=https://nun.example.org npm run build` und den Ordner `dist/` hochladen. Unter einem Unterpfad zusätzlich `NUN_BASE=/pfad/` setzen.

**GitHub Pages (Vorschau).** Pages steht auf Deploy from branch. `./scripts/pages.sh` baut nach `site/`, danach committen und pushen. Jeder Push startet außerdem den Workflow in `.github/workflows/pages.yml`, der baut und testet.

## Offene Punkte

- ISSN bei der Deutschen Nationalbibliothek beantragen und in `content/site.json` eintragen
- DOIs über Zenodo vergeben und in die Beiträge eintragen
- Impressum und Datenschutz ausfüllen und prüfen lassen
- Autorenseite mit Abschlussjahr, Bachelorarbeit und ORCID ergänzen
- PocketBase-Server einrichten und Inhalte mit `npm run pb:import` übertragen
