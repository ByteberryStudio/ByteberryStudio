"""Builds the ByteberryStudio GitHub profile widgets (animated SVGs) and the avatar PNG.

Fonts are the site's own latin subsets (Unbounded, Manrope, Silkscreen), instanced to a
fixed weight, subset to the characters used, and embedded as base64 WOFF2 so the SVGs
render the same everywhere without loading anything external.
"""
import base64
import html
import io
import os
import sys

from fontTools import subset
from fontTools.ttLib import TTFont
from fontTools.varLib import instancer
from PIL import Image, ImageDraw, ImageFilter

S = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(os.path.dirname(S), "assets")
os.makedirs(OUT, exist_ok=True)
WORK_IMG = "D:/ByteBerry/www/public/images/work"

C = dict(ink="#140a18", surface="#1c1022", surface2="#2a1832", line="#3a2440",
         text="#f7eef3", muted="#cdbac7", berry="#ff5c93", berryL="#ffb3cc",
         berryD="#9e1a4c", leaf="#7bd389")

# ---------------------------------------------------------------- fonts
FONT_SPECS = {
    "display": ("unbounded.woff2", 700, "BBDisplay"),
    "sans": ("manrope.woff2", 500, "BBSans"),
    "sansb": ("manrope.woff2", 700, "BBSansBold"),
    "pixel": ("silkscreen.woff2", None, "BBPixel"),
}
FONTS = {}
for key, (file, wght, family) in FONT_SPECS.items():
    f = TTFont(os.path.join(S, "fonts", file))
    if "fvar" in f and wght:
        f = instancer.instantiateVariableFont(f, {"wght": wght})
    FONTS[key] = dict(font=f, family=family, cmap=f.getBestCmap(),
                      upem=f["head"].unitsPerEm, chars=set())


def measure(key, text, size):
    F = FONTS[key]
    hmtx = F["font"]["hmtx"]
    total = 0
    for ch in text:
        g = F["cmap"].get(ord(ch))
        if g is None:
            sys.exit(f"Missing glyph {ch!r} in {key}")
        total += hmtx[g][0]
    return total * size / F["upem"]


def font_css(keys):
    out = []
    for key in keys:
        F = FONTS[key]
        buf = io.BytesIO()
        f = TTFont(io.BytesIO(_ttf_bytes(F["font"])))
        opts = subset.Options()
        opts.flavor = "woff2"
        opts.layout_features = ["kern", "liga"]
        opts.name_IDs = []
        sub = subset.Subsetter(opts)
        sub.populate(text="".join(sorted(F["chars"] | {" "})))
        sub.subset(f)
        f.flavor = "woff2"
        f.save(buf)
        b64 = base64.b64encode(buf.getvalue()).decode()
        out.append(f"@font-face{{font-family:{F['family']};src:url(data:font/woff2;base64,{b64}) format('woff2');}}")
    return "".join(out)


def _ttf_bytes(font):
    buf = io.BytesIO()
    font.flavor = None
    font.save(buf)
    return buf.getvalue()


def text(key, s, x, y, size, fill, extra="", cls=""):
    FONTS[key]["chars"].update(s)
    c = f' class="{cls}"' if cls else ""
    return (f'<text x="{x:.1f}" y="{y:.1f}" font-family="{FONTS[key]["family"]}" font-size="{size}" '
            f'fill="{fill}"{c} {extra}>{html.escape(s)}</text>')


# ---------------------------------------------------------------- shared pieces
# The Byteberry pixel berry on a 7 x 8 grid (same art as the site favicon).
BERRY = []
for r, cols, colour in [(0, [3], "leaf"), (1, [2, 3, 4], "leaf"), (2, range(1, 6), "berry"),
                        (3, range(7), "berry"), (4, range(7), "berry"), (5, range(7), "berry"),
                        (6, range(1, 6), "berry"), (7, [2, 3, 4], "berry")]:
    for c in cols:
        BERRY.append((c, r, colour))
HIGHLIGHT = {(1, 3), (4, 4), (2, 5)}


