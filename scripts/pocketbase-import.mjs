// Überträgt content/*.json und public/pdf/*.pdf nach PocketBase.
// Aufruf: PB_URL=https://pb.example.org PB_EMAIL=admin@… PB_PASSWORT=… node scripts/pocketbase-import.mjs
// Vorhandene Einträge (gleicher slug bzw. gleiche kennung) werden aktualisiert, nicht doppelt angelegt.
import PocketBase from "pocketbase";
import { readFileSync, readdirSync, existsSync } from "node:fs";

const { PB_URL, PB_EMAIL, PB_PASSWORT } = process.env;
if (!PB_URL || !PB_EMAIL || !PB_PASSWORT) {
  console.error("Bitte PB_URL, PB_EMAIL und PB_PASSWORT setzen.");
  process.exit(1);
}
const pb = new PocketBase(PB_URL);
await pb.collection("_superusers").authWithPassword(PB_EMAIL, PB_PASSWORT);
const lies = (p) => JSON.parse(readFileSync(p, "utf8"));

async function speichere(sammlung, schluessel, wert, daten) {
  const vorhanden = await pb.collection(sammlung).getFirstListItem(`${schluessel}="${wert}"`).catch(() => null);
  return vorhanden ? pb.collection(sammlung).update(vorhanden.id, daten) : pb.collection(sammlung).create(daten);
}
const mitPdf = (felder, pfad) => {
  const fd = new FormData();
  for (const [k, v] of Object.entries(felder)) {
    if (v === undefined || v === null) continue;
    if (Array.isArray(v) && k === "autoren") v.forEach((x) => fd.append(k, x));
    else fd.append(k, typeof v === "object" ? JSON.stringify(v) : String(v));
  }
  if (pfad && existsSync(`public/${pfad}`)) {
    fd.append("pdf", new Blob([readFileSync(`public/${pfad}`)], { type: "application/pdf" }), pfad.split("/").pop());
  }
  return fd;
};

const autorIds = new Map();
for (const a of lies("content/autoren.json")) {
  const r = await speichere("autoren", "slug", a.slug, { ...a, abschlussjahr: a.abschlussjahr ?? 0 });
  autorIds.set(a.slug, r.id);
  console.log("Autor", a.slug);
}
const ausgabeIds = new Map();
for (const a of lies("content/ausgaben.json")) {
  const { id, pdf, ...rest } = a;
  const r = await speichere("ausgaben", "kennung", id, mitPdf({ ...rest, kennung: id }, pdf));
  ausgabeIds.set(id, r.id);
  console.log("Ausgabe", id);
}
for (const f of readdirSync("content/beitraege").filter((f) => f.endsWith(".json"))) {
  const b = lies(`content/beitraege/${f}`);
  const { pdf, seiten = [], ausgabe, autoren, ...rest } = b;
  const felder = {
    ...rest, autoren: autoren.map((s) => autorIds.get(s)), ausgabe: ausgabe ? ausgabeIds.get(ausgabe) : "",
    seite_von: seiten[0], seite_bis: seiten[1], datum: `${b.datum} 00:00:00.000Z`, veroeffentlicht: true,
  };
  await speichere("beitraege", "slug", b.slug, mitPdf(felder, pdf));
  console.log("Beitrag", b.slug);
}
console.log("Fertig.");
