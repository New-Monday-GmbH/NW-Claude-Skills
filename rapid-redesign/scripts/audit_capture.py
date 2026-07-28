#!/usr/bin/env python3
"""
audit_capture.py — Rohmaterial-Erfassung für UX/UI-Audits via Playwright.

Zwei Modi:
  survey  Erfasst pro Viewport (Desktop + Mobile) Full-Page- & Fold-Screenshots
          und ein survey.json mit Struktur-, Accessibility- und Kontrastdaten.
  shot    Erzeugt einen fokussierten (optional hervorgehobenen) Screenshot eines
          einzelnen Elements/Ausschnitts — ein Bild pro Finding.

Beispiele:
  python audit_capture.py survey "https://example.com" --out audits/example/survey
  python audit_capture.py shot "https://example.com" --selector "header nav" \
         --viewport desktop --highlight --out audits/example/findings/f01.png
  python audit_capture.py shot "https://example.com" --region "0,0,1440,320" \
         --out audits/example/findings/f02.png
"""
import argparse
import json
import sys
from pathlib import Path

try:
    from playwright.sync_api import sync_playwright
except ImportError:
    sys.exit("Playwright fehlt. Erst 'bash scripts/setup.sh' ausführen und "
             "scripts/.venv/bin/python verwenden.")

DESKTOP = {"width": 1440, "height": 900}
MOBILE = {"width": 390, "height": 844}

# Nicht-HTML-Ziele, die beim Crawl übersprungen werden.
SKIP_EXT = (".pdf", ".jpg", ".jpeg", ".png", ".webp", ".svg", ".zip",
            ".mp4", ".gif", ".doc", ".docx", ".xml", ".css", ".js",
            ".ico", ".woff", ".woff2", ".ttf", ".mp3", ".avi", ".json",
            ".kml", ".txt", ".rss", ".atom", ".csv")