def berry_cells(animated=True, delay0=0.0, step=0.035):
    out = []
    for i, (c, r, colour) in enumerate(BERRY):
        col = C["berryL"] if (c, r) in HIGHLIGHT else C[colour]
        cls = "px" + (" twinkle" if (c, r) in HIGHLIGHT else "") if animated else ""
        style = f' style="animation-delay:{delay0 + (r * 7 + c) * step:.3f}s{_twinkle_delay(c, r, delay0)}"' if animated else ""
        out.append(f'<rect class="{cls}" x="{c * 10}" y="{r * 10}" width="9" height="9" rx="1" fill="{col}"{style}/>')
    return "".join(out)


def _twinkle_delay(c, r, delay0):
    if (c, r) not in HIGHLIGHT:
        return ""
    d = delay0 + (r * 7 + c) * 0.035
    return f",{d + 2.5 + c * 0.7:.2f}s"


def dots_and_glow(w, h, glows):
    g = [f'<rect width="{w}" height="{h}" fill="url(#dots)"/>']
    for i, (cx, cy, rad, grad) in enumerate(glows):
        g.append(f'<circle class="drift{i % 2}" cx="{cx}" cy="{cy}" r="{rad}" fill="url(#{grad})"/>')
    return "".join(g)


COMMON_DEFS = f"""
<pattern id="dots" width="22" height="22" patternUnits="userSpaceOnUse"><circle cx="1" cy="1" r="1" fill="{C['text']}" fill-opacity=".09"/></pattern>
<radialGradient id="glowB"><stop offset="0" stop-color="{C['berry']}" stop-opacity=".42"/><stop offset="1" stop-color="{C['berry']}" stop-opacity="0"/></radialGradient>
<radialGradient id="glowL"><stop offset="0" stop-color="{C['leaf']}" stop-opacity=".2"/><stop offset="1" stop-color="{C['leaf']}" stop-opacity="0"/></radialGradient>
"""

COMMON_CSS = f"""
.px{{opacity:0;transform-box:fill-box;transform-origin:center;animation:pop .55s cubic-bezier(.2,.8,.2,1) forwards}}
.px.twinkle{{animation:pop .55s cubic-bezier(.2,.8,.2,1) forwards,twinkle 5s ease-in-out infinite}}
@keyframes pop{{0%{{opacity:0;transform:scale(.2)}}70%{{opacity:1;transform:scale(1.18)}}100%{{opacity:1;transform:scale(1)}}}}
@keyframes twinkle{{0%,86%,100%{{fill:{C['berryL']}}}92%{{fill:#ffffff}}}}
.bob{{animation:bob 6s ease-in-out 2s infinite}}
@keyframes bob{{0%,100%{{transform:translateY(0)}}50%{{transform:translateY(-9px)}}}}
.rise{{opacity:0;animation:rise .8s cubic-bezier(.2,.8,.2,1) forwards}}
@keyframes rise{{from{{opacity:0;transform:translateY(14px)}}to{{opacity:1;transform:none}}}}
.drift0{{animation:drift0 18s ease-in-out infinite alternate}}
.drift1{{animation:drift1 22s ease-in-out infinite alternate}}
@keyframes drift0{{to{{transform:translate(60px,30px)}}}}
@keyframes drift1{{to{{transform:translate(-70px,-20px)}}}}
.pulse{{transform-box:fill-box;transform-origin:center;animation:pulse 2.2s ease-out infinite}}
@keyframes pulse{{0%{{transform:scale(1);opacity:.7}}100%{{transform:scale(2.8);opacity:0}}}}
.static{{display:none}}
@media (prefers-reduced-motion:reduce){{
  *{{animation:none!important}}
  .px,.rise{{opacity:1}}
  .motion{{display:none}}
  .static{{display:inline}}
}}
"""


