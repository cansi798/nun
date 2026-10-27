"""Tests für den Seitengenerator build.py (nur Standardbibliothek).

Aufruf aus dem Projektordner

    python3 -m unittest discover -s tests -v
"""
from __future__ import annotations

import copy
import importlib
import json
import re
import sys
import tempfile
import time
import unittest
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

BASE = "/nun/"
URL = "https://cansi798.github.io"


def lade_build():
    """Importiert build.py. Bei einem Syntaxfehler (Datei wird gerade bearbeitet) einmal neu versuchen."""
    try:
        import build
        return importlib.reload(build)
    except SyntaxError:
        time.sleep(5)
        sys.modules.pop("build", None)
        import build
        return build


build = lade_build()


class Sammler(HTMLParser):
    """Sammelt href/src-Werte, img-Tags, meta-Tags und JSON-LD-Blöcke."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.links: list[str] = []
        self.imgs: list[dict] = []
        self.meta: list[tuple[str, str]] = []
        self.json_ld: list[str] = []
        self._in_ld = False
        self._ld_puffer: list[str] = []

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        for name in ("href", "src"):
            if a.get(name):
                self.links.append(a[name])
        if tag == "img":
            self.imgs.append(a)
        if tag == "meta" and "name" in a:
            self.meta.append((a["name"], a.get("content", "")))
        if tag == "script" and a.get("type") == "application/ld+json":
            self._in_ld = True
            self._ld_puffer = []

    handle_startendtag = handle_starttag

    def handle_data(self, data):
        if self._in_ld:
            self._ld_puffer.append(data)

    def handle_endtag(self, tag):
        if tag == "script" and self._in_ld:
            self.json_ld.append("".join(self._ld_puffer))
            self._in_ld = False


def parse(pfad: Path) -> Sammler:
    s = Sammler()
    s.feed(pfad.read_text("utf-8"))
    s.close()
    return s


class BuildTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls._tmp = tempfile.TemporaryDirectory()
        cls.out = Path(cls._tmp.name) / "dist"
        cls.d = build.baue(base=BASE, url=URL, ausgabe=cls.out)
        cls.html_dateien = sorted(cls.out.rglob("*.html"))

    @classmethod
    def tearDownClass(cls):
        cls._tmp.cleanup()

    # ------------------------------------------------------------------
    def test_erwartete_seiten(self):
        erwartet = [
            "index.html", "404.html", "sitemap.xml", "robots.txt", "site.webmanifest", "css/tokens.css",
            *(f"{p}/index.html" for p in ("publikationen", "ausgaben", "themen", "autoren", "podcast",
                                          "ueber-uns", "open-access", "impressum", "datenschutz", "intern")),
        ]
        for b in self.d.beitraege:
            erwartet += [f"beitraege/{b['slug']}/index.html",
                         f"beitraege/{b['slug']}/zitat.bib",
                         f"beitraege/{b['slug']}/zitat.ris"]
        erwartet += [f"ausgaben/{a}/index.html" for a in self.d.ausgaben]
        erwartet += [f"autoren/{a}/index.html" for a in self.d.autoren]
        fehlend = [p for p in erwartet if not (self.out / p).is_file()]
        self.assertEqual(fehlend, [], f"Fehlende Dateien: {fehlend}")

    def test_interne_links_aufloesbar(self):
        kaputt = []
        for datei in self.html_dateien:
            for link in parse(datei).links:
                if not link.startswith(BASE):
                    continue
                pfad = urlsplit(link).path[len(BASE):]
                if pfad == "" or pfad.endswith("/"):
                    pfad += "index.html"
                if not (self.out / pfad).is_file():
                    kaputt.append(f"{datei.relative_to(self.out)} -> {link}")
        self.assertEqual(kaputt, [], "Nicht auflösbare interne Links\n  " + "\n  ".join(sorted(set(kaputt))))

    def test_beitrag_metadaten(self):
        for b in self.d.beitraege:
            with self.subTest(beitrag=b["slug"]):
                s = parse(self.out / "beitraege" / b["slug"] / "index.html")
                namen = {k for k, _ in s.meta}
                self.assertIn("citation_title", namen)
                self.assertIn("citation_author", namen)
                if b.get("pdf"):
                    self.assertIn("citation_pdf_url", namen)
                artikel = None
                for block in s.json_ld:
                    daten = json.loads(block)
                    if daten.get("@type") == "ScholarlyArticle":
                        artikel = daten
                self.assertIsNotNone(artikel, "kein JSON-LD vom Typ ScholarlyArticle")
                self.assertIs(artikel.get("isAccessibleForFree"), True)

    def test_site_css_ohne_hexfarben(self):
        css = (ROOT / "static" / "css" / "site.css").read_text("utf-8")
        css = re.sub(r"/\*.*?\*/", "", css, flags=re.S)
        treffer = re.findall(r"#[0-9a-fA-F]{3,8}\b", css)
        self.assertEqual(treffer, [], "site.css darf nur Token-Variablen nutzen")

    def test_tokens_css_enthaelt_alle_farben(self):
        tokens = json.loads((ROOT / "design-system" / "tokens.json").read_text("utf-8"))
        css = (self.out / "css" / "tokens.css").read_text("utf-8")
        fehlend = [t["name"] for t in tokens["color"]["tokens"]
                   if not re.search(rf"--{re.escape(t['name'])}\s*:", css)]
        self.assertEqual(fehlend, [])

    def test_apa(self):
        b = next(b for b in self.d.beitraege if b["autoren"] == ["can-bilger"] and b["datum"].startswith("2026"))
        self.assertTrue(build.apa(self.d, b, html=False).startswith("Bilger, C. (2026)."))
        self.assertTrue(build.apa(self.d, b).startswith("Bilger, C. (2026)."))

    def test_pruefe_unbekannte_rubrik(self):
        d = build.Daten(BASE, URL)
        self.assertEqual(d.pruefe(), [])
        kaputt = copy.deepcopy(d.beitraege[0])
        kaputt["rubrik"] = "gibt-es-nicht"
        d.beitraege[0] = kaputt
        fehler = d.pruefe()
        self.assertTrue(any("unbekannte Rubrik" in f and "gibt-es-nicht" in f for f in fehler), fehler)

    def test_img_alt(self):
        ohne = [f"{datei.relative_to(self.out)}: {img.get('src')}"
                for datei in self.html_dateien for img in parse(datei).imgs if "alt" not in img]
        self.assertEqual(ohne, [])


if __name__ == "__main__":
    unittest.main()
