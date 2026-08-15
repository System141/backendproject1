# -*- coding: utf-8 -*-
"""Generates the BidMont static site (shared shell + 4 pages)."""
import os

# ---------------------------------------------------------------- icons ----
S = 'xmlns="http://www.w3.org/2000/svg" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"'
P = {
 "shield": '<path d="M12 3l7.5 3v5.6c0 4.5-3.1 8-7.5 9.4-4.4-1.4-7.5-4.9-7.5-9.4V6z"/><path d="m9 12 2 2 4-4"/>',
 "lock": '<rect x="4.5" y="10" width="15" height="10" rx="2.2"/><path d="M8 10V7.5a4 4 0 0 1 8 0V10"/>',
 "clock": '<circle cx="12" cy="12" r="8.5"/><path d="M12 7.2V12l3.2 2"/>',
 "car": '<path d="M3.2 13.6 5 8.7A2.5 2.5 0 0 1 7.4 7h9.2a2.5 2.5 0 0 1 2.4 1.7l1.8 4.9v4a1 1 0 0 1-1 1h-1.6a1 1 0 0 1-1-1v-.6H6.8v.6a1 1 0 0 1-1 1H4.2a1 1 0 0 1-1-1z"/><path d="M3.4 13.6h17.2"/><path d="M7.4 15.8h.8M15.8 15.8h.8"/>',
 "bike": '<circle cx="5.6" cy="16.8" r="3.4"/><circle cx="18.4" cy="16.8" r="3.4"/><path d="M5.6 16.8h4l4-6.8h-3M13.6 10l3 6.8M14.6 6.4h3l1.4 3.6"/>',
 "crane": '<path d="M3.5 20.5h17"/><path d="M6 20.5v-4.2h6.4v4.2"/><path d="m12.4 16.3-4.2-9.8h3.1l3.4 7.4"/><path d="M14.7 6.5h4.1l1.9 4.6"/>',
 "home": '<path d="m3.8 11 8.2-7.2 8.2 7.2"/><path d="M6.2 9.9v10.6h11.6V9.9"/><path d="M10 20.5v-5.6h4v5.6"/>',
 "boat": '<path d="M3 17.2h18l-2.3 4.1H5.3z"/><path d="M6.3 17.2V8.9h8.9l4.2 8.3"/><path d="M11.2 8.9V3.6"/>',
 "gem": '<path d="M6.4 3.4h11.2l3.2 5.9L12 20.6 1.2 9.3z"/><path d="M1.4 9.3h21.2"/>',
 "tractor": '<circle cx="7" cy="17.6" r="3.2"/><circle cx="18" cy="18" r="2.6"/><path d="M4.2 17V11h6.3l1.1-4.2h4V18"/><path d="M10.5 11h5.1"/>',
 "monitor": '<rect x="3" y="4.5" width="18" height="11.6" rx="2"/><path d="M9.2 20.4h5.6M12 16.1v4.3"/>',
 "grid": '<circle cx="8" cy="8" r="2.6"/><circle cx="16" cy="8" r="2.6"/><circle cx="8" cy="16" r="2.6"/><circle cx="16" cy="16" r="2.6"/>',
 "search": '<circle cx="11" cy="11" r="7"/><path d="m20.5 20.5-4.2-4.2"/>',
 "sliders": '<path d="M4 7h8M16.5 7H20M4 12h3.5M12 12h8M4 17h8M16.5 17H20"/><circle cx="14.2" cy="7" r="2.1"/><circle cx="9.7" cy="12" r="2.1"/><circle cx="14.2" cy="17" r="2.1"/>',
 "sort": '<path d="M7 4.5v15M4 8.2 7 4.5l3 3.7M17 19.5v-15M14 15.8l3 3.7 3-3.7"/>',
 "heart": '<path d="M20.6 8.7c0 4.5-8.6 10.2-8.6 10.2S3.4 13.2 3.4 8.7a4.5 4.5 0 0 1 8.6-1.8 4.5 4.5 0 0 1 8.6 1.8Z"/>',
 "arrow": '<path d="M4.5 12h14.5"/><path d="m13 6.2 5.8 5.8-5.8 5.8"/>',
 "chev-d": '<path d="m6.5 9.5 5.5 5.5 5.5-5.5"/>',
 "chev-r": '<path d="m9.5 5.5 6.5 6.5-6.5 6.5"/>',
 "check": '<path d="m5 12.6 4.8 4.8L19 6.8"/>',
 "x": '<path d="M6.2 6.2 17.8 17.8M17.8 6.2 6.2 17.8"/>',
 "menu": '<path d="M4 7.5h16M4 12h16M4 16.5h16"/>',
 "mail": '<rect x="3" y="5" width="18" height="14" rx="2.2"/><path d="m3.8 7.2 8.2 5.8 8.2-5.8"/>',
 "user": '<circle cx="12" cy="8.2" r="3.6"/><path d="M4.8 20c1.3-3.4 3.9-5.1 7.2-5.1s5.9 1.7 7.2 5.1"/>',
 "userplus": '<circle cx="10" cy="8.2" r="3.6"/><path d="M3.2 20c1.2-3.3 3.5-4.9 6.8-4.9 1.1 0 2 .2 2.9.5"/><path d="M18 13.5v6M15 16.5h6"/>',
 "phone": '<path d="M6.4 3.4h2.9l1.5 3.9-2 1.5a12 12 0 0 0 6.4 6.4l1.5-2 3.9 1.5v2.9a2 2 0 0 1-2.2 2A16.6 16.6 0 0 1 4.4 5.6a2 2 0 0 1 2-2.2Z"/>',
 "eye": '<path d="M2.6 12S6.1 5.8 12 5.8 21.4 12 21.4 12 17.9 18.2 12 18.2 2.6 12 2.6 12Z"/><circle cx="12" cy="12" r="3"/>',
 "eyeoff": '<path d="M9.9 5.9A9.6 9.6 0 0 1 12 5.8c5.9 0 9.4 6.2 9.4 6.2a17 17 0 0 1-3 3.9M6.4 7.5A16.7 16.7 0 0 0 2.6 12S6.1 18.2 12 18.2c1.5 0 2.8-.4 4-1"/><path d="M4 4l16 16"/>',
 "card": '<rect x="3" y="5" width="18" height="14" rx="2.2"/><path d="M3 9.8h18M6.6 14.8h3.2"/>',
 "zap": '<path d="M13.2 3 5.6 13.6h5.4l-1 7.4 7.4-10.6h-5.3z"/>',
 "headset": '<path d="M4.4 14.4v-2.2a7.6 7.6 0 0 1 15.2 0v2.2"/><path d="M4.4 14h2.9v5.6H5.9A1.5 1.5 0 0 1 4.4 18z"/><path d="M19.6 14h-2.9v5.6h1.4a1.5 1.5 0 0 0 1.5-1.5z"/>',
 "wallet": '<path d="M3.2 8.2V7A2.2 2.2 0 0 1 5.4 4.8h11.2V8"/><rect x="3.2" y="8" width="17.6" height="11.2" rx="2.4"/><circle cx="16.8" cy="13.6" r="1.3"/>',
 "star": '<path d="m12 3.6 2.7 5.5 6 .9-4.3 4.2 1 6-5.4-2.8-5.4 2.8 1-6L3.3 10l6-.9z"/>',
 "users": '<circle cx="9.2" cy="8.4" r="3.4"/><path d="M2.6 19.8c1-3.2 3.4-4.8 6.6-4.8s5.6 1.6 6.6 4.8"/><path d="M16.6 5.6a3.4 3.4 0 0 1 0 5.4M18.4 15.4c1.9.7 3 2.1 3.5 4.4"/>',
 "package": '<path d="M3.2 7.5 12 3.2l8.8 4.3v9L12 20.8l-8.8-4.3z"/><path d="m3.2 7.5 8.8 4.4 8.8-4.4M12 11.9v8.9"/>',
 "truck": '<path d="M2.8 6.8h11.4v9.6H2.8z"/><path d="M14.2 10.2h3.5l3.1 3.5v2.7h-6.6"/><circle cx="7" cy="18.4" r="2"/><circle cx="17.6" cy="18.4" r="2"/>',
 "globe": '<circle cx="12" cy="12" r="8.6"/><path d="M3.6 12h16.8"/><path d="M12 3.4a14 14 0 0 1 0 17.2 14 14 0 0 1 0-17.2Z"/>',
 "idcard": '<rect x="3" y="5" width="18" height="14" rx="2.2"/><circle cx="8.6" cy="10.8" r="2"/><path d="M5.6 16c.6-1.7 1.6-2.5 3-2.5s2.4.8 3 2.5"/><path d="M14.6 10.2h4M14.6 13.6h4"/>',
 "selfie": '<circle cx="12" cy="12" r="8.6"/><circle cx="12" cy="10.2" r="2.6"/><path d="M7.2 18.2c1-2.4 2.6-3.6 4.8-3.6s3.8 1.2 4.8 3.6"/>',
 "doc": '<path d="M14 3.2v5.2h5.2"/><path d="M14 3.2H6.6a1.6 1.6 0 0 0-1.6 1.6v14.4a1.6 1.6 0 0 0 1.6 1.6h10.8a1.6 1.6 0 0 0 1.6-1.6V8.4z"/><path d="M8.4 13h7M8.4 16.6h5"/>',
 "coins": '<ellipse cx="12" cy="6.2" rx="7.4" ry="3"/><path d="M4.6 6.2v5.6c0 1.7 3.3 3 7.4 3s7.4-1.3 7.4-3V6.2"/><path d="M4.6 11.8v5.6c0 1.7 3.3 3 7.4 3s7.4-1.3 7.4-3v-5.6"/>',
 "bank": '<path d="M3.4 9.4 12 4.2l8.6 5.2"/><path d="M5.6 9.8v9M10 9.8v9M14 9.8v9M18.4 9.8v9"/><path d="M3.4 19.4h17.2"/>',
 "target": '<circle cx="12" cy="12" r="8.4"/><circle cx="12" cy="12" r="4.2"/><circle cx="12" cy="12" r=".6"/>',
 "handshake": '<path d="m11 7.6 2.3-2.1 6.1 4.2v6.1"/><path d="M4.6 9.7 9.4 5.5l3.1 2.1-3.6 3.2a1.6 1.6 0 0 0 2.2 2.3l1.5-1.3 4.2 3.7"/><path d="M4.6 9.7v6.4l3.2 2.6"/>',
 "bell": '<path d="M6 8a6 6 0 0 1 12 0c0 3.4 1 5.2 2 6.4a1 1 0 0 1-.8 1.6H4.8A1 1 0 0 1 4 14.4C5 13.2 6 11.4 6 8Z"/><path d="M9.5 18a2.5 2.5 0 0 0 5 0"/>',
}
FILLED = {
 "facebook": '<path d="M13.5 21v-7h2.4l.4-2.9h-2.8V9.3c0-.8.2-1.4 1.4-1.4h1.5V5.3c-.3 0-1.2-.1-2.2-.1-2.2 0-3.7 1.4-3.7 3.8v2.1H8V14h2.5v7z"/>',
 "instagram": '<path d="M12 2.2c-2.7 0-3 0-4 .1-1.1 0-1.8.2-2.4.5a4.9 4.9 0 0 0-1.8 1.2A4.9 4.9 0 0 0 2.6 5.8c-.3.6-.4 1.3-.5 2.4-.1 1-.1 1.3-.1 4s0 3 .1 4c0 1.1.2 1.8.5 2.4.3.7.6 1.3 1.2 1.8a4.9 4.9 0 0 0 1.8 1.2c.6.3 1.3.4 2.4.5 1 .1 1.3.1 4 .1s3 0 4-.1c1.1 0 1.8-.2 2.4-.5a5.1 5.1 0 0 0 2.9-2.9c.3-.6.4-1.3.5-2.4.1-1 .1-1.3.1-4s0-3-.1-4c0-1.1-.2-1.8-.5-2.4a4.9 4.9 0 0 0-1.2-1.8 4.9 4.9 0 0 0-1.8-1.2c-.6-.3-1.3-.4-2.4-.5-1-.1-1.3-.1-4-.1zm0 1.8c2.7 0 3 0 4 .1.9 0 1.4.2 1.8.3.4.2.7.4 1 .7.3.3.5.6.7 1 .1.4.3.9.3 1.8.1 1 .1 1.3.1 4s0 3-.1 4c0 .9-.2 1.4-.3 1.8-.2.4-.4.7-.7 1-.3.3-.6.5-1 .7-.4.1-.9.3-1.8.3-1 .1-1.3.1-4 .1s-3 0-4-.1c-.9 0-1.4-.2-1.8-.3a2.7 2.7 0 0 1-1-.7 2.7 2.7 0 0 1-.7-1c-.1-.4-.3-.9-.3-1.8-.1-1-.1-1.3-.1-4s0-3 .1-4c0-.9.2-1.4.3-1.8.2-.4.4-.7.7-1 .3-.3.6-.5 1-.7.4-.1.9-.3 1.8-.3 1-.1 1.3-.1 4-.1z"/><path d="M12 15.3a3.3 3.3 0 1 1 0-6.6 3.3 3.3 0 0 1 0 6.6zm0-8.4a5.1 5.1 0 1 0 0 10.2 5.1 5.1 0 0 0 0-10.2z"/><circle cx="17.3" cy="6.7" r="1.2"/>',
 "linkedin": '<path d="M6.9 8.6H4V21h2.9zM5.4 3.4a1.7 1.7 0 1 0 0 3.5 1.7 1.7 0 0 0 0-3.5zM20 13.8c0-3.2-1.7-4.8-4-4.8a3.4 3.4 0 0 0-3.1 1.7V8.6H10V21h2.9v-6.6c0-1.7.4-3.4 2.5-3.4s2 2 2 3.5V21H20z"/>',
 "youtube": '<path d="M21.6 7.3s-.2-1.4-.8-2.1c-.8-.8-1.7-.8-2.1-.9C15.9 4 12 4 12 4s-3.9 0-6.7.3c-.4 0-1.3 0-2.1.9-.6.7-.8 2.1-.8 2.1S2.2 9 2.2 10.6v1.6c0 1.7.2 3.3.2 3.3s.2 1.4.8 2.1c.8.8 1.8.8 2.2.9 1.6.2 6.6.3 6.6.3s3.9 0 6.7-.3c.4 0 1.3-.1 2.1-.9.6-.7.8-2.1.8-2.1s.2-1.6.2-3.3v-1.6c0-1.7-.2-3.3-.2-3.3zM9.9 14.3V8.7l5.2 2.8z"/>',
}
GOOGLE = ('<svg viewBox="0 0 24 24" width="17" height="17" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">'
 '<path fill="#4285F4" d="M23 12.3c0-.8-.1-1.6-.2-2.3H12v4.5h6.2a5.3 5.3 0 0 1-2.3 3.5v2.9h3.7c2.2-2 3.4-5 3.4-8.6z"/>'
 '<path fill="#34A853" d="M12 24c3.1 0 5.7-1 7.6-2.8l-3.7-2.9c-1 .7-2.3 1.1-3.9 1.1-3 0-5.5-2-6.4-4.7H1.8v3C3.7 21.4 7.6 24 12 24z"/>'
 '<path fill="#FBBC05" d="M5.6 14.7a7.2 7.2 0 0 1 0-4.6v-3H1.8a12 12 0 0 0 0 10.6z"/>'
 '<path fill="#EA4335" d="M12 4.7c1.7 0 3.2.6 4.4 1.7l3.3-3.3C17.7 1.2 15.1 0 12 0 7.6 0 3.7 2.6 1.8 6.1l3.8 3a7.1 7.1 0 0 1 6.4-4.4z"/></svg>')