# Sammelt strukturierte Audit-Daten im Browser-Kontext.
# Kontrast wird direkt hier berechnet (effektiver Hintergrund per Ancestor-Walk).
COLLECT_JS = r"""
() => {
  const cssPath = (el) => {
    if (!(el instanceof Element)) return '';
    if (el.id) return '#' + CSS.escape(el.id);
    const parts = [];
    let node = el;
    let depth = 0;
    while (node && node.nodeType === 1 && depth < 5) {
      let sel = node.nodeName.toLowerCase();
      if (node.id) { parts.unshift('#' + CSS.escape(node.id)); break; }
      const parent = node.parentNode;
      if (parent) {
        const sameTag = Array.from(parent.children).filter(c => c.nodeName === node.nodeName);
        if (sameTag.length > 1) sel += ':nth-of-type(' + (sameTag.indexOf(node) + 1) + ')';
      }
      parts.unshift(sel);
      node = node.parentElement;
      depth++;
    }
    return parts.join(' > ');
  };

  const parseRGB = (s) => {
    const m = (s || '').match(/rgba?\(([^)]+)\)/);
    if (!m) return null;
    const p = m[1].split(',').map(x => parseFloat(x.trim()));
    return { r: p[0], g: p[1], b: p[2], a: p.length > 3 ? p[3] : 1 };
  };
  // Liefert die effektive Hintergrundfarbe – ODER {unknown:true}, wenn ein
  // Vorfahr einen background-image/Gradient trägt. Dann ist die Farbe nicht
  // messbar und wir überspringen die Kontrastprüfung, statt falsch "1.0" zu melden.
  const effectiveBg = (el) => {
    let node = el;
    while (node && node.nodeType === 1) {
      const st = getComputedStyle(node);
      if (st.backgroundImage && st.backgroundImage !== 'none') return { unknown: true };
      const c = parseRGB(st.backgroundColor);
      if (c && c.a > 0.95) return c;  // deckende Fläche gefunden
      node = node.parentElement;
    }
    return { r: 255, g: 255, b: 255, a: 1 };
  };
  const lum = (c) => {
    const f = (v) => { v /= 255; return v <= 0.03928 ? v / 12.92 : Math.pow((v + 0.055) / 1.055, 2.4); };
    return 0.2126 * f(c.r) + 0.7152 * f(c.g) + 0.0722 * f(c.b);
  };
  const ratio = (a, b) => {
    const l1 = lum(a), l2 = lum(b);
    return (Math.max(l1, l2) + 0.05) / (Math.min(l1, l2) + 0.05);
  };
  const visible = (el) => {
    const r = el.getBoundingClientRect();
    const st = getComputedStyle(el);
    return r.width > 1 && r.height > 1 && st.visibility !== 'hidden' && st.display !== 'none' && parseFloat(st.opacity) > 0.05;
  };

  // Headings
  const headings = Array.from(document.querySelectorAll('h1,h2,h3,h4,h5,h6'))
    .filter(visible)
    .map(h => ({ level: +h.nodeName[1], text: (h.innerText || '').trim().slice(0, 120) }));

  // Bilder ohne Alt
  const imagesMissingAlt = Array.from(document.querySelectorAll('img'))
    .filter(visible)
    .filter(img => !img.getAttribute('alt') || img.getAttribute('alt').trim() === '')
    .slice(0, 600)
    .map(img => ({ src: (img.currentSrc || img.src || '').slice(0, 200), selector: cssPath(img) }));

  // Formularfelder ohne zugängliches Label
  const labelFor = {};
  document.querySelectorAll('label[for]').forEach(l => labelFor[l.getAttribute('for')] = true);
  const formFieldsNoLabel = Array.from(document.querySelectorAll('input,select,textarea'))
    .filter(visible)
    .filter(el => !['hidden', 'submit', 'button'].includes((el.type || '').toLowerCase()))
    .filter(el => {
      const hasLabel = (el.id && labelFor[el.id]) || el.getAttribute('aria-label') ||
        el.getAttribute('aria-labelledby') || el.closest('label');
      return !hasLabel;
    })
    .slice(0, 600)
    .map(el => ({ selector: cssPath(el), type: el.type || el.nodeName.toLowerCase(),
                  placeholder: el.getAttribute('placeholder') || null }));

  // Kontrast-Kandidaten (Text unter WCAG-Schwelle)
  const contrastIssues = [];
  const textEls = Array.from(document.querySelectorAll('body *')).filter(el => {
    if (!visible(el)) return false;
    const direct = Array.from(el.childNodes).some(n => n.nodeType === 3 && n.textContent.trim().length > 0);
    return direct;
  });
  for (const el of textEls) {
    const st = getComputedStyle(el);
    const fg = parseRGB(st.color);
    if (!fg) continue;
    const bg = effectiveBg(el);
    if (bg.unknown) continue;  // Hintergrund nicht messbar (Bild/Gradient) → überspringen
    const size = parseFloat(st.fontSize);
    const weight = parseInt(st.fontWeight) || 400;
    const large = size >= 24 || (size >= 18.66 && weight >= 700);
    const threshold = large ? 3.0 : 4.5;
    const cr = ratio(fg, bg);
    if (cr < threshold) {
      contrastIssues.push({
        selector: cssPath(el),
        text: (el.innerText || '').trim().slice(0, 80),
        ratio: Math.round(cr * 100) / 100,
        required: threshold,
        fontSizePx: Math.round(size),
        color: st.color,
        background: 'rgb(' + bg.r + ',' + bg.g + ',' + bg.b + ')'
      });
    }
    if (contrastIssues.length >= 600) break;
  }

  // Zu kleine Tap-Targets (v. a. Mobile relevant)
  const smallTargets = Array.from(document.querySelectorAll('a,button,input,select,[role=button],[onclick]'))
    .filter(visible)
    .map(el => ({ el, r: el.getBoundingClientRect() }))
    .filter(o => Math.min(o.r.width, o.r.height) < 44 && o.r.width > 0)
    .slice(0, 600)
    .map(o => ({ selector: cssPath(o.el), text: (o.el.innerText || o.el.value || '').trim().slice(0, 40),
                 width: Math.round(o.r.width), height: Math.round(o.r.height) }));

  // CTA-Labels (Buttons + button-artige Links) – Grundlage für die Copy-/Conversion-Analyse
  const ctaLabels = [];
  const seenCta = new Set();
  document.querySelectorAll('button,[role=button],a').forEach(el => {
    if (!visible(el)) return;
    const st = getComputedStyle(el);
    const bg = parseRGB(st.backgroundColor);
    const looksButton = el.tagName === 'BUTTON' || el.getAttribute('role') === 'button'
      || (bg && bg.a > 0.05) || st.borderStyle !== 'none';
    const txt = (el.innerText || '').trim().replace(/\s+/g, ' ');
    if (looksButton && txt && txt.length <= 40 && !seenCta.has(txt.toLowerCase())) {
      seenCta.add(txt.toLowerCase());
      ctaLabels.push(txt);
    }
  });

  // Fließtext-Blöcke (Absätze) – für die inhaltliche Copy-Bewertung
  const paragraphs = Array.from(document.querySelectorAll('p'))
    .filter(visible)
    .map(p => (p.innerText || '').trim().replace(/\s+/g, ' '))
    .filter(t => t.length >= 40)
    .slice(0, 25);

  // Markenfarbe der Seite: dominante gesättigte Akzentfarbe – Grundlage für die
  // Cover-Sektion der Ergebnis-Website (die immer in der Kundenfarbe erscheint).
  const _hex = (c) => '#' + [c.r, c.g, c.b].map(v => Math.max(0, Math.min(255, Math.round(v))).toString(16).padStart(2, '0')).join('');
  const _hsl = (c) => { const r=c.r/255,g=c.g/255,b=c.b/255,mx=Math.max(r,g,b),mn=Math.min(r,g,b),l=(mx+mn)/2,d=mx-mn; let h=0,s=0; if(d){s=l>0.5?d/(2-mx-mn):d/(mx+mn); h=mx===r?((g-b)/d+(g<b?6:0)):mx===g?((b-r)/d+2):((r-g)/d+4); h/=6;} return {h:h*360,s,l}; };
  const _brandy = (c) => { if(!c||c.a<0.5) return false; const s=_hsl(c); return s.s>0.18 && s.l>0.12 && s.l<0.9; };  // gesättigt, nicht weiß/schwarz/grau
  const _cssColor = (val) => { if(!val) return null; const p=document.createElement('span'); p.style.color=val; if(!p.style.color) return null; document.body.appendChild(p); const c=parseRGB(getComputedStyle(p).color); p.remove(); return c; };
  const brandScores = {};
  const _add = (c, wt) => { if(!_brandy(c)) return; const k=_hex(c); brandScores[k]=(brandScores[k]||0)+wt; };
  const _tc = document.querySelector('meta[name=theme-color]');
  if (_tc) _add(_cssColor(_tc.getAttribute('content')), 8);  // theme-color = starkes Signal
  const _rootStyle = getComputedStyle(document.documentElement);
  ['--color-primary','--primary','--primary-color','--brand','--brand-color','--brand-primary','--color-brand','--accent','--accent-color','--color-accent','--bs-primary','--ion-color-primary','--wp--preset--color--primary'].forEach(n => { const v=_rootStyle.getPropertyValue(n).trim(); if(v) _add(_cssColor(v), 6); });
  document.querySelectorAll('button,[role=button],a,.btn,.button').forEach(el => {
    if (!visible(el)) return;
    const bg = parseRGB(getComputedStyle(el).backgroundColor);
    if (!bg) return;
    const r = el.getBoundingClientRect();
    _add(bg, Math.min(6, (r.width * r.height) / 4000));  // größere CTAs zählen mehr
  });
  ['header','nav','[role=banner]'].forEach(sel => { const el=document.querySelector(sel); if(el&&visible(el)) _add(parseRGB(getComputedStyle(el).backgroundColor), 3); });
  const brandRanked = Object.entries(brandScores).sort((a,b)=>b[1]-a[1]).map(([hex,score])=>({hex, score: Math.round(score*10)/10}));

  const viewportMeta = document.querySelector('meta[name=viewport]');
  const desc = document.querySelector('meta[name=description]');

  return {
    title: document.title || null,
    lang: document.documentElement.getAttribute('lang') || null,
    metaDescription: desc ? desc.getAttribute('content') : null,
    viewportMeta: viewportMeta ? viewportMeta.getAttribute('content') : null,
    h1Count: document.querySelectorAll('h1').length,
    headings,
    ctaLabels: ctaLabels.slice(0, 30),
    paragraphs,
    imagesMissingAlt,
    formFieldsNoLabel,
    contrastIssues,
    smallTargets,
    brandColor: brandRanked.length ? brandRanked[0].hex : null,
    brandCandidates: brandRanked.slice(0, 6),
    linkCount: document.querySelectorAll('a').length,
    buttonCount: document.querySelectorAll('button,[role=button]').length,
  };
}
"""

