#!/usr/bin/env python3
"""Shared Space hub generator (Pico.css theme).
Reads project.md manifests -> hub index.html + per-project detail pages.
Uses the vendored Pico.css kit (assets/pico.min.css) — semantic markup,
minimal custom CSS. Never hand-edit generated HTML.
"""
import os, re, glob, html

ROOT = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(ROOT, "index.html")
PICO = "assets/pico.min.css"
PICO_ABS = "/assets/pico.min.css"  # absolute so detail pages in subdirs resolve correctly

# TINY custom layer on top of Pico (things a kit doesn't do well)
CUSTOM_CSS = """
/* Project tiles: tap targets >= 44px, hover lift */
a.tile { display: block; }
a.tile { background: var(--pico-card-background-color); color: inherit;
  padding: var(--pico-block-spacing-vertical) var(--pico-block-spacing-horizontal);
  border-radius: var(--pico-border-radius); transition: transform .08s ease, box-shadow .12s ease; }
a.tile:hover { transform: translateY(-1px); }
a.tile .arrow { margin-left: auto; opacity: .55; }

/* status pill */
.pill { display: inline-block; font-size: .72rem; font-weight: 600;
  padding: 2px 9px; border-radius: 999px; color: #fff; vertical-align: middle; }
.pill.active  { background: #2f9e69; }
.pill.ongoing { background: #2f9e69; }
.pill.parked  { background: #c9a227; }
.pill.done    { background: #5f6b80; }

/* section headings in a project space */
.sp h3, .sp h4 { border-bottom: 1px solid var(--pico-muted-border-color); padding-bottom: 4px; }
li > code, p > code { font-size: .85em; }
/* bullets inside project bodies that aren't wrapped in a list get spacing */
.sp ul { margin-bottom: 0; }

/* mobile comfort */
@media (max-width: 600px) {
  h1 { font-size: 1.5rem; }
  a.tile { padding: 12px 14px; margin-bottom: 8px; }
  article { padding: 16px 12px; }
}
@media (prefers-reduced-motion: reduce) {
  a.tile, a.tile * { transition: none; }
}
"""

def stamp():
    return __import__("datetime").datetime.now().strftime("%b %d %Y, %I:%M %p")

def parse_manifest(path):
    with open(path) as f:
        raw = f.read()
    m = re.search(r"^---\n(.*?)\n---", raw, re.S | re.M)
    meta = {}
    if m:
        for line in m.group(1).splitlines():
            if ":" in line:
                k, _, v = line.partition(":")
                meta[k.strip()] = v.strip().strip("\"'")
    body = re.sub(r"^---\n.*?\n---\n?", "", raw, flags=re.S | re.M).strip()
    return meta, body

def md_to_html(text):
    """Minimal md -> html for manifest body (headings, bullets, bold, code)."""
    out = []
    in_ul = False
    for line in text.splitlines():
        s = line.rstrip()
        if not s.strip():
            if in_ul:
                out.append("</ul>")
                in_ul = False
            continue
        s = s.replace("[ ]", "<code>☐</code>").replace("[x]", "☑").replace("[X]", "☑")
        s = re.sub(r"`([^`]+)`", r"<code>\1</code>", s)
        s = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", s)
        st = s.strip()
        if st.startswith("### "):
            if in_ul: out.append("</ul>"); in_ul = False
            out.append(f"<h4>{html.escape(st[4:])}</h4>")
        elif st.startswith("## "):
            if in_ul: out.append("</ul>"); in_ul = False
            out.append(f"<h3>{html.escape(st[3:])}</h3>")
        elif st.startswith("# "):
            if in_ul: out.append("</ul>"); in_ul = False
            out.append(f"<h2>{html.escape(st[2:])}</h2>")
        elif st.startswith("- "):
            if not in_ul:
                out.append("<ul>"); in_ul = True
            out.append(f"<li>{st[2:]}</li>")
        else:
            if in_ul: out.append("</ul>"); in_ul = False
            out.append(f"<p>{s}</p>")
    if in_ul:
        out.append("</ul>")
    return "\n".join(out)

def about_line(body_text, n=140):
    """First non-heading, non-list line as the tile's blurb."""
    for line in body_text.splitlines():
        st = line.strip()
        if st and not st.startswith(("#", "-", "##")) and len(st) > len(st.split()[0]):
            return html.escape(st[:n])
    return ""

