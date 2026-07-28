"""Abgeleitete Felder fuer deck.json.

Alles hier drin ist etwas, das ein Audit NICHT von Hand schreiben soll, weil es
sich aus dem Inhalt ergibt. Von Hand gepflegt waere es eine stille Fehlerquelle:
eine falsche Zahl bricht das Layout, ohne dass der Build meckert.

Wird von build_deck.py UND check_slide.py benutzt -- damit die Pruefung genau das
sieht, was der Build erzeugt.
"""

# Geschlossenes Vokabular: mehr kennt weder site-styles.css (.pill.*) noch
# die Severity-Skala (--sev-*).
SEV_TEXT = {
    "crit": "Kritisch",
    "high": "Hoch",
    "mid": "Mittel",
    "low": "Niedrig",
}


class ContentError(Exception):
    pass


def enrich(slide):
    """Ergaenzt abgeleitete Felder. Gibt eine neue dict zurueck."""
    s = dict(slide)
    typ = s.get("type")

    # Persona: die erste ist der Fokus (voll ausgeklappt), alle weiteren werden
    # als kompakte Karten daneben angedeutet. Aus einer schlichten Liste in der
    # deck.json abgeleitet, damit dort keine Struktur doppelt gepflegt wird.
    if typ == "persona" and isinstance(s.get("personas"), list):
        p = s["personas"]
        if not p:
            raise ContentError("persona: 'personas' ist leer – mindestens eine Persona nötig")
        # JEDE Persona kann im Admin zur Fokus-Persona werden -> jede braucht
        # sowohl den Einzeiler `kurz` (Karten-Ansicht) als auch die vier Blöcke
        # (Fokus-Ansicht). idx/is_focus steuern die Vor-Render-Sichtbarkeit.
        out = []
        for i, per in enumerate(p):
            per = dict(per)
            if "kurz" not in per:
                raise ContentError(
                    f"persona {i+1} ({per.get('name','?')}): 'kurz' fehlt – "
                    "jede Persona braucht einen Einzeiler (sie kann Fokus werden)"
                )
            per["idx"] = i
            per["is_focus"] = (i == 0)
            out.append(per)
        s["personas"] = out
        s["haupt"] = out[0]
        s["weitere"] = out[1:]
        s["hat_weitere"] = bool(out[1:])
        s["anzahl_weitere"] = len(out) - 1

    # Scope-Kacheln werden GEZAEHLT, nicht behauptet.
    #
    # Jede Zahl auf der Scope-Folie ist die Anzahl der Befunde ihrer Kategorie --
    # und genau diese Befunde stehen mit Beleg im Accordion derselben Folie. So
    # kann keine Zahl entstehen, die nicht belegt ist (frueher stand dort eine
    # handgeschriebene Summe, die sich durch nichts nachweisen liess).
    if typ == "scope" and isinstance(s.get("kategorien"), list) and isinstance(s.get("findings"), list):
        erlaubt = {k["key"] for k in s["kategorien"]}
        for i, f in enumerate(s["findings"], 1):
            kat = f.get("kategorie")
            if kat not in erlaubt:
                raise ContentError(
                    f'Finding {i} ({f.get("ueberschrift","?")}): kategorie "{kat}" '
                    f'unbekannt. Erlaubt: {", ".join(sorted(erlaubt))}'
                )
        kacheln = []
        for k in s["kategorien"]:
            treffer = [f for f in s["findings"] if f.get("kategorie") == k["key"]]
            belege = [f["beleg"] for f in treffer if f.get("beleg")]
            kachel = {
                "zahl": str(len(treffer)),
                "label": k["label"],
                "sub": k.get("sub", ""),
                "belege": belege,
            }
            kacheln.append(kachel)
        s["kacheln"] = kacheln
        s["hat_herleitung"] = any(k["belege"] for k in kacheln)

    # Das Pill-Label ist eine reine Uebersetzung der Stufe. Gilt fuer jede Folie
    # mit findings-Liste (findings-Folie ODER scope mit eingebettetem Accordion).
    if isinstance(s.get("findings"), list):
        out = []
        for i, f in enumerate(s["findings"], 1):
            f = dict(f)
            stufe = f.get("stufe")
            if stufe not in SEV_TEXT:
                raise ContentError(
                    f'Finding {i}: stufe "{stufe}" unbekannt. '
                    f'Erlaubt: {", ".join(SEV_TEXT)}'
                )
            f["stufe_text"] = SEV_TEXT[stufe]
            out.append(f)
        s["findings"] = out

    return s