# Sammelt interne Links (gleiche Domain) für den Site-Crawl.
LINKS_JS = r"""
() => {
  const out = [];
  document.querySelectorAll('a[href]').forEach(a => {
    const href = a.href;
    const text = (a.innerText || '').trim().replace(/\s+/g, ' ').slice(0, 60);
    if (href) out.push({ href, text });
  });
  return out;
}
"""


def _new_page(browser, viewport, is_mobile):
    ctx = browser.new_context(
        viewport=viewport,
        device_scale_factor=2,
        is_mobile=is_mobile,
        user_agent=(
            "Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15 "
            "(KHTML, like Gecko) Version/16.0 Mobile/15E148 Safari/604.1"
        ) if is_mobile else None,
    )
    return ctx, ctx.new_page()


def _autoscroll(page):
    """Scrollt einmal komplett durch die Seite und zurück. Notwendig, weil viele
    Seiten (Elementor, AOS, Framer) Inhalte per Scroll-Animation einblenden oder
    Bilder lazy laden – ohne Scrollen bleibt der Full-Page-Screenshot leer."""
    page.evaluate(
        """async () => {
            await new Promise((resolve) => {
                let y = 0;
                const step = Math.max(300, Math.floor(window.innerHeight * 0.85));
                const timer = setInterval(() => {
                    window.scrollTo(0, y);
                    y += step;
                    if (y >= document.body.scrollHeight) { clearInterval(timer); resolve(); }
                }, 120);
            });
        }"""
    )
    page.wait_for_timeout(600)
    page.evaluate("window.scrollTo(0, 0)")
    page.wait_for_timeout(400)


