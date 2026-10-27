import type { Ausgabe, Autor, Beitrag, Daten } from "./typen";

const BASE = import.meta.env.BASE_URL.endsWith("/") ? import.meta.env.BASE_URL : import.meta.env.BASE_URL + "/";

/** Link innerhalb der Seite, berücksichtigt den Basis-Pfad (etwa /nun/site/). */
export const link = (pfad = "") => (/^https?:/.test(pfad) ? pfad : BASE + pfad.replace(/^\//, ""));
/** Vollständige Adresse für Metadaten. */
export const absolut = (pfad = "") => new URL(link(pfad), import.meta.env.SITE).href;

const MONATE = ["Januar", "Februar", "März", "April", "Mai", "Juni", "Juli",
  "August", "September", "Oktober", "November", "Dezember"];
export function datumLang(iso: string) {
  const [j, m, t] = iso.split("-").map(Number);
  return `${t}. ${MONATE[m - 1]} ${j}`;
}
export const ausgabeText = (a: Ausgabe) => `Jahrgang ${a.jahrgang} · Heft ${a.heft} · ${a.jahreszeit} ${a.jahr}`;
export const autorName = (a: Autor) => `${a.vorname} ${a.nachname}`;
export const anzahl = (n: number, eins: string, viele: string) => (n === 1 ? `1 ${eins}` : `${n} ${viele}`);
export const beitragPfad = (b: Beitrag) => `beitraege/${b.slug}/`;
export const zitierUrl = (b: Beitrag) => (b.doi ? `https://doi.org/${b.doi}` : absolut(beitragPfad(b)));

const esc = (s: unknown) => String(s).replace(/[&<>"']/g, (c) =>
  ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[c]!);

function apaAutoren(autoren: Autor[]) {
  const n = autoren.map((a) => `${a.nachname}, ` +
    a.vorname.split(/[\s-]+/).filter(Boolean).map((t) => `${t[0]}.`).join(" "));
  return n.length === 1 ? n[0] : n.slice(0, -1).join(", ") + ", & " + n.at(-1);
}

/** Zitiervorschlag nach APA 7. html=true setzt kursiv und den Link. */
export function apa(d: Daten, b: Beitrag, html = true) {
  const k = (s: unknown) => (html ? `<i>${esc(s)}</i>` : String(s));
  const t = (s: unknown) => (html ? esc(s) : String(s));
  const url = zitierUrl(b);
  const urlTeil = html ? `<a href="${esc(url)}">${esc(url)}</a>` : url;
  let s = `${t(apaAutoren(b.autoren.map((a) => d.autoren.get(a)!)))} (${b.datum.slice(0, 4)}). `;
  if (b.ausgabe) {
    const a = d.ausgaben.get(b.ausgabe)!;
    const seiten = b.seiten?.length ? `, ${b.seiten[0]}–${b.seiten[1]}` : "";
    s += `${t(b.titel)}. ${k(d.site.name)}, ${k(a.jahrgang)}(${a.heft})${seiten}. ${urlTeil}`;
  } else if (b.format === "abschlussarbeit") {
    s += `${k(b.titel)} [Bachelorarbeit, ${t(d.site.institut)}]. ${d.site.name}. ${urlTeil}`;
  } else {
    s += `${k(b.titel)} [${d.formate.get(b.format)!.name}]. ${d.site.name}. ${urlTeil}`;
  }
  return s;
}

export function bibtex(d: Daten, b: Beitrag) {
  const autoren = b.autoren.map((s) => `${d.autoren.get(s)!.nachname}, ${d.autoren.get(s)!.vorname}`).join(" and ");
  const typ = b.ausgabe ? "article" : b.format === "abschlussarbeit" ? "thesis" : "misc";
  const f: [string, unknown][] = [["author", autoren], ["title", b.titel], ["year", b.datum.slice(0, 4)]];
  if (b.doi) f.push(["doi", b.doi]);
  f.push(["url", zitierUrl(b)], ["langid", "german"], ["license", d.site.lizenz.name]);
  if (b.reihe) f.push(["series", b.reihe.split(" · ")[0]]);
  if (b.ausgabe) {
    const a = d.ausgaben.get(b.ausgabe)!;
    f.push(["journal", d.site.name], ["volume", a.jahrgang], ["number", a.heft], ["issn", d.site.issn]);
    if (b.seiten?.length) f.push(["pages", `${b.seiten[0]}--${b.seiten[1]}`]);
  } else {
    f.push(["publisher", d.site.name]);
    if (typ === "thesis") f.push(["type", "Bachelorarbeit"], ["institution", d.site.institut]);
  }
  const key = `${d.autoren.get(b.autoren[0])!.nachname}${b.datum.slice(0, 4)}${b.slug.split("-")[0]}`
    .toLowerCase().replace(/[^a-z0-9]/g, "");
  return `@${typ}{${key},\n${f.map(([k, v]) => `  ${k} = {${v}}`).join(",\n")}\n}\n`;
}

export function ris(d: Daten, b: Beitrag) {
  const z: [string, unknown][] = [["TY", b.ausgabe ? "JOUR" : b.format === "abschlussarbeit" ? "THES" : "GEN"]];
  for (const s of b.autoren) z.push(["AU", `${d.autoren.get(s)!.nachname}, ${d.autoren.get(s)!.vorname}`]);
  z.push(["TI", b.titel], ["PY", b.datum.slice(0, 4)], ["DA", b.datum.replaceAll("-", "/")]);
  if (b.doi) z.push(["DO", b.doi]);
  z.push(["UR", zitierUrl(b)], ["LA", "de"], ["AB", b.abstract_de]);
  for (const k of b.schlagworte) z.push(["KW", k]);
  if (b.reihe) z.push(["T2", b.reihe.split(" · ")[0]]);
  if (b.ausgabe) {
    const a = d.ausgaben.get(b.ausgabe)!;
    z.push(["JO", d.site.name], ["VL", a.jahrgang], ["IS", a.heft], ["SN", d.site.issn]);
    if (b.seiten?.length) z.push(["SP", b.seiten[0]], ["EP", b.seiten[1]]);
  } else z.push(["PB", d.site.name]);
  z.push(["ER", ""]);
  return z.map(([k, v]) => `${k}  - ${v}`).join("\r\n") + "\r\n";
}

export const anker = (s: string) => s.toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "");