def card(w, h, rx=28):
    """Card background, clip, and an animated light travelling along the border."""
    return f"""
<clipPath id="card"><rect width="{w}" height="{h}" rx="{rx}"/></clipPath>
<linearGradient id="edge" gradientUnits="userSpaceOnUse" x1="0" y1="0" x2="{w}" y2="0">
  <stop offset="0" stop-color="{C['berryL']}" stop-opacity="0"/>
  <stop offset=".44" stop-color="{C['berryL']}" stop-opacity=".75"/>
  <stop offset=".56" stop-color="{C['leaf']}" stop-opacity=".6"/>
  <stop offset="1" stop-color="{C['leaf']}" stop-opacity="0"/>
  <animateTransform attributeName="gradientTransform" type="translate" values="-{w} 0;{w} 0" dur="7s" repeatCount="indefinite"/>
</linearGradient>""", f"""
<rect width="{w}" height="{h}" rx="{rx}" fill="{C['ink']}"/>""", f"""
<rect x=".75" y=".75" width="{w - 1.5}" height="{h - 1.5}" rx="{rx - .75}" fill="none" stroke="{C['line']}" stroke-width="1.5"/>
<rect class="motion" x=".75" y=".75" width="{w - 1.5}" height="{h - 1.5}" rx="{rx - .75}" fill="none" stroke="url(#edge)" stroke-width="1.5"/>"""


def pill(x, y, label, h=36, dot=C["berry"], key="sans", size=16, cls="", style=""):
    tw = measure(key, label, size)
    w = tw + 46
    s = f'<g class="{cls}" style="{style}">' if cls else "<g>"
    s += f'<rect x="{x}" y="{y}" width="{w:.1f}" height="{h}" rx="{h / 2}" fill="{C["surface2"]}" stroke="{C["line"]}"/>'
    s += f'<rect x="{x + 16}" y="{y + h / 2 - 4}" width="8" height="8" rx="1" fill="{dot}"/>'
    s += text(key, label, x + 32, y + h / 2 + size * .36, size, C["text"])
    return s + "</g>", w


def svg(w, h, defs, body, font_keys, title):
    css = font_css(font_keys) + COMMON_CSS + EXTRA_CSS.get(title, "")
    return (f'<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" '
            f'viewBox="0 0 {w} {h}" width="{w}" height="{h}" role="img" aria-label="{html.escape(title)}">'
            f'<title>{html.escape(title)}</title><style>{css}</style><defs>{COMMON_DEFS}{defs}</defs>{body}</svg>')


EXTRA_CSS = {}


