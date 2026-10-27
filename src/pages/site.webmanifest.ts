import type { APIRoute } from "astro";
import { link } from "../lib/hilfen";
export const GET: APIRoute = () => new Response(JSON.stringify({
  name: "NUN", short_name: "NUN", lang: "de", start_url: link(),
  icons: [{ src: link("icon-192.png"), sizes: "192x192", type: "image/png" },
          { src: link("icon-512.png"), sizes: "512x512", type: "image/png" },
          { src: link("icon-maskable-512.png"), sizes: "512x512", type: "image/png", purpose: "maskable" }],
  background_color: "#F5EFE2", theme_color: "#F5EFE2", display: "standalone",
}, null, 2), { headers: { "Content-Type": "application/manifest+json" } });