def i(name, size=18, cls=""):
    c = f' class="{cls}"' if cls else ""
    if name in FILLED:
        return f'<svg{c} viewBox="0 0 24 24" width="{size}" height="{size}" fill="currentColor" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">{FILLED[name]}</svg>'
    return f'<svg{c} viewBox="0 0 24 24" width="{size}" height="{size}" {S} aria-hidden="true">{P[name]}</svg>'


LOGO = ('<img class="logo__img" src="assets/img/logo.webp" '
        'srcset="assets/img/logo-sm.webp 436w, assets/img/logo.webp 871w" sizes="152px" '
        'alt="BidMont" width="871" height="178" decoding="async">')


def logo(cls=""):
    return f'<a class="logo{(" " + cls) if cls else ""}" href="index.html">{LOGO}</a>'


# ---------------------------------------------------------------- shell ----
NAV = [
    ("How It Works", "index.html#how", "how"),
    ("Buy Credits", "credits.html", "credits"),
    ("Auctions", "auctions.html", "auctions"),
    ("Categories", "auctions.html#categories", "categories"),
    ("For Partners", "index.html#partners", "partners"),
    ("Resources", "credits.html#faq", "resources"),
]
DROPDOWN = {"categories", "resources"}


def header(active):
    items = ""
    drawer_items = ""
    for label, href, key in NAV:
        cur = ' aria-current="page"' if key == active else ""
        caret = i("chev-d", 14) if key in DROPDOWN else ""
        items += f'<li><a href="{href}"{cur}>{label}{caret}</a></li>'
        drawer_items += f'<a href="{href}"{cur}>{label}</a>'
    return f'''<header class="hdr">
<div class="wrap hdr__in">
{logo()}
<nav class="nav" aria-label="Main"><ul>{items}</ul></nav>
<div class="notif-wrap is-hidden" id="notif-wrap">
<button class="fav" type="button" id="notif-bell" aria-haspopup="true" aria-expanded="false" aria-label="Notifications">{i("bell", 18)}<span class="notif-badge is-hidden" id="notif-badge">0</span></button>
<div class="notif-dropdown is-hidden" id="notif-dropdown" role="menu" aria-label="Notifications"><ul id="notif-dropdown-list"><li class="tiny">No notifications.</li></ul></div>
</div>
<div class="hdr__actions">
<a class="btn btn--outline btn--sm" href="auth.html">Log in</a>
<a class="btn btn--primary btn--sm" href="auth.html#create">Sign up</a>
</div>
<button class="burger" type="button" data-drawer-open aria-label="Open menu" aria-expanded="false" aria-controls="mobile-menu">{i("menu", 22)}</button>
</div>
</header>

<div class="drawer" id="mobile-menu" data-drawer>
<div class="drawer__bg" data-drawer-close></div>
<div class="drawer__panel" role="dialog" aria-modal="true" aria-label="Menu">
<div class="drawer__top">{logo()}<button class="burger" type="button" data-drawer-close aria-label="Close menu">{i("x", 22)}</button></div>
<nav class="drawer__nav" aria-label="Mobile">{drawer_items}</nav>
<div class="drawer__foot">
<a class="btn btn--outline btn--block" href="auth.html">Log in</a>
<a class="btn btn--primary btn--block" href="auth.html#create">Sign up</a>
</div>
</div>
</div>'''


FOOT_COLS = [
    ("Marketplace", [("Auctions", "auctions.html"), ("Categories", "auctions.html#categories"),
                     ("How It Works", "index.html#how"), ("Buy Credits", "credits.html")]),
    ("For Partners", [("Partner Program", "index.html#partners"), ("Sell with Us", "index.html#partners"),
                      ("Resources", "credits.html#faq"), ("Success Stories", "index.html#partners")]),
    ("Company", [("About Us", "#"), ("Careers", "#"), ("News", "#"), ("Contact Us", "support.html")]),
    ("Support", [("Help Center", "credits.html#faq"), ("Terms of Use", "#"),
                 ("Privacy Policy", "#"), ("Cookie Policy", "#")]),
]


def footer():
    cols = ""
    for title, links in FOOT_COLS:
        ls = "".join(f'<li><a href="{h}">{t}</a></li>' for t, h in links)
        cols += f'<div class="ftr__col"><h4>{title}</h4><ul>{ls}</ul></div>'
    socials = "".join(
        f'<a href="#" aria-label="{n.capitalize()}">{i(n, 17)}</a>'
        for n in ("instagram", "facebook", "linkedin", "youtube"))
    return f'''<footer class="ftr">
<div class="wrap">
<div class="ftr__grid">
<div class="ftr__about">
{logo()}
<p>Buy verified credits to unlock access to verified partner auctions worldwide.</p>
<div class="socials">{socials}</div>
</div>
{cols}
</div>
<div class="ftr__bar">
<p>&copy; 2024 BidMont. All rights reserved.</p>
<div class="ftr__locale">
<label class="select"><span class="sr-only">Language</span><select><option>English</option><option>Türkçe</option><option>Deutsch</option></select></label>
<label class="select"><span class="sr-only">Currency</span><select><option>EUR (€)</option><option>USD ($)</option><option>TRY (₺)</option></select></label>
</div>
</div>
</div>
</footer>'''


def page(title, desc, active, body, body_class="", tabbar="", canonical="", preload=""):
    bc = f' class="{body_class}"' if body_class else ""
    return f'''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>{title}</title>
<meta name="description" content="{desc}">
<meta name="theme-color" content="#e11b22">
<link rel="canonical" href="https://bidmont.me/{canonical}">
<meta property="og:title" content="{title}">
<meta property="og:description" content="{desc}">
<meta property="og:type" content="website">
<meta property="og:site_name" content="BidMont">
<meta property="og:url" content="https://bidmont.me/{canonical}">
<meta name="twitter:card" content="summary_large_image">
<meta property="og:image" content="https://bidmont.me/assets/img/og-image.jpg">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta property="og:image:alt" content="Verified partner auctions on BidMont">
<link rel="icon" href="favicon.ico" sizes="any">
<link rel="icon" type="image/png" href="favicon-32.png" sizes="32x32">
<link rel="apple-touch-icon" href="apple-touch-icon.png">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="assets/css/style.css">{preload}
</head>
<body{bc}>
<a class="sr-only" href="#main">Skip to content</a>
{header(active)}
<main id="main" class="shell">
{body}
</main>
{footer()}
{tabbar}
<script src="assets/js/main.js" defer></script>
<script src="assets/js/api.js" defer></script>
</body>
</html>'''


