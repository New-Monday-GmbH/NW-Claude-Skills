#!/usr/bin/env python3
"""Beschafft die Fotos der Firmenzentralen fuer die Summary-Seiten.

    python3 scripts/hq_bilder.py portfolio.json
    python3 scripts/hq_bilder.py portfolio.json --setzen
    python3 scripts/hq_bilder.py portfolio.json --quelle
    python3 scripts/hq_bilder.py "Deutsche Bank"
    python3 scripts/hq_bilder.py "Deutsche Bank" --zweites
    python3 scripts/hq_bilder.py --selbsttest

Rechts auf der Summary-Seite steht das Gebaeude des Kunden. Das ist kein
Schmuckbild: Es sagt dem Leser, um wen es geht, bevor er den ersten Satz liest.
Ein falsches Gebaeude sagt ihm etwas Falsches - deshalb bricht dieses Skript
lieber ab und meldet die Luecke, als irgendein Buerohaus einzutragen.

Quellenkette je Kunde, wie bei den Logos: erst die Bibliothek (kostet nichts und
ist schon geprueft), dann Wikimedia Commons, dann das Bildmaterial des
Wikipedia-Artikels. Aus beiden Netzquellen kommt nur durch, was Firmenname UND
Gebaeudewort im Dateinamen traegt und kein Werk, Museum oder Autohaus ist. Die
Schranke ist mit Absicht eng: Die Suche nach "Opel headquarters" liefert die
OPEC, "Opel Zentrale" Amtsblaetter, und ueber die Bildbeschreibungen kam ein
niedersaechsischer See als Samsung-Zentrale herein. Lieber nichts finden.

Dass die Schranke haelt, prueft --selbsttest an einer Tabelle echter Fundstuecke
- der guten wie der Fehlgriffe. Ohne Netz, in einer Sekunde: nach jeder Aenderung
an Suche oder Pruefung laufen lassen.

Zwei Projekte beim selben Kunden bekommen zwei Motive. Steht dasselbe Haus
zweimal in einem 33-Seiten-Deck, faellt das auf; --zweites holt ein weiteres,
und der Bericht sagt es, wenn es keins gibt.

Triste Motive werden gemieden: Ein grau verhangenes Foto (Beispiel: das
Citroën-Haendlergebaeude mit Zaun und Regenhimmel, das im Freia-Deck auf der
Summary-Seite stand) zieht die ganze Seite runter - die Referenz (Paul Hecker)
zeigt durchgehend Sonne, blauen Himmel oder stimmungsvolles Abendlicht.
wirkt_trist() misst die Farbsaettigung; trist wirkende Kandidaten werden
uebersprungen, solange es Alternativen gibt, und sonst mit Warnung gesetzt.
Die Schwelle ist Heuristik, kein Urteil: Das gesetzte Bild gehoert trotzdem
angesehen.

BRAUCHT OFFENES NETZ. Lokal und in Claude Desktop funktioniert das; im
Browser-Chat blockt der Proxy fremde Domains. Dort das Bild von Hand ablegen
und den Pfad in die portfolio.json schreiben.

Woher jedes Bild stammt und unter welcher Lizenz, steht in quellen.json neben
den Bildern - immer, nicht auf Zuruf. Die Bilder gehen in ein Kundendokument,
und CC-BY verlangt eine Nennung. --quelle zeigt den Nachweis an.
"""
from __future__ import annotations

import html
import json
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from add_logo import slugify  # noqa: E402
from logo_lib import bibliothek  # noqa: E402
from logos_ergaenzen import slugs  # noqa: E402

# Wikimedia drosselt namenlose Aufrufer hart; die Nutzungsregeln verlangen
# ohnehin eine Kennung mit Kontakt.
KOPF = {"User-Agent": "newmonday-portfolio/1.0 (Portfolio-Aufbereitung; "
                      "+https://newmonday.co)"}

# Die Flaeche ist 1020pt breit und wird auch so gezeigt. Darunter wird das Foto
# sichtbar weich; hochgerechnet wird nichts, das erfindet keine Details.
MIN_BREITE = 1400
# Die Flaeche ist zwar hoch, aber ein Hochformat wirkt darin wie ein Ausschnitt
# aus einem anderen Bild. Querformat und nahezu quadratisch sind richtig.
MIN_VERHAELTNIS = 0.9
MAX_BREITE = 2400          # doppelte Flaechenbreite, mehr braucht der Druck nicht
QUALITAET = 88

