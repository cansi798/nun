// Prüft die gebaute Seite in dist/ (vorher npm run build).
import { test } from "node:test";
import assert from "node:assert/strict";
import { existsSync, readFileSync, readdirSync, statSync } from "node:fs";
import { join } from "node:path";

const DIST = new URL("../dist/", import.meta.url).pathname;
// Basis-Pfad wie beim Bauen, etwa /nun/ in der GitHub-Action
const BASE = process.env.NUN_BASE || "/";
const alle = (d) => readdirSync(d).flatMap((f) => (statSync(join(d, f)).isDirectory() ? alle(join(d, f)) : [join(d, f)]));
const html = alle(DIST).filter((f) => f.endsWith(".html"));
const beitraege = readdirSync("content/beitraege").map((f) => JSON.parse(readFileSync(`content/beitraege/${f}`, "utf8")));

test("alle Seiten existieren", () => {
  for (const p of ["index.html", "publikationen/index.html", "ausgaben/index.html", "themen/index.html", "autoren/index.html",
    "podcast/index.html", "ueber-uns/index.html", "open-access/index.html", "impressum/index.html", "datenschutz/index.html",
    "intern/index.html", "404.html", "sitemap.xml", "robots.txt", "site.webmanifest"])
    assert.ok(existsSync(join(DIST, p)), p);
  for (const b of beitraege) for (const f of ["index.html", "zitat.bib", "zitat.ris"])
    assert.ok(existsSync(join(DIST, "beitraege", b.slug, f)), `${b.slug}/${f}`);
});

test("interne Links führen zu Dateien", () => {
  const kaputt = [];
  for (const f of html) {
    for (const [, url] of readFileSync(f, "utf8").matchAll(/(?:href|src|data|data-src)="(\/[^"#?]*)/g)) {
      assert.ok(url.startsWith(BASE), `${f.replace(DIST, "")} -> ${url} liegt außerhalb von ${BASE}`);
      const pfad = "/" + url.slice(BASE.length);
      const ziel = join(DIST, pfad.endsWith("/") ? pfad + "index.html" : pfad);
      if (!existsSync(ziel)) kaputt.push(`${f.replace(DIST, "")} -> ${url}`);
    }
  }
  assert.deepEqual(kaputt, []);
});

test("Beitragsseiten tragen Scholar-Metadaten und JSON-LD", () => {
  for (const b of beitraege) {
    const s = readFileSync(join(DIST, "beitraege", b.slug, "index.html"), "utf8");
    for (const m of ["citation_title", "citation_author", "citation_publication_date"]) assert.match(s, new RegExp(`name="${m}"`), `${b.slug} ${m}`);
    if (b.pdf) assert.match(s, /name="citation_pdf_url"/);
    const ld = JSON.parse(s.match(/<script type="application\/ld\+json">(.*?)<\/script>/s)[1]);
    assert.equal(ld["@type"], "ScholarlyArticle");
    assert.equal(ld.isAccessibleForFree, true);
  }
});

test("Zitiervorschlag nach APA beginnt mit Autor und Jahr", () => {
  const s = readFileSync(join(DIST, "beitraege", beitraege[0].slug, "index.html"), "utf8");
  assert.match(s, /id="apa">Bilger, C\. \(2026\)\./);
});

test("site.css nutzt nur Tokens, keine festen Farbwerte", () => {
  const css = readFileSync("src/styles/site.css", "utf8").replace(/\/\*[\s\S]*?\*\//g, "");
  assert.deepEqual(css.match(/#[0-9a-fA-F]{3,8}\b/g) ?? [], []);
});

test("tokens.css enthält alle Farben aus tokens.json", () => {
  const t = JSON.parse(readFileSync("design-system/tokens.json", "utf8"));
  const css = readFileSync("src/styles/tokens.css", "utf8");
  for (const tok of t.color.tokens) assert.match(css, new RegExp(`--${tok.name}:`), tok.name);
});

test("jedes Bild hat einen Alternativtext", () => {
  const ohne = [];
  for (const f of html) for (const [img] of readFileSync(f, "utf8").matchAll(/<img\b[^>]*>/g)) if (!/\salt=/.test(img)) ohne.push(f);
  assert.deepEqual(ohne, []);
});