# ------------------------------------------------------------ components ----
def trust(items=None, cls="trust"):
    items = items or [("shield", "Verified partners"), ("lock", "Secure &amp; transparent"), ("clock", "Instant access")]
    return f'<ul class="{cls}">' + "".join(f'<li>{i(n, 17)}{t}</li>' for n, t in items) + "</ul>"


PHOTOS = {"car", "villa", "excavator", "yacht", "generator", "watch", "cnc", "truck", "suv"}

AUCTIONS = [
    ("Copart", "2021 Porsche 911 Turbo S", "Cars", "€138,500", "2 Credits", "car", 16345, True),
    ("Ritchie Bros.", "CAT 320 Excavator", "Heavy Equipment", "€67,000", "3 Credits", "excavator", 108060, True),
    ("Savills Auctions", "Luxury Villa in Tivat", "Real Estate", "€1,250,000", "5 Credits", "villa", 225120, True),
    ("YachtWorld Auctions", "Sunseeker Manhattan 66", "Marine", "€890,000", "4 Credits", "yacht", 291060, True),
    ("Phillips", "Rolex Daytona 116500LN", "Luxury", "€18,500", "1 Credit", "watch", 22367, False),
    ("IronPlanet", "Caterpillar 350 kVA Generator", "Industrial Machinery", "€12,800", "2 Credits", "generator", 120780, False),
    ("Copart", "2019 Volvo FH540", "Trucks", "€42,000", "2 Credits", "truck", 191718, False),
    ("Ritchie Bros.", "Doosan CNC Lathe Puma 3100", "Industrial Machinery", "€31,200", "2 Credits", "cnc", 95040, False),
    ("Copart", "2020 Mercedes-Benz G63 AMG", "Cars", "€145,000", "2 Credits", "suv", 20829, False),
]


def auction_card(a, idx, lazy=True):
    partner, name, cat, price, credits, img, secs, verified = a
    badge = (f'<span class="pill pill--verified">{i("shield", 13)}Verified partner</span>' if verified
             else f'<span class="pill">{partner.upper()}</span>')
    load = ' loading="lazy" decoding="async"' if lazy else ' decoding="async"'
    src = (f'src="assets/img/{img}.webp" '
           f'srcset="assets/img/{img}-md.webp 600w, assets/img/{img}.webp 1200w" '
           f'sizes="(min-width:1000px) 380px, (min-width:600px) 46vw, 92vw"') if img in PHOTOS else f'src="assets/img/{img}.svg"'
    return f'''<article class="auction reveal">
<a class="auction__media" href="#" aria-label="{name}">
<img {src} alt="{name}" width="1200" height="810"{load}>
{badge}
</a>
<button class="fav" type="button" aria-pressed="false" aria-label="Save {name}">{i("heart", 16)}</button>
<div class="auction__body">
<p class="auction__partner">{partner.upper()}</p>
<h3 class="auction__title"><a href="#">{name}</a></h3>
<p class="auction__cat">{cat}</p>
<div class="auction__meta">
<div><span class="lbl">Current price</span><span class="val">{price}</span></div>
<div><span class="lbl">Ends in</span><span class="val val--sm" data-countdown="{secs}">--</span></div>
</div>
<div class="auction__foot"><span class="lbl">Access</span><span class="credits-tag">{credits}</span></div>
</div>
</article>'''


def faq_block(items, open_first=False):
    out = '<div class="faq">'
    for n, (q, a) in enumerate(items):
        op = " is-open" if (open_first and n == 0) else ""
        exp = "true" if op else "false"
        out += f'''<div class="faq__item{op}">
<button class="faq__q" type="button" aria-expanded="{exp}">{q}{i("chev-d", 18)}</button>
<div class="faq__a"><div><p>{a}</p></div></div>
</div>'''
    return out + "</div>"


def plan_card(name, desc, price, credits, feats, popular=False, cta="Get started"):
    tag = f'<span class="pill pill--pop plan__tag">Most popular</span>' if popular else ""
    fs = "".join(f'<li>{i("check", 15)}{f}</li>' for f in feats)
    btn = "btn--primary" if popular else "btn--outline"
    return f'''<div class="plan{' plan--pop' if popular else ''} reveal">{tag}
<div><h3 class="plan__name">{name}</h3><p class="plan__desc">{desc}</p></div>
<p class="plan__price"><b>{price}</b><span>{credits}</span></p>
<ul class="plan__feats">{fs}</ul>
<a class="btn {btn} btn--block" href="auth.html#create">{cta}</a>
</div>'''


def stats(items, extra=""):
    body = "".join(f'<div class="stat">{i(ic, 20, "muted")}<div><b>{v}</b><span>{l}</span></div></div>' for ic, v, l in items)
    return f'<div class="stats{extra}">{body}</div>'


def float_card(img, name, price, credits, cls):
    return f'''<div class="float-card {cls}">
<img src="assets/img/{img}-sm.webp" alt="" width="46" height="42" loading="lazy" decoding="async">
<div class="float-card__body">
<b>{name}</b><span>Partner auction</span>
<div class="row"><span class="price">{price}</span><span class="credits-tag">{credits}</span></div>
</div></div>'''


# ==================================================================== HOME ---
home_floats = (
    float_card("villa", "Luxury Villa in Tivat", "€1,250,000", "5 Credits", "float-card--a") +
    float_card("excavator", "CAT 320 Excavator", "€67,000", "3 Credits", "float-card--b") +
    float_card("car", "Porsche 911 Turbo S", "€138,500", "2 Credits", "float-card--c") +
    float_card("watch", "Rolex Daytona", "€18,500", "1 Credit", "float-card--d")
)

CATS = [("car", "Cars"), ("bike", "Motorcycles"), ("crane", "Heavy Equipment"), ("home", "Real Estate"),
        ("boat", "Boats"), ("gem", "Luxury"), ("tractor", "Industrial Machinery"), ("monitor", "Electronics")]

home_cats = "".join(f'<a class="cat" href="auctions.html">{i(ic, 22)}<span>{n}</span></a>' for ic, n in CATS)

HOW = [("userplus", "Create account", "Sign up and verify your identity in a few minutes."),
       ("wallet", "Buy credits", "Top up your BidMont wallet with the package that fits."),
       ("lock", "Unlock auctions", "Spend credits to open full auction details."),
       ("target", "Bid and win", "Place your bid directly on BidMont — track it live, no redirects.")]
home_steps = ""
for n, (ic, t, d) in enumerate(HOW, 1):
    home_steps += f'''<div class="step reveal"><span class="ic ic--lg">{i(ic, 22)}</span>
<div><p class="step__n">{n}. {t}</p><p>{d}</p></div></div>'''

home_body = f'''
<section class="hero wrap">
<div class="hero__grid">
<div>
<p class="eyebrow">One account.</p>
<h1 class="h1">Every <span class="red">opportunity</span>.</h1>
<p class="lead">Access verified partner auctions across vehicles, heavy equipment, real estate, luxury goods, marine assets, electronics and industrial machinery — all with BidMont credits.</p>
<div class="hero__cta">
<a class="btn btn--primary btn--lg" href="credits.html">Buy credits</a>
<a class="btn btn--outline btn--lg" href="auctions.html">Explore auctions</a>
</div>
{trust()}
</div>
<div class="hero__art">
<img src="assets/img/hero.webp" srcset="assets/img/hero-sm.webp 700w, assets/img/hero.webp 1200w" sizes="(min-width:900px) 640px, 92vw" alt="Cars, heavy equipment, real estate and marine assets available on BidMont" width="1200" height="735" fetchpriority="high" decoding="async">
<div class="hero__floats">{home_floats}</div>
</div>
</div>
</section>

<section class="section wrap" id="search">
<div class="panel">
<h2 class="h3" style="margin-bottom:12px">Find your next opportunity</h2>
<form class="searchbar" role="search" onsubmit="return false">
<div class="searchbar__field">
{i("search", 18, "muted")}
<label class="sr-only" for="q-home">Search auctions</label>
<input id="q-home" type="search" placeholder="Search by keyword, make, model, location…">
<button class="searchbar__btn" type="submit" aria-label="Search">{i("search", 18)}</button>
</div>
<div class="searchbar__opts">
<label class="select"><span class="sr-only">Category</span><select><option>All categories</option><option>Cars</option><option>Heavy equipment</option><option>Real estate</option><option>Marine</option><option>Luxury</option></select></label>
<label class="select"><span class="sr-only">Location</span><select><option>All locations</option><option>United Arab Emirates</option><option>United States</option><option>United Kingdom</option><option>Germany</option><option>Singapore</option></select></label>
</div>
<a class="btn btn--outline btn-filters" href="auctions.html">{i("sliders", 17)}Filters</a>
</form>
<h3 class="tiny" style="margin:20px 0 10px;font-weight:600;color:var(--ink)" id="categories">Browse by category</h3>
<div class="cats">{home_cats}<a class="cat" href="auctions.html">{i("grid", 22)}<span>All categories</span></a></div>
</div>
</section>

<section class="section wrap">
<div class="sec-head">
<h2 class="h2">Featured partner auctions</h2>
<a class="link-arrow" href="auctions.html">View all auctions {i("arrow", 15)}</a>
</div>
<div class="rail">{"".join(auction_card(a, n, lazy=(n > 2)) for n, a in enumerate([AUCTIONS[0], AUCTIONS[1], AUCTIONS[2], AUCTIONS[4], AUCTIONS[3]]))}</div>
</section>

<section class="section wrap" id="how">
<h2 class="h2" style="margin-bottom:20px">How BidMont works</h2>
<div class="panel panel--flat"><div class="steps">{home_steps}</div></div>
</section>

<section class="section wrap" id="pricing">
<div class="sec-head">
<h2 class="h2">Choose the right credit package for you</h2>
<span class="trust" style="font-size:12.5px"><span style="display:flex;gap:8px;align-items:center">{i("shield", 16)}Credits never expire</span></span>
</div>
<div class="plans plans--3">
{plan_card("Starter", "Perfect for getting started", "€49", "500 credits", ["Access to partner auctions", "Standard support"])}
{plan_card("Pro", "More credits, more opportunities", "€149", "1,750 credits", ["Access to partner auctions", "Priority support", "Best value per credit"], popular=True)}
{plan_card("Business", "Built for serious buyers", "€499", "6,500 credits", ["Access to partner auctions", "Priority support", "Dedicated account manager"])}
</div>
<p class="tiny" style="margin-top:12px">All prices exclude VAT where applicable. <a class="red" href="credits.html#compare" style="font-weight:600">Compare all plans</a></p>
</section>

<section class="section wrap" id="partners">
<div class="promo">
<div>
<h2 class="h2" style="margin-bottom:8px">Sell on BidMont</h2>
<p class="lead" style="font-size:13.5px">List vehicles, equipment or commercial assets and reach serious, verified buyers worldwide. Bidding, payments and buyer verification all happen on BidMont — you just list and ship.</p>
<a class="btn btn--outline" href="#" style="margin-top:16px">Learn more</a>
</div>
<div class="promo__items">
<div class="feature"><span class="ic">{i("users", 19)}</span><div><b>Qualified demand</b><span>Buyers arrive verified and ready to bid.</span></div></div>
<div class="feature"><span class="ic">{i("globe", 19)}</span><div><b>Global reach</b><span>Listings surfaced to buyers in 40+ countries.</span></div></div>
<div class="feature"><span class="ic">{i("handshake", 19)}</span><div><b>We handle bidding</b><span>Live bids, payments and buyer verification run on BidMont.</span></div></div>
</div>
</div>
</section>

<section class="section wrap">
{stats([("users", "50,000+", "Registered buyers"), ("shield", "400+", "Verified partners"),
        ("clock", "100,000+", "Auctions every month"), ("package", "€250M+", "In assets unlocked")])}
</section>
'''

