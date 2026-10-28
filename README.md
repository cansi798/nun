# NUN

Website von NUN, Jahrbuch für Islamologie. Herausgegeben vom Islamologischen Institut, Wien.

Die Seite ist rein statisch: HTML-Seiten, eine CSS-Datei, Schriften und Logos. Sie braucht keinen Bauschritt, keine Datenbank und keine Cookies und läuft auf GitHub Pages wie auf jedem Webserver.

## Aufbau

| Datei oder Ordner | Inhalt |
| --- | --- |
| `index.html` | Startseite |
| `lesen.html`, `beitrag.html` | Beitragsübersicht mit Rubrikfilter, Beitragsseite |
| `jahrbuch.html` | Der aktuelle Band, Inhalt, Entstehung, Aufruf |
| `hoeren-und-sehen.html` | Podcast und Video |
| `islamologentag.html` | Programm, Anmeldung, Rückblick |
| `seminare.html` | Lehre am Institut |
| `autoren.html` | Autorinnen und Autoren, Schreiben für NUN |
| `ueber.html`, `bezug.html`, `begriffe.html`, `suche.html`, `kontakt.html`, `impressum.html` | Haus, Bezug, Glossar, Suche, Kontakt, Impressum |
| `assets/css/nun.css` | Gestaltung, alle Farben und Maße |
| `assets/logo/` | Logos als SVG aus dem Markenpaket |
| `assets/fonts/` | Archivo als Webschrift, lokal, keine fremden Server |

## Veröffentlichen

Unter Settings, Pages, Source auf „GitHub Actions“ stellen. Jeder Push auf `main` veröffentlicht die Seite unter https://cansi798.github.io/nun/. Steht Source auf „Deploy from a branch“ mit `main` und `/ (root)`, läuft die Seite ebenfalls, dann ohne den Workflow.

## Pflege

Texte stehen direkt in den HTML-Dateien. Kopf und Fuß sind in jeder Datei gleich aufgebaut, eine Änderung dort wird in allen Dateien nachgezogen. Neue Beiträge entstehen als Kopie von `beitrag.html`.