# ---------------------------------------------------------------- header
def build_header():
    W, H = 1200, 440
    cdefs, cbg, cborder = card(W, H)
    x0 = 400
    parts = [cbg, '<g clip-path="url(#card)">',
             dots_and_glow(W, H, [(250, 200, 300, "glowB"), (1080, 380, 280, "glowL"), (980, 40, 220, "glowB")])]

    # Pixel berry
    parts.append(f'<g transform="translate(92,86)"><g class="bob"><g transform="scale(3.4)">{berry_cells()}</g></g></g>')

    # Status pill with a pulsing dot
    label = "Taking new projects"
    tw = measure("sansb", label, 15)
    pw = tw + 52
    parts.append(f'<g class="rise" style="animation-delay:.9s">'
                 f'<rect x="{x0}" y="64" width="{pw:.1f}" height="34" rx="17" fill="{C["leaf"]}" fill-opacity=".12" stroke="{C["leaf"]}" stroke-opacity=".45"/>'
                 f'<circle class="pulse" cx="{x0 + 20}" cy="81" r="5" fill="{C["leaf"]}"/>'
                 f'<circle cx="{x0 + 20}" cy="81" r="5" fill="{C["leaf"]}"/>'
                 + text("sansb", label, x0 + 34, 86.5, 15, C["leaf"]) + "</g>")

    # Title with a sheen that sweeps across
    title = "Byteberry"
    ts = 88
    tw = measure("display", title, ts)
    cdefs += f"""
<linearGradient id="titleFill" gradientUnits="userSpaceOnUse" x1="{x0}" y1="0" x2="{x0 + tw:.0f}" y2="0">
  <stop offset="0" stop-color="{C['text']}"/><stop offset=".55" stop-color="{C['berryL']}"/><stop offset="1" stop-color="{C['berry']}"/>
</linearGradient>
<linearGradient id="sheen" gradientUnits="userSpaceOnUse" x1="0" y1="0" x2="220" y2="0">
  <stop offset="0" stop-color="#fff" stop-opacity="0"/><stop offset=".5" stop-color="#fff" stop-opacity=".75"/><stop offset="1" stop-color="#fff" stop-opacity="0"/>
  <animateTransform attributeName="gradientTransform" type="translate" values="{x0 - 300} 0;{x0 + tw + 80:.0f} 0;{x0 + tw + 80:.0f} 0" keyTimes="0;.4;1" dur="6s" begin="1.6s" repeatCount="indefinite"/>
</linearGradient>"""
    parts.append(f'<g class="rise" style="animation-delay:.25s">'
                 + text("display", title, x0 - 4, 196, ts, "url(#titleFill)", 'letter-spacing="-1.5"')
                 + text("display", title, x0 - 4, 196, ts, "url(#sheen)", 'letter-spacing="-1.5"', cls="motion")
                 + "</g>")

    sub = "Websites and email marketing for small businesses."
    ss = 25
    while measure("sans", sub, ss) > W - x0 - 50:
        ss -= 1
    parts.append(text("sans", sub, x0, 246, ss, C["text"], cls="rise", extra='style="animation-delay:.45s"'))

    # Typing line: "> websites for <word>" with a blinking cursor
    prefix = "> websites for "
    py, psz = 298, 21
    pw_ = measure("pixel", prefix, psz)
    wx = x0 + pw_
    words = ["clinics", "studios", "wellness brands", "local services"]
    T, slot = 12.0, 3.0
    cursor_events = [(0.0, 0.0)]
    word_svgs = []
    for i, wd in enumerate(words):
        widths = [measure("pixel", wd[:k], psz) for k in range(len(wd) + 1)]
        s0 = i * slot + 0.15
        ev = [(0.0, 0.0)]
        t = s0
        for k in range(1, len(wd) + 1):
            t = s0 + k * 0.075
            ev.append((t, widths[k]))
        hold_end = t + 1.25
        n = len(wd)
        for j, k in enumerate(range(n - 1, -1, -1)):
            ev.append((hold_end + (j + 1) * 0.028, widths[k]))
        cursor_events += ev[1:]
        vals = ";".join(f"{v:.1f}" for _, v in ev)
        kts = ";".join(f"{tt / T:.4f}" for tt, _ in ev)
        cdefs += (f'<clipPath id="w{i}"><rect x="{wx:.1f}" y="{py - 24}" width="0" height="32">'
                  f'<animate attributeName="width" dur="{T}s" repeatCount="indefinite" calcMode="discrete" values="{vals}" keyTimes="{kts}"/>'
                  f'</rect></clipPath>')
        word_svgs.append(f'<g clip-path="url(#w{i})">' + text("pixel", wd, wx, py, psz, C["leaf"]) + "</g>")
    cursor_events.sort()
    cvals = ";".join(f"{wx + v + 3:.1f}" for _, v in cursor_events)
    ckts = ";".join(f"{tt / T:.4f}" for tt, _ in cursor_events)
    EXTRA_CSS["Byteberry"] = ".blink{animation:blink 1s steps(1) infinite}@keyframes blink{50%{opacity:0}}"
    parts.append(f'<g class="rise" style="animation-delay:.65s">'
                 + text("pixel", prefix, x0, py, psz, C["muted"])
                 + '<g class="motion">' + "".join(word_svgs)
                 + f'<rect class="blink" x="{wx + 3:.1f}" y="{py - 18}" width="11" height="20" fill="{C["berry"]}">'
                 f'<animate attributeName="x" dur="{T}s" repeatCount="indefinite" calcMode="discrete" values="{cvals}" keyTimes="{ckts}"/></rect></g>'
                 + text("pixel", "clinics and studios", wx, py, psz, C["leaf"], cls="static")
                 + "</g>")

    # Fact pills
    x = x0
    for i, (label, dot) in enumerate([("Melbourne, Australia", C["berry"]), ("Fixed prices", C["leaf"]),
                                      ("Live in 2 to 3 weeks", C["berryL"])]):
        s, w = pill(x, 336, label, dot=dot, cls="rise", style=f"animation-delay:{.85 + i * .12:.2f}s")
        parts.append(s)
        x += w + 12

    parts.append("</g>")
    parts.append(cborder)
    return svg(W, H, cdefs, "".join(parts), ["display", "sans", "sansb", "pixel"], "Byteberry")


