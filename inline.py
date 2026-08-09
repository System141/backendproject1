# -*- coding: utf-8 -*-
"""Builds self-contained copies of each page: CSS, JS and images inlined as
data URIs so a single .html file renders correctly with nothing beside it."""
import base64, os, re, mimetypes

SRC = "."
OUT = "standalone"
os.makedirs(OUT, exist_ok=True)

css = open(f"{SRC}/assets/css/style.css", encoding="utf-8").read()
js = open(f"{SRC}/assets/js/main.js", encoding="utf-8").read()

cache = {}
def data_uri(path):
    if path not in cache:
        mime = mimetypes.guess_type(path)[0] or "application/octet-stream"
        with open(path, "rb") as f:
            cache[path] = f"data:{mime};base64,{base64.b64encode(f.read()).decode()}"
    return cache[path]

for page in ["index.html", "credits.html", "auctions.html", "auth.html"]:
    html = open(f"{SRC}/{page}", encoding="utf-8").read()

    # srcset/sizes/preload rely on separate files — drop them, keep the full-size src
    html = re.sub(r'\s+srcset="[^"]*"', "", html)
    html = re.sub(r'\s+sizes="[^"]*"', "", html)
    html = re.sub(r'<link rel="preload"[^>]*>\s*', "", html)
    html = re.sub(r'<link rel="icon"[^>]*>\s*', "", html)
    html = re.sub(r'<link rel="apple-touch-icon"[^>]*>\s*', "", html)

    # images -> data URIs
    def sub_img(m):
        p = os.path.join(SRC, m.group(1))
        return f'src="{data_uri(p)}"' if os.path.exists(p) else m.group(0)
    html = re.sub(r'src="(assets/img/[^"]+)"', sub_img, html)

    # keep navigation working between the standalone copies
    for p in ["index", "credits", "auctions", "auth"]:
        html = html.replace(f'href="{p}.html', f'href="{p}-tekdosya.html')

    # stylesheet + script -> inline
    html = html.replace('<link rel="stylesheet" href="assets/css/style.css">',
                        f"<style>\n{css}\n</style>")
    html = html.replace('<script src="assets/js/main.js" defer></script>',
                        f"<script>\n{js}\n</script>")

    name = page.replace(".html", "-tekdosya.html")
    with open(f"{OUT}/{name}", "w", encoding="utf-8") as f:
        f.write(html)
    print(name, round(len(html) / 1024), "KB")
