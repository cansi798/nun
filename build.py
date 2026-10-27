#!/usr/bin/env python3
"""Baut die statische Website von NUN aus content/ nach dist/.

Nur Python-Standardbibliothek. Aufruf

    python3 build.py                                    # lokal, Basis "/"
    python3 build.py --base /nun/ --url https://cansi798.github.io/nun

Alle Angaben eines Beitrags liegen einmal in content/beitraege/<slug>.json.
Daraus entstehen Artikelseite, Scholar-Metadaten, Schema.org, APA-Zitat,
BibTeX und RIS, damit sie immer übereinstimmen (Handbuch, Abschnitt Umsetzung).
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
from datetime import date
from html import escape
from pathlib import Path

ROOT = Path(__file__).resolve().parent
CONTENT = ROOT / "content"
STATIC = ROOT / "static"
TOKENS = ROOT / "design-system" / "tokens.json"

MONATE = ["Januar", "Februar", "März", "April", "Mai", "Juni", "Juli",
          "August", "September", "Oktober", "November", "Dezember"]
PFLICHTFELDER = ["slug", "format", "rubrik", "titel", "autoren", "datum",
                 "abstract_de", "schlagworte"]


def e(text) -> str:
    return escape(str(text), quote=True)


# --------------------------------------------------------------------------
# Daten laden und prüfen
# --------------------------------------------------------------------------

class Daten:
    def __init__(self, base: str, url: str):
        self.base = base
        self.url = url.rstrip("/")
        self.site = json.loads((CONTENT / "site.json").read_text("utf-8"))
        self.autoren = {a["slug"]: a for a in json.loads((CONTENT / "autoren.json").read_text("utf-8"))}
        self.ausgaben = {a["id"]: a for a in json.loads((CONTENT / "ausgaben.json").read_text("utf-8"))}
        self.formate = {f["slug"]: f for f in self.site["formate"]}
        self.rubriken = {r["slug"]: r for r in self.site["rubriken"]}
        self.beitraege = sorted(
            (json.loads(p.read_text("utf-8")) for p in (CONTENT / "beitraege").glob("*.json")),
            key=lambda b: b["datum"], reverse=True)

    def pruefe(self) -> list[str]:
        fehler = []
        slugs = set()
        for b in self.beitraege:
            name = b.get("slug", "?")
            for feld in PFLICHTFELDER:
                if not b.get(feld):
                    fehler.append(f"{name}: Pflichtfeld '{feld}' fehlt")
            if name in slugs:
                fehler.append(f"{name}: slug doppelt vergeben")
            slugs.add(name)
            if b.get("format") not in self.formate:
                fehler.append(f"{name}: unbekanntes Format '{b.get('format')}'")
            if b.get("rubrik") not in self.rubriken:
                fehler.append(f"{name}: unbekannte Rubrik '{b.get('rubrik')}'")
            for a in b.get("autoren", []):
                if a not in self.autoren:
                    fehler.append(f"{name}: unbekannte Autorin oder unbekannter Autor '{a}'")
            if b.get("ausgabe") and b["ausgabe"] not in self.ausgaben:
                fehler.append(f"{name}: unbekannte Ausgabe '{b['ausgabe']}'")
            if len(b.get("schlagworte", [])) > 5:
                fehler.append(f"{name}: höchstens fünf Schlagworte erlaubt")
            if not re.fullmatch(r"[a-z0-9-]+", name):
                fehler.append(f"{name}: slug nur aus a-z, 0-9 und Bindestrich")
            try:
                date.fromisoformat(b.get("datum", ""))
            except ValueError:
                fehler.append(f"{name}: datum muss JJJJ-MM-TT sein")
        return fehler

    # Hilfen für Pfade und Werte
    def link(self, pfad: str = "") -> str:
        return self.base + pfad

    def absolut(self, pfad: str = "") -> str:
        return f"{self.url}{self.base}{pfad}" if self.url else self.base + pfad

    def beitraege_von(self, autor: str):
        return [b for b in self.beitraege if autor in b["autoren"]]

    def beitraege_in(self, ausgabe: str):
        return sorted((b for b in self.beitraege if b.get("ausgabe") == ausgabe),
                      key=lambda b: (b.get("seiten") or [0])[0])


def datum_lang(iso: str) -> str:
    d = date.fromisoformat(iso)
    return f"{d.day}. {MONATE[d.month - 1]} {d.year}"


def ausgabe_text(a: dict) -> str:
    return f"Jahrgang {a['jahrgang']} · Heft {a['heft']} · {a['jahreszeit']} {a['jahr']}"


def autor_name(a: dict) -> str:
    return f"{a['vorname']} {a['nachname']}"


# --------------------------------------------------------------------------
# Zitate: APA 7, BibTeX, RIS
# --------------------------------------------------------------------------

def apa_autoren(autoren: list[dict]) -> str:
    namen = [f"{a['nachname']}, " + " ".join(f"{t[0]}." for t in re.split(r"[\s-]+", a["vorname"]) if t)
             for a in autoren]
    if len(namen) == 1:
        return namen[0]
    return ", ".join(namen[:-1]) + ", & " + namen[-1]


def zitier_url(d: Daten, b: dict) -> str:
    """DOI-Link, solange keine DOI vergeben ist die Adresse der Artikelseite."""
    return f"https://doi.org/{b['doi']}" if b.get("doi") else d.absolut(f"beitraege/{b['slug']}/")


def apa(d: Daten, b: dict, html: bool = True) -> str:
    """Zitiervorschlag nach APA 7. Mit html=True kursiv und mit DOI-Link."""
    kursiv = (lambda s: f"<i>{e(s)}</i>") if html else (lambda s: s)
    autoren = [d.autoren[a] for a in b["autoren"]]
    jahr = b["datum"][:4]
    titel = e(b["titel"]) if html else b["titel"]
    doi = zitier_url(d, b)
    doi_teil = f'<a href="{e(doi)}">{e(doi)}</a>' if html else doi
    teile = f"{e(apa_autoren(autoren)) if html else apa_autoren(autoren)} ({jahr}). "
    if b.get("ausgabe"):
        a = d.ausgaben[b["ausgabe"]]
        seiten = f", {b['seiten'][0]}–{b['seiten'][1]}" if b.get("seiten") else ""
        teile += f"{titel}. {kursiv(d.site['name'])}, {kursiv(a['jahrgang'])}({a['heft']}){seiten}. {doi_teil}"
    elif b["format"] == "abschlussarbeit":
        teile += f"{kursiv(b['titel'])} [Bachelorarbeit, {e(d.site['institut']) if html else d.site['institut']}]. {d.site['name']}. {doi_teil}"
    else:
        art = d.formate[b["format"]]["name"]
        teile += f"{kursiv(b['titel'])} [{art}]. {d.site['name']}. {doi_teil}"
    return teile


def bibtex(d: Daten, b: dict) -> str:
    autoren = " and ".join(f"{d.autoren[a]['nachname']}, {d.autoren[a]['vorname']}" for a in b["autoren"])
    typ = "article" if b.get("ausgabe") else ("thesis" if b["format"] == "abschlussarbeit" else "misc")
    felder = [("author", autoren), ("title", b["titel"]), ("year", b["datum"][:4]),
              *([("doi", b["doi"])] if b.get("doi") else []), ("url", zitier_url(d, b)),
              ("langid", "german"), ("license", d.site["lizenz"]["name"])]
    if b.get("reihe"):
        felder.append(("series", b["reihe"].split(" · ")[0]))
    if b.get("ausgabe"):
        a = d.ausgaben[b["ausgabe"]]
        felder += [("journal", d.site["name"]), ("volume", a["jahrgang"]), ("number", a["heft"]),
                   ("issn", d.site["issn"])]
        if b.get("seiten"):
            felder.append(("pages", f"{b['seiten'][0]}--{b['seiten'][1]}"))
    else:
        felder.append(("publisher", d.site["name"]))
        if typ == "thesis":
            felder += [("type", "Bachelorarbeit"), ("institution", d.site["institut"])]
    key = f"{d.autoren[b['autoren'][0]]['nachname'].lower()}{b['datum'][:4]}{b['slug'].split('-')[0]}"
    key = re.sub(r"[^a-z0-9]", "", key)
    inhalt = ",\n".join(f"  {k} = {{{v}}}" for k, v in felder)
    return f"@{typ}{{{key},\n{inhalt}\n}}\n"


def ris(d: Daten, b: dict) -> str:
    zeilen = [("TY", "JOUR" if b.get("ausgabe") else ("THES" if b["format"] == "abschlussarbeit" else "GEN"))]
    zeilen += [("AU", f"{d.autoren[a]['nachname']}, {d.autoren[a]['vorname']}") for a in b["autoren"]]
    zeilen += [("TI", b["titel"]), ("PY", b["datum"][:4]), ("DA", b["datum"].replace("-", "/")),
               *([("DO", b["doi"])] if b.get("doi") else []), ("UR", zitier_url(d, b)), ("LA", "de"),
               ("AB", b["abstract_de"])]
    zeilen += [("KW", k) for k in b["schlagworte"]]
    if b.get("ausgabe"):
        a = d.ausgaben[b["ausgabe"]]
        zeilen += [("JO", d.site["name"]), ("VL", a["jahrgang"]), ("IS", a["heft"]), ("SN", d.site["issn"])]
        if b.get("seiten"):
            zeilen += [("SP", b["seiten"][0]), ("EP", b["seiten"][1])]
    else:
        zeilen.append(("PB", d.site["name"]))
    zeilen.append(("ER", ""))
    return "\r\n".join(f"{k}  - {v}" for k, v in zeilen) + "\r\n"


# --------------------------------------------------------------------------
# Design-Tokens: tokens.json -> tokens.css
# --------------------------------------------------------------------------

def tokens_css(tokens: dict) -> str:
    hell, dunkel, rest = [], [], []
    themen = [t["id"] for t in tokens["color"]["themes"]]
    for t in tokens["color"]["tokens"]:
        wert = t["value"]
        if isinstance(wert, str):
            wert = {themen[0]: wert}
        hell.append(f"  --{t['name']}: {wert[themen[0]]};")
        if "dark" in wert and wert["dark"] != wert[themen[0]]:
            dunkel.append(f"  --{t['name']}: {wert['dark']};")
    for familie in ("spacing", "radius", "layout", "shadow"):
        for t in tokens.get(familie, {}).get("tokens", []):
            rest.append(f"  --{t['name']}: {t['value']};")
    for schluessel, stapel in tokens["type"]["families"].items():
        rest.append(f"  --font-{schluessel}: {stapel};")

    stile = []
    for gruppe in tokens["type"]["groups"]:
        fam = gruppe["family"]
        for s in gruppe["styles"]:
            regel = [f"font-family: var(--font-{fam})", f"font-size: {s['fontSize']}",
                     f"line-height: {s['lineHeight']}", f"font-weight: {s['fontWeight']}"]
            if s.get("fontStyle"):
                regel.append(f"font-style: {s['fontStyle']}")
            if s.get("letterSpacing"):
                regel.append(f"letter-spacing: {s['letterSpacing']}")
            stile.append(f".t-{s['name']} {{ {'; '.join(regel)}; }}")

    dunkel_block = "\n".join(dunkel)
    return (
        f"/* {tokens['name']} — generated from tokens.json. Nicht von Hand ändern. */\n"
        f":root {{\n{chr(10).join(hell)}\n{chr(10).join(rest)}\n  color-scheme: light;\n}}\n"
        f'[data-theme="dark"] {{\n{dunkel_block}\n  color-scheme: dark;\n}}\n'
        + "\n".join(stile) + "\n"
    )


# --------------------------------------------------------------------------
# Bausteine (siehe design-system/komponenten/)
# --------------------------------------------------------------------------

ICON_SCHLOSS = ('<svg viewBox="0 0 16 16" aria-hidden="true"><rect x="3" y="7" width="10" height="7" rx="1"/>'
                '<path d="M5.5 7V5a2.5 2.5 0 0 1 5 0"/></svg>')
ICON_LUPE = ('<svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="11" cy="11" r="7"/>'
             '<path d="m20 20-3.5-3.5"/></svg>')
ICON_MENUE = '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M4 7h16M4 12h16M4 17h16"/></svg>'
ICON_THEMA = ('<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M20 14.5A8 8 0 1 1 9.5 4a6.5 6.5 0 0 0 '
              '10.5 10.5Z"/></svg>')


def punkt() -> str:
    return '<span class="punkt" aria-hidden="true"></span>'


def kopf(d: Daten, aktiv: str) -> str:
    links = "".join(
        f'<a href="{d.link(n["pfad"])}"{" class=\"on\" aria-current=\"page\"" if n["pfad"] == aktiv else ""}>'
        f'{e(n["titel"])}</a>'
        for n in d.site["navigation"])
    return f"""<header class="kopf">
  <div class="kopf-in">
    <a class="logo" href="{d.link()}" aria-label="NUN Startseite">
      <img class="nur-hell" src="{d.link('logo/wortmarke.svg')}" alt="NUN" width="160" height="90">
      <img class="nur-dunkel" src="{d.link('logo/wortmarke-hell.svg')}" alt="NUN" width="160" height="90">
    </a>
    <nav class="hauptnav" id="hauptnav" aria-label="Hauptnavigation">{links}</nav>
    <div class="kopf-knoepfe">
      <button class="icon-knopf" type="button" data-thema-wechsel aria-label="Helles oder dunkles Thema">{ICON_THEMA}</button>
      <button class="icon-knopf menue-knopf" type="button" aria-controls="hauptnav" aria-expanded="false" aria-label="Menü">{ICON_MENUE}</button>
    </div>
  </div>