# ================================================================= CREDITS ---
credit_feats = "".join(
    f'<div class="feature"><span class="ic">{i(ic, 19)}</span><div><b>{t}</b><span>{d}</span></div></div>'
    for ic, t, d in [("clock", "No expiration", "Credits never expire"),
                     ("zap", "Instant delivery", "Credits added instantly"),
                     ("lock", "Secure payments", "Encrypted &amp; protected"),
                     ("headset", "24/7 support", "We&rsquo;re here to help")])

HOWC = [("card", "Buy credits", "Choose a plan and complete your purchase."),
        ("doc", "Access auctions", "Use credits to view verified auction details."),
        ("target", "Place bids", "Bid on vehicles, equipment, real estate and more.")]
credit_steps = ""
for n, (ic, t, d) in enumerate(HOWC, 1):
    credit_steps += f'''<div class="step"><span class="ic ic--lg">{i(ic, 22)}</span>
<div><p class="step__n">{n}. {t}</p><p>{d}</p></div></div>'''

COMPARE_ROWS = [
    ("Access to partner auctions", [1, 1, 1, 1]),
    ("Credits never expire", [1, 1, 1, 1]),
    ("Priority support", [0, 1, 1, 1]),
    ("Advanced search &amp; filters", [0, 1, 1, 1]),
    ("Watchlist &amp; saved searches", [0, 0, 1, 1]),
    ("Dedicated account manager", [0, 0, 0, 1]),
    ("Custom credit packages", [0, 0, 0, 1]),
    ("API access", [0, 0, 0, 1]),
]
COMPARE_COLS = [("Starter", "50 credits"), ("Plus", "175 credits"), ("Pro", "650 credits"), ("Business", "1,400 credits")]
thead = '<tr><th scope="col">Feature</th>'
for n, (nm, cr) in enumerate(COMPARE_COLS):
    pop = " col-pop" if n == 2 else ""
    thead += f'<th scope="col" class="{pop.strip()}">{nm}<small>{cr}</small></th>'
thead += "</tr>"
tbody = ""
for label, vals in COMPARE_ROWS:
    tbody += f'<tr><th scope="row">{label}</th>'
    for n, v in enumerate(vals):
        pop = " col-pop" if n == 2 else ""
        cell = f'<span class="yes" role="img" aria-label="Included">{i("check", 15)}</span>' if v else '<span class="no" aria-label="Not included">—</span>'
        tbody += f'<td class="{pop.strip()}">{cell}</td>'
    tbody += "</tr>"

FAQ_ITEMS = [
    ("What are BidMont credits?", "Credits are the access currency on BidMont. You spend them to open the full details of a verified auction — photos, condition reports, seller information — then bid directly on BidMont."),
    ("Can I get a refund?", "Unused credit packages can be refunded within 14 days of purchase. Credits already spent on unlocking an auction are non-refundable. Contact support and we will handle it within two business days."),
    ("How many credits does an auction cost?", "Between 1 and 5 credits, depending on the category. Luxury items usually cost 1 credit, cars 2, heavy equipment 3, marine 4 and real estate 5."),
    ("Can I upgrade or downgrade my plan?", "Yes. Buy any package at any time — credits stack in the same wallet and always keep the rate you paid for them."),
    ("Do credits expire?", "No. Credits stay in your wallet until you use them, with no monthly minimum and no dormancy fees."),
    ("Do you offer custom credit packages?", "Yes. If you unlock more than 2,000 credits a month, contact sales for volume pricing, invoicing and API access."),
]

credits_body = f'''
<section class="hero wrap">
<div class="hero__grid hero__grid--even">
<div>
<p class="eyebrow">Buy credits</p>
<h1 class="h1">Buy credits.<br><span class="red">Unlock opportunities.</span></h1>
<p class="lead" style="margin-top:14px">BidMont credits give you access to verified partner auctions across vehicles, heavy equipment, real estate, and more.</p>
<div style="margin-top:22px">{trust()}</div>
</div>
<div class="hero__art">
<img src="assets/img/hero.webp" srcset="assets/img/hero-sm.webp 700w, assets/img/hero.webp 1200w" sizes="(min-width:900px) 640px, 92vw" alt="Assets available through BidMont partner auctions" width="1200" height="735" fetchpriority="high" decoding="async">
</div>
</div>
</section>

<section class="section--tight wrap">
<div class="panel" style="display:grid;gap:18px">
<a class="wallet" href="#pricing">
<div>
<p class="wallet__lbl">Your wallet balance</p>
<p class="wallet__amt">125 <small>Credits</small></p>
<p class="wallet__sub">= €1,250 value</p>
</div>
{i("chev-r", 20, "muted")}
</a>
<div class="features">{credit_feats}</div>
</div>
</section>

<section class="section wrap">
<div class="panel">
<h2 class="h3">How credits work</h2>
<p class="tiny" style="margin-bottom:18px">Credits are used to access auction details and place bids, right here on BidMont.</p>
<div style="display:grid;gap:20px" class="how-credits">
<div class="steps steps--3">{credit_steps}</div>
<div class="usage">
<p class="tiny" style="margin-bottom:4px">Usage</p>
<p><b>1&ndash;5 credits</b> per auction</p>
<p class="tiny">depending on category</p>
<a class="link-arrow" href="auctions.html" style="margin-top:8px">View categories {i("arrow", 15)}</a>
</div>
</div>
</div>
</section>

<section class="section wrap" id="pricing">
<div class="sec-head">
<h2 class="h2">Choose the right credit package for you</h2>
<p class="tiny">Need a custom package? <a class="red" href="#" style="font-weight:600">Contact sales</a></p>
</div>
<div class="plans plans--4">
{plan_card("Starter", "Perfect for getting started", "€49", "50 credits", ["Access to partner auctions", "Standard support", "Credits never expire"])}
{plan_card("Plus", "More access, more flexibility", "€149", "175 credits", ["Access to partner auctions", "Priority support", "Advanced search filters", "Credits never expire"])}
{plan_card("Pro", "Best value for active buyers", "€499", "650 credits", ["Access to all partner auctions", "Priority support", "Advanced search &amp; alerts", "Watchlist &amp; saved searches", "Credits never expire"], popular=True)}
{plan_card("Business", "For teams and high-volume buyers", "€999", "1,400 credits", ["Everything in Pro", "Dedicated account manager", "Custom credit packages", "API access", "Credits never expire"])}
</div>
<p class="tiny" style="margin-top:14px;text-align:center">All prices are exclusive of VAT where applicable.</p>
</section>

<section class="section--tight wrap">
<h2 class="h3" style="margin-bottom:14px">Trusted by thousands of buyers worldwide</h2>
{stats([("users", "50,000+", "Registered buyers"), ("shield", "400+", "Verified partners"),
        ("clock", "100,000+", "Auctions every month"), ("package", "€250M+", "In assets unlocked"),
        ("star", "4.8/5", "Buyer rating")], extra=" stats--5")}
</section>

<section class="section wrap" id="compare">
<h2 class="h2" style="margin-bottom:16px">Compare plans</h2>
<div class="table-scroll">
<table class="ctable">
<caption class="sr-only">Feature comparison across the four BidMont credit packages</caption>
<thead>{thead}</thead>
<tbody>{tbody}</tbody>
</table>
</div>
</section>

<section class="section wrap" id="faq">
<h2 class="h2" style="margin-bottom:16px">Frequently asked questions</h2>
{faq_block(FAQ_ITEMS, open_first=True)}
</section>

<section class="section wrap">
<div class="cta-banner">
<div class="cta-banner__bg"><img src="assets/img/handshake.webp" srcset="assets/img/handshake-sm.webp 700w, assets/img/handshake.webp 1400w" sizes="(min-width:900px) 1180px, 100vw" alt="" width="1400" height="500" loading="lazy" decoding="async"></div>
<div class="cta-banner__in">
<div>
<h2 class="h2">Ready to unlock the world of verified partner auctions?</h2>
<p class="lead" style="margin-top:8px">Join thousands of buyers who trust BidMont to grow their business.</p>
</div>
<div class="btns">
<a class="btn btn--primary btn--lg" href="#pricing">Buy credits now</a>
<a class="btn btn--outline btn--lg" href="auctions.html">Explore auctions</a>
</div>
</div>
</div>
</section>
'''

# ================================================================ AUCTIONS ---
CHIPS = [("grid", "All categories", True), ("car", "Cars", False), ("crane", "Heavy Equipment", False),
         ("home", "Real Estate", False), ("boat", "Marine", False), ("gem", "Luxury", False),
         ("tractor", "Industrial Machinery", False), ("monitor", "Electronics", False), ("truck", "Trucks", False)]
chips = "".join(
    f'<button class="chip{" is-active" if act else ""}" type="button" aria-pressed="{"true" if act else "false"}">{i(ic, 16)}{n}</button>'
    for ic, n, act in CHIPS)

PARTNERS = [("Ritchie Bros. Auctioneers", True), ("Copart", True), ("IronPlanet", False),
            ("YachtWorld Auctions", False), ("Savills Auctions", False)]
LOCATIONS = [("All locations", True), ("United Arab Emirates", False), ("United States", False),
             ("United Kingdom", False), ("Germany", False), ("Singapore", False)]


def checks(name, items):
    out = ""
    for n, (label, checked) in enumerate(items):
        ck = " checked" if checked else ""
        out += f'''<label class="check"><input type="checkbox" name="{name}"{ck}><span class="check__box">{i("check", 11)}</span>
<span class="check__label">{label}</span>{'<span class="pill pill--blue">Verified</span>' if name == "partner" else ""}</label>'''
    return out


ENDTIMES = ["Any time", "Ending within 24 hours", "Ending within 3 days", "Ending within 7 days", "Ending in 7+ days"]


