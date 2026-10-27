# PublicationCard

Die Publikationskarte stellt einen Beitrag in Übersichten und auf der Startseite vor.

- Aufbau von oben nach unten mit Rubrik und Lesezeit (`meta`, `gold-text`, getrennt durch einen goldenen Punkt), Titel (`h3`, Cormorant), Autor und Datum (`ink-muted`), Abstract in zwei bis drei Zeilen (Source Serif 16px) und Textlink "Artikel lesen".
- Hintergrund `surface-raised`, Haarlinie `linie`, Ecken `radius-sm`, Innenabstand `space-4`, keine Schatten.
- Hover verändert nur die Linie zu `gold-linie`.
- Im Raster drei Karten nebeneinander mit Abstand `space-5`, mobil eine Spalte.
- Der Inhalt kommt aus der Datenbank, die Karte gibt nur Form und Reihenfolge vor.