# Ein Treffer muss beides tragen: den Firmennamen und ein Gebaeudewort. Die
# Gebaeudewoerter stehen schon in Slug-Schreibweise da, weil gegen den
# zerlegten Dateinamen verglichen wird.
# SITZ nennt das Haus ausdruecklich als Firmensitz - die beste Auskunft, die ein
# Dateiname geben kann. Zaehlt, wo immer es steht, und rangiert vorn.
SITZ = frozenset("""
    headquarters headquarter hq zentrale konzernzentrale unternehmenszentrale
    hauptsitz firmensitz konzernsitz stammsitz hauptverwaltung
""".split())
# BAU benennt ein Haus der Firma, aber nicht zwingend ihren Sitz. Zaehlt genauso,
# rangiert aber dahinter: Das Postbank-Hochhaus in Essen ist ein Postbank-Haus,
# die Zentrale steht in Bonn.
BAU = frozenset("""
    hauptgebaeude verwaltungsgebaeude tower towers hochhaus turm campus
""".split())
STARK = SITZ | BAU
# SCHWACH sagt nur "hier steht ein Haus" oder zeigt einen Teil davon. Das trifft
# auf jedes Gebaeude zu, das den Firmennamen irgendwo im Titel traegt, und muss
# deshalb an den Namen gebunden sein - siehe angrenzend(). Portal und Eingang
# stehen mit dabei, weil deutsche Zentralen oft von der Tuer her fotografiert
# sind: das Adam-Opel-Haus liegt auf Commons als "…OpelHauptportalAdamOpel".
SCHWACH = frozenset("""
    building buildings office offices house
    sitz verwaltung buerogebaeude firmengebaeude gebaeude haus stammhaus
    portal hauptportal eingang haupteingang entrance
""".split())
# Kein Foto eines Hauses, sondern Marke, Karte oder Schaubild - oder gar kein
# Foto: Commons fuehrt zunehmend KI-generierte Bilder und Renderings, und ein
# erzeugtes Gebaeude auf einer Kundenseite ist schlimmer als ein fehlendes.
# Die Marker stehen als Mehrwort-Zeichenfolgen in allen drei Schreibweisen
# (Leerzeichen, Bindestrich, Unterstrich), weil Commons-Titel kanonisch mit
# Leerzeichen kommen, Dateinamen aber alle drei fuehren; ein blosses "ai"
# traefe jedes "Main". Die Schranke faengt nur die ehrlich beschrifteten -
# den Rest muss der Blick auf das Bild fangen (siehe SKILL.md, Schritt 5).
KEIN_FOTO = ("logo", "wordmark", "icon", "map", "karte", "flag", "flagge",
             "seal", "wappen", "diagram", "chart", "grafik", "schema",
             "ai generated", "ai-generated", "ai_generated", "aigenerated",
             "ki generiert", "ki-generiert", "ki_generiert",
             "generated by", "generated-by", "generated_by", "generated image",
             "midjourney", "dall-e", "dalle", "dall_e", "dall·e",
             "stable diffusion", "stable-diffusion", "stable_diffusion",
             "text to image", "text-to-image", "text_to_image",
             "render", "3d model", "3d-model", "illustration", "artwork",
             "concept")
# Traegt zwar Firmenname und Gebaeudewort, ist aber nicht die Zentrale. Das
# Verwaltungsgebaeude eines Werks als Firmensitz auszugeben ist eine
# Falschaussage - dann lieber die Luecke.
NICHT_ZENTRALE = frozenset("""
    werk werke werks werksgelaende werkshalle fabrik factory plant
    produktion produktionswerk montagewerk lager logistikzentrum
    museum musee filiale autohaus baustelle ruine
    dealership dealer showroom garage concession niederlassung
    park parc garden jardin garten denkmal monument stadion stadium
""".split())
BILDENDUNGEN = (".jpg", ".jpeg", ".png")

# Unter dieser mittleren Farbsaettigung wirkt ein Foto grau und trist. An der
# Bibliothek kalibriert: die tristen Motive (Citroën-Haendler mit Regenhimmel
# 0,08, Boeing unter weissem Himmel 0,08) liegen weit unter den freundlichen
# (Opel 0,32-0,38, Postbank 0,33, Samsung 0,41, Deutsche Bank 0,53-0,55).
TRIST_SAETTIGUNG = 0.16
# Zweite Stufe: kaum Saettigung UND kein blauer Himmel im oberen Bilddrittel.
TRIST_GRAU, TRIST_BLAU = 0.22, 0.03

_pause = 0.0               # Commons antwortet auf Salven mit HTTP 429


def hq_bibliothek() -> Path:
    """Sammelort neben der Logobibliothek. Gefundene Bilder bleiben liegen,
    damit der Bestand ueber die Laeufe waechst - genau wie bei den Logos."""
    ordner = bibliothek().parent / "hq"
    ordner.mkdir(parents=True, exist_ok=True)
    return ordner


def laden(url: str) -> bytes:
    """Mit Bremse und zweitem Anlauf. Wikimedia beantwortet Salven mit 429, und
    ein 429 saehe im Bericht sonst aus wie ein ehrliches 'nichts gefunden'."""
    global _pause
    anfrage = urllib.request.Request(url, headers=KOPF)
    for versuch in range(3):
        warten = _pause - time.monotonic()
        if warten > 0:
            time.sleep(warten)
        _pause = time.monotonic() + 1.0
        try:
            with urllib.request.urlopen(anfrage, timeout=30) as antwort:
                return antwort.read()
        except urllib.error.HTTPError as fehler:
            if fehler.code not in (429, 503) or versuch == 2:
                raise
            _pause = time.monotonic() + 5.0 * (versuch + 1)
    raise RuntimeError("unerreichbar")           # nur der Vollstaendigkeit halber


def api(host: str, **felder) -> dict:
    felder.setdefault("format", "json")
    felder.setdefault("action", "query")
    url = f"https://{host}/w/api.php?" + urllib.parse.urlencode(felder)
    return json.loads(laden(url))


