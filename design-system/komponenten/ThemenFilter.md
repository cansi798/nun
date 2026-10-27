# ThemenFilter

Der Themenfilter ordnet die Übersicht der Publikationen nach Rubrik und Format.

- Zwei Zeilen. Oben die Rubriken aus dem Abschnitt Publikationen, unten die Formate. Beide als Liste von Schaltflächen mit `aria-pressed`.
- Eine Schaltfläche ist Text im Stil `button` in `ink` mit Haarlinie `linie` und `radius-sm`, Höhe 36px. Aktiv wird sie `nachtblau` gefüllt mit `ink-invers` und einem goldenen Punkt vor dem Wort.
- Die erste Schaltfläche heißt "Alle" und ist anfangs aktiv. Mehrere Rubriken gleichzeitig sind erlaubt.
- Rechts daneben ein Suchfeld mit Lupe als Linienicon für Titel, Autor und Schlagwort.
- Mobil scrollen die Zeilen waagerecht, statt umzubrechen.
- Die Seite filtert die Liste und hält die Auswahl in der Adresse fest, etwa `?rubrik=fiqh&format=artikel`, damit Links auf eine Auswahl funktionieren.
