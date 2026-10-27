# UploadFeld

Das Upload-Feld nimmt im internen Bereich ein PDF per Drag and Drop oder Klick an.

- Fläche `surface-raised`, gestrichelte Kontur 1px in `ink-muted`, Ecken `radius-sm`, Mindesthöhe 180px, Inhalt mittig.
- In der Mitte das Emblem als kleines Zeichen (64px inklusive Schutzzone, `nun_emblem_transparent.svg` bzw. `transparent_hell`), darunter "PDF hierher ziehen" im Stil `label` und "oder Datei auswählen" als Textlink in `gold-text`.
- Darunter der Hinweis "PDF, höchstens 50 MB" in `ink-muted`.
- Beim Darüberziehen wird die Kontur durchgezogen in `gold` und die Fläche `gold-hauch`.
- Nach dem Hochladen zeigt eine Zeile Dateiname, Größe und einen goldenen Statuspunkt.
- Das Feld ist ein `label` für ein verstecktes `input type="file" accept="application/pdf"`, damit es auch per Tastatur bedienbar ist. Fokusring 2px in `fokus`.
- Die Seite übernimmt das eigentliche Hochladen und die Prüfung der Datei.