# ---------------------------------------------------------------- tech stack
ICONS = [("wordpress", "WordPress"), ("shopify", "Shopify"), ("nextdotjs", "Next.js"), ("react", "React"),
         ("typescript", "TypeScript"), ("tailwindcss", "Tailwind CSS"), ("googleanalytics", "Google Analytics")]


def icon_path(name):
    import re
    raw = open(os.path.join(S, "icons", f"{name}.svg"), encoding="utf-8").read()
    return re.search(r'<path d="([^"]+)"', raw).group(1)


def build_stack():
    W = 1200
    pad, gap, ch, size = 40, 14, 58, 19
    chips, x, y = [], pad, 84
    per_row = (len(ICONS) + 1) // 2
    for i, (icon, label) in enumerate(ICONS):
        w = 22 + 26 + 12 + measure("sans", label, size) + 24
        if i and i % per_row == 0:
            x, y = pad, y + ch + gap
        chips.append((x, y, w, icon, label, i))
        x += w + gap
    H = y + ch + 40
    cdefs, cbg, cborder = card(W, H, 24)
    n = len(chips)
    period = 1.1 * n
    EXTRA_CSS["Tools I build with"] = (
        f".chip{{animation:chip {period:.1f}s ease-in-out infinite}}"
        f"@keyframes chip{{0%,{100 / n * 1.6:.1f}%,100%{{stroke:{C['line']};fill:{C['surface']}}}{100 / n * .8:.1f}%{{stroke:{C['berry']};fill:{C['surface2']}}}}}")
    parts = [cbg, '<g clip-path="url(#card)">', dots_and_glow(W, H, [(1100, 0, 260, "glowB"), (100, H, 220, "glowL")])]
    parts.append(text("pixel", "Tools I build with", pad, 52, 17, C["berryL"], cls="rise"))
    for (x, y, w, icon, label, i) in chips:
        parts.append(f'<g class="rise" style="animation-delay:{.15 + i * .08:.2f}s">'
                     f'<rect class="chip" style="animation-delay:{1.2 + i * 1.1:.1f}s" x="{x:.1f}" y="{y}" width="{w:.1f}" height="{ch}" rx="{ch / 2}" fill="{C["surface"]}" stroke="{C["line"]}" stroke-width="1.5"/>'
                     f'<path transform="translate({x + 22:.1f},{y + 16}) scale({26 / 24:.4f})" d="{icon_path(icon)}" fill="{C["berryL"]}"/>'
                     + text("sans", label, x + 22 + 26 + 12, y + ch / 2 + size * .36, size, C["text"]) + "</g>")
    parts.append("</g>")
    parts.append(cborder)
    return svg(W, H, cdefs, "".join(parts), ["sans", "pixel"], "Tools I build with")


# ---------------------------------------------------------------- featured work
def b64_image(path, width, quality=80):
    im = Image.open(path).convert("RGB")
    h = round(im.height * width / im.width)
    im = im.resize((width, h), Image.LANCZOS)
    buf = io.BytesIO()
    im.save(buf, "WEBP", quality=quality, method=6)
    return base64.b64encode(buf.getvalue()).decode(), im.width, im.height


def wrap(key, s, size, maxw):
    lines, cur = [], ""
    for word in s.split():
        trial = (cur + " " + word).strip()
        if measure(key, trial, size) > maxw and cur:
            lines.append(cur)
            cur = word
        else:
            cur = trial
    return lines + [cur]


