"""Mini-Template-Engine fuer das Audit-Deck (mustache-lite, keine Dependencies).

Bewusst winzig: Der Skill verspricht "kein Build-Schritt, keine npm-Abhaengigkeiten".
Diese Datei ist die einzige Logik zwischen deck.json und index.html.

Syntax
------
  {{key}}              Wert einsetzen. ROH, nicht escaped -- Inhalte duerfen
                       Inline-HTML enthalten (<b>, <code>, <br>), das ist Absicht.
                       Fehlt der Key, wirft der Renderer (kein stilles Loch im Deck).
  {{key?}}             Wie {{key}}, aber optional: fehlt der Key -> leerer String.
  {{a.b}}              Verschachtelt.
  {{#liste}}...{{/liste}}
                       Schleife. Item ist ein dict -> dessen Keys gelten im Block.
                       Item ist ein String -> im Block als {{.}} verfuegbar.
                       Ist der Wert truthy aber keine Liste -> Block einmal rendern
                       (Bedingung).
  {{^liste}}...{{/liste}}
                       Invers: rendert, wenn Wert fehlt/leer/false.
  {{@index}}           1-basierter Zaehler innerhalb einer Schleife.
  {{@index2}}          Wie @index, aber zweistellig ("01", "02") -- fuer Kicker
                       wie "Erkenntnis 03".

Aufbau: parse() -> AST, dann render_ast(). Zwei getrennte Schritte, damit das
Auffinden des Blockendes nichts auswertet (sonst wuerden {{@index}} ausserhalb
ihrer Schleife ausgewertet).
"""

import re

_TOKEN = re.compile(r"\{\{([#^/@]?)([\w.?]+)\}\}")


class TemplateError(Exception):
    pass


# ---------------------------------------------------------------- parse
def parse(tpl):
    """Template-String -> AST (Liste von Knoten)."""
    pos = 0
    stack = [("<root>", [])]

    while True:
        m = _TOKEN.search(tpl, pos)
        if not m:
            if tpl[pos:]:
                stack[-1][1].append(("text", tpl[pos:]))
            break

        if tpl[pos:m.start()]:
            stack[-1][1].append(("text", tpl[pos:m.start()]))
        sigil, key = m.group(1), m.group(2)
        pos = m.end()

        if sigil in ("#", "^"):
            stack.append((key, [], sigil))
        elif sigil == "/":
            if len(stack) == 1:
                raise TemplateError(f"{{{{/{key}}}}} ohne oeffnenden Block")
            name, kids, sig = stack.pop()
            if name != key:
                raise TemplateError(f"{{{{/{key}}}}} passt nicht zu {{{{{sig}{name}}}}}")
            stack[-1][1].append(("section", key, sig, kids))
        elif sigil == "@":
            stack[-1][1].append(("counter", key))
        else:
            stack[-1][1].append(("var", key))

    if len(stack) != 1:
        raise TemplateError(f"{{{{#{stack[-1][0]}}}}} wurde nie geschlossen")
    return stack[0][1]


# --------------------------------------------------------------- lookup
def _lookup(ctx_stack, key):
    optional = key.endswith("?")
    if optional:
        key = key[:-1]

    # "." = das aktuelle Schleifen-Item selbst (Liste aus Strings).
    # Muss vor dem split(".") stehen, sonst zerfaellt es zu ["", ""].
    parts = ["."] if key == "." else key.split(".")

    for ctx in reversed(ctx_stack):
        if not isinstance(ctx, dict):
            continue
        cur, ok = ctx, True
        for part in parts:
            if isinstance(cur, dict) and part in cur:
                cur = cur[part]
            else:
                ok = False
                break
        if ok:
            return cur, True

    if optional:
        return "", True
    return None, False


# --------------------------------------------------------------- render
def render_ast(nodes, ctx_stack):
    buf = []
    for node in nodes:
        kind = node[0]

        if kind == "text":
            buf.append(node[1])

        elif kind == "var":
            val, found = _lookup(ctx_stack, node[1])
            if not found:
                raise TemplateError(
                    f"{{{{{node[1]}}}}} fehlt im deck.json "
                    f"(optionale Felder als {{{{{node[1]}?}}}} schreiben)"
                )
            buf.append("" if val is None else str(val))

        elif kind == "counter":
            val, found = _lookup(ctx_stack, "@" + node[1])
            if not found:
                raise TemplateError(f"{{{{@{node[1]}}}}} nur innerhalb einer Schleife")
            buf.append(str(val))

        elif kind == "section":
            _, key, sigil, kids = node
            val, found = _lookup(ctx_stack, key)
            if not found:
                val = None
            truthy = bool(val)

            if sigil == "^":
                if not truthy:
                    buf.append(render_ast(kids, ctx_stack))
            elif truthy:
                items = val if isinstance(val, list) else [val]
                for n, item in enumerate(items, 1):
                    frame = dict(item) if isinstance(item, dict) else {".": item}
                    frame["@index"] = n
                    frame["@index2"] = f"{n:02d}"
                    buf.append(render_ast(kids, ctx_stack + [frame]))

    return "".join(buf)


def render(template, context):
    """Rendert template (str) mit context (dict) -> str."""
    return render_ast(parse(template), [context])