</header>"""


def fuss(d: Daten) -> str:
    def spalte(titel, eintraege):
        li = "".join(f'<li><a href="{d.link(p)}">{e(t)}</a></li>' for t, p in eintraege)
        return f"<div><h2 class=\"fuss-titel\">{e(titel)}</h2><ul>{li}</ul></div>"
    return f"""<footer class="fuss">
  <div class="fuss-in">
    <div class="fuss-oben">
      <img class="fuss-logo" src="{d.link('logo/logo-quer-hell.svg')}" alt="NUN, Damit wir einander kennen" width="240" height="88">
      <div class="fuss-spalten">
        {spalte("Inhalte", [("Publikationen", "publikationen/"), ("Ausgaben", "ausgaben/"), ("Abschlussarbeiten", "publikationen/?format=abschlussarbeit"), ("Podcast", "podcast/")])}
        {spalte("NUN", [("Über uns", "ueber-uns/"), ("Autoren", "autoren/"), ("Open Access", "open-access/"), ("Interner Bereich", "intern/")])}
      </div>
    </div>
    <div class="fuss-unten">
      <span>Alle Beiträge frei zugänglich unter {e(d.site['lizenz']['name'])} · ISSN {e(d.site['issn'])}</span>
      <span><a href="{d.link('impressum/')}">Impressum</a><a href="{d.link('datenschutz/')}">Datenschutz</a><a href="{d.link('ueber-uns/#kontakt')}">Kontakt</a></span>
    </div>
  </div>