# ── Pruefen, ob ein Fund wirklich zur Firma gehoert ──────────────────────

def normal(text: str) -> str:
    """Vergleichsform. Dieselbe Umschrift wie bei den Dateinamen, sonst finden
    'Müller-Zentrale' und der Slug 'mueller' nicht zusammen."""
    return slugify(text).replace("-", "") if text else ""


def wortteile(text: str) -> list[str]:
    """Den Namen in seine Woerter zerlegen.

    Commons-Dateinamen sind haeufig zusammengeschrieben; ihre Wortgrenzen
    stehen dann nur noch in den Grossbuchstaben - das Adam-Opel-Haus liegt dort
    als 'RüsselsheimMainMarktstrOpelHauptportalAdamOpel.JPG'. Ohne diesen
    Schnitt sieht die Wort-fuer-Wort-Pruefung darin ein einziges Wort und
    findet weder Firma noch Gebaeude.
    """
    getrennt = re.sub(r"(?<=[a-zäöüß0-9])(?=[A-ZÄÖÜ])"
                      r"|(?<=[A-ZÄÖÜ])(?=[A-ZÄÖÜ][a-zäöüß])", " ", text)
    return slugify(getrennt).split("-")


def kernwoerter(firma: str) -> list[str]:
    """Die tragenden Namensteile ohne Rechtsform - 'Arvato Systems GmbH' wird
    zu ['arvato', 'systems']. Kuerzel unter drei Zeichen tragen nichts."""
    grund = (slugs(firma) or [slugify(firma)])[-1]
    woerter = [w for w in grund.split("-") if len(w) >= 3]
    return woerter or [normal(firma)]


def gemeint(text: str, firma: str) -> bool:
    """Steht der Firmenname im Text - am Stueck?

    Am Stueck, weil die Namensteile einzeln zu viel treffen: 'Hauptverwaltung
    Deutsche Bundesbank Stuttgart' traegt 'deutsche' und 'bank' und ist trotzdem
    eine andere Bank. Ohne Trenner verglichen, damit der Name auch erkannt wird,
    wo er zusammengeschrieben steht - 'AdamOpel' und 'Opel-Haus' meinen beide
    Opel.

    Zwei Zeichen Luft zwischen den Namensteilen, weil Deutsch die Firma beugt:
    'der Deutschen Bahn' ist dieselbe Bahn. Fuer 'Deutsche Bundesbank' reicht
    diese Luft nicht - genau so soll es sein.
    """
    muster = "[a-z]{0,2}".join(re.escape(w) for w in kernwoerter(firma))
    return re.search(muster, normal(text)) is not None


def angrenzend(teile: list[str], wort: str, firma: str) -> bool:
    """Steht das Gebaeudewort unmittelbar neben einem Namensteil der Firma?"""
    kern = set(kernwoerter(firma))
    for i, teil in enumerate(teile):
        if teil != wort:
            continue
        if set(teile[max(0, i - 1):i] + teile[i + 1:i + 2]) & kern:
            return True
    return False


def zeigt_gebaeude(text: str, firma: str) -> bool:
    """Das Gebaeudewort muss als eigenes Wort dastehen. Als blosse Zeichenfolge
    steckt 'haus' auch in 'Heiligenhaus' und 'zentrale' in 'Zentrales Ufer' -
    darueber kam ein Opel Zafira als Opel-Zentrale herein.

    Ein schwaches Wort muss ausserdem am Namen haengen. 'Buildings in Meguro -
    Peugeot' und 'Building in the Parc André Citroën' nennen beides, meinen aber
    ein Autohaus in Tokio und ein Gewaechshaus in einem Pariser Park."""
    teile = wortteile(text)
    vorhanden = set(teile)
    if vorhanden & STARK:
        return True
    return any(angrenzend(teile, w, firma) for w in vorhanden & SCHWACH)


def brauchbar(titel: str, firma: str) -> bool:
    """Nur der Dateiname zaehlt, nicht die Beschreibung. Deren Text schleppt
    Kameramodelle und Nachbarkategorien mit: darueber kam ein niedersaechsischer
    See als Samsung-Zentrale herein und ein Autohaus als Opel-Zentrale."""
    name = titel.removeprefix("File:").removeprefix("Datei:")
    if not name.lower().endswith(BILDENDUNGEN):
        return False
    if any(w in name.lower() for w in KEIN_FOTO):
        return False
    if set(wortteile(name)) & NICHT_ZENTRALE:
        return False
    return gemeint(name, firma) and zeigt_gebaeude(name, firma)


def rang(fund: dict) -> tuple:
    """Reihenfolge unter den Treffern: erst die, die den Sitz beim Namen nennen,
    dann die uebrigen Firmengebaeude, dann Querformat, dann die groessere
    Datei."""
    teile = set(wortteile(fund["titel"]))
    quer = fund["breite"] / max(1, fund["hoehe"])
    return (
        -bool(teile & SITZ),
        -bool(teile & BAU),
        -(1.2 <= quer <= 2.4),
        -fund["breite"],
    )


# ── Quellen ──────────────────────────────────────────────────────────────