def _goto(page, url, console_errors, scroll=False):
    page.on("console", lambda m: console_errors.append(m.text) if m.type in ("error", "warning") else None)
    page.on("pageerror", lambda e: console_errors.append(str(e)))
    page.goto(url, wait_until="load", timeout=45000)
    try:
        page.wait_for_load_state("networkidle", timeout=8000)
    except Exception:
        pass
    page.wait_for_timeout(1200)  # Lazy-Content nachladen lassen
    if scroll:
        _autoscroll(page)


def survey(url, out_dir):
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    result = {"url": url, "viewports": {}}
    with sync_playwright() as p:
        browser = p.chromium.launch()
        for name, vp, is_mobile in [("desktop", DESKTOP, False), ("mobile", MOBILE, True)]:
            ctx, page = _new_page(browser, vp, is_mobile)
            console_errors = []
            try:
                _goto(page, url, console_errors)
                page.screenshot(path=str(out / f"{name}-fold.png"))  # Fold vor dem Scrollen
                _autoscroll(page)  # Animationen/Lazy-Content auslösen für Full-Page + Daten
                page.screenshot(path=str(out / f"{name}-full.png"), full_page=True)
                data = page.evaluate(COLLECT_JS)
            except Exception as e:
                data = {"error": str(e)}
            data["consoleErrors"] = console_errors[:30]
            result["viewports"][name] = data
            ctx.close()
        browser.close()
    (out / "survey.json").write_text(json.dumps(result, indent=2, ensure_ascii=False))
    _write_summary(out / "survey.md", result)
    print(f"✓ Survey gespeichert: {out}/survey.json + {out}/*.png")


def _write_summary(path, result):
    d = result["viewports"].get("desktop", {})
    m = result["viewports"].get("mobile", {})
    lines = [f"# Survey: {result['url']}", ""]
    lines.append(f"- Title: {d.get('title')}")
    lines.append(f"- lang: {d.get('lang')} | viewport-meta: {d.get('viewportMeta')}")
    lines.append(f"- H1-Anzahl: {d.get('h1Count')} | Links: {d.get('linkCount')} | Buttons: {d.get('buttonCount')}")
    lines.append(f"- Bilder ohne Alt (Desktop): {len(d.get('imagesMissingAlt', []))}")
    lines.append(f"- Kontrast-Kandidaten (Desktop): {len(d.get('contrastIssues', []))}")
    lines.append(f"- Formularfelder ohne Label (Desktop): {len(d.get('formFieldsNoLabel', []))}")
    lines.append(f"- Zu kleine Tap-Targets (Mobile): {len(m.get('smallTargets', []))}")
    lines.append(f"- CTA-Labels (Desktop): {len(d.get('ctaLabels', []))}")
    lines.append(f"- Markenfarbe (erkannt): {d.get('brandColor')} | Kandidaten: {', '.join(c.get('hex','') for c in d.get('brandCandidates', []))}")
    lines.append(f"- Konsolenfehler (Desktop): {len(d.get('consoleErrors', []))}")
    lines.append("\nVollständige Daten in `survey.json`. Screenshots: `*-fold.png`, `*-full.png`.")
    path.write_text("\n".join(lines))


