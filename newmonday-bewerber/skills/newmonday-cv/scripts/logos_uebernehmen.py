#!/usr/bin/env python3
"""Uebernimmt neue Logos aus ~/.newmonday/logos/ ins Repo - fuer Pfleger.

    python3 scripts/logos_uebernehmen.py                       # nur anzeigen
    python3 scripts/logos_uebernehmen.py ~/NW-Claude-Skills    # nur anzeigen
    python3 scripts/logos_uebernehmen.py ~/NW-Claude-Skills --uebernehmen

Neue Funde landen nie im Skill-Ordner (siehe logo_lib.py), sondern in
~/.newmonday/logos/. Damit sie jeder bekommt, gehoeren sie in den Grundstock
im Repo: newmonday-bewerber/skills/newmonday-cv/assets/logos/. Ohne Pfad wird
der Grundstock genommen, neben dem dieses Skript liegt - aber nur, wenn er in
einem Git-Checkout liegt (Symlink-Installation), nie im Plugin-Cache.

--uebernehmen verschiebt die Dateien in den Checkout und fuehrt aliase.json
zusammen. Danach liegt jedes Logo nur noch an einer Stelle: bliebe die Kopie in
~/.newmonday/logos/ liegen, verdeckte sie spaetere Verbesserungen im Repo.
Committen und pushen bleibt Handarbeit - der Befehl steht am Ende.
"""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import logo_lib  # noqa: E402

IM_REPO = Path("newmonday-bewerber/skills/newmonday-cv/assets/logos")


def repo_wurzel(ordner: Path) -> Path | None:
    try:
        aus = subprocess.run(["git", "-C", str(ordner), "rev-parse", "--show-toplevel"],
                             capture_output=True, text=True, check=True)
    except (OSError, subprocess.CalledProcessError):
        return None
    return Path(aus.stdout.strip())


def ziel_finden(argument: str | None) -> Path:
    if argument:
        wurzel = repo_wurzel(Path(argument).expanduser())
        if not wurzel:
            raise SystemExit(f"{argument} ist kein Git-Checkout.")
    else:
        wurzel = repo_wurzel(logo_lib.GRUNDSTOCK.resolve())
        if not wurzel:
            raise SystemExit(
                "Dieser Skill liegt in keinem Git-Checkout (Plugin-Installation).\n"
                "Pfad zum Repo angeben: python3 scripts/logos_uebernehmen.py "
                "~/NW-Claude-Skills --uebernehmen")
    ziel = wurzel / IM_REPO
    if not ziel.is_dir():
        raise SystemExit(f"{ziel} fehlt - ist das der Checkout von NW-Claude-Skills?")
    return ziel


def aliase_zusammenfuehren(quelle: Path, ziel: Path) -> list[str]:
    neu = json.loads(quelle.read_text(encoding="utf-8"))
    alt = json.loads(ziel.read_text(encoding="utf-8")) if ziel.is_file() else {}
    geaendert = [k for k, v in neu.items() if alt.get(k) != v]
    alt.update(neu)
    ziel.write_text(json.dumps(alt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    quelle.unlink()
    return geaendert


def main() -> None:
    argumente = [a for a in sys.argv[1:] if not a.startswith("--")]
    uebernehmen = "--uebernehmen" in sys.argv
    offen = logo_lib.neue()
    if not offen:
        print(f"Nichts zu uebernehmen: {logo_lib.bibliothek()} enthaelt nichts Neues.")
        return
    ziel = ziel_finden(argumente[0] if argumente else None)
    if ziel.resolve() == logo_lib.bibliothek().resolve():
        raise SystemExit("Quelle und Ziel sind derselbe Ordner.")

    print(f"Neu in {logo_lib.bibliothek()}:")
    for p in offen:
        art = "ersetzt" if (ziel / p.name).exists() else "neu"
        print(f"  {p.name} ({art})")
    if not uebernehmen:
        print(f"\nMit --uebernehmen werden sie nach {ziel} verschoben.")
        return

    for p in offen:
        if p.name == "aliase.json":
            schluessel = aliase_zusammenfuehren(p, ziel / "aliase.json")
            print(f"aliase.json: {len(schluessel)} Eintraege uebernommen")
        else:
            shutil.move(str(p), str(ziel / p.name))
    for p in logo_lib.bibliothek().iterdir():   # Reste, die es im Repo schon gibt
        if p.is_file() and (ziel / p.name).is_file() \
                and p.read_bytes() == (ziel / p.name).read_bytes():
            p.unlink()
    wurzel = repo_wurzel(ziel)
    print(f"\nVerschoben nach {ziel}. Jetzt ansehen, dann committen:")
    print(f'  cd {wurzel} && git add {IM_REPO} && git commit -m "Logos ergaenzt" && git push')


if __name__ == "__main__":
    main()
