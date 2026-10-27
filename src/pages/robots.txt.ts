import type { APIRoute } from "astro";
import { absolut, link } from "../lib/hilfen";
export const GET: APIRoute = () =>
  new Response(`User-agent: *\nDisallow: ${link("intern/")}\nSitemap: ${absolut("sitemap.xml")}\n`);