def _norm(root, path):
    return root + ((path or "/").rstrip("/") or "/")


def _fetch_sitemap_urls(ctx, root, netloc):
    """Liest /sitemap.xml (inkl. Sitemap-Index, eine Ebene tief) und aus robots.txt
    referenzierte Sitemaps aus. Liefert interne HTML-URLs. Sitemaps decken die
    *ganze* Website ab – deshalb die primäre Quelle für einen vollständigen Audit."""
    import re
    from urllib.parse import urlparse
    urls = set()
    candidates = [root + "/sitemap.xml", root + "/sitemap_index.xml", root + "/sitemap-index.xml"]
    try:
        rb = ctx.request.get(root + "/robots.txt", timeout=15000)
        if rb.ok:
            for line in rb.text().splitlines():
                if line.lower().startswith("sitemap:"):
                    candidates.append(line.split(":", 1)[1].strip())
    except Exception:
        pass
    seen_sm, queue = set(), list(dict.fromkeys(candidates))
    while queue and len(seen_sm) < 25:
        sm = queue.pop(0)
        if sm in seen_sm:
            continue
        seen_sm.add(sm)
        try:
            resp = ctx.request.get(sm, timeout=15000)
            if not resp.ok:
                continue
            body = resp.text()
        except Exception:
            continue
        locs = re.findall(r"<loc>\s*([^<\s]+)\s*</loc>", body, re.I)
        if "<sitemapindex" in body.lower():
            for loc in locs:  # verschachtelte Sitemaps auflösen
                if loc not in seen_sm:
                    queue.append(loc)
        else:
            for loc in locs:
                if urlparse(loc).netloc == netloc:
                    urls.add(loc)
    return urls


def crawl(url, out_dir, depth=2, max_pages=120):
    """Entdeckt ALLE internen Seiten (gleiche Domain): zuerst per Sitemap/robots.txt,
    dann per Link-BFS bis `depth`. Grundlage für den site-weiten Audit – standardmäßig
    werden alle gefundenen Seiten auditiert, nicht nur eine Auswahl."""
    from urllib.parse import urlparse
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    base = urlparse(url)
    root = f"{base.scheme}://{base.netloc}"
    netloc = base.netloc
    found = {}  # norm_url -> label

    with sync_playwright() as p:
        browser = p.chromium.launch()
        ctx, page = _new_page(browser, DESKTOP, False)

        # 1) Sitemap / robots.txt – deckt idealerweise die ganze Website ab
        for loc in _fetch_sitemap_urls(ctx, root, netloc):
            u = urlparse(loc)
            if any((u.path or "").lower().endswith(e) for e in SKIP_EXT):
                continue
            found.setdefault(_norm(root, u.path), "")

        # 2) Link-BFS als Ergänzung (findet Seiten ohne Sitemap-Eintrag)
        to_visit, visited, level = [url], set(), 0
        while to_visit and level < depth and len(visited) < max_pages:
            next_level = []
            for vurl in to_visit:
                if vurl in visited or len(visited) >= max_pages:
                    continue
                visited.add(vurl)
                try:
                    _goto(page, vurl, [], scroll=True)  # Scrollen lädt Footer-/Nav-Links
                    links = page.evaluate(LINKS_JS)
                except Exception:
                    links = []
                for l in links:
                    u = urlparse(l.get("href", ""))
                    if u.netloc != netloc or u.scheme not in ("http", "https"):
                        continue
                    if any((u.path or "/").lower().endswith(e) for e in SKIP_EXT):
                        continue
                    n = _norm(root, u.path)
                    if not found.get(n):
                        found[n] = l.get("text", "") or found.get(n, "")
                    if n not in visited and n not in next_level:
                        next_level.append(n)
            to_visit, level = next_level, level + 1

        browser.close()

    pages = [{"url": k, "text": v} for k, v in found.items()]
    pages.sort(key=lambda x: (x["url"].count("/"), len(x["url"])))
    (out / "crawl.json").write_text(json.dumps(
        {"start": url, "root": root, "count": len(pages), "pages": pages},
        indent=2, ensure_ascii=False))
    print(f"✓ {len(pages)} interne Seiten gefunden (Sitemap + Crawl bis Tiefe {depth}) → {out}/crawl.json")
    for pg in pages:
        label = f"   · {pg['text']}" if pg["text"] else ""
        print(f"  {pg['url']}{label}")