def write(path, content):
    tmp = path + ".tmp"
    with open(tmp, "w") as f:
        f.write(content)
    os.replace(tmp, path)

def head(title):
    return f"""<!DOCTYPE html>
<html lang="en" data-theme="auto"><head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="color-scheme" content="light dark">
<title>{html.escape(title)}</title>
<link rel="stylesheet" href="{PICO_ABS}">
<style>{CUSTOM_CSS}</style>
</head><body>
<main class="container" style="padding-top:1rem">
"""

def foot():
    return f"""<div class="footer" style="margin-top:2.5rem;text-align:center;color:var(--pico-muted-color);font-size:.8rem">
  Shared space · generated {stamp()} · edit project.md and rerun generate.py
</div>
</main>
</body></html>"""

def main():
    manifests = sorted(glob.glob(os.path.join(ROOT, "*", "project.md")))
    spaces = []
    for pm in manifests:
        meta, body = parse_manifest(pm)
        slug = os.path.basename(os.path.dirname(pm))
        name = meta.get("name") or slug.replace("-", " ").title()
        status = (meta.get("status") or "active").lower()
        spaces.append({
            "slug": slug, "name": name, "status": status,
            "updated": meta.get("updated", ""),
            "tags": [t.strip() for t in meta.get("tags", "").split(",") if t.strip()],
            "body": md_to_html(body or "<p><i>empty space</i></p>"),
            "body_text": body,
        })
    spaces.sort(key=lambda s: (0 if s["status"] in ("active", "ongoing") else 1,
                                s["updated"] or ""))

    # ---- Hub ----
    if not spaces:
        tiles = "<article><p>No project spaces yet.</p><p>When you tell me something belongs in the shared space, I create a project here.</p></article>"
    else:
        tile_html = []
        for s in spaces:
            taghtml = "".join(f"<span class='pill' style='background:var(--pico-secondary-background);color:var(--pico-secondary-inverse)'>{html.escape(t)}</span> " for t in s["tags"])
            about = about_line(s["body_text"])
            tile_html.append(f"""
  <a class="tile" href="/{s['slug']}/" role="button" style="text-align:left">
    <span style="display:block;font-size:1.05rem;font-weight:600">{html.escape(s['name'])}
      <span class="pill {html.escape(s['status'])}" style="margin-left:.4rem">{html.escape(s['status'])}</span>
      <span class="arrow">›</span>
    </span>
    <span style="display:block;margin-top:.4rem;color:var(--pico-muted-color);font-size:.9rem">{about}</span>
    <span style="display:block;margin-top:.4rem;font-size:.72rem">{taghtml}<span class="pill" style="background:var(--pico-muted-border-color);color:var(--pico-muted-color)">updated {html.escape(s['updated'])}</span></span>
  </a>""")
        tiles = "\n".join(tile_html)

    hub = head("Shared Space · Andrew")
    hub += f"""<h1 style="margin-bottom:.25rem">Shared Space</h1>
<p style="color:var(--pico-muted-color);margin-bottom:1.4rem">Updated {stamp()} · {len(spaces)} project(s) · tap one to open it</p>
{tiles}
"""
    hub += foot()
    write(OUT, hub)

    # ---- Detail pages ----
    for s in spaces:
        taghtml = "".join(f"<span class='pill' style='background:var(--pico-secondary-background);color:var(--pico-secondary-inverse)'>{html.escape(t)}</span> " for t in s["tags"])
        detail = head(f"{s['name']} · Shared Space")
        detail += f"""<p><a href="/">&larr; All projects</a></p>
<article class="sp" style="margin-top:.4rem">
  <h1 style="font-size:1.35rem;margin-bottom:.15rem">{html.escape(s['name'])}
    <span class="pill {html.escape(s['status'])}" style="margin-left:.4rem;font-size:.78rem">{html.escape(s['status'])}</span>
  </h1>
  <p style="margin:0;color:var(--pico-muted-color);font-size:.82rem">
    {taghtml} <span>updated {html.escape(s['updated'])}</span>
  </p>
</article>
{s['body']}
"""
        detail += foot()
        write(os.path.join(ROOT, s["slug"], "index.html"), detail)

    print(f"Wrote hub ({len(spaces)} tiles) + {len(spaces)} detail page(s) using {PICO}")

if __name__ == "__main__":
    main()