</footer>"""


def kennzeile(d: Daten, b: dict, mit_lesezeit: bool = True) -> str:
    teile = [e(d.formate[b["format"]]["name"]), e(d.rubriken[b["rubrik"]]["name"])]
    if mit_lesezeit and b.get("lesezeit"):
        teile.append(f"{b['lesezeit']} Min Lesezeit")
    return f'<div class="meta kennzeile">{punkt().join(teile)}</div>'


def karte(d: Daten, b: dict) -> str:
    autoren = ", ".join(autor_name(d.autoren[a]) for a in b["autoren"])
    such = " ".join([b["titel"], b.get("untertitel", ""), autoren, *b["schlagworte"]]).lower()
    return f"""<article class="karte" data-rubrik="{e(b['rubrik'])}" data-format="{e(b['format'])}" data-suche="{e(such)}">
  {kennzeile(d, b)}
  <h3 class="t-h3"><a class="karte-link" href="{d.link('beitraege/' + b['slug'] + '/')}">{e(b['titel'])}</a></h3>
  <p class="unterzeile">{e(autoren)} · {datum_lang(b['datum'])}</p>
  <p class="karte-abstract">{e(b['abstract_de'])}</p>
  <span class="textlink" aria-hidden="true">Artikel lesen</span>
</article>"""


def ausgabe_karte(d: Daten, a: dict, mit_inhalt_link: bool = True) -> str:
    beitraege = d.beitraege_in(a["id"])
    titel_liste = "".join(f"<li>{e(b['titel'])}</li>" for b in beitraege[:3])
    links = []
    if mit_inhalt_link:
        links.append(f'<a class="textlink" href="{d.link("ausgaben/" + a["id"] + "/")}">Inhaltsverzeichnis</a>')
    if a.get("pdf"):
        links.append(f'<a class="textlink" href="{d.link(a["pdf"])}">Gesamt-PDF</a>')
    anzahl = f"{len(beitraege)} Beitrag" if len(beitraege) == 1 else f"{len(beitraege)} Beiträge"
    return f"""<article class="ausgabe-karte">
  <div class="heft-titel" aria-hidden="true">
    <img src="{d.link('logo/emblem-hell.svg')}" alt="" width="110" height="110">
    <b>NUN</b><span>Jahrgang {a['jahrgang']} · Heft {a['heft']}</span>
  </div>
  <div>
    <div class="meta gold">Jahrgang {a['jahrgang']} · Heft {a['heft']} · {e(a['jahreszeit'])} {a['jahr']}</div>
    <h3 class="t-h3">{e(a['titel'])}</h3>
    <p class="unterzeile">{anzahl} · ISSN {e(d.site['issn'])}</p>
    <ul class="punktliste">{titel_liste}</ul>
    <div class="link-zeile">{''.join(links)}</div>
  </div>
</article>"""


def aaya(block: dict) -> str:
    return f"""<figure class="aaya">
  <p class="t-arabisch aaya-ar" dir="rtl" lang="ar">{e(block['arabisch'])}</p>
  <p class="aaya-de">{e(block['uebersetzung'])}</p>
  <figcaption class="meta gold">{e(block['quelle'])}</figcaption>
</figure>"""


def inhalt_html(bloecke: list[dict]) -> str:
    teile = []
    for b in bloecke:
        typ = b["typ"]
        if typ == "absatz":
            teile.append(f"<p>{e(b['text'])}</p>")
        elif typ in ("h2", "h3"):
            anker = re.sub(r"[^a-z0-9]+", "-", b["text"].lower()).strip("-")
            teile.append(f'<{typ} class="t-{typ}" id="{anker}">{e(b["text"])}</{typ}>')
        elif typ == "aaya":
            teile.append(aaya(b))
        elif typ == "liste":
            teile.append('<ul class="punktliste">' + "".join(f"<li>{e(p)}</li>" for p in b["punkte"]) + "</ul>")
        elif typ == "nummern":
            teile.append('<ol class="nummernliste">' + "".join(f"<li>{e(p)}</li>" for p in b["punkte"]) + "</ol>")
        elif typ == "zitat":
            teile.append(f"<blockquote><p>{e(b['text'])}</p></blockquote>")
        else:
            raise ValueError(f"Unbekannter Inhaltsblock '{typ}'")
    return "\n".join(teile)


def seitenkopf(titel: str, einleitung: str = "", rubrik: str = "") -> str:
    r = f'<div class="meta gold">{e(rubrik)}</div>' if rubrik else ""
    l = f'<p class="t-lead einleitung">{e(einleitung)}</p>' if einleitung else ""
    return f'<div class="seitenkopf">{r}<h1 class="t-h1">{e(titel)}</h1><hr class="goldlinie">{l}</div>'


# --------------------------------------------------------------------------
# Seitenrahmen
# --------------------------------------------------------------------------

def rahmen(d: Daten, pfad: str, titel: str, inhalt: str, aktiv: str = "",
           beschreibung: str = "", kopf_extra: str = "", noindex: bool = False) -> str:
    voll = f"{titel} · NUN" if titel else f"NUN · {d.site['leitsatz']}"
    beschreibung = beschreibung or d.site["beschreibung"]
    robots = '<meta name="robots" content="noindex">' if noindex else ""
    return f"""<!doctype html>
<html lang="de" data-theme="light">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{e(voll)}</title>
<meta name="description" content="{e(beschreibung)}">
{robots}
<link rel="canonical" href="{e(d.absolut(pfad))}">
<link rel="icon" href="{d.link('favicon.ico')}" sizes="any">
<link rel="icon" href="{d.link('favicon.svg')}" type="image/svg+xml">
<link rel="apple-touch-icon" href="{d.link('apple-touch-icon.png')}">
<link rel="manifest" href="{d.link('site.webmanifest')}">
<meta name="theme-color" content="#F5EFE2" media="(prefers-color-scheme: light)">
<meta name="theme-color" content="#1F2E4D" media="(prefers-color-scheme: dark)">
<meta property="og:title" content="{e(voll)}">
<meta property="og:description" content="{e(beschreibung)}">
<meta property="og:image" content="{e(d.absolut('icon-512.png'))}">
<meta property="og:locale" content="de_DE">
<script>try{{var t=localStorage.getItem("nun-thema")||(matchMedia("(prefers-color-scheme: dark)").matches?"dark":"light");document.documentElement.dataset.theme=t}}catch(_){{}}</script>
<link rel="stylesheet" href="{d.link('css/fonts.css')}">
<link rel="stylesheet" href="{d.link('css/tokens.css')}">
<link rel="stylesheet" href="{d.link('css/site.css')}">
{kopf_extra}
</head>
<body>
<a class="sprung" href="#inhalt">Zum Inhalt springen</a>
{kopf(d, aktiv)}
<main id="inhalt">
{inhalt}
</main>
{fuss(d)}
<script src="{d.link('js/site.js')}" defer></script>
</body>
</html>
"""


# --------------------------------------------------------------------------
# Seiten
# --------------------------------------------------------------------------

def seite_start(d: Daten) -> str:
    """Startseite nach dem Mockup Startseite (Hero geteilt, Heft-Band, Themen, Reihe, Säulen)."""
    neueste = "".join(karte(d, b) for b in d.beitraege[:3])
    ausgabe = next(iter(sorted(d.ausgaben.values(), key=lambda a: (a["jahrgang"], a["heft"]), reverse=True)), None)
    themen = "".join(
        f'<a class="thema-zelle" href="{d.link("publikationen/?rubrik=" + r["slug"])}">'
        f'<span class="thema-name">{e(r["name"])}</span><span class="thema-faecher">{e(r["faecher"])}</span></a>'
        for r in d.site["rubriken"])

    heft = ""
    if ausgabe:
        beitraege = d.beitraege_in(ausgabe["id"])
        if beitraege:
            liste = "".join(f"<li>{e(b['titel'])}</li>" for b in beitraege[:3])
            anzahl = f"{len(beitraege)} Beiträge"
        else:
            liste = "<li>Die Beiträge werden zurzeit begutachtet und erscheinen vorab online.</li>"
            anzahl = "In Vorbereitung"
        pdf = (f'<a class="knopf sekundaer-invers" href="{d.link(ausgabe["pdf"])}">Gesamt-PDF</a>'
               if ausgabe.get("pdf") else "")
        heft = f"""<section class="heft-band" id="ausgaben">
  <div class="heft-band-in">
    <div class="heft-titel gross" aria-hidden="true">
      <img src="{d.link('logo/emblem-hell.svg')}" alt="" width="150" height="150">
      <b>NUN</b><span>Jahrgang {ausgabe['jahrgang']} · Heft {ausgabe['heft']}</span>
    </div>
    <div class="heft-text">
      <div class="meta gold-hell">Aktuelles Heft · {e(ausgabe['jahreszeit'])} {ausgabe['jahr']}</div>
      <h2 class="t-h1">{e(ausgabe['titel'])}</h2>
      <p class="heft-info">{anzahl} · ISSN {e(d.site['issn'])}</p>
      <ul class="punktliste invers">{liste}</ul>
      <div class="knopf-zeile">
        <a class="knopf hell" href="{d.link('ausgaben/' + ausgabe['id'] + '/')}">Inhaltsverzeichnis</a>
        {pdf}
      </div>
    </div>
  </div>
