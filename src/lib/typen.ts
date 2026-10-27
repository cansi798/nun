// Datenmodell nach dem CI-Handbuch, Abschnitt Umsetzung, "Daten eines Beitrags".
export interface Autor {
  slug: string; vorname: string; nachname: string; abschluss: string;
  abschlussjahr: number | null; bachelorarbeit: string; orcid: string; bio: string;
}
export interface Ausgabe {
  id: string; jahrgang: number; heft: number; jahreszeit: string; jahr: number; titel: string; pdf: string;
}
export type Block =
  | { typ: "absatz" | "zitat"; text: string }
  | { typ: "h2" | "h3"; text: string }
  | { typ: "liste" | "nummern"; punkte: string[] }
  | { typ: "aaya"; arabisch: string; uebersetzung: string; quelle: string };
export interface Version { version: number; datum: string; hinweis: string }
export interface Beitrag {
  slug: string; format: string; rubrik: string; reihe?: string;
  titel: string; untertitel?: string; autoren: string[];
  ausgabe?: string; seiten?: number[]; datum: string; doi?: string;
  lesezeit?: number; umfang_seiten?: number; abschlussjahr?: number; betreuung?: string;
  abstract_de: string; abstract_en?: string; schlagworte: string[];
  pdf?: string; version: number; versionen?: Version[];
  inhalt?: Block[]; literatur?: string[]; beispiel?: boolean;
}
export interface Format { slug: string; name: string; kennzeichnung: string; umfang: string; beschreibung: string }
export interface Rubrik { slug: string; name: string; faecher: string }
export interface Site {
  name: string; leitsatz: string; beschreibung: string; issn: string;
  lizenz: { name: string; url: string }; institut: string; kontakt: string;
  navigation: { titel: string; pfad: string }[]; formate: Format[]; rubriken: Rubrik[];
}
export interface Daten {
  site: Site;
  autoren: Map<string, Autor>;
  ausgaben: Map<string, Ausgabe>;
  formate: Map<string, Format>;
  rubriken: Map<string, Rubrik>;
  beitraege: Beitrag[];
}
