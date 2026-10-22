#!/usr/bin/env python3
"""Shared Space hub generator.
Reads project.md manifests -> hub index.html + per-project detail pages.
Phone-friendly, self-contained, dark/light. Never hand-edit generated HTML.
"""
import os, re, glob, html

ROOT = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(ROOT, "index.html")

STATUS_COLORS = {
    "active": "#2d9e4f", "ongoing": "#2d9e4f",
    "parked": "#c99700", "done": "#5f6b7a",
}

CSS = """
:root {{ color-scheme: light dark; }}
* {{ box-sizing: border-box; margin:0; padding:0; }}
html {{ scroll-behavior: smooth; }}
body {{
  font-family: system-ui, -apple-system, "Segoe UI", sans-serif;
  background:#f6f7f9; color:#1a1a1a; line-height:1.5; max-width:760px;
  margin:0 auto; padding:20px 18px 60px;
}}
h1 {{ font-size:1.4rem; font-weight:700; }}
h3 {{ font-size:.98rem; font-weight:600; margin:16px 0 4px; }}
.sub {{ color:#666; font-size:.85rem; margin:6px 0; }}
.back {{ display:inline-block; margin:0 0 12px; color:#0f7a59; font-size:.85rem;
  font-weight:600; text-decoration:none; }}
.tile {{ display:block; text-decoration:none; border:1px solid #d9dce2;
  border-radius:11px; background:#fff; padding:13px 14px; margin:8px 0; }}
.tile-top {{ display:flex; align-items:center; gap:10px; }}
.dot {{ width:10px; height:10px; border-radius:50%; flex:0 0 auto; }}
.t-name {{ font-weight:600; font-size:1.02rem; flex:1; }}
.pill {{ font-size:.68rem; background:#e8ecf3; color:#516e9c; border-radius:10px; padding:1px 8px; }}
.t-arrow {{ color:#888; font-weight:700; }}
.t-about {{ display:block; color:#555; font-size:.85rem; margin-top:8px; line-height:1.4; }}
.tag {{ display:inline-block; font-size:.7rem; background:#e4e9f2; color:#4a6a9c;
  border-radius:9px; padding:1px 8px; margin:0 4px 0 0; }}
.card {{ border:1px solid #d9dce2; border-radius:11px; background:#fff; padding:16px; margin:8px 0; }}
.card h3 {{ margin-top:0; }}
.card h3, .card h4 {{ font-size:.95rem; color:#444; font-weight:600; }}
.card ul {{ margin:6px 0; padding-left:18px; }}
.card li {{ font-size:.9rem; margin:3px 0; }}
.card p {{ font-size:.9rem; margin:6px 0; }}
.sec {{ margin:14px 0; }}
.sec h5 {{ font-size:.85rem; font-weight:600; color:#555; margin:0 0 6px;
  text-transform:uppercase; letter-spacing:.4px; }}
.empty {{ padding:28px; color:#666; text-align:center; }}
.foot {{ margin-top:30px; color:#888; font-size:.75rem; text-align:center; }}
::-webkit-tap-highlight-color {{ transparent; }}
@media (prefers-color-scheme: dark) {{
  body {{ background:#14161a; color:#e8e8e8; }}
  .tile, .card {{ background:#1a1d23; border-color:#2b3038; }}
  .t-about {{ color:#aab; }} .pill {{ background:#2a3040; color:#8aa4d8; }}
  .tag {{ background:#2a3040; color:#8aa4d8; }}
  .card h3, .card h4, .sec h5 {{ color:#aeb4bf; }}
  .sub {{ color:#a8adb8; }} .foot {{ color:#7d828d; }} .t-arrow {{ color:#8a8f9a; }}
  .empty {{ color:#9aa0ab; }} .back {{ color:#5fd7a3; }}
}}
"""

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
    for line in text.splitlines():
        s = line.rstrip()
        if not s.strip():
            continue
        s = s.replace("[ ]", "☐").replace("[x]", "☑").replace("[X]", "☑")
        s = re.sub(r"`([^`]+)`", r"<code>\1</code>", s)
        s = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", s)
        st = s.strip()
        if st.startswith("### "):
            out.append(f"<h4>{html.escape(st[4:])}</h4>")
        elif st.startswith("## "):
            out.append(f"<h4>{html.escape(st[3:])}</h4>")
        elif st.startswith("# "):
            out.append(f"<h4>{html.escape(st[2:])}</h4>")
        elif st.startswith("- "):
            out.append(f"<li>{st[2:]}</li>")
        else:
            out.append(f"<p>{s}</p>")
    return "\n".join(out)