</section>"""

    saeulen = [
        ("Frei zugänglich", f"Alle Beiträge sind ohne Anmeldung lesbar und dürfen unter {d.site['lizenz']['name']} geteilt werden."),
        ("Zitierfähig", "Jeder Beitrag erhält eine DOI und einen Zitiervorschlag nach APA 7 und ist für Google Scholar ausgezeichnet."),
        ("Aus dem Studium", "Die Autorinnen und Autoren haben Islam-Wissenschaft am Islamologischen Institut studiert."),
    ]
    saeulen_html = "".join(f'<div class="saeule"><span class="saeule-punkt" aria-hidden="true"></span>'
                           f'<h3 class="t-h3">{e(t)}</h3><p>{e(x)}</p></div>' for t, x in saeulen)

    reihe = next((b["reihe"] for b in d.beitraege if b.get("reihe")), "")
    reihe_panel = f"""<div class="panel gold-flaeche">
    <div class="meta gold">Reihe</div>
    <h2 class="t-h2">{e(reihe.split(' · ')[0])}</h2>
    <p>{e(reihe.split(' · ')[1]) if ' · ' in reihe else ''}. Kompakte Bände zu Fragen, die Muslime im deutschsprachigen Raum heute bewegen, mit Quraan-Bedeutungen nach Amir Zaidan und belegten Quellen.</p>
    <a class="textlink" href="{d.link('publikationen/?format=kurzbeitrag')}">Alle Bände der Reihe</a>
  </div>""" if reihe else f"""<div class="panel gold-flaeche">
    <div class="meta gold">Abschlussarbeiten</div>
    <h2 class="t-h2">Bachelorarbeiten aus dem Studium der Islam-Wissenschaft</h2>
    <p>Überarbeitete Abschlussarbeiten, geordnet nach Jahrgang.</p>
    <a class="textlink" href="{d.link('publikationen/?format=abschlussarbeit')}">Zu den Abschlussarbeiten</a>
  </div>"""

    inhalt = f"""<section class="hero">
  <div class="hero-text">
    <div class="meta gold kennzeile">Open Access{punkt()}Islamwissenschaften im deutschsprachigen Raum</div>
    <h1 class="t-hero">Islamisches Wissen, wissenschaftlich aufbereitet und frei für alle</h1>
    <hr class="goldlinie">
    <p class="t-lead">Fachartikel, Abschlussarbeiten und Übersetzungen von Absolventinnen und Absolventen des Islamologischen Instituts. Ohne Anmeldung, ohne Bezahlschranke, mit DOI und Zitiervorschlag.</p>
    <div class="knopf-zeile">
      <a class="knopf primaer" href="{d.link('publikationen/')}">Publikationen entdecken</a>
      <a class="knopf sekundaer" href="{d.link('ausgaben/')}">Aktuelles Heft</a>
    </div>
    <p class="t-slogan leitsatz">{e(d.site['leitsatz'])}</p>
  </div>
  <div class="hero-flaeche" aria-hidden="true">
    <img src="{d.link('logo/emblem-hell.svg')}" alt="" width="440" height="440">
  </div>
</section>

<section class="abschnitt seite">
  <div class="abschnitt-kopf zeile">
    <div><h2 class="t-h1">Neue Beiträge</h2><hr class="goldlinie"></div>
    <a class="textlink" href="{d.link('publikationen/')}">Alle Publikationen</a>
  </div>
  <div class="raster">{neueste}</div>
</section>

{heft}

<section class="abschnitt seite" id="themen">
  <h2 class="t-h1">Themen</h2>
  <hr class="goldlinie">
  <p class="abschnitt-text">Die Rubriken folgen den Fächern des Studiums der Islam-Wissenschaft.</p>
  <div class="themen-gitter">{themen}</div>
</section>

<section class="abschnitt seite panels">
  {reihe_panel}
  <div class="panel" id="podcast">
    <div class="meta gold">Podcast</div>
    <h2 class="t-h2">Die Autoren im Gespräch über ihre Beiträge</h2>
    <p>Die ersten Folgen sind in Vorbereitung.</p>
    <a class="knopf primaer mit-icon" href="{d.link('podcast/')}"><svg viewBox="0 0 14 14" aria-hidden="true"><path d="M3 1.5v11l9-5.5z"/></svg>Zum Podcast</a>
  </div>
</section>

<section class="abschnitt seite saeulen" id="ueber">{saeulen_html}</section>"""
    return rahmen(d, "", "", inhalt)


def knopf_gruppe(name: str, label: str, eintraege: list[tuple[str, str]]) -> str:
    knoepfe = "".join(f'<button type="button" data-wert="{e(s)}" aria-pressed="false">{e(n)}</button>' for s, n in eintraege)
    return (f'<div class="filter-zeile" role="group" aria-label="{e(label)}" data-gruppe="{name}">'
            f'<span class="meta filter-label">{e(label)}</span>'
            f'<div class="filter-knoepfe"><button type="button" data-wert="" aria-pressed="true">Alle</button>{knoepfe}</div></div>')


def seite_publikationen(d: Daten) -> str:
    rubriken = [(r["slug"], r["name"]) for r in d.site["rubriken"]]
    formate = [(f["slug"], f["name"]) for f in d.site["formate"]]
    karten = "".join(karte(d, b) for b in d.beitraege)
    inhalt = f"""<div class="seite">
{seitenkopf("Publikationen", "Alle Beiträge auf NUN, frei zugänglich unter CC BY 4.0. Wählen Sie Rubriken und Formate oder suchen Sie nach Titel, Autor und Schlagwort.")}
<div class="filter" data-filter>
  {knopf_gruppe("rubrik", "Rubrik", rubriken)}
  {knopf_gruppe("format", "Format", formate)}
  <label class="suche"><span class="sr">Suche</span>{ICON_LUPE}<input type="search" name="q" placeholder="Titel, Autor oder Schlagwort" autocomplete="off"></label>