def filters_markup(sfx):
    radios = "".join(
        f'<label class="radio"><input type="radio" name="end-{sfx}"{" checked" if n == 0 else ""}><span class="radio__dot"></span>{t}</label>'
        for n, t in enumerate(ENDTIMES))
    return f'''<div class="filters__group is-open">
<button class="filters__head" type="button" aria-expanded="true">Partner auction {i("chev-d", 17)}</button>
<div class="filters__body"><div><div class="inner">
<div class="input-search"><label class="sr-only" for="pf-{sfx}">Search partner</label><input class="input" id="pf-{sfx}" type="search" placeholder="Search partner…">{i("search", 15)}</div>
{checks("partner", PARTNERS)}
<a class="link-arrow" href="#">View all partners</a>
</div></div></div>
</div>
<div class="filters__group">
<button class="filters__head" type="button" aria-expanded="false">Location {i("chev-d", 17)}</button>
<div class="filters__body"><div><div class="inner">
<div class="input-search"><label class="sr-only" for="lf-{sfx}">Search location</label><input class="input" id="lf-{sfx}" type="search" placeholder="Search location…">{i("search", 15)}</div>
{checks("location", LOCATIONS)}
<a class="link-arrow" href="#">View all</a>
</div></div></div>
</div>
<div class="filters__group">
<button class="filters__head" type="button" aria-expanded="false">Price range (current price) {i("chev-d", 17)}</button>
<div class="filters__body"><div><div class="inner">
<div class="range-row">
<label class="sr-only" for="pmin-{sfx}">Minimum price</label><input class="input" id="pmin-{sfx}" type="number" min="0" placeholder="Min price">
<span>to</span>
<label class="sr-only" for="pmax-{sfx}">Maximum price</label><input class="input" id="pmax-{sfx}" type="number" min="0" placeholder="Max price">
</div>
</div></div></div>
</div>
<div class="filters__group">
<button class="filters__head" type="button" aria-expanded="false">End time {i("chev-d", 17)}</button>
<div class="filters__body"><div><div class="inner">{radios}</div></div></div>
</div>
<div class="filters__group">
<button class="filters__head" type="button" aria-expanded="false">Access credits {i("chev-d", 17)}</button>
<div class="filters__body"><div><div class="inner">
<div class="range-row">
<label class="sr-only" for="cmin-{sfx}">Minimum credits</label><input class="input" id="cmin-{sfx}" type="number" min="0" placeholder="Min credits">
<span>to</span>
<label class="sr-only" for="cmax-{sfx}">Maximum credits</label><input class="input" id="cmax-{sfx}" type="number" min="0" placeholder="Max credits">
</div>
</div></div></div>
</div>
<div class="filters__actions">
<button class="btn btn--primary btn--block" type="button">Apply filters</button>
<button class="btn btn--outline btn--block" type="button" data-reset-filters>Reset filters</button>
</div>'''


PARTNER_CARDS = [("rb.", "Ritchie Bros.", "40,000+", "15+"), ("cp", "Copart", "200,000+", "11+"),
                 ("IP", "IronPlanet", "85,000+", "9+"), ("YW", "YachtWorld Auctions", "12,000+", "3+")]
partner_cards = "".join(f'''<div class="partner-card">
<div class="partner-card__top"><span class="partner-card__logo">{lg}</span>
<div><b>{nm}</b><p class="tiny" style="display:flex;align-items:center;gap:4px">{i("shield", 12)}Verified partner</p></div></div>
<div class="partner-card__nums"><div><b>{a}</b><span>Auctions sold</span></div><div><b>{c}</b><span>Countries</span></div></div>
</div>''' for lg, nm, a, c in PARTNER_CARDS)

TREND = [("cat-cars", "Cars", "12,540+ auctions"), ("cat-heavy", "Heavy Equipment", "8,320+ auctions"),
         ("cat-real-estate", "Real Estate", "2,150+ auctions"), ("cat-marine", "Marine", "1,250+ auctions"),
         ("cat-industrial", "Industrial Machinery", "6,780+ auctions")]
trend = "".join(f'''<figure class="trend__card"><a href="#"><img src="assets/img/{im}.webp" srcset="assets/img/{im}-md.webp 400w, assets/img/{im}.webp 800w" sizes="(min-width:760px) 230px, 46vw" alt="{t}" width="800" height="640" loading="lazy" decoding="async">
<figcaption><b>{t}</b><span>{s}</span></figcaption></a></figure>''' for im, t, s in TREND)

auctions_body = f'''
<section class="section--tight wrap">
<nav class="crumbs" aria-label="Breadcrumb"><a href="index.html">Home</a>{i("chev-r", 13)}<span aria-current="page">Partner auctions</span></nav>
<div class="sec-head" style="margin-bottom:14px">
<div>
<h1 class="h1" style="font-size:clamp(28px,5vw,40px)">Live <span class="red">Auctions</span></h1>
<p class="lead" style="margin-top:8px;font-size:13.5px">Bid directly on verified auctions across vehicles, heavy equipment, real estate, marine assets, industrial machinery and more.</p>
</div>
{trust([("shield", "Verified partners"), ("lock", "Secure payments"), ("clock", "Transparent access")])}
</div>

<form class="searchbar" role="search" onsubmit="return false" style="margin-bottom:14px">
<div class="searchbar__field">
{i("search", 18, "muted")}
<label class="sr-only" for="q-auctions">Search auctions</label>
<input id="q-auctions" type="search" placeholder="Search by keyword, make, model, location…">
<button class="searchbar__btn" type="submit" aria-label="Search">{i("search", 18)}</button>
</div>
<div class="searchbar__opts">
<label class="select"><span class="sr-only">Category</span><select><option>All categories</option><option>Cars</option><option>Heavy equipment</option><option>Real estate</option><option>Marine</option><option>Luxury</option></select></label>
<label class="select"><span class="sr-only">Location</span><select><option>All locations</option><option>United Arab Emirates</option><option>United States</option><option>United Kingdom</option><option>Germany</option></select></label>
</div>
<button class="btn btn--outline btn-filters" type="button" data-filters-open>{i("sliders", 17)}Filters</button>
</form>

<div class="chips" id="categories" role="group" aria-label="Category filter">{chips}</div>
</section>

<section class="wrap" style="padding-bottom:36px">
<div class="layout-auctions">
<aside class="filters filters-desktop" aria-label="Filters">{filters_markup("d")}</aside>
<div>
<div class="results-head">
<p class="count">1,248 results found</p>
<div style="display:flex;gap:8px;align-items:center">
<label class="select"><span class="sr-only">Sort by</span>
<select><option>Ending soonest</option><option>Newly listed</option><option>Price: low to high</option><option>Price: high to low</option><option>Fewest credits</option></select></label>
</div>
</div>
<div class="grid-auctions">{"".join(auction_card(a, n, lazy=(n > 2)) for n, a in enumerate(AUCTIONS))}</div>
<div style="display:flex;justify-content:center;margin-top:24px">
<button class="btn btn--outline btn--lg" type="button">Load more auctions</button>
</div>
</div>
</div>
</section>

<section class="section--tight wrap">
<div class="promo">
<div>
<h2 class="h3" style="margin-bottom:6px">Access more. Bid with confidence.</h2>
<p class="tiny">Join BidMont to access verified partner auctions and exclusive opportunities.</p>
<a class="btn btn--primary" href="auth.html#create" style="margin-top:14px">Sign up now</a>
</div>
<div class="promo__items">
<div class="feature"><span class="ic">{i("users", 19)}</span><div><b>Trusted partners</b><span>We work only with verified auction houses.</span></div></div>
<div class="feature"><span class="ic">{i("shield", 19)}</span><div><b>Secure &amp; transparent</b><span>Fair access, clear pricing and secure payments.</span></div></div>
<div class="feature"><span class="ic">{i("globe", 19)}</span><div><b>Global opportunities</b><span>Access premium assets across the globe.</span></div></div>
</div>
</div>
</section>

<section class="section--tight wrap">
<div class="sec-head"><h2 class="h3">Featured partners</h2><a class="link-arrow" href="#">View all partners {i("arrow", 15)}</a></div>
<div class="partners">{partner_cards}</div>
</section>

<section class="section wrap">
<div class="sec-head"><h2 class="h3">Trending categories</h2><a class="link-arrow" href="#">View all categories {i("arrow", 15)}</a></div>
<div class="trend">{trend}</div>
</section>

<div class="filter-drawer" data-filters>
<div class="filter-drawer__bg" data-filters-close></div>
<div class="filter-drawer__panel" role="dialog" aria-modal="true" aria-label="Filters">
<div class="filter-drawer__top">
<strong style="display:flex;align-items:center;gap:8px;font-size:15px">{i("sliders", 18)}Filters</strong>
<button class="burger" type="button" data-filters-close aria-label="Close filters">{i("x", 20)}</button>
</div>
<div class="filter-drawer__body">{filters_markup("m")}</div>
</div>
</div>
'''

TABBAR = f'''<nav class="tabbar" aria-label="Quick navigation">
<a href="index.html">{i("home", 20)}<span>Home</span></a>
<a href="auctions.html" aria-current="page">{i("crane", 20)}<span>Auctions</span></a>
<a href="auctions.html#categories">{i("grid", 20)}<span>Categories</span></a>
<a href="credits.html">{i("coins", 20)}<span>Credits</span></a>
<a href="account.html">{i("user", 20)}<span>Account</span></a>
</nav>'''

# ==================================================================== AUTH ---
UPLOADS = [("idcard", "ID document", "Upload a government-issued ID"),
           ("bank", "Proof of address", "Upload a recent utility bill or bank statement"),
           ("selfie", "Selfie verification", "Take a selfie to confirm your identity")]
uploads = "".join(f'''<button class="upload" type="button" data-upload>
<span class="ic">{i(ic, 19)}</span><span><b>{t}</b><span>{d}</span></span><span class="chev">{i("chev-r", 17)}</span>
</button>''' for ic, t, d in UPLOADS)

COUNTRIES = ["Select your country", "Türkiye", "United Arab Emirates", "United States", "United Kingdom",
             "Germany", "Netherlands", "Singapore", "Montenegro"]
country_opts = "".join(f'<option{" value=" if False else ""}>{c}</option>' for c in COUNTRIES)