def about_line(body_text, n=140):
    """First non-heading, non-list line as the tile's about blurb."""
    for line in body_text.splitlines():
        st = line.strip()
        if st and not st.startswith(("#", "-", "##")) and not re.match(r"^[A-Z][a-z]+$", st):
            return html.escape(st[:n])
    return ""

def write(path, content):
    tmp = path + ".tmp"
    with open(tmp, "w") as f:
        f.write(content)
    os.replace(tmp, path)

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

    now = __import__("datetime").datetime.now().strftime("%b %d %Y, %I:%M %p")

    # ---- Hub (tiles linking to detail pages) ----
    if not spaces:
        tiles = "<div class='empty'><p>No project spaces yet.</p><p>When you tell me something belongs in the shared space, I create a project here.</p></div>"
    else:
        tile_html = []
        for s in spaces:
            sc = STATUS_COLORS.get(s["status"], "#5f6b7a")
            taghtml = "".join(f"<span class='tag'>{html.escape(t)}</span>" for t in s["tags"])
            about = about_line(s["body_text"])
            tile_html.append(f"""
  <a class="tile" href="/{s['slug']}/">
    <span class="tile-top">
      <span class="dot" style="background:{sc}"></span>
      <span class="t-name">{html.escape(s['name'])}</span>
      <span class="pill">{html.escape(s['status'])}</span>
      <span class="t-arrow">›</span>
    </span>
    <span class="t-about">{about}</span>
    <span style="display:block;margin-top:6px">{taghtml}<span class="meta" style="color:#888;font-size:.72rem;margin-left:6px">updated {html.escape(s['updated'])}</span></span>
  </a>""")
        tiles = "\n".join(tile_html)

    hub = f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Shared Space · Andrew</title><style>{CSS}</style></head><body>
<h1>Shared Space</h1>
<div class="sub">Updated {now} · {len(spaces)} project space(s) · tap one to open it</div>
<h3>Projects</h3>
{tiles}
<div class="foot">Shared space · generated from project notes · regenerated automatically · <a href="https://github.com/andrewsouthard/shared-space">repo</a></div>
</body></html>"""
    write(OUT, hub)

    # ---- Detail pages ----
    for s in spaces:
        sc = STATUS_COLORS.get(s["status"], "#5f6b7a")
        taghtml = "".join(f"<span class='tag'>{html.escape(t)}</span>" for t in s["tags"])
        detail = f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(s['name'])} · Shared Space</title><style>{CSS}</style></head><body>
<a class="back" href="/">← All projects</a>
<div class="card">
  <h1 style="font-size:1.25rem">{html.escape(s['name'])}
    <span class="dot" style="background:{sc};display:inline-block;width:12px;height:12px;border-radius:50%"></span>
  </h1>
  <div style="margin-top:6px">{taghtml}<span class="sub" style="color:#888;font-size:.75rem">· updated {html.escape(s['updated'])} · status {html.escape(s['status'])}</span></div>
</div>
{s['body']}
<div class="foot">Part of Andrew's shared space · edit ~/repos/shared-space/{s['slug']}/project.md and rerun generate.py</div>
</body></html>"""
        dpath = os.path.join(ROOT, s["slug"], "index.html")
        write(dpath, detail)

    print(f"Wrote hub ({len(spaces)} tiles) + {len(spaces)} detail page(s)")

if __name__ == "__main__":
    main()