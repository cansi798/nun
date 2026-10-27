import type { APIRoute } from "astro";
import { ladeDaten } from "../../../lib/daten";
import { bibtex } from "../../../lib/hilfen";
export async function getStaticPaths() {
  return (await ladeDaten()).beitraege.map((b) => ({ params: { slug: b.slug } }));
}
export const GET: APIRoute = async ({ params }) => {
  const d = await ladeDaten();
  return new Response(bibtex(d, d.beitraege.find((b) => b.slug === params.slug)!),
    { headers: { "Content-Type": "application/x-bibtex; charset=utf-8" } });
};