def build_work():
    W, H = 1200, 560
    cdefs, cbg, cborder = card(W, H)
    parts = [cbg, '<g clip-path="url(#card)">', dots_and_glow(W, H, [(860, 300, 360, "glowB"), (120, 520, 240, "glowL")])]
    lx = 56
    parts.append(text("pixel", "Featured work", lx, 92, 17, C["berryL"], cls="rise"))
    parts.append(text("display", "Lovelysmiles", lx - 2, 152, 46, C["text"], 'letter-spacing="-1"', cls="rise", ) .replace('class="rise"', 'class="rise" style="animation-delay:.1s"'))
    parts.append(text("sans", "Teeth whitening, Auckland and Wellington", lx, 190, 18, C["muted"], cls="rise", extra='style="animation-delay:.2s"'))
    desc = "A booking-first WordPress redesign for a clinic with two locations. Clients pick a clinic and book in a couple of minutes."
    for i, line in enumerate(wrap("sans", desc, 20, 400)):
        parts.append(text("sans", line, lx, 246 + i * 31, 20, C["text"], cls="rise", extra=f'style="animation-delay:{.3 + i * .05:.2f}s"'))
    ty = 246 + 4 * 31 + 10
    x = lx
    for i, (label, dot) in enumerate([("WordPress", C["berry"]), ("Online booking", C["leaf"]), ("Email", C["berryL"])]):
        s, w = pill(x, ty, label, dot=dot, size=15, h=34, cls="rise", style=f"animation-delay:{.5 + i * .08:.2f}s")
        parts.append(s)
        x += w + 10
    link = "Visit lovelysmiles.co"
    lw = measure("sansb", link, 18)
    parts.append(f'<g class="rise" style="animation-delay:.75s">' + text("sansb", link, lx, ty + 86, 18, C["berry"])
                 + f'<path d="M{lx + lw + 10} {ty + 80}l10-10m-8 0h8v8" stroke="{C["berry"]}" stroke-width="2.4" fill="none" stroke-linecap="round" stroke-linejoin="round"/></g>')

    # The cover is already a device render, so show it on its own in a rounded frame
    d64, iw, ih = b64_image(os.path.join(WORK_IMG, "lovelysmiles-cover.webp"), 1300, quality=82)
    bw = 640
    bh = bw * ih / iw
    bx, by = W - 48 - bw, (H - bh) / 2
    cdefs += (f'<clipPath id="shot"><rect x="{bx}" y="{by:.1f}" width="{bw}" height="{bh:.1f}" rx="18"/></clipPath>'
              f'<filter id="shadow" x="-20%" y="-20%" width="140%" height="150%"><feDropShadow dx="0" dy="22" stdDeviation="24" flood-color="#000" flood-opacity=".5"/></filter>')
    EXTRA_CSS["Featured work: Lovelysmiles"] = (".kb{transform-box:fill-box;transform-origin:50% 40%;animation:kb 16s ease-in-out infinite alternate}"
                                                "@keyframes kb{to{transform:scale(1.05)}}")
    parts.append(f'<g class="rise" style="animation-delay:.35s"><g filter="url(#shadow)">'
                 f'<rect x="{bx}" y="{by:.1f}" width="{bw}" height="{bh:.1f}" rx="18" fill="{C["surface"]}"/></g>'
                 f'<g clip-path="url(#shot)"><image class="kb" x="{bx}" y="{by:.1f}" width="{bw}" height="{bh:.1f}" preserveAspectRatio="xMidYMid slice" href="data:image/webp;base64,{d64}"/></g>'
                 f'<rect x="{bx + .75}" y="{by + .75:.1f}" width="{bw - 1.5}" height="{bh - 1.5:.1f}" rx="17.25" fill="none" stroke="{C["text"]}" stroke-opacity=".12" stroke-width="1.5"/></g>')
    parts.append("</g>")
    parts.append(cborder)
    return svg(W, H, cdefs, "".join(parts), ["display", "sans", "sansb", "pixel"], "Featured work: Lovelysmiles")