auth_body = f'''
<section class="section wrap">
<div class="auth">
<div class="auth__form">
<div class="tabs" role="tablist" aria-label="Account access">
<button class="tab" id="tab-login" role="tab" aria-selected="true" aria-controls="pane-login" type="button">{i("user", 17)}Log in</button>
<button class="tab" id="tab-create" role="tab" aria-selected="false" aria-controls="pane-create" type="button" tabindex="-1">{i("userplus", 17)}Create account</button>
</div>

<div class="pane is-active" id="pane-login" role="tabpanel" aria-labelledby="tab-login">
<h1 class="h2" style="font-size:24px">Welcome back</h1>
<p class="lead" style="font-size:13.5px;margin:6px 0 22px">Log in to your BidMont account</p>
<form novalidate data-form="login">
<div class="field">
<label for="login-email">Email address</label>
<div class="field__wrap">{i("mail", 17)}<input id="login-email" name="email" type="email" autocomplete="email" placeholder="Enter your email" required></div>
<p class="field__error">Enter a valid email address.</p>
</div>
<div class="field">
<label for="login-pass">Password</label>
<div class="field__wrap">{i("lock", 17)}<input id="login-pass" name="password" type="password" autocomplete="current-password" placeholder="Enter your password" required>
<button class="eye" type="button" data-toggle-pass aria-label="Show password" aria-pressed="false">{i("eye", 17)}</button></div>
<p class="field__error">Enter your password.</p>
</div>
<div class="field is-hidden" id="login-totp-wrap">
<label for="login-totp">Authenticator code</label>
<div class="field__wrap">{i("lock", 17)}<input id="login-totp" name="totp_code" type="text" inputmode="numeric" autocomplete="one-time-code" placeholder="123456" maxlength="6"></div>
<p class="field__hint">This account has 2FA enabled — enter the 6-digit code from your authenticator app.</p>
</div>
<div class="form-row">
<label class="check"><input type="checkbox" checked><span class="check__box">{i("check", 11)}</span><span class="check__label">Remember me</span></label>
<a class="red" href="#" style="font-size:12.5px;font-weight:600">Forgot password?</a>
</div>
<button class="btn btn--primary btn--block btn--lg" type="submit">Log in</button>
</form>
<div class="divider">or</div>
<button class="btn btn--outline btn--block" type="button">{GOOGLE}Continue with Google</button>
<p class="tiny" style="text-align:center;margin-top:18px">Don&rsquo;t have an account? <button class="red" style="font-weight:600" type="button" data-goto-tab="create">Create account</button></p>
</div>

<div class="pane" id="pane-create" role="tabpanel" aria-labelledby="tab-create" tabindex="0">
<div class="stepper" data-stepper>
<div class="stepper__item is-active" data-step="1"><span class="stepper__dot">1</span><span class="stepper__lbl">Account</span></div>
<span class="stepper__bar"></span>
<div class="stepper__item" data-step="2"><span class="stepper__dot">2</span><span class="stepper__lbl">Verify</span></div>
<span class="stepper__bar"></span>
<div class="stepper__item" data-step="3"><span class="stepper__dot">3</span><span class="stepper__lbl">Complete</span></div>
</div>

<div class="pane is-active" data-substep="1">
<h1 class="h2" style="font-size:24px">Create your account</h1>
<p class="lead" style="font-size:13.5px;margin:6px 0 22px">Join BidMont to access partner auctions</p>
<form novalidate data-form="signup">
<div class="field">
<label for="su-name">Full name</label>
<div class="field__wrap">{i("user", 17)}<input id="su-name" name="name" type="text" autocomplete="name" placeholder="Enter your full name" required></div>
<p class="field__error">Enter your full name.</p>
</div>
<div class="field">
<label for="su-email">Email address</label>
<div class="field__wrap">{i("mail", 17)}<input id="su-email" name="email" type="email" autocomplete="email" placeholder="Enter your email" required></div>
<p class="field__error">Enter a valid email address.</p>
</div>
<div class="field">
<label for="su-phone">Phone number</label>
<div class="phone">
<div class="field__wrap"><label class="sr-only" for="su-code">Country code</label>
<select id="su-code"><option>+90</option><option>+971</option><option>+1</option><option>+44</option><option>+49</option></select>{i("chev-d", 14)}</div>
<div class="field__wrap">{i("phone", 17)}<input id="su-phone" name="phone" type="tel" autocomplete="tel" placeholder="Enter your phone number" required></div>
</div>
<p class="field__error">Enter your phone number.</p>
</div>
<div class="field">
<label for="su-pass">Password</label>
<div class="field__wrap">{i("lock", 17)}<input id="su-pass" name="password" type="password" autocomplete="new-password" placeholder="Create a password" required minlength="8">
<button class="eye" type="button" data-toggle-pass aria-label="Show password" aria-pressed="false">{i("eye", 17)}</button></div>
<p class="field__hint">At least 8 characters, with one number.</p>
<p class="field__error">Use at least 8 characters, including a number.</p>
</div>
<div class="field">
<label for="su-country">Country</label>
<div class="field__wrap">{i("globe", 17)}<select id="su-country" name="country" required>{country_opts}</select>{i("chev-d", 14)}</div>
<p class="field__error">Select your country.</p>
</div>
<div class="field">
<label class="check" style="align-items:flex-start"><input type="checkbox" name="terms" required><span class="check__box" style="margin-top:1px">{i("check", 11)}</span>
<span class="check__label tiny">I agree to the <a class="red" href="#" style="font-weight:600;text-decoration:underline">Terms of Service</a> and <a class="red" href="#" style="font-weight:600;text-decoration:underline">Privacy Policy</a></span></label>
<p class="field__error">Accept the terms to continue.</p>
</div>
<button class="btn btn--primary btn--block btn--lg" type="submit">Create account</button>
</form>
<p class="tiny" style="text-align:center;margin-top:16px">Already have an account? <button class="red" style="font-weight:600" type="button" data-goto-tab="login">Log in</button></p>
</div>

<div class="pane" data-substep="2">
<h2 class="h2" style="font-size:22px">Verify your account</h2>
<p class="lead" style="font-size:13.5px;margin:6px 0 20px">To keep the platform secure, we need to verify your identity.</p>
<div class="stack">{uploads}</div>
<p class="tiny" style="display:flex;gap:7px;align-items:center;justify-content:center;margin-top:20px">{i("lock", 14)}Your information is encrypted and secure.</p>
<div style="display:grid;gap:9px;margin-top:20px">
<button class="btn btn--primary btn--block btn--lg" type="button" data-next-step>Submit for verification</button>
<button class="btn btn--outline btn--block" type="button" data-prev-step>Back</button>
</div>
</div>

<div class="pane" data-substep="3">
<div style="text-align:center">
<span class="success-mark">{i("check", 40)}</span>
<h2 class="h2" style="font-size:22px">Verification submitted</h2>
<p class="lead" style="font-size:13.5px;margin:8px auto 20px">Thank you. We&rsquo;re reviewing your information and will notify you once your account is verified.</p>
</div>
<div class="panel panel--flat">
<h3 class="h3" style="font-size:14px;margin-bottom:12px">What happens next</h3>
<ul class="checklist">
<li>{i("check", 15)}We review your documents</li>
<li>{i("check", 15)}We verify your information</li>
<li>{i("check", 15)}We approve your account</li>
<li>{i("check", 15)}You get full access to partner auctions</li>
</ul>
</div>
<a class="btn btn--ghostred btn--block btn--lg" href="index.html" style="margin-top:18px">Back to home</a>
</div>
</div>
</div>

<aside class="auth__side">
<h2 class="h2">Access <span class="red">verified</span> partner auctions</h2>
<p class="lead" style="font-size:13.5px;margin-top:8px">Join BidMont to access exclusive partner auctions across vehicles, heavy machinery, marine assets, electronics and more.</p>
<ul class="side-feats">
<li><span class="ic">{i("shield", 19)}</span><div><b>Verified partners</b><span>Work with trusted, pre-vetted auction houses.</span></div></li>
<li><span class="ic">{i("lock", 19)}</span><div><b>Secure payments</b><span>Your payments and data are always protected.</span></div></li>
<li><span class="ic">{i("clock", 19)}</span><div><b>Transparent access</b><span>Clear auction details and fair access for everyone.</span></div></li>
</ul>
<img src="assets/img/hero-sm.webp" alt="Assets available through BidMont partner auctions" width="700" height="429" style="border-radius:var(--r);margin-bottom:16px" loading="lazy" decoding="async">
<div class="notice">
<span class="ic" style="width:34px;height:34px">{i("shield", 17)}</span>
<div><b>Account verification required</b><p>Access to partner auctions requires a verified account.</p>
<a class="red" href="#" style="font-size:12px;font-weight:600;text-decoration:underline">Learn more</a></div>
</div>
</aside>
</div>
</section>
'''

HERO_PRELOAD = ('\n<link rel="preload" as="image" href="assets/img/hero.webp" '
                'imagesrcset="assets/img/hero-sm.webp 700w, assets/img/hero.webp 1200w" '
                'imagesizes="(min-width:900px) 640px, 92vw">')

# =================================================================== DETAIL ---
# Shell only - one auction, so no server-rendered data here. assets/js/api.js's
# wireAuctionDetail() reads `?id=` and fills every #det-* element client-side.
auction_detail_body = f'''
<section class="section--tight wrap">
<nav class="crumbs" aria-label="Breadcrumb"><a href="index.html">Home</a>{i("chev-r", 13)}<a href="auctions.html">Auctions</a>{i("chev-r", 13)}<span id="det-crumb" aria-current="page">Loading…</span></nav>
</section>

<section class="wrap" style="padding-bottom:36px">
<div class="layout-detail" id="det-notfound" style="display:none">
<div class="panel" style="text-align:center;grid-column:1/-1">
<h1 class="h2">Auction not found</h1>
<p class="lead" style="margin-top:8px">This listing may have been removed or the link is incorrect.</p>
<a class="btn btn--primary" href="auctions.html" style="margin-top:16px">Browse auctions</a>
</div>
</div>
<div class="layout-detail" id="det-root">
<div class="detail-main">
<div class="detail-gallery" id="det-gallery">
<div class="detail-gallery__main"><img id="det-image" src="assets/img/car.webp" alt=""></div>
<div class="detail-gallery__thumbs" id="det-thumbs"></div>
</div>
<div class="panel">
<div class="sec-head">
<div>
<p class="auction__cat" id="det-cat"></p>
<h1 class="h2" id="det-title">Loading…</h1>
<p class="tiny" id="det-meta"></p>
</div>
<button class="fav" id="det-watch" type="button" aria-pressed="false" aria-label="Save this auction">{i("heart", 18)}</button>
</div>
<p id="det-desc" style="margin-top:12px"></p>
<dl class="detail-specs" id="det-specs"></dl>
</div>
<div class="panel is-hidden" id="det-docs-wrap">
<h2 class="h3">Documents</h2>
<ul class="checklist" id="det-docs"></ul>
</div>
<div class="panel">
<h2 class="h3">Bid history</h2>
<div class="table-scroll"><table class="ctable">
<thead><tr><th scope="col">Bidder</th><th scope="col">Amount</th><th scope="col">Time</th></tr></thead>
<tbody id="det-bids"><tr><td colspan="3" class="tiny">No bids yet.</td></tr></tbody>
</table></div>
</div>
</div>
<aside class="detail-side">
<div class="panel" id="det-price-panel">
<p class="lbl">Current price</p>
<p class="detail-price" id="det-price">—</p>
<p class="tiny" style="margin-top:4px">Ends in <b id="det-ends">—</b></p>
<p class="tiny" id="det-status-note" style="margin-top:4px"></p>
<div id="det-bid-area">
<div class="field">
<label for="det-bid-amount">Your bid (€)</label>
<div class="field__wrap"><input id="det-bid-amount" type="number" min="0" step="1" placeholder="0"></div>
</div>
<button class="btn btn--primary btn--block btn--lg" id="det-bid-btn" type="button">Place bid</button>
<p class="tiny" id="det-credit-note" style="margin-top:8px"></p>
</div>
</div>
<div class="panel is-hidden" id="det-contact-panel">
<h2 class="h3">Contact details</h2>
<p class="tiny" id="det-contact-body" style="margin-top:6px"></p>
</div>
</aside>
</div>
</section>

<div class="lightbox" id="det-lightbox" data-lightbox>
<div class="lightbox__bg" data-lightbox-close></div>
<button class="burger lightbox__close" type="button" data-lightbox-close aria-label="Close image">{i("x", 22)}</button>
<button class="lightbox__nav lightbox__prev" type="button" data-lightbox-prev aria-label="Previous image">{i("chev-r", 22)}</button>
<img class="lightbox__img" id="det-lightbox-img" src="" alt="">
<button class="lightbox__nav lightbox__next" type="button" data-lightbox-next aria-label="Next image">{i("chev-r", 22)}</button>
</div>
'''