def _funde(seiten: dict, woher: str) -> list[dict]:
    """imageinfo-Antwort in flache Eintraege wandeln."""
    ergebnis = []
    for seite in (seiten or {}).values():
        info = (seite.get("imageinfo") or [{}])[0]
        if not info.get("width"):
            continue
        meta = info.get("extmetadata", {})

        def feld(name):
            return html.unescape(re.sub(r"<[^>]+>", " ",
                                        meta.get(name, {}).get("value", "")))

        ergebnis.append({
            "titel": seite["title"],
            "breite": info["width"],
            "hoehe": info["height"],
            "url": info.get("thumburl") or info["url"],
            "seite": info.get("descriptionurl", ""),
            "lizenz": feld("LicenseShortName").strip() or "unbekannt",
            "urheber": " ".join(feld("Artist").split())[:120],
            "woher": woher,
        })
    return ergebnis


def suchname(firma: str) -> str:
    """Der Name, mit dem gesucht wird: ohne Rechtsform und ohne die zweite Firma
    hinter dem Komma. 'Opel, Peugeot und Citroën headquarters' findet nichts,
    'Opel headquarters' schon. Dieselbe Grundlage wie kernwoerter(), damit
    Suchfrage und Pruefung nicht auseinanderlaufen."""
    return " ".join(kernwoerter(firma))


# Wonach gefragt wird. Die ersten drei fragen allgemein nach dem Sitz, die
# uebrigen nach dem Eigennamen: Deutsche Firmenzentralen heissen oft
# "Adam-Opel-Haus", "Postbank-Hochhaus" oder "Silberturm" und stehen unter
# keiner der allgemeinen Fragen - das Adam-Opel-Haus taucht weder unter
# "Opel headquarters" noch unter "Opel building" auf, unter "Opel Haus" sofort.
FRAGEN = ("headquarters", "Zentrale", "building",
          "Hauptverwaltung", "Haus", "Hochhaus", "Turm")


def aus_commons(firma: str) -> list[dict]:
    """Commons durchsuchen. Mehrere Anlaeufe, weil dieselbe Zentrale mal
    englisch, mal deutsch und mal nur unter ihrem Eigennamen beschriftet ist."""
    name = suchname(firma)
    funde, gesehen = [], set()
    for wort in FRAGEN:
        antwort = api("commons.wikimedia.org", generator="search", gsrnamespace=6,
                      gsrlimit=12, gsrsearch=f"{name} {wort}", prop="imageinfo",
                      iiprop="url|size|extmetadata", iiurlwidth=MAX_BREITE)
        for fund in _funde(antwort.get("query", {}).get("pages"), "Wikimedia Commons"):
            if fund["titel"] not in gesehen:
                gesehen.add(fund["titel"])
                funde.append(fund)
    return funde


def aus_wikipedia(firma: str) -> list[dict]:
    """Das Bildmaterial des Firmenartikels, in der Reihenfolge des Artikels -
    die Infobox steht oben, ihr Gebaeudefoto kommt damit zuerst."""
    for sprache in ("de", "en"):
        host = f"{sprache}.wikipedia.org"
        treffer = api(host, list="search", srlimit=1,
                      srsearch=suchname(firma)).get("query", {}).get("search", [])
        if not treffer:
            continue
        artikel = treffer[0]["title"]
        seiten = api(host, prop="revisions", rvprop="content", rvslots="main",
                     titles=artikel).get("query", {}).get("pages", {})
        text = ""
        for seite in seiten.values():
            text = (seite.get("revisions") or [{}])[0].get(
                "slots", {}).get("main", {}).get("*", "")
        namen = []
        for name in re.findall(r"\[\[\s*(?:Datei|File|Bild)\s*:\s*([^\|\]\n]+)", text):
            name = name.strip()
            if name.lower().endswith(BILDENDUNGEN) and name not in namen:
                namen.append(name)
        namen = [n for n in namen if brauchbar(n, firma)][:8]
        if not namen:
            continue
        antwort = api("commons.wikimedia.org", prop="imageinfo",
                      iiprop="url|size|extmetadata", iiurlwidth=MAX_BREITE,
                      titles="|".join("File:" + n for n in namen))
        funde = _funde(antwort.get("query", {}).get("pages"),
                       f"Wikipedia {sprache} ({artikel})")
        if funde:
            return funde
    return []


QUELLEN = [aus_commons, aus_wikipedia]


# ── Triste Motive ────────────────────────────────────────────────────────

def wirkt_trist(bild) -> bool:
    """Wirkt das Foto grau und trist? Gemessen wird die mittlere Saettigung
    und der Anteil blauen Himmels im oberen Bilddrittel. Ein sonniges Motiv
    hat satte Farben; ein verhangenes ist entsaettigt, auch wenn der Himmel
    einen Blaustich traegt. Heuristik, kein Urteil - das gesetzte Bild gehoert
    trotzdem angesehen."""
    im = bild.convert("RGB").resize((64, 64))
    oben = list(im.crop((0, 0, 64, 22)).getdata())
    blau = sum(1 for r, g, b in oben if b > r + 12 and b >= g and b > 90) / len(oben)
    hsv = im.convert("HSV")
    s = list(hsv.getchannel("S").getdata())
    saettigung = sum(s) / len(s) / 255
    return saettigung < TRIST_SAETTIGUNG or (saettigung < TRIST_GRAU
                                             and blau < TRIST_BLAU)


