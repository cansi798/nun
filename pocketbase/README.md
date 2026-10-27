# PocketBase für NUN

Die Website liest ihre Inhalte heute aus `content/`. Später kommen sie aus PocketBase. Die Seiten selbst ändern sich dafür nicht, nur die Datenquelle in `src/lib/daten.ts`. Getestet mit PocketBase 0.25.9 und dem JS-SDK 0.25.0.

## Sammlungen

| Sammlung | Zweck | Lesen | Schreiben |
| --- | --- | --- | --- |
| `redaktion` | Anmeldung des Teams (Auth-Sammlung) | nur eigener Eintrag | nur Superuser |
| `autoren` | Autorinnen und Autoren, Schlüssel `slug` | öffentlich | Redaktion |
| `ausgaben` | Hefte, Schlüssel `kennung` wie `jahrgang-1-heft-1`, Gesamt-PDF | öffentlich | Redaktion |
| `beitraege` | alle Beiträge mit PDF, Schlüssel `slug` | öffentlich, wenn `veroeffentlicht` | Redaktion |

Die Felder entsprechen der Tabelle "Daten eines Beitrags" im Handbuch (design-system/Umsetzung.md). Format und Rubrik sind Auswahlfelder mit genau den Werten aus `content/site.json`. Löschen ist bewusst niemandem außer dem Superuser erlaubt, denn ein veröffentlichter Beitrag wird nicht still entfernt.

## Einrichten

1. PocketBase auf dem Server starten, etwa `./pocketbase serve --http=0.0.0.0:8090`, und einen Superuser anlegen.
2. Im Admin-Bereich unter Settings, Import collections den Inhalt von `pb_schema.json` einfügen und importieren.
3. Bestehende Inhalte übertragen.

```
PB_URL=https://pb.example.org PB_EMAIL=admin@example.org PB_PASSWORT=… npm run pb:import
```

4. Für jedes Teammitglied einen Eintrag in `redaktion` anlegen.

## Website aus PocketBase bauen

```
NUN_QUELLE=pocketbase PB_URL=https://pb.example.org npm run build
```

Die Seite bleibt statisch. Nach jeder Veröffentlichung wird sie neu gebaut, etwa über einen Webhook oder einen Cron-Job auf dem Server. PDFs werden direkt von PocketBase ausgeliefert.

## Interner Bereich

Wird beim Bauen `PUBLIC_PB_URL` gesetzt, meldet sich das Team unter `/intern/` an und speichert neue Beiträge direkt als Entwurf (`veroeffentlicht = false`). Ein zweites Teammitglied prüft den Entwurf im Admin-Bereich, trägt sich unter `geprueft_von` ein und setzt `veroeffentlicht`. Ohne `PUBLIC_PB_URL` erzeugt das Formular nur die JSON-Datei für `content/beitraege`.