def shot(url, out_file, selector=None, region=None, viewport="desktop", highlight=False, fold=False):
    out = Path(out_file)
    out.parent.mkdir(parents=True, exist_ok=True)
    vp, is_mobile = (MOBILE, True) if viewport == "mobile" else (DESKTOP, False)
    with sync_playwright() as p:
        browser = p.chromium.launch()
        ctx, page = _new_page(browser, vp, is_mobile)
        _goto(page, url, [], scroll=True)  # sicherstellen, dass auch tiefere Elemente sichtbar sind
        if selector:
            try:
                el = page.locator(selector).first
                el.scroll_into_view_if_needed(timeout=5000)
                if highlight:
                    # Element rot rahmen + Umgebung abdunkeln und den *Kontext*
                    # (Viewport) aufnehmen – zeigt auf der Slide, WO das Problem sitzt.
                    # Styling direkt am gefundenen Node (funktioniert mit CSS- und
                    # Playwright-Selektoren wie text=, has-text usw.).
                    el.evaluate(
                        "(e) => { e.style.outline='4px solid #E4002B'; e.style.outlineOffset='3px';"
                        "e.style.boxShadow='0 0 0 4000px rgba(0,0,0,0.45)';"
                        "if(getComputedStyle(e).position==='static') e.style.position='relative';"
                        "e.style.zIndex='2147483647'; }"
                    )
                    page.wait_for_timeout(250)
                    page.screenshot(path=str(out))  # Viewport mit Highlight = Kontext
                else:
                    el.screenshot(path=str(out))  # sauberer Element-Ausschnitt
            except Exception as e:
                print(f"⚠ Selektor '{selector}' nicht gefunden ({e}); mache Fold-Screenshot.")
                page.screenshot(path=str(out))
        elif region:
            x, y, w, h = [float(v) for v in region.split(",")]
            page.screenshot(path=str(out), clip={"x": x, "y": y, "width": w, "height": h})
        else:
            page.screenshot(path=str(out), full_page=not fold)
        ctx.close()
        browser.close()
    print(f"✓ Screenshot gespeichert: {out}")


def main():
    ap = argparse.ArgumentParser(description="UX/UI-Audit Capture via Playwright")
    sub = ap.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("survey", help="Rohmaterial über Desktop + Mobile erfassen")
    s.add_argument("url")
    s.add_argument("--out", required=True, help="Zielordner")

    cr = sub.add_parser("crawl", help="ALLE internen Seiten entdecken (Sitemap + Link-BFS)")
    cr.add_argument("url")
    cr.add_argument("--out", required=True, help="Zielordner für crawl.json")
    cr.add_argument("--depth", type=int, default=2, help="Crawl-Tiefe für den Link-BFS (Default 2)")
    cr.add_argument("--max-pages", type=int, default=120, help="Obergrenze besuchter Seiten im BFS")

    sh = sub.add_parser("shot", help="Einzel-Screenshot für ein Finding")
    sh.add_argument("url")
    sh.add_argument("--out", required=True, help="Ziel-PNG")
    sh.add_argument("--selector", help="CSS-Selektor des Elements")
    sh.add_argument("--region", help="Ausschnitt 'x,y,w,h'")
    sh.add_argument("--viewport", choices=["desktop", "mobile"], default="desktop")
    sh.add_argument("--highlight", action="store_true", help="Element rot rahmen + abdunkeln")
    sh.add_argument("--fold", action="store_true", help="Nur sichtbaren Bereich statt Full-Page")

    a = ap.parse_args()
    if a.cmd == "survey":
        survey(a.url, a.out)
    elif a.cmd == "crawl":
        crawl(a.url, a.out, a.depth, a.max_pages)
    else:
        shot(a.url, a.out, a.selector, a.region, a.viewport, a.highlight, a.fold)


if __name__ == "__main__":
    main()