def datei_trist(pfad: Path) -> bool:
    from PIL import Image
    try:
        with Image.open(pfad) as bild:
            return wirkt_trist(bild)
    except Exception:
        return False


def bytes_trist(daten: bytes) -> bool:
    import io

    from PIL import Image
    try:
        return wirkt_trist(Image.open(io.BytesIO(daten)))
    except Exception:
        return False


# ── Ablegen ──────────────────────────────────────────────────────────────

def ablegen(daten: bytes, name: str) -> Path:
    """Als JPEG in die Bibliothek. Grosse Fassungen werden verkleinert, kleine
    bleiben klein - hochrechnen bringt keine Details, nur Dateigroesse."""
    import io

    from PIL import Image

    bild = Image.open(io.BytesIO(daten))
    if bild.mode != "RGB":
        bild = bild.convert("RGB")
    if bild.width > MAX_BREITE:
        hoehe = round(bild.height * MAX_BREITE / bild.width)
        bild = bild.resize((MAX_BREITE, hoehe), Image.LANCZOS)
    ziel = hq_bibliothek() / f"{name}.jpg"
    bild.save(ziel, "JPEG", quality=QUALITAET, optimize=True)
    return ziel


def nachweis_schreiben(datei: str, firma: str, fund: dict) -> None:
    """Herkunft und Lizenz festhalten. CC-BY verlangt eine Nennung, und die
    Uebergabe kann sie nur nennen, wenn sie jemand aufgeschrieben hat."""
    pfad = hq_bibliothek() / "quellen.json"
    register = {}
    if pfad.exists():
        try:
            register = json.loads(pfad.read_text(encoding="utf-8"))
        except ValueError:
            register = {}
    register[datei] = {
        "firma": firma,
        "quelle": fund["woher"],
        "datei": fund["titel"],
        "seite": fund.get("seite", ""),
        "lizenz": fund.get("lizenz", "unbekannt"),
        "urheber": fund.get("urheber", ""),
        "geholt": date.today().isoformat(),
    }
    pfad.write_text(json.dumps(register, ensure_ascii=False, indent=2) + "\n",
                    encoding="utf-8")


def nachweis_lesen() -> dict:
    pfad = hq_bibliothek() / "quellen.json"
    if not pfad.exists():
        return {}
    try:
        return json.loads(pfad.read_text(encoding="utf-8"))
    except ValueError:
        return {}


def aus_bibliothek(firma: str) -> list[Path]:
    """Alle Bilder der Bibliothek zu dieser Firma, das genaueste zuerst.

    Eine Liste, keine einzelne Datei: Zwei Projekte beim selben Kunden brauchen
    zwei Motive, und das zweite liegt oft schon da.
    """
    ordner = hq_bibliothek()
    vorhanden = sorted(p for p in ordner.iterdir() if p.suffix == ".jpg")
    treffer: list[Path] = []
    for s in slugs(firma):
        genau = [p for p in vorhanden if p.stem == s]
        # "team" trifft "team-gmbh", "opel" trifft das zweite Motiv "opel-2"
        aehnlich = [p for p in vorhanden if p.stem != s
                    and (p.stem.startswith(s + "-") or s.startswith(p.stem + "-"))]
        for pfad in genau + aehnlich:
            if pfad not in treffer:
                treffer.append(pfad)
    return treffer


def freier_name(basis: str) -> str:
    """Naechster unbelegter Dateiname. Das zweite Motiv derselben Firma heisst
    'opel-2' - so bleibt der Bestand pro Firma beieinander und aus_bibliothek()
    findet beide."""
    ordner = hq_bibliothek()
    if not (ordner / f"{basis}.jpg").exists():
        return basis
    for n in range(2, 100):
        if not (ordner / f"{basis}-{n}.jpg").exists():
            return f"{basis}-{n}"
    return basis