</div>
<p class="meta treffer" aria-live="polite" data-treffer>{len(d.beitraege)} Beiträge</p>
<div class="raster" data-liste>{karten}</div>
<p class="leer" data-leer hidden>Zu dieser Auswahl gibt es noch keine Beiträge.</p>
</div>"""
    return rahmen(d, "publikationen/", "Publikationen", inhalt, aktiv="publikationen/")


def scholar_meta(d: Daten, b: dict) -> str:
    m = [("citation_title", b["titel"])]
    m += [("citation_author", f"{d.autoren[a]['nachname']}, {d.autoren[a]['vorname']}") for a in b["autoren"]]
    m += [("citation_publication_date", b["datum"].replace("-", "/")),
          ("citation_journal_title", d.site["name"]), ("citation_language", "de"),
          ("citation_keywords", "; ".join(b["schlagworte"])),
          ("citation_abstract_html_url", d.absolut(f"beitraege/{b['slug']}/")),
          ("DC.rights", d.site["lizenz"]["url"])]
    if b.get("doi"):
        m.append(("citation_doi", b["doi"]))
    if b.get("pdf"):
        m.append(("citation_pdf_url", d.absolut(b["pdf"])))
    if b.get("ausgabe"):
        a = d.ausgaben[b["ausgabe"]]
        m += [("citation_volume", a["jahrgang"]), ("citation_issue", a["heft"]), ("citation_issn", d.site["issn"])]
        if b.get("seiten"):
            m += [("citation_firstpage", b["seiten"][0]), ("citation_lastpage", b["seiten"][1])]
    if b["format"] == "abschlussarbeit":
        m += [("citation_dissertation_institution", d.site["institut"]),
              ("citation_dissertation_name", "Bachelorarbeit")]
    zeilen = [f'<meta name="{k}" content="{e(v)}">' for k, v in m]
    zeilen.append(f'<link rel="license" href="{e(d.site["lizenz"]["url"])}">')

    ld = {
        "@context": "https://schema.org", "@type": "ScholarlyArticle",
        "headline": b["titel"], "alternativeHeadline": b.get("untertitel", ""),
        "author": [{"@type": "Person", "name": autor_name(d.autoren[a]),
                    **({"sameAs": f"https://orcid.org/{d.autoren[a]['orcid']}"} if d.autoren[a].get("orcid") else {})}
                   for a in b["autoren"]],
        "datePublished": b["datum"], "inLanguage": "de", "keywords": b["schlagworte"],
        "abstract": b["abstract_de"], "license": d.site["lizenz"]["url"],
        "isAccessibleForFree": True, "identifier": zitier_url(d, b),
        "url": d.absolut(f"beitraege/{b['slug']}/"),
        "publisher": {"@type": "Organization", "name": d.site["name"]},
    }
    if b.get("ausgabe"):
        a = d.ausgaben[b["ausgabe"]]
        ld["isPartOf"] = {"@type": "PublicationIssue", "issueNumber": a["heft"],
                          "isPartOf": {"@type": "PublicationVolume", "volumeNumber": a["jahrgang"],
                                       "isPartOf": {"@type": "Periodical", "name": d.site["name"], "issn": d.site["issn"]}}}
        if b.get("seiten"):
            ld["pageStart"], ld["pageEnd"] = b["seiten"]
    json_ld = json.dumps(ld, ensure_ascii=False).replace("</", "<\\/")
    zeilen.append(f'<script type="application/ld+json">{json_ld}</script>')
    return "\n".join(zeilen)


def seite_beitrag(d: Daten, b: dict) -> str:
    autoren_html = "".join(
        f"""<div class="autor">
  <a class="autor-name" href="{d.link('autoren/' + a['slug'] + '/')}">{e(autor_name(a))}</a>
  <small>{e(a['abschluss'])}, {e(d.site['institut'])}</small>
  {f'<a class="orcid" href="https://orcid.org/{e(a["orcid"])}">ORCID {e(a["orcid"])}</a>' if a.get('orcid') else ''}
</div>""" for a in (d.autoren[s] for s in b["autoren"]))

    angaben = []
    if b.get("ausgabe"):
        a = d.ausgaben[b["ausgabe"]]
        angaben.append(f'<a href="{d.link("ausgaben/" + a["id"] + "/")}">{ausgabe_text(a)}</a>')
        if b.get("seiten"):
            angaben.append(f"S. {b['seiten'][0]}–{b['seiten'][1]}")
    else:
        angaben.append(datum_lang(b["datum"]))
        if b.get("abschlussjahr"):
            angaben.append(f"Abschlussjahr {b['abschlussjahr']}")
    if b.get("umfang_seiten"):
        angaben.append(f"{b['umfang_seiten']} Seiten")
    if b.get("doi"):
        angaben.append(f'<a href="https://doi.org/{e(b["doi"])}">doi.org/{e(b["doi"])}</a>')
    else:
        angaben.append("DOI beantragt")
    angaben.append(f'<a class="oa-plakette" href="{d.link("open-access/")}">{ICON_SCHLOSS}Open Access · {e(d.site["lizenz"]["name"])}</a>')
    angaben_html = punkt().join(f"<span>{x}</span>" for x in angaben)

    knoepfe = []
    if b.get("pdf"):
        knoepfe.append(f'<a class="knopf primaer" href="{d.link(b["pdf"])}" download>PDF herunterladen</a>')
    knoepfe.append('<a class="knopf sekundaer" href="#zitieren">Zitieren</a>')

    betreuung = (f'<p class="unterzeile">Betreuung {e(b["betreuung"])}</p>' if b.get("betreuung") else "")
    hinweis = ('<p class="hinweis-beispiel meta">Beispielbeitrag zur Vorschau. Er wird vor dem Start durch echte Inhalte ersetzt.</p>'
               if b.get("beispiel") else "")
    abstract_en = (f'<h2 class="meta gold">Abstract (English)</h2><p lang="en">{e(b["abstract_en"])}</p>'
                   if b.get("abstract_en") else "")
    literatur = ""
    if b.get("literatur"):
        literatur = ('<section class="literatur"><h2 class="t-h2" id="literatur">Literatur</h2><ul>'
                     + "".join(f"<li>{e(x)}</li>" for x in b["literatur"]) + "</ul></section>")
    versionen = ""
    if b.get("versionen"):
        versionen = ('<section class="versionen"><h2 class="meta gold">Versionen</h2><ul class="punktliste">'
                     + "".join(f"<li>Version {v['version']} vom {datum_lang(v['datum'])}. {e(v['hinweis'])}</li>"
                               for v in b["versionen"]) + "</ul></section>")
    schlagworte = "".join(f"<li>{e(s)}</li>" for s in b["schlagworte"])
    pdf_ansicht = ""
    if b.get("pdf"):
        pdf_ansicht = f"""<section class="pdf-ansicht" aria-labelledby="pdf-titel">
  <h2 class="t-h2" id="pdf-titel">Den Beitrag lesen</h2>
  <object data="{d.link(b['pdf'])}#view=FitH" type="application/pdf" aria-label="PDF {e(b['titel'])}">
    <p>Ihr Browser zeigt das PDF hier nicht an. <a href="{d.link(b['pdf'])}">PDF öffnen</a></p>
  </object>
  <p class="unterzeile">Das PDF ist frei verwendbar unter {e(d.site['lizenz']['name'])}. <a href="{d.link(b['pdf'])}" download>PDF herunterladen</a></p>
</section>"""

    inhalt = f"""<article class="seite beitrag">
<header class="artikelkopf">
  {hinweis}
  {kennzeile(d, b, mit_lesezeit=False)}
  {f'<p class="reihe">{e(b["reihe"])}</p>' if b.get('reihe') else ''}
  <h1 class="t-h1">{e(b['titel'])}</h1>
  {f'<p class="untertitel">{e(b["untertitel"])}</p>' if b.get('untertitel') else ''}
  <hr class="goldlinie">
  {autoren_html}
  {betreuung}
  <div class="meta angaben">{angaben_html}</div>
  <div class="knopf-zeile">{''.join(knoepfe)}</div>
