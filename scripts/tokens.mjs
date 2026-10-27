// Erzeugt src/styles/tokens.css aus design-system/tokens.json (CI-Handbuch).
// tokens.css nie von Hand ändern, sondern tokens.json.
import { readFileSync, writeFileSync } from "node:fs";

const t = JSON.parse(readFileSync(new URL("../design-system/tokens.json", import.meta.url), "utf8"));
const erstes = t.color.themes[0].id;
const hell = [], dunkel = [], rest = [], stile = [];

for (const tok of t.color.tokens) {
  const v = typeof tok.value === "string" ? { [erstes]: tok.value } : tok.value;
  hell.push(`  --${tok.name}: ${v[erstes]};`);
  if (v.dark && v.dark !== v[erstes]) dunkel.push(`  --${tok.name}: ${v.dark};`);
}
for (const fam of ["spacing", "radius", "layout", "shadow"]) {
  for (const tok of t[fam]?.tokens ?? []) rest.push(`  --${tok.name}: ${tok.value};`);
}
for (const [k, v] of Object.entries(t.type.families)) rest.push(`  --font-${k}: ${v};`);
for (const g of t.type.groups) {
  for (const s of g.styles) {
    const r = [`font-family: var(--font-${g.family})`, `font-size: ${s.fontSize}`,
      `line-height: ${s.lineHeight}`, `font-weight: ${s.fontWeight}`];
    if (s.fontStyle) r.push(`font-style: ${s.fontStyle}`);
    if (s.letterSpacing) r.push(`letter-spacing: ${s.letterSpacing}`);
    stile.push(`.t-${s.name} { ${r.join("; ")}; }`);
  }
}
const css = `/* ${t.name} — generated from tokens.json. Nicht von Hand ändern. */
:root {
${hell.join("\n")}
${rest.join("\n")}
  color-scheme: light;
}
[data-theme="dark"] {
${dunkel.join("\n")}
  color-scheme: dark;
}
${stile.join("\n")}
`;
writeFileSync(new URL("../src/styles/tokens.css", import.meta.url), css);
console.log(`tokens.css erzeugt (${hell.length} Farben, ${stile.length} Textstile)`);
