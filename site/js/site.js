// NUN · kleine Helfer ohne Abhängigkeiten. Die Seite funktioniert auch ohne JavaScript.
(function () {
  "use strict";
  var doc = document.documentElement;

  // Helles und dunkles Thema
  document.querySelectorAll("[data-thema-wechsel]").forEach(function (knopf) {
    knopf.addEventListener("click", function () {
      var neu = doc.dataset.theme === "dark" ? "light" : "dark";
      doc.dataset.theme = neu;
      try { localStorage.setItem("nun-thema", neu); } catch (_) {}
    });
  });

  // Mobiles Menü
  var menue = document.querySelector(".menue-knopf");
  var nav = document.getElementById("hauptnav");
  if (menue && nav) {
    menue.addEventListener("click", function () {
      var offen = nav.classList.toggle("offen");
      menue.setAttribute("aria-expanded", String(offen));
    });
    document.addEventListener("keydown", function (ev) {
      if (ev.key === "Escape" && nav.classList.contains("offen")) {
        nav.classList.remove("offen");
        menue.setAttribute("aria-expanded", "false");
        menue.focus();
      }
    });
  }

  // Themenfilter. Auswahl steht in der Adresse, etwa ?rubrik=fiqh&format=artikel
  var filter = document.querySelector("[data-filter]");
  if (filter) {
    var karten = Array.prototype.slice.call(document.querySelectorAll("[data-liste] .karte"));
    var suche = filter.querySelector("input[type=search]");
    var treffer = document.querySelector("[data-treffer]");
    var leer = document.querySelector("[data-leer]");
    var gruppen = Array.prototype.slice.call(filter.querySelectorAll("[data-gruppe]"));

    var auswahl = function (gruppe) {
      return Array.prototype.slice.call(gruppe.querySelectorAll('button[aria-pressed="true"]'))
        .map(function (b) { return b.dataset.wert; }).filter(Boolean);
    };

    var passt = function (karte, rubriken, formate, wort) {
      if (rubriken.length && rubriken.indexOf(karte.dataset.rubrik) < 0) return false;
      if (formate.length && formate.indexOf(karte.dataset.format) < 0) return false;
      if (!wort) return true;
      return wort.split(/\s+/).every(function (w) { return karte.dataset.suche.indexOf(w) >= 0; });
    };

    var anwenden = function (adresseSchreiben) {
      var werte = {};
      gruppen.forEach(function (g) { werte[g.dataset.gruppe] = auswahl(g); });
      var wort = (suche.value || "").trim().toLowerCase();
      var n = 0;
      karten.forEach(function (k) {
        var zeigen = passt(k, werte.rubrik, werte.format, wort);
        k.hidden = !zeigen;
        if (zeigen) n++;
      });
      treffer.textContent = n === 1 ? "1 Beitrag" : n + " Beiträge";
      leer.hidden = n > 0;
      if (adresseSchreiben) {
        var p = new URLSearchParams();
        if (werte.rubrik.length) p.set("rubrik", werte.rubrik.join(","));
        if (werte.format.length) p.set("format", werte.format.join(","));
        if (wort) p.set("q", wort);
        var q = p.toString();
        history.replaceState(null, "", location.pathname + (q ? "?" + q : ""));
      }
    };

    var setzen = function (gruppe, werte) {
      var knoepfe = Array.prototype.slice.call(gruppe.querySelectorAll("button"));
      knoepfe.forEach(function (b) {
        b.setAttribute("aria-pressed", String(b.dataset.wert ? werte.indexOf(b.dataset.wert) >= 0 : werte.length === 0));
      });
    };

    var start = new URLSearchParams(location.search);
    gruppen.forEach(function (g) {
      var werte = (start.get(g.dataset.gruppe) || "").split(",").filter(Boolean);
      setzen(g, werte);
      g.addEventListener("click", function (ev) {
        var b = ev.target.closest("button");
        if (!b) return;
        var jetzt = auswahl(g);
        if (!b.dataset.wert) { jetzt = []; }
        else if (jetzt.indexOf(b.dataset.wert) >= 0) { jetzt.splice(jetzt.indexOf(b.dataset.wert), 1); }
        else { jetzt.push(b.dataset.wert); }
        setzen(g, jetzt);
        anwenden(true);
      });
    });
    suche.value = start.get("q") || "";
    suche.addEventListener("input", function () { anwenden(true); });
    anwenden(false);
  }

  // Zitiervorschlag kopieren
  document.querySelectorAll("[data-kopieren]").forEach(function (knopf) {
    knopf.addEventListener("click", function () {
      var ziel = document.querySelector(knopf.dataset.kopieren);
      if (!ziel) return;
      var fertig = function () {
        knopf.textContent = "Kopiert";
        setTimeout(function () { knopf.textContent = "Kopieren"; }, 2000);
      };
      if (navigator.clipboard) navigator.clipboard.writeText(ziel.innerText).then(fertig, fertig);
      else fertig();
    });
  });

  // Button "Zitieren" springt zum Zitiervorschlag und setzt den Fokus dorthin
  document.querySelectorAll('a[href="#zitieren"]').forEach(function (a) {
    a.addEventListener("click", function () {
      var z = document.getElementById("zitieren");
      if (z) setTimeout(function () { z.focus({ preventScroll: true }); }, 0);
    });
  });

  // Interner Bereich. Erzeugt die JSON-Datei für content/beitraege und prüft das PDF
  var form = document.querySelector("[data-einstellen]");
  if (form) {
    var feld = form.querySelector("[data-upload]");
    var input = feld.querySelector("input[type=file]");
    var anzeige = form.querySelector("[data-upload-datei]");
    var fehler = form.querySelector("[data-fehler]");
    var datei = null;
    var MAX = 50 * 1024 * 1024;

    var zeigeDatei = function (f) {
      if (!f) return;
      if (f.type !== "application/pdf") { melde("Bitte nur PDF-Dateien hochladen."); return; }
      if (f.size > MAX) { melde("Die Datei ist größer als 50 MB."); return; }
      datei = f;
      fehler.hidden = true;
      anzeige.hidden = false;
      anzeige.textContent = f.name + " · " + (f.size / 1048576).toFixed(1).replace(".", ",") + " MB · bereit";
    };
    var melde = function (text) { fehler.textContent = text; fehler.hidden = false; };

    ["dragenter", "dragover"].forEach(function (t) {
      feld.addEventListener(t, function (ev) { ev.preventDefault(); feld.classList.add("ueber"); });
    });
    ["dragleave", "drop"].forEach(function (t) {
      feld.addEventListener(t, function (ev) { ev.preventDefault(); feld.classList.remove("ueber"); });
    });
    feld.addEventListener("drop", function (ev) { zeigeDatei(ev.dataTransfer.files[0]); });
    input.addEventListener("change", function () { zeigeDatei(input.files[0]); });

    var slug = function (s) {
      return s.toLowerCase().replace(/ä/g, "ae").replace(/ö/g, "oe").replace(/ü/g, "ue").replace(/ß/g, "ss")
        .replace(/[^a-z0-9]+/g, "-").replace(/^-+|-+$/g, "").slice(0, 60);
    };

    form.addEventListener("submit", function (ev) {
      ev.preventDefault();
      var d = new FormData(form);
      var worte = String(d.get("schlagworte")).split(",").map(function (s) { return s.trim(); }).filter(Boolean);
      if (worte.length > 5) { melde("Höchstens fünf Schlagworte."); return; }
      var von = parseInt(d.get("seite_von"), 10), bis = parseInt(d.get("seite_bis"), 10);
      var s = slug(String(d.get("titel")));
      var beitrag = {
        slug: s, format: d.get("format"), rubrik: d.get("rubrik"),
        titel: d.get("titel"), untertitel: d.get("untertitel"),
        autoren: d.getAll("autoren"), ausgabe: d.get("ausgabe"),
        seiten: von && bis ? [von, bis] : [], datum: d.get("datum"), doi: d.get("doi"),
        abstract_de: d.get("abstract_de"), abstract_en: d.get("abstract_en"),
        schlagworte: worte, pdf: datei ? "pdf/" + s + ".pdf" : "",
        version: 1, versionen: [], inhalt: [], literatur: []
      };
      var blob = new Blob([JSON.stringify(beitrag, null, 2) + "\n"], { type: "application/json" });
      var a = document.createElement("a");
      a.href = URL.createObjectURL(blob);
      a.download = s + ".json";
      a.click();
      URL.revokeObjectURL(a.href);
      fehler.hidden = false;
      fehler.textContent = "Datei " + s + ".json erstellt. Legen Sie sie in content/beitraege und das PDF als static/pdf/" + s + ".pdf ab.";
    });
  }
})();