</header>
<section class="abstract" aria-labelledby="abstract-titel">
  <h2 class="meta gold" id="abstract-titel">Abstract</h2>
  <p class="t-lead">{e(b['abstract_de'])}</p>
  {abstract_en}
  <h2 class="meta gold">Schlagworte</h2>
  <ul class="schlagworte">{schlagworte}</ul>
</section>
<div class="fliesstext">
{inhalt_html(b.get('inhalt', []))}
</div>
{pdf_ansicht}
{literatur}
{versionen}
<section class="zitiervorschlag" id="zitieren" tabindex="-1">
  <div class="zitier-kopf"><h2 class="meta gold">So zitieren Sie diesen Beitrag</h2>
  <button class="knopf sekundaer klein" type="button" data-kopieren="#apa">Kopieren</button></div>
  <p class="zitat-text" id="apa">{apa(d, b)}</p>
  <div class="link-zeile">
    <a class="textlink" href="{d.link('beitraege/' + b['slug'] + '/zitat.bib')}" download>BibTeX</a>
    <a class="textlink" href="{d.link('beitraege/' + b['slug'] + '/zitat.ris')}" download>RIS</a>
  </div>
</section>
</article>"""
    return rahmen(d, f"beitraege/{b['slug']}/", b["titel"], inhalt, aktiv="publikationen/",
                  beschreibung=b["abstract_de"], kopf_extra=scholar_meta(d, b))


def seite_ausgaben(d: Daten) -> str:
    karten = "".join(ausgabe_karte(d, a) for a in
                     sorted(d.ausgaben.values(), key=lambda a: (a["jahrgang"], a["heft"]), reverse=True))
    reihe = sorted({b.get("abschlussjahr") for b in d.beitraege if b["format"] == "abschlussarbeit" and b.get("abschlussjahr")}, reverse=True)
    reihe_html = ""
    if reihe:
        teile = []
        for jahr in reihe:
            arbeiten = [b for b in d.beitraege if b["format"] == "abschlussarbeit" and b.get("abschlussjahr") == jahr]
            teile.append(f'<h3 class="t-h3">Abschlussjahr {jahr}</h3><div class="raster">{"".join(karte(d, b) for b in arbeiten)}</div>')
        reihe_html = f"""<section class="abschnitt">
  <div class="abschnitt-kopf"><h2 class="t-h2">Reihe Abschlussarbeiten</h2><hr class="goldlinie"></div>
  {''.join(teile)}
</section>"""
    inhalt = f"""<div class="seite">
{seitenkopf("Ausgaben", "Fachartikel und Kurzbeiträge erscheinen in Heften, zweimal im Jahr im Frühjahr und im Herbst. Abschlussarbeiten erscheinen in einer eigenen Reihe nach Abschlussjahr.")}
<div class="ausgaben-liste">{karten}</div>
{reihe_html}
</div>"""
    return rahmen(d, "ausgaben/", "Ausgaben", inhalt, aktiv="ausgaben/")


def seite_ausgabe(d: Daten, a: dict) -> str:
    zeilen = []
    for b in d.beitraege_in(a["id"]):
        autoren = ", ".join(autor_name(d.autoren[s]) for s in b["autoren"])
        seiten = f"S. {b['seiten'][0]}–{b['seiten'][1]}" if b.get("seiten") else ""
        zeilen.append(f"""<li>
  {kennzeile(d, b, mit_lesezeit=False)}
  <a class="t-h3 toc-titel" href="{d.link('beitraege/' + b['slug'] + '/')}">{e(b['titel'])}</a>
  <p class="unterzeile">{e(autoren)}{' · ' + seiten if seiten else ''}</p>
</li>""")
    pdf = (f'<p><a class="knopf primaer" href="{d.link(a["pdf"])}" download>Gesamt-PDF herunterladen</a></p>'
           if a.get("pdf") else "")
    inhalt = f"""<div class="seite">
{seitenkopf(a['titel'], rubrik=ausgabe_text(a))}
<p class="unterzeile">ISSN {e(d.site['issn'])}</p>
{pdf}
<section class="abschnitt-klein">
  <h2 class="t-h2">Inhaltsverzeichnis</h2>
  <ol class="toc">{''.join(zeilen) or '<li>Noch keine Beiträge zugeordnet.</li>'}</ol>
</section>
</div>"""
    return rahmen(d, f"ausgaben/{a['id']}/", f"{a['titel']} · Heft {a['heft']}", inhalt, aktiv="ausgaben/")


def seite_themen(d: Daten) -> str:
    zeilen = []
    for r in d.site["rubriken"]:
        n = sum(1 for b in d.beitraege if b["rubrik"] == r["slug"])
        anzahl = "noch keine Beiträge" if n == 0 else ("1 Beitrag" if n == 1 else f"{n} Beiträge")
        zeilen.append(f"""<li class="thema">
  <a class="t-h3" href="{d.link('publikationen/?rubrik=' + r['slug'])}">{e(r['name'])}</a>
  <p>{e(r['faecher'])}</p>
  <span class="meta">{anzahl}</span>
</li>""")
    inhalt = f"""<div class="seite">
{seitenkopf("Themen", "Die Rubriken folgen den Fächern des Studienplans. Jeder Beitrag hat genau eine Rubrik und bis zu fünf Schlagworte.")}
<ul class="themen-raster">{''.join(zeilen)}</ul>
</div>"""
    return rahmen(d, "themen/", "Themen", inhalt, aktiv="themen/")


def seite_autoren(d: Daten) -> str:
    eintraege = "".join(
        f"""<li class="karte">
  <h2 class="t-h3"><a class="karte-link" href="{d.link('autoren/' + a['slug'] + '/')}">{e(autor_name(a))}</a></h2>
  <p class="unterzeile">{e(a['abschluss'])}{f" · Abschlussjahr {a['abschlussjahr']}" if a.get('abschlussjahr') else ''}</p>
  <p class="meta gold">{len(d.beitraege_von(a['slug']))} Beiträge auf NUN</p>
</li>""" for a in sorted(d.autoren.values(), key=lambda a: a["nachname"]))
    inhalt = f"""<div class="seite">
{seitenkopf("Autorinnen und Autoren", "Alle Personen, die auf NUN veröffentlichen, sind Absolventinnen und Absolventen des Islamologischen Instituts.")}
<ul class="raster">{eintraege}</ul>
</div>"""
    return rahmen(d, "autoren/", "Autorinnen und Autoren", inhalt)


def seite_autor(d: Daten, a: dict) -> str:
    karten = "".join(karte(d, b) for b in d.beitraege_von(a["slug"]))
    orcid = (f'<p><a class="textlink" href="https://orcid.org/{e(a["orcid"])}">ORCID {e(a["orcid"])}</a></p>'
             if a.get("orcid") else "")
    ld = json.dumps({"@context": "https://schema.org", "@type": "Person", "name": autor_name(a),
                     **({"sameAs": f"https://orcid.org/{a['orcid']}"} if a.get("orcid") else {})},
                    ensure_ascii=False).replace("</", "<\\/")
    inhalt = f"""<div class="seite">
{seitenkopf(autor_name(a), rubrik="Autorin oder Autor")}
<div class="schmal">
  <p class="unterzeile">{e(a['abschluss'])}, {e(d.site['institut'])}{f" · Abschlussjahr {a['abschlussjahr']}" if a.get('abschlussjahr') else ''}</p>
  <p>{e(a['bio'])}</p>
  {f'<p class="unterzeile">Thema der Bachelorarbeit · {e(a["bachelorarbeit"])}</p>' if a.get('bachelorarbeit') else ''}
  {orcid}
