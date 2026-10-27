# Umsetzung

Dieser Abschnitt zeigt, wie das Handbuch technisch auf die Website kommt. Er gilt für jede Technik, ob Astro, eine Webapp mit Supabase oder WordPress.

## Dateien ins Projekt übernehmen

| Datei aus dem Logopaket | Ziel im Projekt |
| --- | --- |
| `05_Wortmarke/nun_wortmarke_transparent.svg` | `public/logo/wortmarke.svg` |
| `05_Wortmarke/nun_wortmarke_transparent_hell.svg` | `public/logo/wortmarke-hell.svg` |
| `03_Logo_quer/nun_logo_quer_transparent_hell.svg` | `public/logo/logo-quer-hell.svg` |
| `01_Logo/nun_logo_transparent.svg` | `public/logo/logo.svg` |
| `08_Web_und_App/favicon.ico` | `public/favicon.ico` |
| `08_Web_und_App/app_symbol_nachtblau.svg` | `public/favicon.svg` |
| `08_Web_und_App/apple-touch-icon.png` | `public/apple-touch-icon.png` |
| `08_Web_und_App/icon-192.png`, `icon-512.png` | `public/` |

Die Farben, Abstände und Schriften stehen als CSS-Variablen in der Datei `tokens.css` dieses Handbuchs. Sie wird einmal global eingebunden. Danach nutzt jede Seite nur noch die Namen, etwa `var(--nachtblau)` oder `var(--space-4)`, und nie feste Farbwerte.

## Kopf jeder Seite

```html
<html lang="de" data-theme="light">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <link rel="icon" href="/favicon.ico" sizes="32x32">
  <link rel="icon" href="/favicon.svg" type="image/svg+xml">
  <link rel="apple-touch-icon" href="/apple-touch-icon.png">
  <link rel="manifest" href="/site.webmanifest">
  <meta name="theme-color" content="#F5EFE2" media="(prefers-color-scheme: light)">
  <meta name="theme-color" content="#1F2E4D" media="(prefers-color-scheme: dark)">
  <link rel="stylesheet" href="/css/fonts.css">
  <link rel="stylesheet" href="/css/tokens.css">
</head>
```

Die Datei `site.webmanifest` für die Installation als App:

```json
{
  "name": "NUN",
  "short_name": "NUN",
  "icons": [
    { "src": "/icon-192.png", "sizes": "192x192", "type": "image/png" },
    { "src": "/icon-512.png", "sizes": "512x512", "type": "image/png" }
  ],
  "background_color": "#F5EFE2",
  "theme_color": "#1F2E4D",
  "display": "standalone"
}
```

## Logo im hellen und dunklen Thema

Die Wortmarke wechselt mit dem Thema die Datei. So bleibt der goldene Punkt immer gold.

```html
<a href="/" class="logo" aria-label="NUN Startseite">
  <img class="logo-hell" src="/logo/wortmarke.svg" alt="NUN" height="36">
  <img class="logo-dunkel" src="/logo/wortmarke-hell.svg" alt="NUN" height="36">
</a>
```

```css
.logo-dunkel { display: none; }
[data-theme="dark"] .logo-hell { display: none; }
[data-theme="dark"] .logo-dunkel { display: inline; }
```

## Schriften lokal einbinden

Die vier Schriften werden von Google Fonts einmal heruntergeladen (zum Beispiel über google-webfonts-helper oder Fontsource) und als WOFF2 auf den eigenen Server gelegt. Benötigt werden diese Schnitte.

| Schrift | Schnitte |
| --- | --- |
| Cormorant Garamond | 500, 600, 400 kursiv |
| Source Serif 4 | 400, 400 kursiv, 600 |
| Inter | 400, 500 |
| Amiri | 400, 700 |

```css
@font-face {
  font-family: "Cormorant Garamond";
  src: url("/fonts/cormorant-garamond-500.woff2") format("woff2");
  font-weight: 500;
  font-display: swap;
}
```

## Metadaten für Google Scholar

Jede Artikelseite trägt im Kopf die Angaben, die Google Scholar liest. Damit erscheinen die Beiträge dort mit Autor, Jahr und PDF.

```html
<meta name="citation_title" content="Titel des Beitrags">
<meta name="citation_author" content="Bilger, Can">
<meta name="citation_publication_date" content="2026/10/27">
<meta name="citation_journal_title" content="NUN">
<meta name="citation_language" content="de">
<meta name="citation_pdf_url" content="https://…/beitrag.pdf">
<meta name="citation_doi" content="10.5281/zenodo.0000000">
<meta name="citation_volume" content="1">
<meta name="citation_issue" content="1">
<meta name="citation_firstpage" content="12">
<meta name="citation_lastpage" content="34">
<meta name="citation_issn" content="0000-0000">
<meta name="citation_keywords" content="Fiqh; Idschmaa'; Hanafiyyah">
<meta name="DC.rights" content="https://creativecommons.org/licenses/by/4.0/">
<link rel="license" href="https://creativecommons.org/licenses/by/4.0/">
```

Bei Abschlussarbeiten kommen `citation_dissertation_institution` (Islamologisches Institut / FIS Novi Pazar) und `citation_dissertation_name` (Bachelorarbeit) dazu, statt Jahrgang und Heft.

Zusätzlich steht im Quelltext ein Block nach Schema.org vom Typ `ScholarlyArticle` mit Titel, Autor, Datum, DOI, Lizenz und `isAccessibleForFree: true`. So erkennen Suchmaschinen den freien Zugang.

## Daten eines Beitrags

Damit Website, PDF, Zitiervorschlag und Metadaten immer übereinstimmen, liegen die Angaben einmal in der Datenbank.

| Feld | Beispiel |
| --- | --- |
| format | artikel, abschlussarbeit, kurzbeitrag, uebersetzung, arbeitspapier, rezension, buch, podcast |
| rubrik | fiqh |
| titel, untertitel | Text |
| autoren | Name, Abschluss, Abschlussjahr, ORCID-iD |
| ausgabe | Jahrgang, Heft, Jahreszeit, Seiten (leer bei laufenden Formaten) |
| datum | Erscheinungsdatum |
| doi | 10.5281/zenodo.0000000 |
| lizenz | CC BY 4.0 |
| abstract_de, abstract_en | Text |
| schlagworte | bis zu fünf |
| pdf | Datei aus dem Upload-Feld |
| version | 1, 2, … mit Datum und Hinweis zur Korrektur |

## PDF-Vorlage für Beiträge

Damit Website und PDF zusammengehören, gelten für die PDFs dieselben Regeln.

- A4, Ränder 25 mm, Logo quer ohne Leitsatz `transparent` oben links, 40 mm breit.
- Titel in Cormorant Garamond 24 pt, Fließtext in Source Serif 4 mit 10,5 pt auf 15 pt.
- Abstract auf einer Fläche in Gold-Hauch #EDE4D0.
- Erste Seite mit Format und Rubrik, Titel, Autorenzeile mit Abschluss, Ausgabe, DOI, Lizenzhinweis CC BY 4.0, Abstract und Zitiervorschlag.
- Fußzeile mit Seitenzahl, Kurztitel, DOI und "NUN · Damit wir einander kennen" in 8 pt.