def hq_bild(firma: str, belegt: frozenset[str] = frozenset()) -> tuple[Path | None, str]:
    """Foto der Firmenzentrale besorgen.

    belegt sind die Bibliotheksdateien, die im selben Dokument schon stehen.
    Dasselbe Haus zweimal im Deck faellt auf, also wird darum herumgesucht -
    in der Bibliothek wie im Netz.

    Gibt (Pfad, Herkunft) oder (None, Grund). Der Grund unterscheidet die
    ehrliche Fehlanzeige von einer stummen Quelle - nur das erste heisst
    'gibt es nicht', das zweite heisst 'nochmal laufen lassen'.

    Trist wirkende Motive (wirkt_trist) sind Notnagel, nicht Erstwahl: Erst
    kommt ein freundliches Bibliotheksbild, dann ein freundlicher Netzfund,
    dann das beste triste Motiv - mit Warnung in der Herkunft, damit sie in
    der Uebergabe steht.
    """
    TRIST_WARNUNG = (" – Achtung: wirkt trist (grauer Himmel, wenig Farbe). "
                     "Besseres Motiv suchen oder beim Kunden anfragen.")
    trist_reserve: tuple[Path, str] | None = None
    for vorhanden in aus_bibliothek(firma):
        if vorhanden.name in belegt:
            continue
        if datei_trist(vorhanden):
            if trist_reserve is None:
                trist_reserve = (vorhanden, "Bibliothek" + TRIST_WARNUNG)
            continue
        return vorhanden, "Bibliothek"

    # Woher die belegten Bilder stammen: dieselbe Commons-Datei unter neuem
    # Dateinamen ergaebe wieder dasselbe Motiv.
    register = nachweis_lesen()
    gezeigt = {register[d].get("datei") for d in belegt if d in register}

    name = slugs(firma)[-1] or slugify(firma)
    verworfen, stoerungen = [], []
    netz_reserve: tuple[bytes, dict] | None = None
    for quelle in QUELLEN:
        try:
            funde = quelle(firma)
        except Exception as fehler:
            stoerungen.append(f"{quelle.__name__}: {fehler}")
            continue
        passend = [f for f in funde
                   if brauchbar(f["titel"], firma) and f["titel"] not in gezeigt]
        for fund in sorted(passend, key=rang):
            if fund["breite"] < MIN_BREITE:
                verworfen.append(f"{fund['titel']} ({fund['breite']}px zu schmal)")
                continue
            if fund["breite"] / fund["hoehe"] < MIN_VERHAELTNIS:
                verworfen.append(f"{fund['titel']} (Hochformat)")
                continue
            try:
                daten = laden(fund["url"])
            except Exception as fehler:
                verworfen.append(f"{fund['titel']} (nicht verwertbar: {fehler})")
                continue
            if bytes_trist(daten):
                if netz_reserve is None:
                    netz_reserve = (daten, fund)
                verworfen.append(f"{fund['titel']} (wirkt trist)")
                continue
            try:
                ziel = ablegen(daten, freier_name(name))
            except Exception as fehler:
                verworfen.append(f"{fund['titel']} (nicht verwertbar: {fehler})")
                continue
            nachweis_schreiben(ziel.name, firma, fund)
            return ziel, f"{fund['woher']}: {fund['titel']}"

    # Nichts Freundliches gefunden: lieber ein tristes Haus der richtigen Firma
    # als gar keins - aber mit Warnung, die bis in die Uebergabe traegt.
    if trist_reserve:
        return trist_reserve
    if netz_reserve:
        daten, fund = netz_reserve
        try:
            ziel = ablegen(daten, freier_name(name))
            nachweis_schreiben(ziel.name, firma, fund)
            return ziel, f"{fund['woher']}: {fund['titel']}{TRIST_WARNUNG}"
        except Exception as fehler:
            verworfen.append(f"{fund['titel']} (nicht verwertbar: {fehler})")

    if stoerungen:
        return None, "Quelle stumm — " + "; ".join(stoerungen)
    if verworfen:
        return None, "nichts Brauchbares — verworfen: " + "; ".join(verworfen[:4])
    return None, "kein Treffer mit Firmenname und Gebäude im Dateinamen"


# ── Selbsttest ───────────────────────────────────────────────────────────