</div>
<section class="abschnitt-klein">
  <h2 class="t-h2">Beiträge auf NUN</h2>
  <div class="raster">{karten}</div>
</section>
</div>"""
    return rahmen(d, f"autoren/{a['slug']}/", autor_name(a), inhalt,
                  kopf_extra=f'<script type="application/ld+json">{ld}</script>')


def seite_podcast(d: Daten) -> str:
    folgen = [b for b in d.beitraege if b["format"] == "podcast"]
    liste = (f'<div class="raster">{"".join(karte(d, b) for b in folgen)}</div>' if folgen else
             '<p>Die ersten Folgen sind in Vorbereitung. Hier erscheinen Gespräche und Vorträge zu den Beiträgen auf NUN.</p>')
    inhalt = f"""<div class="seite">
{seitenkopf("Podcast", "Gespräche und Vorträge zu den Beiträgen auf NUN, jeweils 20 bis 60 Minuten.")}
<div class="schmal">{liste}</div>
</div>"""
    return rahmen(d, "podcast/", "Podcast", inhalt, aktiv="podcast/")


def seite_ueber(d: Daten) -> str:
    inhalt = f"""<div class="seite">
{seitenkopf("Über uns", "NUN ist eine Plattform der Absolventinnen und Absolventen des Islamologischen Instituts.")}
<div class="schmal fliesstext">
  <p>Auf NUN veröffentlichen Absolventinnen und Absolventen des Bachelorstudiums Islam-Wissenschaft am Islamologischen Institut, in Kooperation mit der Faculty of Islamic Studies der International University of Novi Pazar. Sie schreiben Fachartikel, Abschlussarbeiten, Übersetzungen und Bücher zu allen Fächern ihres Studiums.</p>
  <p>Alle Beiträge sind frei zugänglich, ohne Anmeldung, ohne Bezahlschranke und ohne Gebühren für die Autorinnen und Autoren. Dieses Modell heißt Diamond Open Access.</p>
  {aaya({"arabisch": "وَجَعَلْنَاكُمْ شُعُوبًا وَقَبَائِلَ لِتَعَارَفُوا", "uebersetzung": d.site["leitsatz"], "quelle": "Leitsatz nach Suura al-Hudschuraat 49:13"})}
  <h2 class="t-h2">Der Name</h2>
  <p>Das Signet ist ein Kreis aus 23 Punkten, der oben offen ist, mit einem goldenen Punkt in der Mitte. Die Form erinnert an den Buchstaben Nuun, eine offene Schale mit einem Punkt. Zugleich steht sie für eine Gemeinschaft um einen gemeinsamen Kern.</p>
  <h2 class="t-h2" id="kontakt">Kontakt</h2>
  <p>Sie erreichen die Redaktion per E-Mail an <a href="mailto:{e(d.site['kontakt'])}">{e(d.site['kontakt'])}</a>.</p>
</div>
</div>"""
    return rahmen(d, "ueber-uns/", "Über uns", inhalt, aktiv="ueber-uns/")


def seite_open_access(d: Daten) -> str:
    punkte = [
        ("Zugang", "Frei lesbar und herunterladbar, ohne Anmeldung."),
        ("Lizenz", f"Creative Commons Namensnennung 4.0 ({d.site['lizenz']['name']}). Jeder darf teilen und weiterverwenden, wenn NUN und die Autoren genannt werden."),
        ("Kennung", "Jeder Beitrag erhält eine DOI über Zenodo."),
        ("ISSN", f"Die Zeitschrift trägt die ISSN {d.site['issn']}."),
        ("Archivierung", "Die PDFs werden an die Deutsche Nationalbibliothek abgeliefert. Eine Kopie liegt zusätzlich auf Zenodo."),
        ("Auffindbarkeit", "Jede Artikelseite enthält Metadaten für Google Scholar und Schema.org."),
        ("Versionen", "Ein veröffentlichter Beitrag wird nicht mehr still geändert. Korrekturen erscheinen als neue Version mit Datum und Hinweis."),
        ("Prüfung", "Jeder Beitrag wird vor der Veröffentlichung von einem zweiten Mitglied des Teams gelesen."),
    ]
    zeilen = "".join(f"<tr><th scope=\"row\">{e(k)}</th><td>{e(v)}</td></tr>" for k, v in punkte)
    formate = "".join(f"<tr><th scope=\"row\">{e(f['name'])}</th><td>{e(f['beschreibung'])}</td><td>{e(f['umfang'])}</td></tr>"
                      for f in d.site["formate"])
    inhalt = f"""<div class="seite">
{seitenkopf("Open Access", "Alle Beiträge auf NUN sind frei zugänglich, ohne Bezahlschranke und ohne Gebühren für die Autorinnen und Autoren.")}
<div class="schmal">
  <table class="tabelle"><tbody>{zeilen}</tbody></table>
  <h2 class="t-h2">Formate</h2>
  <table class="tabelle"><thead><tr><th scope="col">Format</th><th scope="col">Was es ist</th><th scope="col">Umfang</th></tr></thead><tbody>{formate}</tbody></table>
  <h2 class="t-h2">Zitieren</h2>
  <p>Zitiert wird nach APA 7. Jede Artikelseite zeigt einen fertigen Zitiervorschlag und bietet ihn als BibTeX und RIS für Zotero und Citavi an.</p>
</div>
</div>"""
    return rahmen(d, "open-access/", "Open Access", inhalt)


def seite_recht(d: Daten, pfad: str, titel: str, absaetze: list[str]) -> str:
    text = "".join(f"<p>{a}</p>" for a in absaetze)
    inhalt = f"""<div class="seite">
{seitenkopf(titel)}
<div class="schmal fliesstext"><p class="hinweis-beispiel meta">Vorlage. Die Angaben in eckigen Klammern müssen vor dem Start ergänzt und rechtlich geprüft werden.</p>{text}</div>
</div>"""
    return rahmen(d, pfad, titel, inhalt)


def seite_intern(d: Daten) -> str:
    rubriken = "".join(f'<option value="{e(r["slug"])}">{e(r["name"])}</option>' for r in d.site["rubriken"])
    formate = "".join(f'<option value="{e(f["slug"])}">{e(f["name"])}</option>' for f in d.site["formate"])
    autoren = "".join(f'<option value="{e(a["slug"])}">{e(autor_name(a))}</option>' for a in d.autoren.values())
    ausgaben = "".join(f'<option value="{e(a["id"])}">{e(ausgabe_text(a))}</option>' for a in d.ausgaben.values())
    inhalt = f"""<div class="seite">
{seitenkopf("Beitrag einstellen", "Interner Bereich für das Team. Das Formular erzeugt die Datei für content/beitraege und prüft das PDF.")}
<form class="formular schmal" data-einstellen>
  <span class="feld-label">Beitrag als PDF</span>
  <label class="upload" data-upload>
    <input type="file" accept="application/pdf" name="pdf">
    <img class="nur-hell" src="{d.link('logo/emblem.svg')}" alt="" width="64" height="64">
    <img class="nur-dunkel" src="{d.link('logo/emblem-hell.svg')}" alt="" width="64" height="64">
    <span class="upload-text">PDF hierher ziehen <span>oder Datei auswählen</span></span>
    <span class="unterzeile">PDF, höchstens 50 MB</span>
  </label>
  <div class="upload-datei" data-upload-datei hidden></div>
  <label class="feld"><span class="feld-label">Format</span><select name="format" required>{formate}</select></label>
  <label class="feld"><span class="feld-label">Rubrik</span><select name="rubrik" required>{rubriken}</select></label>
  <label class="feld"><span class="feld-label">Titel</span><input name="titel" required></label>
  <label class="feld"><span class="feld-label">Untertitel</span><input name="untertitel"></label>
  <label class="feld"><span class="feld-label">Autorin oder Autor</span><select name="autoren" multiple required>{autoren}</select></label>
  <label class="feld"><span class="feld-label">Ausgabe</span><select name="ausgabe"><option value="">Ohne Heft (laufend)</option>{ausgaben}</select></label>
  <div class="feld-paar">
    <label class="feld"><span class="feld-label">Erste Seite</span><input name="seite_von" type="number" min="1"></label>
    <label class="feld"><span class="feld-label">Letzte Seite</span><input name="seite_bis" type="number" min="1"></label>
  </div>
  <label class="feld"><span class="feld-label">Erscheinungsdatum</span><input name="datum" type="date" required></label>
  <label class="feld"><span class="feld-label">DOI</span><input name="doi" placeholder="10.5281/zenodo.0000000" pattern="10\\.\\d{{4,}}/.+" required></label>
  <label class="feld"><span class="feld-label">Abstract auf Deutsch</span><textarea name="abstract_de" rows="5" required></textarea></label>
  <label class="feld"><span class="feld-label">Abstract auf Englisch</span><textarea name="abstract_en" rows="4"></textarea></label>
  <label class="feld"><span class="feld-label">Schlagworte, durch Komma getrennt, höchstens fünf</span><input name="schlagworte" required></label>
  <p class="formular-fehler" data-fehler role="alert" hidden></p>
  <div class="knopf-zeile"><button class="knopf primaer" type="submit">Beitrag veröffentlichen</button></div>
