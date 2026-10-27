// @ts-check
import { defineConfig } from "astro/config";

// Hosting-unabhängig. Pfad und Adresse kommen aus der Umgebung,
// damit dieselbe Seite auf GitHub Pages (/nun/site/) und später auf einem
// eigenen Server (/) läuft.
export default defineConfig({
  site: process.env.NUN_SITE || "https://nun.example.org",
  base: process.env.NUN_BASE || "/",
  outDir: process.env.NUN_OUT || "dist",
  trailingSlash: "always",
  build: { format: "directory" },
  output: "static",
});