# ---------------------------------------------------------------- call to action
def build_cta():
    W, H = 1200, 230
    cdefs, cbg, cborder = card(W, H)
    parts = [cbg, '<g clip-path="url(#card)">', dots_and_glow(W, H, [(140, 115, 200, "glowB"), (1050, 115, 240, "glowB")])]
    parts.append(f'<g transform="translate(64,59)"><g class="bob"><g transform="scale(1.4)">{berry_cells(delay0=.1, step=.02)}</g></g></g>')
    tx = 190
    parts.append(text("display", "Got a project in mind?", tx, 106, 36, C["text"], 'letter-spacing="-.8"', cls="rise"))
    parts.append(text("sans", "Tell me about your business and I'll come back with a fixed quote.", tx, 146, 19, C["muted"], cls="rise", extra='style="animation-delay:.15s"'))
    label = "Get in touch"
    lw = measure("sansb", label, 20)
    bw, bh = lw + 84, 62
    bx, by = W - 56 - bw, (H - bh) / 2
    EXTRA_CSS["Got a project in mind? Get in touch"] = (".ring{transform-box:fill-box;transform-origin:center;animation:ring 2.4s ease-out infinite}"
                                                        "@keyframes ring{0%{transform:scale(1);opacity:.6}100%{transform:scale(1.25,1.6);opacity:0}}"
                                                        ".nudge{animation:nudge 2.4s ease-in-out infinite}@keyframes nudge{0%,60%,100%{transform:none}75%{transform:translateX(5px)}}")
    parts.append(f'<g class="rise" style="animation-delay:.3s">'
                 f'<rect class="ring motion" x="{bx}" y="{by}" width="{bw:.1f}" height="{bh}" rx="{bh / 2}" fill="none" stroke="{C["berry"]}" stroke-width="2"/>'
                 f'<rect x="{bx}" y="{by}" width="{bw:.1f}" height="{bh}" rx="{bh / 2}" fill="{C["berry"]}"/>'
                 + text("sansb", label, bx + 30, by + bh / 2 + 7, 20, C["ink"])
                 + f'<path class="nudge" d="M{bx + 30 + lw + 14} {by + bh / 2}h16m-6-6 6 6-6 6" stroke="{C["ink"]}" stroke-width="2.6" fill="none" stroke-linecap="round" stroke-linejoin="round"/></g>')
    parts.append("</g>")
    parts.append(cborder)
    return svg(W, H, cdefs, "".join(parts), ["display", "sans", "sansb"], "Got a project in mind? Get in touch")


# ---------------------------------------------------------------- avatar
def build_avatar(path, size=1024):
    im = Image.new("RGB", (size, size), C["ink"])
    glow = Image.new("RGB", (size, size), C["ink"])
    gd = ImageDraw.Draw(glow)
    gd.ellipse((size * .18, size * .2, size * .82, size * .84), fill="#5a1f3e")
    glow = glow.filter(ImageFilter.GaussianBlur(size * .12))
    im.paste(glow)
    d = ImageDraw.Draw(im)
    step = size * 0.066
    for gx in range(int(size / step) + 1):
        for gy in range(int(size / step) + 1):
            cx, cy = gx * step + step / 2, gy * step + step / 2
            d.ellipse((cx - 2, cy - 2, cx + 2, cy + 2), fill="#2a1a2f")
    cell = size * 0.068
    gw, gh = 7 * cell, 8 * cell
    ox, oy = (size - gw) / 2, (size - gh) / 2
    gap = cell * 0.1
    for c, r, colour in BERRY:
        col = C["berryL"] if (c, r) in HIGHLIGHT else C[colour]
        x, y = ox + c * cell, oy + r * cell
        d.rounded_rectangle((x, y, x + cell - gap, y + cell - gap), radius=cell * 0.1, fill=col)
    im.save(path, "PNG", optimize=True)


if __name__ == "__main__":
    files = {
        "header.svg": build_header(),
        "stack.svg": build_stack(),
        "work-lovelysmiles.svg": build_work(),
        "cta.svg": build_cta(),
    }
    for name, content in files.items():
        with open(os.path.join(OUT, name), "w", encoding="utf-8") as fh:
            fh.write(content)
        print(f"{name}: {len(content) / 1024:.0f} KB")
    build_avatar(os.path.join(OUT, "avatar.png"))
    print("avatar.png written")
