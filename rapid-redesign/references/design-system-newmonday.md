# Design-System: New Monday (offiziell)

Diese Tokens stammen aus dem **offiziellen New-Monday-Design-System** (Figma `4GSkSOZdYvYsoE44hpK1Bg`, „WIP Design System New Monday", nur lesend genutzt). Sie sind die verbindliche Grundlage für die Audit-Website. **Nicht** die alte rote „Angebot-Präsi"-Palette verwenden — die Markenfarbe von New Monday ist **Teal**, der Akzent **Coral**.

> Ausnahme: Die **erste Sektion (Cover/Hero)** wird in der **Primärfarbe der auditierten Firma** eingefärbt, nicht in New-Monday-Teal (siehe `website-build.md` → „Cover in Kundenfarbe"). Alle übrigen Sektionen nutzen das New-Monday-System unten.

## New Monday – Firmendaten (für Abschluss-Sektion, fest)
- **Anschrift:** New Monday GmbH, Stresemannstraße 23, 10963 Berlin
- **Web/Mail/Tel:** newmonday.com · hello@newmonday.co · +49 030 62933131
- **Social:** LinkedIn · Instagram · Dribbble
- **Tagline:** „Dein UX-Partner für smarte Unternehmenssoftware"
- **Positionierung (Über-uns-Slide):** seit 2018 spezialisiert auf UX-Design für Unternehmenssoftware, führende Agentur in Berlin, B2B-Fokus · Auszeichnung: „UX Design Awards – nominated" / „Beste UX Design Agentur".

### UX-Design-Awards-Siegel (Inline-SVG, für den Über-uns-Slide)
Schwarzes Siegel statt Text-Badge:
```svg
<svg viewBox="0 0 168 196" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="UX Design Awards – nominated">
  <rect width="168" height="196" rx="10" fill="#111"/>
  <text x="50" y="88" font-family="Rethink Sans,sans-serif" font-weight="800" font-size="66" fill="#fff" text-anchor="middle">U</text>
  <polygon points="92,42 132,42 112,68" fill="#fff"/>
  <polygon points="112,68 92,94 132,94" fill="#fff"/>
  <rect x="34" y="114" width="100" height="2" fill="#fff"/>
  <text x="84" y="138" font-family="Inter,sans-serif" font-weight="600" font-size="12.5" letter-spacing="3" fill="#fff" text-anchor="middle">DESIGN AWARDS</text>
  <text x="84" y="172" font-family="Inter,sans-serif" font-weight="500" font-size="13" fill="#b8b8c0" text-anchor="middle">nominated 2026</text>
</svg>
```

## Farben (Primitives)

| Rolle | Skala | Hex |
|-------|-------|-----|
| **Brand / NM (Teal)** | 50 / 100 / 200 / 300 / 400 / **500** / **600** / 700 / 800 / 900 | `#f0feff` · `#d4fbfc` · `#88e1e3` · `#4dd5d8` · `#00c7ca` · `#008893` · `#007d7f` · `#006769` · `#004f51` · `#004142` |
| **Accent (Coral)** | 50 / 100 / 200 / 300 / 400 / **500** / 600 / 700 / 800 / 900 | `#fff1f0` · `#ffd2d1` · `#ffbcbb` · `#ff9e9d` · `#ff8b89` · `#ff6e6c` · `#e86462` · `#b54e4d` · `#8c3d3b` · `#6b2e2d` |
| **UXGA (Violett)** | 50 / 100 / 200 / 300 / 400 / **500** / 600 / 700 / 800 / 900 | `#f2effb` · `#d7cdf3` · `#c4b5ed` · `#a994e4` · `#997fdf` · `#7f5fd7` · `#7456c4` · `#5a4399` · `#463476` · `#35285a` |
| **Neutral** | 50 / 100 / 200 / 300 / 400 / 500 / 600 / 700 / 800 / 900 | `#f8fafc` · `#ebf2f5` · `#dde5e8` · `#c9cfd1` · `#b3bbbd` · `#9ea8aa` · `#8a9496` · `#738082` · `#5d6c6e` · `#48575a` |
| Base | white / black | `#ffffff` · `#000000` |

**Semantische Ableitungen (Light):** `text-primary` = black · `text-secondary` = Neutral/800 `#5d6c6e` · `text-tertiary` = Neutral/700 `#738082` · `text-quaternary` = Neutral/500 · `text-on-brand` = white · `brand-fg` = NM/600 `#007d7f` · `border-secondary` = `rgba(0,0,0,.1)` · `bg-surface` = Neutral/50 `#f8fafc` · `bg-brand-solid` = NM/600.

**Schweregrad-Skala für Findings** (aus dem System abgeleitet): Kritisch = Accent/500 `#ff6e6c` · Hoch = `#f2994a` · Mittel = `#e0b341` · Niedrig = NM/500 `#008893`. Positiv/Stärke = Grün `#25a825` bzw. NM/500.

## Typografie

- **Display / Headings: „Rethink Sans"** — Styles Regular, Medium, SemiBold, ExtraBold (Achtung: `SemiBold`/`ExtraBold` **ohne** Leerzeichen).
- **Body / UI: „Inter"** — Regular, Medium, Semi Bold.
- **Type-Skala** (Name → px / line-height):
  - Display: `2xl` 96/108% · `xl` 72/110% · `lg` 60/110% · `md` 48/110% · `sm` 36/110% · `xs` 32/112%
  - Body: `xl` 28/115% · `lg` 24/125% · `md` 20/150% · `sm` 16/150% · `xs` 14/150%
- Für die Website skaliert (Web liest sich kleiner als Präsentation): Hero-Titel `clamp(2.5rem, 6vw, 5rem)`, Sektions-Titel `clamp(2rem, 4vw, 3.25rem)`, Body 1.125–1.25rem.
- Web-Fonts via Google Fonts (`Rethink+Sans` + `Inter`) mit System-Fallback `-apple-system, "Segoe UI", Roboto, sans-serif`.

## Weitere Tokens

- **Spacing-Skala** (kompatibel zum DS): 4 · 8 · 12 · 16 · 24 · 32 · 48 · 64 · 96 · 128 px.
- **Radius:** sm 8 · md 12 · lg 16 · xl 24 · pill 999 px.
- **Container:** Content-Maxbreite ~1200–1280 px, seitliches Padding `clamp(1.25rem, 5vw, 5rem)`.
- **Schatten (Cards):** `0 1px 2px rgba(0,0,0,.05), 0 12px 32px rgba(0,0,0,.08)`.

## CSS-Variablen-Block (direkt in `<style>` einsetzen)

```css
:root{
  /* Brand — Teal */
  --nm-50:#f0feff; --nm-100:#d4fbfc; --nm-200:#88e1e3; --nm-300:#4dd5d8; --nm-400:#00c7ca;
  --nm-500:#008893; --nm-600:#007d7f; --nm-700:#006769; --nm-800:#004f51; --nm-900:#004142;
  /* Accent — Coral */
  --acc-50:#fff1f0; --acc-100:#ffd2d1; --acc-300:#ff9e9d; --acc-500:#ff6e6c; --acc-600:#e86462; --acc-700:#b54e4d;
  /* UXGA — Violett */
  --ux-100:#d7cdf3; --ux-300:#a994e4; --ux-500:#7f5fd7; --ux-700:#5a4399;
  /* Neutral */
  --n-50:#f8fafc; --n-100:#ebf2f5; --n-200:#dde5e8; --n-300:#c9cfd1; --n-400:#b3bbbd;
  --n-500:#9ea8aa; --n-600:#8a9496; --n-700:#738082; --n-800:#5d6c6e; --n-900:#48575a;
  --white:#fff; --black:#000;
  /* Semantic */
  --brand:var(--nm-600); --brand-strong:var(--nm-700); --brand-soft:var(--nm-50);
  --text:#0b1416; --text-2:var(--n-800); --text-3:var(--n-700); --on-brand:#fff;
  --surface:var(--n-50); --border:rgba(0,0,0,.10);
  /* Severity */
  --sev-crit:#ff6e6c; --sev-high:#f2994a; --sev-mid:#e0b341; --sev-low:#008893; --pos:#25a825;
  /* Cover — wird pro Audit auf die Kundenfarbe gesetzt (JS/inline) */
  --client:#7f5fd7; --client-ink:#fff;
  /* Type */
  --font-display:"Rethink Sans", -apple-system,"Segoe UI",Roboto,sans-serif;
  --font-body:"Inter", -apple-system,"Segoe UI",Roboto,sans-serif;
  /* Space & radius */
  --r-sm:8px; --r-md:12px; --r-lg:16px; --r-xl:24px; --r-pill:999px;
  --shadow:0 1px 2px rgba(0,0,0,.05), 0 12px 32px rgba(0,0,0,.08);
  --maxw:1240px; --pad:clamp(1.25rem,5vw,5rem);
}
```

## Logo (NEW MONDAY, SVG)

Weiß gefüllt; für helle Untergründe `fill="white"` → `fill="#0b1416"` ersetzen. Auf der Cover-Sektion (Kundenfarbe) i. d. R. weiß.

```svg
<svg width="296" height="31" viewBox="0 0 296 31" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="M14.8495 0V14.8494C23.0469 14.8494 29.6989 21.5013 29.6989 29.6987H44.5482C44.5482 13.3006 31.2476 0 14.8495 0ZM0.00354004 29.6987H14.8529V14.8494C6.65215 14.8494 0.00354004 21.5013 0.00354004 29.6987Z" fill="white"/><path d="M74.2464 29.6987H59.3971C59.3971 21.498 52.7451 14.8494 44.5477 14.8494V0C60.9458 0 74.2464 13.2939 74.2464 29.6987Z" fill="white"/><path d="M14.8493 14.8494V29.6987H0C0 21.5014 6.64861 14.8494 14.8493 14.8494Z" fill="white"/><path d="M107.215 8.04176V29.7211H103.254L93.8204 16.0745H93.6626V29.7211H89.0801V8.04176H93.1048L102.465 21.6783H102.656V8.04176H107.218H107.212H107.215Z" fill="white"/><path d="M110.619 29.7211V8.04176H125.229V11.8246H115.208V16.9917H124.484V20.7746H115.208V25.9517H125.276V29.7346H110.625V29.7245L110.619 29.7211Z" fill="white"/><path d="M133.648 29.7211L127.446 8.04176H132.456L136.044 23.1028H136.222L140.183 8.04176H144.469L148.42 23.1364H148.608L152.196 8.04176H157.206L151.004 29.7211H146.536L142.407 15.5471H142.239L138.12 29.7211H133.652H133.648Z" fill="white"/><path d="M166.562 8.04176H172.213L178.183 22.6089H178.435L184.405 8.04176H190.059V29.7211H185.614V15.6109H185.436L179.822 29.617H176.792L171.178 15.5605H171V29.7245H166.555V8.04176H166.562Z" fill="white"/><path d="M213.334 18.8797C213.334 21.2449 212.888 23.2539 211.994 24.9135C211.097 26.5732 209.884 27.8397 208.352 28.7099C206.817 29.58 205.097 30.0167 203.178 30.0167C201.26 30.0167 199.52 29.58 197.991 28.7065C196.463 27.8296 195.25 26.5631 194.359 24.9068C193.469 23.2472 193.029 21.2382 193.029 18.8831C193.029 16.528 193.476 14.5089 194.359 12.8493C195.246 11.1897 196.459 9.92308 197.991 9.05295C199.52 8.18282 201.253 7.74608 203.178 7.74608C205.103 7.74608 206.817 8.18282 208.352 9.05295C209.887 9.92308 211.1 11.1897 211.994 12.8493C212.891 14.5089 213.334 16.5179 213.334 18.8831V18.8797ZM208.688 18.8797C208.688 17.3511 208.46 16.0577 208.006 15.0028C207.553 13.9546 206.911 13.155 206.084 12.6107C205.258 12.0665 204.294 11.7944 203.185 11.7944C202.076 11.7944 201.112 12.0665 200.286 12.6107C199.459 13.155 198.821 13.9512 198.364 15.0028C197.907 16.051 197.682 17.3444 197.682 18.8797C197.682 20.4151 197.911 21.7018 198.364 22.7567C198.818 23.8116 199.459 24.6078 200.286 25.1487C201.112 25.693 202.076 25.9651 203.185 25.9651C204.294 25.9651 205.258 25.693 206.084 25.1487C206.911 24.6045 207.549 23.8082 208.006 22.7567C208.463 21.7085 208.688 20.4151 208.688 18.8797Z" fill="white"/><path d="M234.42 8.04176V29.7211H230.459L221.025 16.0745H220.867V29.7211H216.285V8.04176H220.31L229.669 21.6783H229.857V8.04176H234.42Z" fill="white"/><path d="M245.509 29.7211H237.822V8.04176H245.573C247.756 8.04176 249.631 8.47178 251.207 9.33856C252.779 10.2053 253.992 11.4417 254.845 13.061C255.695 14.6803 256.122 16.6087 256.122 18.863C256.122 21.1173 255.695 23.0591 254.845 24.6851C253.995 26.3078 252.776 27.5542 251.193 28.421C249.607 29.2878 247.713 29.7211 245.515 29.7211H245.509ZM242.408 25.7904H245.317C246.675 25.7904 247.813 25.5485 248.744 25.0681C249.668 24.5843 250.373 23.8318 250.844 22.8105C251.314 21.7925 251.546 20.4756 251.546 18.8563C251.546 17.2369 251.314 15.9469 250.844 14.9255C250.373 13.9109 249.675 13.1651 248.754 12.6847C247.83 12.2043 246.691 11.9658 245.334 11.9658H242.415V25.7904H242.411H242.408Z" fill="white"/><path d="M261.746 29.7211H256.837L264.319 8.04176H270.225L277.7 29.7211H272.789L267.36 12.9971H267.192L261.752 29.7211H261.749H261.746ZM261.44 21.1979H273.041V24.7758H261.44V21.1979Z" fill="white"/><path d="M275.631 8.04176H280.764L285.71 17.378H285.921L290.867 8.04176H296L288.092 22.0579V29.7211H283.539V22.0579L275.631 8.04176Z" fill="white"/></svg>
```
