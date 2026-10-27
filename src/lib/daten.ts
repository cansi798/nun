// Eine Stelle für alle Inhalte. Quelle wählbar über NUN_QUELLE.
//   json        Dateien in content/ (Standard)
//   pocketbase  PocketBase unter PB_URL, Sammlungen siehe pocketbase/README.md
// Seiten rufen nur ladeDaten() auf und wissen nicht, woher die Daten kommen.
import { readFileSync, readdirSync } from "node:fs";
import { join } from "node:path";
import type { Ausgabe, Autor, Beitrag, Daten, Site } from "./typen";

const ROOT = process.cwd();
const lies = <T>(p: string): T => JSON.parse(readFileSync(join(ROOT, p), "utf8"));

async function ausJson(): Promise<Omit<Daten, "site" | "formate" | "rubriken">> {
  const dir = join(ROOT, "content/beitraege");
  const beitraege = readdirSync(dir).filter((f) => f.endsWith(".json"))
    .map((f) => lies<Beitrag>(`content/beitraege/${f}`));
  return {
    autoren: new Map(lies<Autor[]>("content/autoren.json").map((a) => [a.slug, a])),
    ausgaben: new Map(lies<Ausgabe[]>("content/ausgaben.json").map((a) => [a.id, a])),
    beitraege,
  };
}

async function ausPocketBase(): Promise<Omit<Daten, "site" | "formate" | "rubriken">> {
  const { default: PocketBase } = await import("pocketbase");
  const url = process.env.PB_URL;
  if (!url) throw new Error("NUN_QUELLE=pocketbase braucht PB_URL");
  const pb = new PocketBase(url);
  if (process.env.PB_TOKEN) pb.authStore.save(process.env.PB_TOKEN, null);
  const datei = (r: any, feld: string) => (r[feld] ? pb.files.getURL(r, r[feld]) : "");

  const autorenRoh = await pb.collection("autoren").getFullList();
  const ausgabenRoh = await pb.collection("ausgaben").getFullList();
  const beitraegeRoh = await pb.collection("beitraege").getFullList({
    filter: "veroeffentlicht = true", expand: "autoren,ausgabe",
  });
  const autorSlug = new Map(autorenRoh.map((a: any) => [a.id, a.slug]));
  const ausgabeId = new Map(ausgabenRoh.map((a: any) => [a.id, a.kennung]));

  return {
    autoren: new Map(autorenRoh.map((a: any) => [a.slug, {
      slug: a.slug, vorname: a.vorname, nachname: a.nachname, abschluss: a.abschluss,
      abschlussjahr: a.abschlussjahr || null, bachelorarbeit: a.bachelorarbeit, orcid: a.orcid, bio: a.bio,
    }])),
    ausgaben: new Map(ausgabenRoh.map((a: any) => [a.kennung, {
      id: a.kennung, jahrgang: a.jahrgang, heft: a.heft, jahreszeit: a.jahreszeit,
      jahr: a.jahr, titel: a.titel, pdf: datei(a, "pdf"),
    }])),
    beitraege: beitraegeRoh.map((b: any) => ({
      slug: b.slug, format: b.format, rubrik: b.rubrik, reihe: b.reihe,
      titel: b.titel, untertitel: b.untertitel,
      autoren: (b.autoren as string[]).map((id) => autorSlug.get(id) ?? id),
      ausgabe: b.ausgabe ? ausgabeId.get(b.ausgabe) : "",
      seiten: b.seite_von && b.seite_bis ? [b.seite_von, b.seite_bis] : [],
      datum: String(b.datum).slice(0, 10), doi: b.doi, lesezeit: b.lesezeit || undefined,
      umfang_seiten: b.umfang_seiten || undefined, abschlussjahr: b.abschlussjahr || undefined,
      betreuung: b.betreuung || undefined, beispiel: !!b.beispiel, abstract_de: b.abstract_de, abstract_en: b.abstract_en,
      schlagworte: b.schlagworte ?? [], pdf: datei(b, "pdf"), version: b.version || 1,
      versionen: b.versionen ?? [], inhalt: b.inhalt ?? [], literatur: b.literatur ?? [],
    })),
  };
}

let cache: Promise<Daten> | undefined;

export function ladeDaten(): Promise<Daten> {
  cache ??= (async () => {
    // Formate und Rubriken legt das Handbuch fest, sie bleiben in content/site.json.
    const site = lies<Site>("content/site.json");
    const quelle = process.env.NUN_QUELLE === "pocketbase" ? await ausPocketBase() : await ausJson();
    const d: Daten = {
      site, ...quelle,
      formate: new Map(site.formate.map((f) => [f.slug, f])),
      rubriken: new Map(site.rubriken.map((r) => [r.slug, r])),
      beitraege: quelle.beitraege.sort((a, b) => b.datum.localeCompare(a.datum)),
    };
    const fehler = pruefe(d);
    if (fehler.length) throw new Error("Fehler in den Inhalten\n  " + fehler.join("\n  "));
    return d;
  })();
  return cache;
}

export function pruefe(d: Daten): string[] {
  const f: string[] = [];
  const slugs = new Set<string>();
  for (const b of d.beitraege) {
    const n = b.slug || "?";
    for (const feld of ["slug", "format", "rubrik", "titel", "datum", "abstract_de"] as const)
      if (!b[feld]) f.push(`${n}: Pflichtfeld '${feld}' fehlt`);
    if (!b.autoren?.length) f.push(`${n}: keine Autorin und kein Autor`);
    if (slugs.has(n)) f.push(`${n}: slug doppelt`);
    slugs.add(n);
    if (!/^[a-z0-9-]+$/.test(n)) f.push(`${n}: slug nur a-z, 0-9 und Bindestrich`);
    if (!d.formate.has(b.format)) f.push(`${n}: unbekanntes Format '${b.format}'`);
    if (!d.rubriken.has(b.rubrik)) f.push(`${n}: unbekannte Rubrik '${b.rubrik}'`);
    for (const a of b.autoren ?? []) if (!d.autoren.has(a)) f.push(`${n}: unbekannte Person '${a}'`);
    if (b.ausgabe && !d.ausgaben.has(b.ausgabe)) f.push(`${n}: unbekannte Ausgabe '${b.ausgabe}'`);
    if ((b.schlagworte?.length ?? 0) > 5) f.push(`${n}: höchstens fünf Schlagworte`);
    if (b.format === "abschlussarbeit" && !b.abschlussjahr) f.push(`${n}: abschlussjahr fehlt`);
    if (!/^\d{4}-\d{2}-\d{2}$/.test(b.datum)) f.push(`${n}: datum als JJJJ-MM-TT`);
  }
  return f;
}

export const beitraegeVon = (d: Daten, autor: string) => d.beitraege.filter((b) => b.autoren.includes(autor));
export const beitraegeIn = (d: Daten, ausgabe: string) =>
  d.beitraege.filter((b) => b.ausgabe === ausgabe).sort((a, b) => (a.seiten?.[0] ?? 0) - (b.seiten?.[0] ?? 0));
export const aktuelleAusgabe = (d: Daten) =>
  [...d.ausgaben.values()].sort((a, b) => b.jahrgang - a.jahrgang || b.heft - a.heft)[0];