# Echte Fundstuecke von Commons, die guten wie die Fehlgriffe. Jede Zeile hat
# einmal Geld gekostet: Die vier oberen stehen so in der Bibliothek, die unteren
# sind durchgerutscht, bevor die Schranke da war. Nach jeder Aenderung an Suche
# oder Pruefung laufen lassen - die Schranke darf weder enger noch weiter werden,
# als sie hier steht.
PRUEFTABELLE = (
    # (Firma, Dateiname, soll durchkommen, warum)
    ("Deutsche Bank", "File:Deutsche Bank tower Frankfurt am Main 2019-09-15 02.jpg",
     True, "Zwillingstuerme Frankfurt, liegt in der Bibliothek"),
    ("Samsung", "File:Samsung headquarters.jpg",
     True, "Suwon, liegt in der Bibliothek"),
    ("Postbank & FYRST",
     "File:2014-07-24 Zentrale Deutsche Postbank AG, Friedrich-Ebert-Allee "
     "114-126, Bonn-Gronau IMG 2172.jpg",
     True, "Bonn, liegt in der Bibliothek — Zweitname hinter dem & stoert nicht"),
    ("Boeing", "File:Chicago - Chicago River - Boeing International Headquarters.jpg",
     True, "Chicago, liegt in der Bibliothek"),
    ("Opel", "File:Russelsheim Adam-Opel-Haus 1.jpg",
     True, "Eigenname: 'Haus' haengt am Firmennamen"),
    ("Opel", "File:RüsselsheimMainMarktstrOpelHauptportalAdamOpel.JPG",
     True, "zusammengeschrieben, Wortgrenzen nur in den Grossbuchstaben"),
    ("Opel, Peugeot und Citroën", "File:Russelsheim Adam-Opel-Haus 2.jpg",
     True, "gesucht wird nach der ersten Firma, nicht nach der ganzen Zeile"),
    ("Citroën", "File:Citroën Deutschland Hauptverwaltung.JPG",
     True, "Hauptverwaltung Köln"),
    ("Deutsche Bahn", "File:Verwaltungsgebäude der Deutschen Bahn in Hamburg.jpg",
     True, "gebeugt — 'der Deutschen Bahn' ist dieselbe Bahn"),
    ("Peugeot", "File:Buildings in Meguro- Peugeot.jpg",
     False, "Autohaus in Tokio — 'buildings' haengt nicht am Firmennamen"),
    ("Citroën", "File:Building in the Parc André Citroën.jpg",
     False, "Gewächshaus im Pariser Park"),
    ("Citroën", "File:Glass Building in the Parc André Citroën.jpg",
     False, "dasselbe Gewächshaus"),
    ("Deutsche Bank", "File:Hauptverwaltung Deutsche Bundesbank Stuttgart 01.jpg",
     False, "andere Bank — 'deutsche' und 'bank' stehen drin, 'deutschebank' nicht"),
    ("Opel", "File:RüsselsheimMainMarktstrWeisenauerStrOpelwerk.JPG",
     False, "Werk, nicht Zentrale — kein Gebäudewort am Namen"),
    ("Opel", "File:Opel Zafira Tourer 2.0 CDTI Innovation (C) – Frontansicht, "
     "23. Mai 2013, Heiligenhaus.jpg",
     False, "Auto vor Heiligenhaus — 'haus' steckt nur im Ortsnamen"),
    ("Arvato Systems", "File:Arvato Zentrale An der Autobahn Gütersloh.jpg",
     False, "Zentrale des Mutterkonzerns, nicht die von Arvato Systems"),
    ("Deutsche Bank", "File:Deutsche Bank Logo.svg",
     False, "Marke, kein Haus — und kein Bildformat"),
    ("Deutsche Bank", "File:AI generated image of Deutsche Bank headquarters.jpg",
     False, "KI-Bild, ehrlich beschriftet — Leerzeichen-Schreibweise"),
    ("Deutsche Bank", "File:Deutsche Bank Zentrale (KI generiert).jpg",
     False, "KI-Bild, deutsche Beschriftung"),
    ("Deutsche Bank", "File:Deutsche Bank headquarters stable diffusion.jpg",
     False, "KI-Bild, Werkzeugname im Titel"),
    ("Opel", "File:Opel Hauptverwaltung 3D rendering.jpg",
     False, "Rendering, kein Foto"),
)


def selbsttest() -> int:
    """Die Pruefliste durchrechnen. Ohne Netz, damit sie bei jeder Aenderung
    laufen kann."""
    fehler = 0
    for firma, titel, soll, warum in PRUEFTABELLE:
        ist = brauchbar(titel, firma)
        if ist != soll:
            fehler += 1
            print(f"FEHLER  {firma}: {titel}\n        erwartet "
                  f"{'ja' if soll else 'nein'}, ist {'ja' if ist else 'nein'} "
                  f"— {warum}")
    zahl = len(PRUEFTABELLE)
    if fehler:
        print(f"\n{fehler} von {zahl} Faellen falsch beurteilt. Nicht ausliefern.")
    else:
        print(f"Prüftabelle: {zahl} von {zahl} richtig beurteilt.")
    return 1 if fehler else 0


# ── Bericht ──────────────────────────────────────────────────────────────

def summary(projekt: dict) -> dict | None:
    """Der Summary-Knoten, wenn er einer ist. Alte Dateien fuehren dort
    manchmal blossen Text - der bekommt kein Bild, aber auch keinen Absturz."""
    knoten = projekt.get("summary")
    if knoten is None:
        knoten = {}
        projekt["summary"] = knoten
    return knoten if isinstance(knoten, dict) else None


def material(pfad: Path, quelle: Path) -> str:
    """Kopie neben die portfolio.json legen. Der Bestand bleibt in der
    Bibliothek, aber die JSON soll ohne absolute Pfade weiterreichbar sein."""
    ordner = pfad.parent / "material"
    ordner.mkdir(parents=True, exist_ok=True)
    ziel = ordner / f"hq-{quelle.name}"
    ziel.write_bytes(quelle.read_bytes())
    return f"material/{ziel.name}"