# =================================================================== ACCOUNT ---
# Shell only, like auction.html — assets/js/api.js's wireAccountPage() fills every
# #acct-*/pane-* element once it knows who's logged in. The "watchlist" grid tab
# gets one hidden demo card so renderAuctionGrid()'s existing
# container.querySelector(".auction") template-clone trick just works, same as
# index.html/auctions.html — no changes to that function needed. "My listings"
# is seller-owned auctions (with edit/delete/resubmit actions), rendered from
# scratch by api.js instead — a buyer-facing auction_card has no room for those.
ACCT_TABS = [("overview", "Overview"), ("bids", "My bids"), ("joined", "Joined"),
             ("watchlist", "Watchlist"), ("notifications", "Notifications"),
             ("settings", "Settings"), ("listings", "My listings")]
acct_tabs_nav = "".join(
    f'<button class="tab" id="tab-{k}" role="tab" aria-selected="{"true" if n == 0 else "false"}" '
    f'aria-controls="pane-{k}" type="button"{"" if n == 0 else " tabindex=\"-1\""}{" is-hidden" if k == "listings" else ""}>{t}</button>'
    for n, (k, t) in enumerate(ACCT_TABS))

account_body = f'''
<section class="section--tight wrap">
<nav class="crumbs" aria-label="Breadcrumb"><a href="index.html">Home</a>{i("chev-r", 13)}<span aria-current="page">My account</span></nav>
<h1 class="h1" style="font-size:clamp(24px,4vw,32px)">My account</h1>
</section>

<section class="wrap" style="padding-bottom:36px">
<div class="panel" id="acct-loggedout">
<p class="lead" style="font-size:13.5px">Log in to see your bids, watchlist and credit balance.</p>
<a class="btn btn--primary" href="auth.html" style="margin-top:12px">Log in</a>
</div>

<div id="acct-root" class="is-hidden">
<div class="tabs tabs--scroll" role="tablist" aria-label="Account sections">{acct_tabs_nav}</div>

<div class="pane is-active" id="pane-overview" role="tabpanel" aria-labelledby="tab-overview">
<div class="panel">
<p class="wallet__lbl">Credit balance</p>
<p class="wallet__amt" id="acct-balance">— <small>Credits</small></p>
<a class="btn btn--outline" href="credits.html" style="margin-top:12px">Buy more credits</a>
</div>
<div class="panel" style="margin-top:14px">
<h2 class="h3" style="margin-bottom:10px">Recent credit activity</h2>
<div class="table-scroll"><table class="ctable">
<thead><tr><th scope="col">Type</th><th scope="col">Amount</th><th scope="col">Balance after</th><th scope="col">Date</th></tr></thead>
<tbody id="acct-ledger"><tr><td colspan="4" class="tiny">No activity yet.</td></tr></tbody>
</table></div>
</div>
</div>

<div class="pane" id="pane-bids" role="tabpanel" aria-labelledby="tab-bids" tabindex="0">
<div class="panel"><div class="table-scroll"><table class="ctable">
<thead><tr><th scope="col">Auction</th><th scope="col">My bid</th><th scope="col">Status</th><th scope="col">Date</th></tr></thead>
<tbody id="acct-bids-body"><tr><td colspan="4" class="tiny">No bids yet.</td></tr></tbody>
</table></div></div>
</div>

<div class="pane" id="pane-joined" role="tabpanel" aria-labelledby="tab-joined" tabindex="0">
<div class="panel"><div class="table-scroll"><table class="ctable">
<thead><tr><th scope="col">Auction</th><th scope="col">Credits spent</th><th scope="col">My status</th><th scope="col">Joined</th></tr></thead>
<tbody id="acct-joined-body"><tr><td colspan="4" class="tiny">You haven't joined any auctions yet.</td></tr></tbody>
</table></div></div>
</div>

<div class="pane" id="pane-watchlist" role="tabpanel" aria-labelledby="tab-watchlist" tabindex="0">
<div class="grid-auctions" id="acct-watchlist-grid">{auction_card(AUCTIONS[0], 0, lazy=False)}</div>
</div>

<div class="pane" id="pane-notifications" role="tabpanel" aria-labelledby="tab-notifications" tabindex="0">
<div class="panel"><ul class="notif-list" id="acct-notif-list"><li class="tiny">No notifications yet.</li></ul></div>
</div>

<div class="pane" id="pane-settings" role="tabpanel" aria-labelledby="tab-settings" tabindex="0">
<div class="panel">
<h2 class="h3" style="margin-bottom:14px">Profile</h2>
<form id="acct-profile-form">
<div class="field"><label for="acct-name">Full name</label><div class="field__wrap">{i("user", 17)}<input id="acct-name" type="text"></div></div>
<div class="field"><label for="acct-phone">Phone</label><div class="field__wrap">{i("phone", 17)}<input id="acct-phone" type="tel"></div></div>
<div class="field"><label for="acct-city">City</label><div class="field__wrap">{i("home", 17)}<input id="acct-city" type="text"></div></div>
<div class="field"><label for="acct-address">Address</label><div class="field__wrap">{i("doc", 17)}<input id="acct-address" type="text"></div></div>
<button class="btn btn--primary" type="submit">Save profile</button>
</form>
</div>
<div class="panel" style="margin-top:14px">
<h2 class="h3" style="margin-bottom:14px">Change password</h2>
<form id="acct-password-form">
<div class="field"><label for="acct-pw-current">Current password</label><div class="field__wrap">{i("lock", 17)}<input id="acct-pw-current" type="password" autocomplete="current-password"></div></div>
<div class="field"><label for="acct-pw-new">New password</label><div class="field__wrap">{i("lock", 17)}<input id="acct-pw-new" type="password" autocomplete="new-password" minlength="6"></div></div>
<button class="btn btn--primary" type="submit">Update password</button>
</form>
</div>
<div class="panel" id="acct-seller-apply-wrap" style="margin-top:14px">
<h2 class="h3" style="margin-bottom:6px">Sell on BidMont</h2>
<p class="tiny" style="margin-bottom:12px" id="acct-seller-apply-note">Verify your email, then apply to become a seller.</p>
<form id="acct-seller-form">
<div class="field"><label for="acct-seller-type">Account type</label><div class="field__wrap">{i("user", 17)}<select id="acct-seller-type"><option value="individual">Individual</option><option value="company">Company</option></select></div></div>
<button class="btn btn--outline" type="submit">Apply to sell</button>
</form>
</div>
<button class="btn btn--ghostred" type="button" id="acct-logout" style="margin-top:14px">Log out</button>
</div>

<div class="pane" id="pane-listings" role="tabpanel" aria-labelledby="tab-listings" tabindex="0">
<div class="features" id="acct-seller-stats" style="margin-bottom:14px"></div>
<div class="panel" style="margin-bottom:14px">
<button class="btn btn--outline" type="button" id="acct-listing-new-btn">+ New listing</button>
<form id="acct-listing-form" class="is-hidden" style="margin-top:14px" novalidate>
<input type="hidden" id="lst-id">
<div class="field"><label for="lst-title">Title</label><div class="field__wrap">{i("doc", 17)}<input id="lst-title" type="text" required minlength="3" maxlength="200"></div></div>
<div class="field"><label for="lst-desc">Description</label><div class="field__wrap" style="align-items:flex-start;padding:10px 12px"><textarea id="lst-desc" rows="4" required minlength="10" maxlength="5000" style="border:0;outline:0;width:100%;font:inherit;resize:vertical;background:transparent"></textarea></div></div>
<div class="field"><label for="lst-category">Category</label><div class="field__wrap">{i("grid", 17)}<select id="lst-category" required></select></div></div>
<div class="field"><label for="lst-price">Starting price (EUR)</label><div class="field__wrap">{i("coins", 17)}<input id="lst-price" type="number" min="0.01" step="0.01" required></div></div>
<div class="field"><label for="lst-increment">Minimum bid increment (EUR)</label><div class="field__wrap">{i("coins", 17)}<input id="lst-increment" type="number" min="0.01" step="0.01" required></div></div>
<div class="field"><label for="lst-end">Ends at</label><div class="field__wrap">{i("clock", 17)}<input id="lst-end" type="datetime-local" required></div></div>
<div class="field"><label for="lst-location">Location</label><div class="field__wrap">{i("home", 17)}<input id="lst-location" type="text"></div></div>
<h3 class="h3" style="margin:14px 0 8px">Item details (optional)</h3>
<div class="field"><label for="lst-brand">Brand</label><div class="field__wrap">{i("car", 17)}<input id="lst-brand" type="text" maxlength="100"></div></div>
<div class="field"><label for="lst-model">Model</label><div class="field__wrap">{i("car", 17)}<input id="lst-model" type="text" maxlength="100"></div></div>
<div class="field"><label for="lst-year">Year</label><div class="field__wrap">{i("clock", 17)}<input id="lst-year" type="number" min="1900" max="2100"></div></div>
<div class="field"><label for="lst-mileage">Mileage (km)</label><div class="field__wrap">{i("car", 17)}<input id="lst-mileage" type="number" min="0"></div></div>
<div class="field"><label for="lst-fuel">Fuel type</label><div class="field__wrap">{i("car", 17)}<input id="lst-fuel" type="text" maxlength="50"></div></div>
<div class="field"><label for="lst-transmission">Transmission</label><div class="field__wrap">{i("car", 17)}<input id="lst-transmission" type="text" maxlength="50"></div></div>
<div class="field"><label for="lst-equip-brand">Equipment brand</label><div class="field__wrap">{i("package", 17)}<input id="lst-equip-brand" type="text" maxlength="100"></div></div>
<div class="field"><label for="lst-serial">Serial number</label><div class="field__wrap">{i("package", 17)}<input id="lst-serial" type="text" maxlength="100"></div></div>
<div class="field"><label for="lst-condition">Condition</label><div class="field__wrap">{i("package", 17)}<input id="lst-condition" type="text" maxlength="100"></div></div>
<div class="field"><label for="lst-hours">Operating hours</label><div class="field__wrap">{i("clock", 17)}<input id="lst-hours" type="number" min="0"></div></div>
<div class="field"><label for="lst-quantity">Quantity (commercial goods)</label><div class="field__wrap">{i("package", 17)}<input id="lst-quantity" type="number" min="0"></div></div>
<div class="field"><label for="lst-photos">Photos</label><div class="field__wrap">{i("doc", 17)}<input id="lst-photos" type="file" accept="image/jpeg,image/png,image/webp" multiple style="border:0;padding:6px 0"></div></div>
<div class="field"><label for="lst-doc-category">Document type</label><div class="field__wrap">{i("doc", 17)}<select id="lst-doc-category"><option value="registration">Registration</option><option value="inspection">Inspection</option><option value="service">Service history</option><option value="other">Other</option></select></div></div>
<div class="field"><label for="lst-documents">Documents (registration, inspection, service — private, staff-reviewed only)</label><div class="field__wrap">{i("doc", 17)}<input id="lst-documents" type="file" accept="image/jpeg,image/png,image/webp,application/pdf" multiple style="border:0;padding:6px 0"></div></div>
<label class="check" id="lst-declaration-wrap" style="align-items:flex-start;margin-top:8px"><input type="checkbox" id="lst-declaration"><span class="check__box" style="margin-top:1px">{i("check", 11)}</span>
<span class="check__label tiny">I confirm I have the authority to list this item and all details given are accurate.</span></label>
<div style="display:flex;gap:10px;margin-top:12px">
<button class="btn btn--primary" type="submit" id="lst-submit-btn">Publish listing</button>
<button class="btn btn--ghostred" type="button" id="acct-listing-cancel-btn">Cancel</button>
</div>
</form>
</div>
<div id="acct-listings-list"><p class="tiny">Loading…</p></div>
</div>
</div>
</section>
'''