</form>
</div>"""
    return rahmen(d, "intern/", "Beitrag einstellen", inhalt, noindex=True)


def seite_404(d: Daten) -> str:
    inhalt = f"""<div class="seite">
{seitenkopf("Seite nicht gefunden", "Die Adresse gibt es nicht oder nicht mehr. Veröffentlichte Beiträge bleiben über ihre DOI immer erreichbar.")}
<div class="knopf-zeile"><a class="knopf primaer" href="{d.link('publikationen/')}">Zu den Publikationen</a><a class="knopf sekundaer" href="{d.link()}">Zur Startseite</a></div>
</div>"""
    return rahmen(d, "404.html", "Seite nicht gefunden", inhalt, noindex=True)


# --------------------------------------------------------------------------
# Bauen
# --------------------------------------------------------------------------

IMPRESSUM = [
    "Angaben nach § 5 DDG",
    "[Name des Vereins oder der verantwortlichen Person]<br>[Straße und Hausnummer]<br>[PLZ und Ort]",
    "E-Mail [Adresse]",
    "Verantwortlich für den Inhalt nach § 18 Abs. 2 MStV [Name und Anschrift]",
    "ISSN [nach Vergabe durch die Deutsche Nationalbibliothek eintragen]",
]
DATENSCHUTZ = [
    "Diese Website lädt keine Inhalte von fremden Servern. Schriften liegen auf dem eigenen Server, es gibt keine Analyse- oder Werbedienste und keine Cookies.",
    "Die Einstellung für helles oder dunkles Thema wird nur im Browser gespeichert und nicht übertragen.",
    "Verantwortlich [Name und Anschrift wie im Impressum]",
    "Hosting [Anbieter, Sitz und Rechtsgrundlage eintragen, etwa GitHub Pages]",
    "Ihre Rechte auf Auskunft, Berichtigung, Löschung und Beschwerde bei einer Aufsichtsbehörde [ergänzen]",
]


def schreibe(ziel: Path, text: str | bytes):
    ziel.parent.mkdir(parents=True, exist_ok=True)
    if isinstance(text, bytes):
        ziel.write_bytes(text)
    else:
        ziel.write_text(text, "utf-8")


def baue(base: str = "/", url: str = "", ausgabe: Path = ROOT / "dist") -> Daten:
    if not base.startswith("/") or not base.endswith("/"):
        raise SystemExit("--base muss mit / beginnen und enden, etwa /nun/")
    d = Daten(base, url)
    fehler = d.pruefe()
    if fehler:
        raise SystemExit("Fehler in content/\n  " + "\n  ".join(fehler))

    if ausgabe.exists():
        shutil.rmtree(ausgabe)
    shutil.copytree(STATIC, ausgabe)
    schreibe(ausgabe / "css" / "tokens.css", tokens_css(json.loads(TOKENS.read_text("utf-8"))))

    seiten = {
        "index.html": seite_start(d),
        "publikationen/index.html": seite_publikationen(d),
        "ausgaben/index.html": seite_ausgaben(d),
        "themen/index.html": seite_themen(d),
        "autoren/index.html": seite_autoren(d),
        "podcast/index.html": seite_podcast(d),
        "ueber-uns/index.html": seite_ueber(d),
        "open-access/index.html": seite_open_access(d),
        "impressum/index.html": seite_recht(d, "impressum/", "Impressum", IMPRESSUM),
        "datenschutz/index.html": seite_recht(d, "datenschutz/", "Datenschutz", DATENSCHUTZ),
        "intern/index.html": seite_intern(d),
        "404.html": seite_404(d),
    }
    for b in d.beitraege:
        seiten[f"beitraege/{b['slug']}/index.html"] = seite_beitrag(d, b)
        schreibe(ausgabe / "beitraege" / b["slug"] / "zitat.bib", bibtex(d, b))
        schreibe(ausgabe / "beitraege" / b["slug"] / "zitat.ris", ris(d, b))
    for a in d.ausgaben.values():
        seiten[f"ausgaben/{a['id']}/index.html"] = seite_ausgabe(d, a)
    for a in d.autoren.values():
        seiten[f"autoren/{a['slug']}/index.html"] = seite_autor(d, a)

    for pfad, html in seiten.items():
        schreibe(ausgabe / pfad, html)

    # Daten für das interne Formular (Autorennamen und Pfade)
    schreibe(ausgabe / "site.webmanifest", json.dumps({
        "name": d.site["name"], "short_name": d.site["name"], "start_url": base,
        "icons": [{"src": f"{base}icon-192.png", "sizes": "192x192", "type": "image/png"},
                  {"src": f"{base}icon-512.png", "sizes": "512x512", "type": "image/png"}],
        "background_color": "#F5EFE2", "theme_color": "#1F2E4D", "display": "standalone"}, indent=2))
    oeffentlich = [p for p in seiten if p not in ("intern/index.html", "404.html")]
    urls = "".join(f"<url><loc>{e(d.absolut(p.removesuffix('index.html')))}</loc></url>" for p in oeffentlich)
    schreibe(ausgabe / "sitemap.xml",
             f'<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">{urls}</urlset>\n')
    schreibe(ausgabe / "robots.txt", f"User-agent: *\nDisallow: {base}intern/\nSitemap: {d.absolut('sitemap.xml')}\n")
    return d


def main():
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--base", default="/", help="Pfad, unter dem die Seite liegt, etwa /nun/")
    p.add_argument("--url", default="", help="Adresse ohne Pfad, etwa https://cansi798.github.io")
    p.add_argument("--out", default=str(ROOT / "dist"))
    a = p.parse_args()
    d = baue(a.base, a.url, Path(a.out))
    print(f"Gebaut nach {a.out} mit {len(d.beitraege)} Beiträgen, {len(d.ausgaben)} Ausgaben, {len(d.autoren)} Autoren.")


if __name__ == "__main__":
    sys.exit(main())
