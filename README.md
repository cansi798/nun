# NUN

NUN ist eine wissenschaftliche Open-Access-Plattform für islamische Publikationen in Deutschland, Österreich und der Schweiz. Hier veröffentlichen Absolventinnen und Absolventen des Islamologischen Instituts Fachartikel, Abschlussarbeiten, Übersetzungen und Bücher zu allen Fächern ihres Studiums. Alle Beiträge sind frei zugänglich unter CC BY 4.0.

> Damit wir einander kennen

Dieses Repository enthält die statische Website. Sie wird mit `build.py` erzeugt und braucht nur Python 3 mit der Standardbibliothek.

## Aufbau

| Pfad | Inhalt |
| --- | --- |
| `build.py` | Generator. Liest `content/`, prüft die Daten und schreibt die fertige Seite nach `dist/` |
| `content/site.json` | Name, ISSN, Lizenz, Navigation, Formate und Rubriken |
| `content/autoren.json` | Autorinnen und Autoren |
| `content/ausgaben.json` | Hefte mit Jahrgang, Heft und Jahreszeit |
| `content/beitraege/*.json` | ein Beitrag pro Datei |
| `static/` | Dateien, die unverändert kopiert werden (CSS, JavaScript, Schriften, Logos, PDFs) |
| `design-system/` | Handbuch, Umsetzung, Komponenten und `tokens.json` |
| `tests/` | Tests für den Generator |
| `.github/workflows/pages.yml` | Bauen und Veröffentlichen auf GitHub Pages |

Aus jedem Beitrag entstehen Artikelseite, Metadaten für Google Scholar, ein Block nach Schema.org, der Zitiervorschlag nach APA 7 sowie `zitat.bib` und `zitat.ris`. So stimmen alle Angaben immer überein.

## Lokal bauen und ansehen

```sh
python3 build.py && python3 -m http.server -d dist 8000
```

Danach ist die Seite unter `http://localhost:8000` erreichbar. Für eine Seite in einem Unterordner gibt es die Optionen `--base` und `--url`.

```sh
python3 build.py --base /nun/ --url https://cansi798.github.io
```

Die Tests laufen mit diesem Befehl.

```sh
python3 -m unittest discover -s tests -v
```

## Neuen Beitrag anlegen

1. Das PDF nach `static/pdf/<slug>.pdf` legen.
2. Eine Datei `content/beitraege/<slug>.json` anlegen. Am einfachsten kopieren Sie einen vorhandenen Beitrag und passen ihn an.
3. `python3 build.py` ausführen. Der Generator meldet fehlende Pflichtfelder, unbekannte Rubriken, Formate, Autoren oder Ausgaben und bricht dann ab.

| Feld | Bedeutung |
| --- | --- |
| `slug` | Adresse des Beitrags, nur a bis z, Ziffern und Bindestrich |
| `format` | artikel, abschlussarbeit, kurzbeitrag, uebersetzung, arbeitspapier, rezension, buch oder podcast |
| `rubrik` | Slug einer Rubrik aus `content/site.json`, etwa `fiqh` |
| `titel`, `untertitel` | Text |
| `autoren` | Liste von Slugs aus `content/autoren.json` |
| `ausgabe`, `seiten` | ID aus `content/ausgaben.json` und erste und letzte Seite, leer bei laufenden Formaten |
| `datum` | Erscheinungsdatum als JJJJ-MM-TT |
| `doi` | etwa `10.5281/zenodo.0000000`, leer solange noch keine DOI vergeben ist |
| `abstract_de`, `abstract_en` | Text |
| `schlagworte` | bis zu fünf |
| `pdf` | Pfad unter `static/`, etwa `pdf/<slug>.pdf` |
| `version`, `versionen` | Nummer und Liste früherer Fassungen mit Datum und Hinweis |
| `inhalt` | optionale Textblöcke vom Typ absatz, h2, h3, liste, nummern, zitat oder aaya |

Pflicht sind `slug`, `format`, `rubrik`, `titel`, `autoren`, `datum`, `abstract_de` und `schlagworte`. Die Lizenz CC BY 4.0 gilt für alle Beiträge und steht in `content/site.json`.

## Design-Tokens

Farben, Abstände und Schriften stehen in `design-system/tokens.json`. Daraus erzeugt `build.py` bei jedem Lauf die Datei `css/tokens.css`. Sie wird nicht von Hand geändert. `static/css/site.css` nutzt nur die Variablen daraus und keine festen Farbwerte. Ein Test prüft das.

## Veröffentlichung

Die Seite liegt unter https://cansi798.github.io/nun/site/ und wird aus dem Ordner `site/` im Zweig `main` ausgeliefert (Pages im Modus Deploy from branch). Vor jedem Push wird sie deshalb neu gebaut.

```
python3 build.py --base /nun/site/ --url https://cansi798.github.io --out site
git add -A && git commit && git push
```

Jeder Push startet außerdem den Workflow in `.github/workflows/pages.yml`, der die Tests ausführt. Für saubere Adressen ohne `site/` stellt man einmalig unter Settings, Pages, Source auf "GitHub Actions" um und entfernt im Workflow die Zeile `if` beim Schritt deploy. Danach baut und veröffentlicht der Workflow `dist/` selbst, und der Ordner `site/` kann entfallen.

## Offene Punkte

- ISSN bei der Deutschen Nationalbibliothek beantragen und in `content/site.json` eintragen.
- DOIs über Zenodo vergeben und in die Beiträge eintragen.
- Impressum und Datenschutz ausfüllen und rechtlich prüfen lassen.
- Echte Autorendaten mit Abschlussjahr, Bio und ORCID-iD ergänzen.
- Der Upload-Bereich unter `intern/` arbeitet nur im Browser. Für echtes Hochladen braucht er später ein Backend.