# ===================================================================== ADMIN ---
# Shell only, like account.html — assets/js/api.js's wireAdminPage() fills every
# #adm-*/pane-adm-* element after confirming the viewer is staff (admin/
# super_admin/support). Every list renders from scratch (table rows built by
# JS), no clone-trick demo data anywhere — a fabricated row in an admin table
# is worse than one in a buyer-facing grid, so every pane starts genuinely
# empty and every fetch path has a real error state.
ADMIN_TABS = [("overview", "Overview"), ("users", "Users"), ("sellers", "Sellers"),
              ("auctions", "Auctions"), ("bids", "Bids"), ("categories", "Categories"), ("support", "Support")]
admin_tabs_nav = "".join(
    f'<button class="tab" id="tab-adm-{k}" role="tab" aria-selected="{"true" if n == 0 else "false"}" '
    f'aria-controls="pane-adm-{k}" type="button"{"" if n == 0 else " tabindex=\"-1\""}>{t}</button>'
    for n, (k, t) in enumerate(ADMIN_TABS))

admin_body = f'''
<section class="section--tight wrap">
<nav class="crumbs" aria-label="Breadcrumb"><a href="index.html">Home</a>{i("chev-r", 13)}<span aria-current="page">Admin</span></nav>
<h1 class="h1" style="font-size:clamp(24px,4vw,32px)">Admin panel</h1>
</section>

<section class="wrap" style="padding-bottom:36px">
<div class="panel" id="adm-denied">
<p class="lead" style="font-size:13.5px">Checking access…</p>
</div>

<div id="adm-root" class="is-hidden">
<div class="tabs tabs--scroll" role="tablist" aria-label="Admin sections">{admin_tabs_nav}</div>

<div class="pane is-active" id="pane-adm-overview" role="tabpanel" aria-labelledby="tab-adm-overview">
<div class="features" id="adm-stats"></div>
</div>

<div class="pane" id="pane-adm-users" role="tabpanel" aria-labelledby="tab-adm-users" tabindex="0">
<div class="panel" style="margin-bottom:14px">
<div class="field" style="margin-bottom:0"><div class="field__wrap">{i("search", 17)}<input id="adm-users-search" type="text" placeholder="Search name or email"></div></div>
</div>
<div id="adm-users-list"><p class="tiny">Loading…</p></div>
</div>

<div class="pane" id="pane-adm-sellers" role="tabpanel" aria-labelledby="tab-adm-sellers" tabindex="0">
<div class="chips" id="adm-sellers-filter" role="group" aria-label="Seller status filter" style="margin-bottom:14px">
<button class="adm-chip is-active" type="button" data-status="pending">Pending</button>
<button class="adm-chip" type="button" data-status="verified">Verified</button>
<button class="adm-chip" type="button" data-status="rejected">Rejected</button>
<button class="adm-chip" type="button" data-status="">All</button>
</div>
<div id="adm-sellers-list"><p class="tiny">Loading…</p></div>
</div>

<div class="pane" id="pane-adm-auctions" role="tabpanel" aria-labelledby="tab-adm-auctions" tabindex="0">
<div class="chips" id="adm-auctions-filter" role="group" aria-label="Auction status filter" style="margin-bottom:14px">
<button class="adm-chip is-active" type="button" data-status="under_review">Pending review</button>
<button class="adm-chip" type="button" data-status="upcoming">Upcoming</button>
<button class="adm-chip" type="button" data-status="live">Live</button>
<button class="adm-chip" type="button" data-status="ended">Ended</button>
<button class="adm-chip" type="button" data-status="cancelled">Cancelled</button>
<button class="adm-chip" type="button" data-status="">All</button>
</div>
<div id="adm-auctions-list"><p class="tiny">Loading…</p></div>
</div>

<div class="pane" id="pane-adm-bids" role="tabpanel" aria-labelledby="tab-adm-bids" tabindex="0">
<div class="panel" style="margin-bottom:14px">
<div class="field" style="margin-bottom:0"><div class="field__wrap">{i("grid", 17)}<select id="adm-bids-auction-filter"><option value="">All auctions</option></select></div></div>
</div>
<div id="adm-bids-list"><p class="tiny">Loading…</p></div>
</div>

<div class="pane" id="pane-adm-categories" role="tabpanel" aria-labelledby="tab-adm-categories" tabindex="0">
<div class="panel" style="margin-bottom:14px">
<h2 class="h3" style="margin-bottom:10px">New category</h2>
<form id="adm-category-form">
<div class="field"><label for="adm-cat-name">Name</label><div class="field__wrap">{i("grid", 17)}<input id="adm-cat-name" type="text" required></div></div>
<div class="field"><label for="adm-cat-slug">Slug</label><div class="field__wrap">{i("grid", 17)}<input id="adm-cat-slug" type="text" required placeholder="e.g. heavy-equipment"></div></div>
<div class="field"><label for="adm-cat-parent">Parent (optional)</label><div class="field__wrap">{i("grid", 17)}<select id="adm-cat-parent"><option value="">— None —</option></select></div></div>
<button class="btn btn--primary" type="submit">Add category</button>
</form>
</div>
<div id="adm-categories-list"><p class="tiny">Loading…</p></div>
</div>

<div class="pane" id="pane-adm-support" role="tabpanel" aria-labelledby="tab-adm-support" tabindex="0">
<div class="chips" id="adm-support-filter" role="group" aria-label="Ticket status filter" style="margin-bottom:14px">
<button class="adm-chip is-active" type="button" data-status="open">Open</button>
<button class="adm-chip" type="button" data-status="in_progress">In progress</button>
<button class="adm-chip" type="button" data-status="resolved">Resolved</button>
<button class="adm-chip" type="button" data-status="closed">Closed</button>
<button class="adm-chip" type="button" data-status="">All</button>
</div>
<div id="adm-support-list"><p class="tiny">Loading…</p></div>
</div>
</div>
</section>
'''

# =================================================================== SUPPORT ---
SUPPORT_CATEGORIES = [("account", "Account"), ("credits_payment", "Credits & payment"),
                      ("auction_bid", "Auction & bidding"), ("seller_application", "Seller application"),
                      ("listing", "Listing"), ("technical_issue", "Technical issue"), ("other", "Other")]
support_cat_opts = "".join(
    f'<option value="{k}"{" selected" if k == "other" else ""}>{t}</option>' for k, t in SUPPORT_CATEGORIES)

support_body = f'''
<section class="section--tight wrap">
<nav class="crumbs" aria-label="Breadcrumb"><a href="index.html">Home</a>{i("chev-r", 13)}<span aria-current="page">Support</span></nav>
<h1 class="h1" style="font-size:clamp(24px,4vw,32px)">Contact support</h1>
<p class="lead" style="margin-top:6px;font-size:13.5px">Questions about your account, credits, an auction or a listing? Send us a message.</p>
</section>

<section class="wrap" style="padding-bottom:36px">
<div class="layout-detail">
<div class="detail-main">
<div class="panel">
<h2 class="h3" style="margin-bottom:14px">Send us a message</h2>
<form id="support-form" novalidate>
<div class="field"><label for="sup-subject">Subject</label><div class="field__wrap">{i("mail", 17)}<input id="sup-subject" type="text" required></div></div>
<div class="field"><label for="sup-category">Category</label><div class="field__wrap">{i("sliders", 17)}<select id="sup-category">{support_cat_opts}</select></div></div>
<div class="field"><label for="sup-lot">Lot ID (optional)</label><div class="field__wrap">{i("doc", 17)}<input id="sup-lot" type="text" placeholder="e.g. BM-VEH-000001"></div></div>
<div class="field"><label for="sup-message">Message</label>
<div class="field__wrap" style="align-items:flex-start;padding:10px 12px">
<textarea id="sup-message" rows="6" required style="border:0;outline:0;width:100%;font:inherit;resize:vertical;background:transparent"></textarea>
</div></div>
<button class="btn btn--primary btn--lg" type="submit">Send message</button>
</form>
</div>
</div>
<aside class="detail-side">
<div class="panel">
<h2 class="h3" style="margin-bottom:8px">Need a faster answer?</h2>
<p class="tiny">Check our <a class="red" href="credits.html#faq" style="font-weight:600">FAQ</a> for common questions about credits and auctions.</p>
</div>
<div class="panel is-hidden" id="sup-my-tickets-wrap">
<h2 class="h3" style="margin-bottom:10px">Your tickets</h2>
<ul class="notif-list" id="sup-my-tickets"><li class="tiny">No tickets yet.</li></ul>
</div>
</aside>
</div>
</section>
'''

# ---------------------------------------------------------------- output ----
PAGES = [
    ("index.html", page("BidMont — One account. Every opportunity.",
                        "Access verified partner auctions across vehicles, heavy equipment, real estate, marine assets and more with BidMont credits.",
                        "home", home_body, preload=HERO_PRELOAD)),
    ("credits.html", page("Buy credits — BidMont",
                          "Buy BidMont credits to unlock verified partner auctions. Credits never expire, delivery is instant and payments are secure.",
                          "credits", credits_body, canonical="credits.html", preload=HERO_PRELOAD)),
    ("auctions.html", page("Partner auctions — BidMont",
                           "Browse 1,248 verified partner auctions across cars, heavy equipment, real estate, marine, luxury and industrial machinery.",
                           "auctions", auctions_body, body_class="has-tabbar", tabbar=TABBAR, canonical="auctions.html")),
    ("auth.html", page("Log in or create your account — BidMont",
                       "Log in to BidMont or create an account to access verified partner auctions worldwide.",
                       "auth", auth_body, canonical="auth.html")),
    ("auction.html", page("Auction details — BidMont",
                          "View auction details, bid history and place a bid on this BidMont listing.",
                          "auctions", auction_detail_body, canonical="auction.html")),
    ("account.html", page("My account — BidMont",
                          "View your bids, watchlist, credit balance and account settings on BidMont.",
                          "account", account_body, canonical="account.html")),
    ("support.html", page("Contact support — BidMont",
                          "Get help with your BidMont account, credits, an auction or a listing.",
                          "support", support_body, canonical="support.html")),
    ("admin.html", page("Admin panel — BidMont",
                        "BidMont staff panel: users, seller applications, listings, categories and support tickets.",
                        "admin", admin_body, canonical="admin.html")),
]

for fn, html in PAGES:
    with open(fn, "w", encoding="utf-8") as f:
        f.write(html)
    print(fn, len(html), "bytes")
