#!/usr/bin/env python3
"""Shared Space hub generator (Pico.css theme).
Reads project.md manifests -> hub index.html + per-project detail pages.
Uses the vendored Pico.css kit (assets/pico.min.css); semantic markup with a
tiny layer of classes for tiles/pills. Never hand-edit generated HTML.
"""
import os, re, glob, html

ROOT = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(ROOT, "index.html")
PICO_HREF = "/assets/pico.min.css"

# Small layer on top of Pico — only layout bits a classless kit can't infer.
# Kept minimal on purpose; don't fight the kit.
CUSTOM_CSS = """
/* Project title tile on the hub */
a.tile { display: block; }
a.tile { background: var(--pico-card-background-color);
  padding: var(--pico-block-spacing-vertical) var(--pico-block-spacing-horizontal);
  border-radius: var(--pico-border-radius);
  transition: transform .08s ease, box-shadow .12s ease; }
a.tile:active { transform: scale(.99); }
a.tile .title { font-size: 1.05rem; font-weight: 600; }
a.tile .title .arrow { margin-left: auto; opacity: .5; }
a.tile .about { display: block; margin-top: .35rem;
  color: var(--pico-muted-color); font-size: .88rem; }
a.tile .row { display: block; margin-top: .5rem; }

/* Status pill */
.pill { display: inline-block; font-size: .72rem; font-weight: 600;
  padding: 2px 9px; border-radius: 999px; color: #fff; vertical-align: middle; }
.pill.active  { background: #2f9e69; }
.pill.ongoing { background: #2f9e69; }
.pill.parked  { background: #c9a227; }
.pill.done    { background: #6c7686; }

/* Tags use a muted, non-accent pill */
.tag { display: inline-block; font-size: .7rem; font-weight: 600;
  padding: 1px 8px; border-radius: 999px; vertical-align: middle;
  background: var(--pico-secondary-background);
  color: var(--pico-secondary-inverse); }
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

def inline(text):
    """Escape then apply inline md: `code`, **bold**, checkbox glyphs."""
    s = html.escape(text)
    s = s.replace("[ ]", "<code>☐</code>").replace("[x]", "☑").replace("[X]", "☑")
    s = re.sub(r"`([^`]+)`", r"<code>\1</code>", s)
    s = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", s)
    return s

def md_to_html(text, skip_first_h1=False):
    """Minimal md -> html for manifest body (headings, bullets, bold, code).
    Properly escapes content so <slug> or similar aren't eaten as tags."""
    out = []
    in_ul = False
    first = skip_first_h1  # if True, drop a leading '# Heading' (dup of card title)
    for line in text.splitlines():
        s = line.rstrip()
        if not s.strip():
            if in_ul:
                out.append("</ul>"); in_ul = False
            continue
        st = s.strip()
        if st.startswith("# ") and first:
            first = False
            continue  # skip the manifest's own title; card already shows it
        if st.startswith("### "):
            if in_ul: out.append("</ul>"); in_ul = False
            out.append(f"<h4>{inline(st[4:])}</h4>")
        elif st.startswith("## "):
            if in_ul: out.append("</ul>"); in_ul = False
            out.append(f"<h3>{inline(st[3:])}</h3>")
        elif st.startswith("# "):
            if in_ul: out.append("</ul>"); in_ul = False
            out.append(f"<h2>{inline(st[2:])}</h2>")
        elif st.startswith("- "):
            if not in_ul:
                out.append("<ul>"); in_ul = True
            out.append(f"<li>{inline(st[2:])}</li>")
        else:
            if in_ul: out.append("</ul>"); in_ul = False
            out.append(f"<p>{inline(s)}</p>")
    if in_ul:
        out.append("</ul>")
    return "\n".join(out)

def about_line(body_text, n=130):
    """First non-heading, non-list line as the tile's blurb (unescaped -> caller)."""
    seen_title = False
    for line in body_text.splitlines():
        st = line.strip()
        if not st:
            continue
        if st.startswith("# "):
            seen_title = True
            continue
        if st.startswith(("#", "##", "###", "-")):
            continue
        if seen_title or True:
            return st[:n]
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
<link rel="stylesheet" href="{PICO_HREF}">
<style>{CUSTOM_CSS}</style>
</head><body>
<main class="container">
"""

def foot():
    return f"""<div class="footer" style="margin-top:2.5rem;text-align:center;color:var(--pico-muted-color);font-size:.8rem">
  Shared space · generated {stamp()} · <a href="https://github.com/andrewsouthard/shared-space">repo</a>
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
            "body": md_to_html(body, skip_first_h1=True),
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
            taghtml = "".join(f"<span class='tag'>{html.escape(t)}</span> " for t in s["tags"])
            about = html.escape(about_line(s["body_text"]))
            tile_html.append(f"""
  <a class="tile" href="/{s['slug']}/">
    <span class="title">{html.escape(s['name'])}
      <span class="pill {html.escape(s['status'])}" style="margin-left:.4rem">{html.escape(s['status'])}</span>
      <span class="arrow">›</span>
    </span>
    <span class="about">{about}</span>
    <span class="row">{taghtml}<span class="pill" style="background:var(--pico-muted-border-color);color:var(--pico-muted-color);margin-left:.4rem">updated {html.escape(s['updated'])}</span></span>
  </a>""")
        tiles = "\n".join(tile_html)

    hub = head("Shared Space · Andrew")
    hub += f"""<h1 style="margin-bottom:.25rem">Shared Space</h1>
<p style="color:var(--pico-muted-color);margin-bottom:1.5rem">Updated {stamp()} · {len(spaces)} project(s) · tap one to open it</p>
{tiles}
"""
    hub += foot()
    write(OUT, hub)

    # ---- Detail pages ----
    for s in spaces:
        taghtml = "".join(f"<span class='tag'>{html.escape(t)}</span> " for t in s["tags"])
        detail = head(f"{s['name']} · Shared Space")
        detail += f"""<p><a href="/">&larr; All projects</a></p>
<article>
  <h1 style="margin:.25rem 0 .1rem">{html.escape(s['name'])}
    <span class="pill {html.escape(s['status'])}" style="margin-left:.4rem;font-size:.78rem">{html.escape(s['status'])}</span>
  </h1>
  <p style="margin:0;color:var(--pico-muted-color);font-size:.85rem">
    {taghtml}<span style="margin-left:.35rem">updated {html.escape(s['updated'])}</span>
  </p>
</article>
{s['body']}
"""
        detail += foot()
        write(os.path.join(ROOT, s["slug"], "index.html"), detail)

    print(f"Wrote hub ({len(spaces)} tiles) + {len(spaces)} detail page(s) using Pico")

if __name__ == "__main__":
    main()