def main() -> None:
    if len(sys.argv) < 2:
        raise SystemExit(__doc__)
    arg = sys.argv[1]
    setzen = "--setzen" in sys.argv
    zeigen = "--quelle" in sys.argv or "--quellen" in sys.argv
    zweites = "--zweites" in sys.argv

    if arg in ("--selbsttest", "--test"):
        raise SystemExit(selbsttest())

    if not arg.lower().endswith(".json"):
        # --zweites: alles, was zu dieser Firma schon liegt, gilt als belegt -
        # dann bleibt nur ein anderes Motiv uebrig.
        belegt = frozenset(p.name for p in aus_bibliothek(arg)) if zweites \
            else frozenset()
        ziel, woher = hq_bild(arg, belegt)
        if not ziel and zweites:
            raise SystemExit(
                f"Kein zweites Motiv der Zentrale von '{arg}' gefunden ({woher}).\n"
                "Beide Summary-Seiten zeigen sonst dasselbe Haus."
            )
        if not ziel:
            raise SystemExit(
                f"Kein Bild der Zentrale von '{arg}' gefunden ({woher}).\n"
                "Lieber eine Lücke als ein fremdes Haus: Bild beim Kunden "
                "anfragen oder von dessen Presseseite laden und als "
                '"summary": {"bild": "…"} eintragen.'
            )
        print(f"{ziel}  ({woher})")
        if zeigen:
            print(json.dumps(nachweis_lesen().get(ziel.name, {}),
                             ensure_ascii=False, indent=2))
        return

    pfad = Path(arg)
    daten = json.loads(pfad.read_text(encoding="utf-8"))
    aus_lib, neu, offen, uebersprungen, benutzt = [], [], [], [], []
    doppelt, trist = [], []
    # Was in diesem Dokument schon steht. Zwei Projekte beim selben Kunden
    # sollen zwei Motive zeigen - im Deck stehen sie oft nur Seiten auseinander.
    belegt: set[str] = set()

    for projekt in daten.get("projekte", []):
        firma = projekt.get("kunde")
        if not firma:
            continue
        knoten = summary(projekt)
        if knoten is None:
            uebersprungen.append(f"{firma} (summary ist kein Objekt)")
            continue
        if knoten.get("bild"):
            # Schon gesetzt - aber fuer den Nachweis mitzaehlen. Sonst steht der
            # Bildnachweis genau dann leer da, wenn er gebraucht wird: nach dem
            # Lauf mit --setzen, bei der Uebergabe.
            name = Path(str(knoten["bild"])).name
            if name.startswith("hq-"):
                if name[3:] in belegt:
                    doppelt.append(f"{firma} -> {name} (steht schon auf einer "
                                   "anderen Seite; Eintrag löschen und erneut "
                                   "laufen lassen holt ein zweites Motiv)")
                benutzt.append(name[3:])
                belegt.add(name[3:])
            # Auch gesetzte Bilder auf Tristheit ansehen - das triste Motiv im
            # Freia-Deck stand laengst in der JSON, als es auffiel.
            for kandidat in (Path(str(knoten["bild"])),
                             pfad.parent / str(knoten["bild"])):
                if kandidat.is_file():
                    if datei_trist(kandidat):
                        trist.append(f"{firma} -> {knoten['bild']}")
                    break
            continue
        print(f"{firma} …")
        ziel, woher = hq_bild(firma, frozenset(belegt))
        if not ziel and belegt:
            # Kein zweites Motiv. Eine leere Seite waere schlimmer als ein
            # zweites Mal dasselbe Haus - das ist wenigstens die richtige Firma.
            ziel, woher = hq_bild(firma)
            if ziel:
                doppelt.append(f"{firma} -> {ziel.name} (kein zweites Motiv "
                               "gefunden, Bild steht jetzt zweimal im Deck)")
        if not ziel:
            offen.append(f"{firma} — {woher}")
            continue
        eintrag = material(pfad, ziel) if setzen else str(ziel)
        if setzen:
            knoten["bild"] = eintrag
        benutzt.append(ziel.name)
        belegt.add(ziel.name)
        (aus_lib if woher == "Bibliothek" else neu).append(
            f"{firma} -> {eintrag} ({woher})")

    if setzen:
        pfad.write_text(json.dumps(daten, ensure_ascii=False, indent=2) + "\n",
                        encoding="utf-8")

    print()
    if aus_lib:
        print("Aus der Bibliothek:")
        for z in aus_lib:
            print("  " + z)
    if neu:
        print("Neu gefunden (bitte ansehen — steht da wirklich diese Firma?):")
        for z in neu:
            print("  " + z)
    if doppelt:
        print("Zweimal dasselbe Haus — beim Kunden ein zweites Motiv anfragen:")
        for z in doppelt:
            print("  " + z)
    if trist:
        print("Wirkt trist (grauer Himmel, wenig Farbe) — besseres Motiv suchen")
        print("oder beim Kunden anfragen; die Referenz zeigt Sonne und Himmel:")
        for z in trist:
            print("  " + z)
    if uebersprungen:
        print("Übersprungen:")
        for z in uebersprungen:
            print("  " + z)
    if offen:
        print("Offen — kein Foto gefunden. Kein fremdes Gebäude eintragen; statt-")
        print("dessen ein KI-Bild generieren (Kaskade in SKILL.md, Schritt 5:")
        print("fotorealistisch, ohne Firmenschriftzug, Datei hq-<firma>-ki.jpg,")
        print("in der Übergabe als KI-generiert kennzeichnen):")
        for z in offen:
            print("  " + z)
    if not setzen and (aus_lib or neu):
        print("\nNoch nichts eingetragen. Mit --setzen in die portfolio.json schreiben.")
    if zeigen:
        register = nachweis_lesen()
        print("\nBildnachweis (gehört in die Übergabe):")
        for datei in sorted(set(benutzt)):
            eintrag = register.get(datei)
            if not eintrag:                    # von Hand abgelegt, ohne Nachweis
                print(f"  {datei}: Herkunft unbekannt — vor der Übergabe klären")
                continue
            print(f"  {datei}: {eintrag['firma']}, {eintrag['datei']}, "
                  f"{eintrag['lizenz']}, {eintrag['urheber'] or 'ohne Urheberangabe'}")
    print(f"\nBibliothek: {hq_bibliothek()}")


if __name__ == "__main__":
    main()
