import type { APIRoute } from "astro";
import { ladeDaten } from "../lib/daten";
import { absolut } from "../lib/hilfen";
export const GET: APIRoute = async () => {
  const d = await ladeDaten();
  const pfade = ["", "publikationen/", "ausgaben/", "themen/", "autoren/", "podcast/", "ueber-uns/", "open-access/", "impressum/", "datenschutz/",
    ...d.beitraege.map((b) => `beitraege/${b.slug}/`), ...[...d.ausgaben.keys()].map((a) => `ausgaben/${a}/`),
    ...[...d.autoren.keys()].map((a) => `autoren/${a}/`)];
  const urls = pfade.map((p) => `<url><loc>${absolut(p)}</loc></url>`).join("");
  return new Response(`<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">${urls}</urlset>\n`,
    { headers: { "Content-Type": "application/xml" } });
};
