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
# i18n: site default language is Montenegrin ("me") - baked directly as the
# literal text below, so it works with zero JS. assets/js/i18n.js toggles to
# English at runtime via data-i18n (textContent) / data-i18n-attr
# ("attr:key", setAttribute) / data-i18n-html (innerHTML, only for the few
# strings with an embedded link) using the dict in that file, which is keyed
# by the same strings used here. NAV's existing 3rd tuple element (the page
# "active" key) doubles as the i18n key prefix - one less thing to invent.
NAV = [
    ("Kako funkcioniše", "index.html#how", "how"),
    ("Kupi kredite", "credits.html", "credits"),
    ("Aukcije", "auctions.html", "auctions"),
    ("Kategorije", "auctions.html#categories", "categories"),
    ("Za partnere", "index.html#partners", "partners"),
    ("Resursi", "credits.html#faq", "resources"),
]
DROPDOWN = {"categories", "resources"}


def header(active):
    items = ""
    drawer_items = ""
    for label, href, key in NAV:
        cur = ' aria-current="page"' if key == active else ""
        caret = i("chev-d", 14) if key in DROPDOWN else ""
        items += f'<li><a href="{href}"{cur}><span data-i18n="nav_{key}">{label}</span>{caret}</a></li>'
        drawer_items += f'<a href="{href}"{cur}><span data-i18n="nav_{key}">{label}</span></a>'
    return f'''<header class="hdr">
<div class="wrap hdr__in">
{logo()}
<nav class="nav" aria-label="Glavna navigacija" data-i18n-attr="aria-label:aria_main_nav"><ul>{items}</ul></nav>
<div class="notif-wrap is-hidden" id="notif-wrap">
<button class="fav" type="button" id="notif-bell" aria-haspopup="true" aria-expanded="false" aria-label="Obavještenja" data-i18n-attr="aria-label:notifications">{i("bell", 18)}<span class="notif-badge is-hidden" id="notif-badge">0</span></button>
<div class="notif-dropdown is-hidden" id="notif-dropdown" role="menu" aria-label="Obavještenja" data-i18n-attr="aria-label:notifications"><ul id="notif-dropdown-list"><li class="tiny" data-i18n="notif_empty">Nema obavještenja.</li></ul></div>
</div>
<div class="hdr__actions">
<a class="btn btn--outline btn--sm" href="auth.html" data-i18n="hdr_login">Prijava</a>
<a class="btn btn--primary btn--sm" href="auth.html#create" data-i18n="hdr_signup">Registracija</a>
</div>
<button class="burger" type="button" data-drawer-open aria-label="Otvori meni" data-i18n-attr="aria-label:menu_open" aria-expanded="false" aria-controls="mobile-menu">{i("menu", 22)}</button>
</div>
</header>

<div class="drawer" id="mobile-menu" data-drawer>
<div class="drawer__bg" data-drawer-close></div>
<div class="drawer__panel" role="dialog" aria-modal="true" aria-label="Meni" data-i18n-attr="aria-label:menu">
<div class="drawer__top">{logo()}<button class="burger" type="button" data-drawer-close aria-label="Zatvori meni" data-i18n-attr="aria-label:menu_close">{i("x", 22)}</button></div>
<nav class="drawer__nav" aria-label="Mobilna navigacija" data-i18n-attr="aria-label:aria_mobile_nav">{drawer_items}</nav>
<div class="drawer__foot">
<a class="btn btn--outline btn--block" href="auth.html" data-i18n="hdr_login">Prijava</a>
<a class="btn btn--primary btn--block" href="auth.html#create" data-i18n="hdr_signup">Registracija</a>
</div>
</div>
</div>'''


FOOT_COLS = [
    ("Tržište", "ftr_col_marketplace", [("Aukcije", "auctions.html", "nav_auctions"), ("Kategorije", "auctions.html#categories", "nav_categories"),
                     ("Kako funkcioniše", "index.html#how", "nav_how"), ("Kupi kredite", "credits.html", "nav_credits")]),
    ("Za partnere", "ftr_col_partners", [("Partnerski program", "index.html#partners", "ftr_partner_program"), ("Prodajte sa nama", "index.html#partners", "ftr_sell_with_us"),
                      ("Resursi", "credits.html#faq", "nav_resources"), ("Priče o uspjehu", "index.html#partners", "ftr_success_stories")]),
    ("Kompanija", "ftr_col_company", [("O nama", "index.html#about", "about_us"), ("Karijera", "#", "careers"), ("Vijesti", "#", "news"), ("Kontaktirajte nas", "support.html", "contact_us")]),
    ("Podrška", "ftr_col_support", [("Centar za pomoć", "credits.html#faq", "help_center"), ("Uslovi korišćenja", "legal:terms_of_service", "terms_of_service"),
                 ("Politika privatnosti", "legal:privacy_policy", "privacy_policy"), ("Politika kolačića", "legal:cookie_policy", "cookie_policy")]),
]


def _foot_link(t, h, key):
    # "legal:<document_type>" opens the legal-content dialog instead of navigating
    # (see wireLegalModal() in assets/js/api.js) - the text itself lives in the
    # TermsDocument table (admin-authored via POST /api/admin/legal), not here.
    if h.startswith("legal:"):
        return f'<li><a href="#" data-legal="{h[6:]}"><span data-i18n="{key}">{t}</span></a></li>'
    return f'<li><a href="{h}"><span data-i18n="{key}">{t}</span></a></li>'


def footer():
    cols = ""
    for title, tkey, links in FOOT_COLS:
        ls = "".join(_foot_link(t, h, key) for t, h, key in links)
        cols += f'<div class="ftr__col"><h4 data-i18n="{tkey}">{title}</h4><ul>{ls}</ul></div>'
    socials = "".join(
        f'<a href="#" aria-label="{n.capitalize()}">{i(n, 17)}</a>'
        for n in ("instagram", "facebook", "linkedin", "youtube"))
    return f'''<footer class="ftr">
<div class="wrap">
<div class="ftr__grid">
<div class="ftr__about">
{logo()}
<p data-i18n="ftr_about">Kupujte provjerene kredite i otključajte pristup provjerenim partnerskim aukcijama širom svijeta.</p>
<div class="socials">{socials}</div>
</div>
{cols}
</div>
<div class="ftr__bar">
<p data-i18n="ftr_copyright">© 2024 BidMont. Sva prava zadržana.</p>
<div class="ftr__locale">
<label class="select"><span class="sr-only" data-i18n="ftr_lang_label">Jezik</span><select id="lang-select"><option value="me">Crnogorski</option><option value="en">English</option></select></label>
<label class="select"><span class="sr-only" data-i18n="ftr_currency_label">Valuta</span><select><option>EUR (€)</option><option>USD ($)</option><option>TRY (₺)</option></select></label>
</div>
</div>
</div>
</footer>
<dialog id="legal-modal" class="legal-modal">
<div class="legal-modal__head"><h3 id="legal-modal-title"></h3><button type="button" class="legal-modal__close" aria-label="Zatvori" data-i18n-attr="aria-label:close">{i("x", 16)}</button></div>
<div id="legal-modal-body" class="legal-modal__body"></div>
</dialog>'''


def page(title, desc, active, body, body_class="", tabbar="", canonical="", preload="", title_key=""):
    bc = f' class="{body_class}"' if body_class else ""
    title_attr = f' data-i18n="{title_key}"' if title_key else ""
    return f'''<!doctype html>
<html lang="cnr">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title{title_attr}>{title}</title>
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
<meta property="og:image:alt" content="Provjerene partnerske aukcije na BidMont-u">
<link rel="icon" href="favicon.ico" sizes="any">
<link rel="icon" type="image/png" href="favicon-32.png" sizes="32x32">
<link rel="apple-touch-icon" href="apple-touch-icon.png">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="assets/css/style.css">{preload}
</head>
<body{bc}>
<a class="sr-only" href="#main" data-i18n="skip_to_content">Preskoči na sadržaj</a>
{header(active)}
<main id="main" class="shell">
{body}
</main>
{footer()}
{tabbar}
<script src="assets/js/i18n.js" defer></script>
<script src="assets/js/main.js" defer></script>
<script src="assets/js/api.js" defer></script>
</body>
</html>'''


# ------------------------------------------------------------ components ----
def trust(items=None, cls="trust"):
    items = items or [("shield", "trust_verified", "Provjereni partneri"), ("lock", "trust_secure", "Bezbjedno i transparentno"), ("clock", "trust_instant", "Trenutan pristup")]
    return f'<ul class="{cls}">' + "".join(f'<li>{i(n, 17)}<span data-i18n="{k}">{t}</span></li>' for n, k, t in items) + "</ul>"


PHOTOS = {"car", "villa", "excavator", "yacht", "generator", "watch", "cnc", "truck", "suv"}

# Demo/placeholder listings baked server-side for first paint - assets/js/api.js
# replaces these with live data from GET /api/auctions client-side. Names/prices
# are product data (like a real seller's listing title), not UI chrome, so they
# stay as authored - same reasoning as not translating a live auction's title.
# "cat" also stays untranslated: it must keep matching whatever the live API
# returns for category_id (currently English, see category_seed.py TOP_LEVEL),
# so a demo card looks identical to the real card that replaces it.
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
    badge = (f'<span class="pill pill--verified">{i("shield", 13)}<span data-i18n="verified_partner">Provjereni partner</span></span>' if verified
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
<button class="fav" type="button" aria-pressed="false" aria-label="Sačuvaj {name}">{i("heart", 16)}</button>
<div class="auction__body">
<p class="auction__partner">{partner.upper()}</p>
<h3 class="auction__title"><a href="#">{name}</a></h3>
<p class="auction__cat">{cat}</p>
<div class="auction__meta">
<div><span class="lbl" data-i18n="lbl_current_price">Trenutna cijena</span><span class="val">{price}</span></div>
<div><span class="lbl" data-i18n="lbl_ends_in">Ističe za</span><span class="val val--sm" data-countdown="{secs}">--</span></div>
</div>
<div class="auction__foot"><span class="lbl" data-i18n="lbl_access">Pristup</span><span class="credits-tag">{credits}</span></div>
</div>
</article>'''


def faq_block(items, open_first=False):
    out = '<div class="faq">'
    for n, (qkey, q, akey, a) in enumerate(items):
        op = " is-open" if (open_first and n == 0) else ""
        exp = "true" if op else "false"
        out += f'''<div class="faq__item{op}">
<button class="faq__q" type="button" aria-expanded="{exp}"><span data-i18n="{qkey}">{q}</span>{i("chev-d", 18)}</button>
<div class="faq__a"><div><p data-i18n="{akey}">{a}</p></div></div>
</div>'''
    return out + "</div>"


def plan_card(name, desc_key, desc, price, credits, feats, popular=False):
    tag = f'<span class="pill pill--pop plan__tag" data-i18n="most_popular">Najpopularniji</span>' if popular else ""
    fs = "".join(f'<li>{i("check", 15)}<span data-i18n="{k}">{f}</span></li>' for k, f in feats)
    btn = "btn--primary" if popular else "btn--outline"
    return f'''<div class="plan{' plan--pop' if popular else ''} reveal">{tag}
<div><h3 class="plan__name">{name}</h3><p class="plan__desc" data-i18n="{desc_key}">{desc}</p></div>
<p class="plan__price"><b>{price}</b><span>{credits}</span></p>
<ul class="plan__feats">{fs}</ul>
<a class="btn {btn} btn--block" href="auth.html#create" data-i18n="cta_get_started">Započni</a>
</div>'''


def stats(items, extra=""):
    body = "".join(f'<div class="stat">{i(ic, 20, "muted")}<div><b>{v}</b><span data-i18n="{k}">{l}</span></div></div>' for ic, k, v, l in items)
    return f'<div class="stats{extra}">{body}</div>'


def float_card(img, name, price, credits, cls):
    return f'''<div class="float-card {cls}">
<img src="assets/img/{img}-sm.webp" alt="" width="46" height="42" loading="lazy" decoding="async">
<div class="float-card__body">
<b>{name}</b><span data-i18n="partner_auction">Partnerska aukcija</span>
<div class="row"><span class="price">{price}</span><span class="credits-tag">{credits}</span></div>
</div></div>'''


# ==================================================================== HOME ---
home_floats = (
    float_card("villa", "Luxury Villa in Tivat", "€1,250,000", "5 Credits", "float-card--a") +
    float_card("excavator", "CAT 320 Excavator", "€67,000", "3 Credits", "float-card--b") +
    float_card("car", "Porsche 911 Turbo S", "€138,500", "2 Credits", "float-card--c") +
    float_card("watch", "Rolex Daytona", "€18,500", "1 Credit", "float-card--d")
)

# CATS is pure decorative navigation (links straight to auctions.html, no JS
# reads its text), so unlike CHIPS it needs no data-cat/value decoupling -
# only the visible label. Shares keys with CHIPS where the English source
# label is identical (see category_seed.py TOP_LEVEL for why that list can't
# be translated the same way).
CATS = [("car", "cat_cars", "Automobili"), ("bike", "cat_motorcycles", "Motocikli"), ("crane", "cat_heavy_equipment", "Teška mehanizacija"),
        ("home", "cat_real_estate", "Nekretnine"), ("boat", "cat_boats", "Čamci"), ("gem", "cat_luxury", "Luksuz"),
        ("tractor", "cat_industrial", "Industrijske mašine"), ("monitor", "cat_electronics", "Elektronika")]

home_cats = "".join(f'<a class="cat" href="auctions.html">{i(ic, 22)}<span data-i18n="{k}">{n}</span></a>' for ic, k, n in CATS)

HOW = [("userplus", "step1_t", "Kreirajte nalog", "step1_d", "Registrujte se i potvrdite identitet za nekoliko minuta."),
       ("wallet", "step2_t", "Kupite kredite", "step2_d", "Dopunite svoj BidMont novčanik paketom koji vam odgovara."),
       ("lock", "step3_t", "Otključajte aukcije", "step3_d", "Iskoristite kredite da otvorite sve detalje aukcije."),
       ("target", "step4_t", "Licitirajte i pobijedite", "step4_d", "Postavite ponudu direktno na BidMont-u — pratite je uživo, bez preusmjeravanja.")]
home_steps = ""
for n, (ic, tkey, t, dkey, d) in enumerate(HOW, 1):
    home_steps += f'''<div class="step reveal"><span class="ic ic--lg">{i(ic, 22)}</span>
<div><p class="step__n">{n}. <span data-i18n="{tkey}">{t}</span></p><p data-i18n="{dkey}">{d}</p></div></div>'''

home_body = f'''
<section class="hero wrap">
<div class="hero__grid">
<div>
<p class="eyebrow" data-i18n="eyebrow_one_account">Jedan nalog.</p>
<h1 class="h1" data-i18n-html="h1_every_opportunity">Svaka <span class="red">prilika</span>.</h1>
<p class="lead" data-i18n="home_lead">Pristupite provjerenim partnerskim aukcijama vozila, teške mehanizacije, nekretnina, luksuznih dobara, plovila, elektronike i industrijskih mašina — sve uz BidMont kredite.</p>
<div class="hero__cta">
<a class="btn btn--primary btn--lg" href="credits.html" data-i18n="nav_credits">Kupi kredite</a>
<a class="btn btn--outline btn--lg" href="auctions.html" data-i18n="explore_auctions">Istraži aukcije</a>
</div>
{trust()}
</div>
<div class="hero__art">
<img src="assets/img/hero.webp" srcset="assets/img/hero-sm.webp 700w, assets/img/hero.webp 1200w" sizes="(min-width:900px) 640px, 92vw" alt="Automobili, teška mehanizacija, nekretnine i plovila dostupni na BidMont-u" width="1200" height="735" fetchpriority="high" decoding="async">
<div class="hero__floats">{home_floats}</div>
</div>
</div>
</section>

<section class="section wrap" id="search">
<div class="panel">
<h2 class="h3" style="margin-bottom:12px" data-i18n="find_next_opportunity">Pronađite sljedeću priliku</h2>
<form class="searchbar" role="search" onsubmit="return false">
<div class="searchbar__field">
{i("search", 18, "muted")}
<label class="sr-only" for="q-home" data-i18n="search_auctions">Pretraži aukcije</label>
<input id="q-home" type="search" placeholder="Pretražite po ključnoj riječi, marki, modelu, lokaciji…" data-i18n-attr="placeholder:ph_search_auctions">
<button class="searchbar__btn" type="submit" aria-label="Pretraga" data-i18n-attr="aria-label:search">{i("search", 18)}</button>
</div>
<div class="searchbar__opts">
<label class="select"><span class="sr-only" data-i18n="field_category">Kategorija</span><select><option data-i18n="cat_all">Sve kategorije</option><option data-i18n="cat_cars">Automobili</option><option data-i18n="cat_heavy_equipment_short">Teška oprema</option><option data-i18n="cat_real_estate">Nekretnine</option><option data-i18n="cat_marine">Plovila</option><option data-i18n="cat_luxury">Luksuz</option></select></label>
<label class="select"><span class="sr-only" data-i18n="field_location">Lokacija</span><select><option data-i18n="loc_all">Sve lokacije</option><option data-i18n="loc_uae">Ujedinjeni Arapski Emirati</option><option data-i18n="loc_us">Sjedinjene Američke Države</option><option data-i18n="loc_uk">Ujedinjeno Kraljevstvo</option><option data-i18n="loc_de">Njemačka</option><option data-i18n="loc_sg">Singapur</option></select></label>
</div>
<a class="btn btn--outline btn-filters" href="auctions.html">{i("sliders", 17)}<span data-i18n="filters">Filteri</span></a>
</form>
<h3 class="tiny" style="margin:20px 0 10px;font-weight:600;color:var(--ink)" id="categories" data-i18n="browse_by_category">Pregledaj po kategoriji</h3>
<div class="cats">{home_cats}<a class="cat" href="auctions.html">{i("grid", 22)}<span data-i18n="cat_all">Sve kategorije</span></a></div>
</div>
</section>

<section class="section wrap">
<div class="sec-head">
<h2 class="h2" data-i18n="featured_auctions">Izdvojene partnerske aukcije</h2>
<a class="link-arrow" href="auctions.html"><span data-i18n="view_all_auctions">Pogledaj sve aukcije</span> {i("arrow", 15)}</a>
</div>
<div class="rail">{"".join(auction_card(a, n, lazy=(n > 2)) for n, a in enumerate([AUCTIONS[0], AUCTIONS[1], AUCTIONS[2], AUCTIONS[4], AUCTIONS[3]]))}</div>
</section>

<section class="section wrap" id="how">
<h2 class="h2" style="margin-bottom:20px" data-i18n="how_bidmont_works">Kako BidMont funkcioniše</h2>
<div class="panel panel--flat"><div class="steps">{home_steps}</div></div>
</section>

<section class="section wrap" id="pricing">
<div class="sec-head">
<h2 class="h2" data-i18n="choose_plan_heading">Izaberite pravi paket kredita za sebe</h2>
<span class="trust" style="font-size:12.5px"><span style="display:flex;gap:8px;align-items:center">{i("shield", 16)}<span data-i18n="credits_never_expire">Krediti nikad ne ističu</span></span></span>
</div>
<div class="plans plans--3">
{plan_card("Starter", "desc_starter", "Idealno za početak", "€49", "500 kredita", [("feat_access_auctions", "Pristup partnerskim aukcijama"), ("feat_standard_support", "Standardna podrška")])}
{plan_card("Pro", "desc_pro_home", "Više kredita, više prilika", "€149", "1,750 kredita", [("feat_access_auctions", "Pristup partnerskim aukcijama"), ("feat_priority_support", "Prioritetna podrška"), ("feat_best_value", "Najbolja vrijednost po kreditu")], popular=True)}
{plan_card("Business", "desc_business_home", "Napravljeno za ozbiljne kupce", "€499", "6,500 kredita", [("feat_access_auctions", "Pristup partnerskim aukcijama"), ("feat_priority_support", "Prioritetna podrška"), ("feat_dedicated_manager", "Posvećeni menadžer naloga")])}
</div>
<p class="tiny" style="margin-top:12px" data-i18n-html="vat_notice_with_link">Sve cijene su bez PDV-a, gdje je primjenjivo. <a class="red" href="credits.html#compare" style="font-weight:600">Uporedi sve pakete</a></p>
</section>

<section class="section wrap" id="partners">
<div class="promo">
<div>
<h2 class="h2" style="margin-bottom:8px" data-i18n="sell_on_bidmont">Prodajte na BidMont-u</h2>
<p class="lead" style="font-size:13.5px" data-i18n="sell_on_bidmont_desc">Oglasite vozila, opremu ili komercijalna dobra i dođite do ozbiljnih, provjerenih kupaca širom svijeta. Licitacija, plaćanja i provjera kupaca odvijaju se na BidMont-u — vi samo objavite oglas i pošaljete robu.</p>
<a class="btn btn--outline" href="#" style="margin-top:16px" data-i18n="learn_more">Saznaj više</a>
</div>
<div class="promo__items">
<div class="feature"><span class="ic">{i("users", 19)}</span><div><b data-i18n="qualified_demand">Kvalifikovana tražnja</b><span data-i18n="qualified_demand_desc">Kupci dolaze provjereni i spremni da licitiraju.</span></div></div>
<div class="feature"><span class="ic">{i("globe", 19)}</span><div><b data-i18n="global_reach">Globalni doseg</b><span data-i18n="global_reach_desc">Oglasi se prikazuju kupcima u više od 40 zemalja.</span></div></div>
<div class="feature"><span class="ic">{i("handshake", 19)}</span><div><b data-i18n="we_handle_bidding">Mi vodimo licitaciju</b><span data-i18n="we_handle_bidding_desc">Licitacija uživo, plaćanja i provjera kupaca odvijaju se na BidMont-u.</span></div></div>
</div>
</div>
</section>

<section class="section wrap">
{stats([("users", "stat_registered_buyers", "50,000+", "Registrovani kupci"), ("shield", "trust_verified", "400+", "Provjereni partneri"),
        ("clock", "stat_auctions_monthly", "100,000+", "Aukcija mjesečno"), ("package", "stat_assets_unlocked", "€250M+", "Otključane vrijednosti")])}
</section>

<section class="section--tight wrap" id="about">
<h2 class="h2" style="margin-bottom:8px" data-i18n="about_bidmont">O BidMont-u</h2>
<p class="lead" style="font-size:13.5px;max-width:640px" data-i18n="about_bidmont_desc">BidMont je onlajn platforma za aukcije za Crnu Goru i širi region Balkana, koja povezuje provjerene prodavce vozila, opreme i komercijalnih dobara sa ozbiljnim kupcima potkrijepljenim kreditima. Svaki oglas i svaki učesnik prolazi kroz naš proces provjere prije nego što se postavi ijedna ponuda.</p>
</section>
'''

# ================================================================= CREDITS ---
credit_feats = "".join(
    f'<div class="feature"><span class="ic">{i(ic, 19)}</span><div><b data-i18n="{tk}">{t}</b><span data-i18n="{dk}">{d}</span></div></div>'
    for ic, tk, t, dk, d in [("clock", "feat_title_no_expiration", "Bez isteka", "credits_never_expire", "Krediti nikad ne ističu"),
                     ("zap", "feat_title_instant", "Trenutna isporuka", "feat_desc_instant", "Krediti se dodaju odmah"),
                     ("lock", "trust_secure_payments", "Bezbjedne uplate", "feat_desc_encrypted", "Šifrovano i zaštićeno"),
                     ("headset", "feat_title_247", "Podrška 24/7", "feat_desc_247", "Tu smo da pomognemo")])

HOWC = [("card", "nav_credits", "Kupi kredite", "step_desc_buy", "Izaberite paket i završite kupovinu."),
        ("doc", "step_title_access", "Pristupite aukcijama", "step_desc_access", "Iskoristite kredite da vidite detalje provjerene aukcije."),
        ("target", "step_title_bid", "Licitirajte", "step_desc_bid", "Licitirajte na vozila, opremu, nekretnine i drugo.")]
credit_steps = ""
for n, (ic, tkey, t, dkey, d) in enumerate(HOWC, 1):
    credit_steps += f'''<div class="step"><span class="ic ic--lg">{i(ic, 22)}</span>
<div><p class="step__n">{n}. <span data-i18n="{tkey}">{t}</span></p><p data-i18n="{dkey}">{d}</p></div></div>'''

COMPARE_ROWS = [
    ("feat_access_auctions", "Pristup partnerskim aukcijama", [1, 1, 1, 1]),
    ("credits_never_expire", "Krediti nikad ne ističu", [1, 1, 1, 1]),
    ("feat_priority_support", "Prioritetna podrška", [0, 1, 1, 1]),
    ("feat_advanced_search", "Napredna pretraga i filteri", [0, 1, 1, 1]),
    ("feat_watchlist", "Lista praćenja i sačuvane pretrage", [0, 0, 1, 1]),
    ("feat_dedicated_manager", "Posvećeni menadžer naloga", [0, 0, 0, 1]),
    ("feat_custom_packages", "Prilagođeni paketi kredita", [0, 0, 0, 1]),
    ("feat_api_access", "API pristup", [0, 0, 0, 1]),
]
COMPARE_COLS = [("Starter", "50 kredita"), ("Plus", "175 kredita"), ("Pro", "650 kredita"), ("Business", "1,400 kredita")]
thead = f'<tr><th scope="col" data-i18n="th_feature">Funkcija</th>'
for n, (nm, cr) in enumerate(COMPARE_COLS):
    pop = " col-pop" if n == 2 else ""
    thead += f'<th scope="col" class="{pop.strip()}">{nm}<small>{cr}</small></th>'
thead += "</tr>"
tbody = ""
for key, label, vals in COMPARE_ROWS:
    tbody += f'<tr><th scope="row" data-i18n="{key}">{label}</th>'
    for n, v in enumerate(vals):
        pop = " col-pop" if n == 2 else ""
        cell = f'<span class="yes" role="img" aria-label="Uključeno" data-i18n-attr="aria-label:included">{i("check", 15)}</span>' if v else '<span class="no" aria-label="Nije uključeno" data-i18n-attr="aria-label:not_included">—</span>'
        tbody += f'<td class="{pop.strip()}">{cell}</td>'
    tbody += "</tr>"

FAQ_ITEMS = [
    ("faq_q1", "Šta su BidMont krediti?", "faq_a1", "Krediti su valuta pristupa na BidMont-u. Trošite ih da otvorite sve detalje provjerene aukcije — fotografije, izvještaje o stanju, informacije o prodavcu — a zatim licitirate direktno na BidMont-u."),
    ("faq_q2", "Mogu li dobiti povrat novca?", "faq_a2", "Nekorišćeni paketi kredita mogu se refundirati u roku od 14 dana od kupovine. Krediti već potrošeni na otključavanje aukcije se ne refundiraju. Kontaktirajte podršku i riješićemo to u roku od dva radna dana."),
    ("faq_q3", "Koliko kredita košta aukcija?", "faq_a3", "Između 1 i 5 kredita, zavisno od kategorije. Luksuzni predmeti obično koštaju 1 kredit, automobili 2, teška mehanizacija 3, plovila 4, a nekretnine 5."),
    ("faq_q4", "Mogu li promijeniti svoj paket?", "faq_a4", "Da. Kupite bilo koji paket u bilo kom trenutku — krediti se sabiraju u istom novčaniku i uvijek zadržavaju cijenu po kojoj su kupljeni."),
    ("faq_q5", "Da li krediti ističu?", "faq_a5", "Ne. Krediti ostaju u vašem novčaniku dok ih ne iskoristite, bez mjesečnog minimuma i naknada za neaktivnost."),
    ("faq_q6", "Da li nudite prilagođene pakete kredita?", "faq_a6", "Da. Ako mjesečno otključavate više od 2.000 kredita, kontaktirajte prodaju za popuste na količinu, fakturisanje i API pristup."),
]

credits_body = f'''
<section class="hero wrap">
<div class="hero__grid hero__grid--even">
<div>
<p class="eyebrow" data-i18n="eyebrow_buy_credits">Kupovina kredita</p>
<h1 class="h1" data-i18n-html="credits_h1">Kupite kredite.<br><span class="red">Otključajte prilike.</span></h1>
<p class="lead" style="margin-top:14px" data-i18n="credits_hero_desc">BidMont krediti vam daju pristup provjerenim partnerskim aukcijama vozila, teške mehanizacije, nekretnina i drugog.</p>
<div style="margin-top:22px">{trust()}</div>
</div>
<div class="hero__art">
<img src="assets/img/hero.webp" srcset="assets/img/hero-sm.webp 700w, assets/img/hero.webp 1200w" sizes="(min-width:900px) 640px, 92vw" alt="Dobra dostupna kroz BidMont partnerske aukcije" width="1200" height="735" fetchpriority="high" decoding="async">
</div>
</div>
</section>

<section class="section--tight wrap">
<div class="panel" style="display:grid;gap:18px">
<a class="wallet" href="#pricing">
<div>
<p class="wallet__lbl" data-i18n="wallet_balance_label">Stanje novčanika</p>
<p class="wallet__amt">125 <small data-i18n="credits_word">Krediti</small></p>
<p class="wallet__sub" data-i18n-html="wallet_value">= €1.250 vrijednosti</p>
</div>
{i("chev-r", 20, "muted")}
</a>
<div class="features">{credit_feats}</div>
</div>
</section>

<section class="section wrap">
<div class="panel">
<h2 class="h3" data-i18n="how_credits_heading">Kako krediti funkcionišu</h2>
<p class="tiny" style="margin-bottom:18px" data-i18n="how_credits_desc">Krediti se koriste za pristup detaljima aukcije i za licitiranje, direktno ovdje na BidMont-u.</p>
<div style="display:grid;gap:20px" class="how-credits">
<div class="steps steps--3">{credit_steps}</div>
<div class="usage">
<p class="tiny" style="margin-bottom:4px" data-i18n="usage_label">Potrošnja</p>
<p><b data-i18n="usage_amount">1–5 kredita</b> <span data-i18n="usage_per_auction">po aukciji</span></p>
<p class="tiny" data-i18n="usage_depends">zavisno od kategorije</p>
<a class="link-arrow" href="auctions.html" style="margin-top:8px"><span data-i18n="view_categories">Pogledaj kategorije</span> {i("arrow", 15)}</a>
</div>
</div>
</div>
</section>

<section class="section wrap" id="pricing">
<div class="sec-head">
<h2 class="h2" data-i18n="choose_plan_heading">Izaberite pravi paket kredita za sebe</h2>
<p class="tiny" data-i18n-html="custom_package_prompt">Potreban vam je prilagođeni paket? <a class="red" href="#" style="font-weight:600">Kontaktirajte prodaju</a></p>
</div>
<div class="plans plans--4">
{plan_card("Starter", "desc_starter", "Idealno za početak", "€49", "50 kredita", [("feat_access_auctions", "Pristup partnerskim aukcijama"), ("feat_standard_support", "Standardna podrška"), ("credits_never_expire", "Krediti nikad ne ističu")])}
{plan_card("Plus", "desc_plus", "Više pristupa, više fleksibilnosti", "€149", "175 kredita", [("feat_access_auctions", "Pristup partnerskim aukcijama"), ("feat_priority_support", "Prioritetna podrška"), ("feat_advanced_search", "Napredna pretraga i filteri"), ("credits_never_expire", "Krediti nikad ne ističu")])}
{plan_card("Pro", "desc_pro_credits", "Najbolja vrijednost za aktivne kupce", "€499", "650 kredita", [("feat_access_all_auctions", "Pristup svim partnerskim aukcijama"), ("feat_priority_support", "Prioritetna podrška"), ("feat_advanced_search_alerts", "Napredna pretraga i obavještenja"), ("feat_watchlist", "Lista praćenja i sačuvane pretrage"), ("credits_never_expire", "Krediti nikad ne ističu")], popular=True)}
{plan_card("Business", "desc_business_credits", "Za timove i kupce sa velikim obimom", "€999", "1,400 kredita", [("feat_everything_pro", "Sve iz Pro paketa"), ("feat_dedicated_manager", "Posvećeni menadžer naloga"), ("feat_custom_packages", "Prilagođeni paketi kredita"), ("feat_api_access", "API pristup"), ("credits_never_expire", "Krediti nikad ne ističu")])}
</div>
<p class="tiny" style="margin-top:14px;text-align:center" data-i18n="vat_notice_only">Sve cijene su bez PDV-a, gdje je primjenjivo.</p>
</section>

<section class="section--tight wrap">
<h2 class="h3" style="margin-bottom:14px" data-i18n="trusted_heading">Povjerenje hiljada kupaca širom svijeta</h2>
{stats([("users", "stat_registered_buyers", "50,000+", "Registrovani kupci"), ("shield", "trust_verified", "400+", "Provjereni partneri"),
        ("clock", "stat_auctions_monthly", "100,000+", "Aukcija mjesečno"), ("package", "stat_assets_unlocked", "€250M+", "Otključane vrijednosti"),
        ("star", "stat_buyer_rating", "4.8/5", "Ocjena kupaca")], extra=" stats--5")}
</section>

<section class="section wrap" id="compare">
<h2 class="h2" style="margin-bottom:16px" data-i18n="compare_plans_heading">Uporedi pakete</h2>
<div class="table-scroll">
<table class="ctable">
<caption class="sr-only" data-i18n="caption_compare">Poređenje funkcija četiri BidMont paketa kredita</caption>
<thead>{thead}</thead>
<tbody>{tbody}</tbody>
</table>
</div>
</section>

<section class="section wrap" id="faq">
<h2 class="h2" style="margin-bottom:16px" data-i18n="faq_heading">Često postavljana pitanja</h2>
{faq_block(FAQ_ITEMS, open_first=True)}
</section>

<section class="section wrap">
<div class="cta-banner">
<div class="cta-banner__bg"><img src="assets/img/handshake.webp" srcset="assets/img/handshake-sm.webp 700w, assets/img/handshake.webp 1400w" sizes="(min-width:900px) 1180px, 100vw" alt="" width="1400" height="500" loading="lazy" decoding="async"></div>
<div class="cta-banner__in">
<div>
<h2 class="h2" data-i18n="cta_banner_heading">Spremni da otključate svijet provjerenih partnerskih aukcija?</h2>
<p class="lead" style="margin-top:8px" data-i18n="cta_banner_desc">Pridružite se hiljadama kupaca koji vjeruju BidMont-u za rast svog poslovanja.</p>
</div>
<div class="btns">
<a class="btn btn--primary btn--lg" href="#pricing" data-i18n="buy_credits_now">Kupi kredite sada</a>
<a class="btn btn--outline btn--lg" href="auctions.html" data-i18n="explore_auctions">Istraži aukcije</a>
</div>
</div>
</div>
</section>
'''

# ================================================================ AUCTIONS ---
# data-cat carries the canonical English category name (must match
# category_seed.py's TOP_LEVEL by name - see comment there) so assets/js/api.js
# can match a click to the live category_id regardless of which language is
# displayed. "" is the sentinel for "no category filter", mirroring how
# sb-location's "All locations" option already uses value="" below.
CHIPS = [("grid", "", "cat_all", "Sve kategorije", True), ("car", "Cars", "cat_cars", "Automobili", False),
         ("crane", "Heavy Equipment", "cat_heavy_equipment", "Teška mehanizacija", False),
         ("home", "Real Estate", "cat_real_estate", "Nekretnine", False), ("boat", "Marine", "cat_marine", "Plovila", False),
         ("gem", "Luxury", "cat_luxury", "Luksuz", False), ("tractor", "Industrial Machinery", "cat_industrial", "Industrijske mašine", False),
         ("monitor", "Electronics", "cat_electronics", "Elektronika", False), ("truck", "Trucks", "cat_trucks", "Kamioni", False)]
chips = "".join(
    f'<button class="chip{" is-active" if act else ""}" type="button" data-cat="{cat}" aria-pressed="{"true" if act else "false"}">{i(ic, 16)}<span data-i18n="{k}">{n}</span></button>'
    for ic, cat, k, n, act in CHIPS)

# value= stays the English slug (SELLER_TYPES/ENDTIMES already worked this way;
# LOCATIONS did not, and needed the same treatment for the same reason - see
# the coupling-fix note by sb-category/sort-select below).
SELLER_TYPES = [("dealer_type", "Diler", "dealer", False), ("rent_a_car", "Rent-a-car", "rent-a-car", False), ("insurer_type", "Osiguravajuće društvo", "insurer", False),
                ("construction_type", "Građevina", "construction", False), ("individual_type", "Fizičko lice", "individual", False)]
LOCATIONS = [("loc_all", "Sve lokacije", "", True), ("loc_uae", "Ujedinjeni Arapski Emirati", "United Arab Emirates", False),
             ("loc_us", "Sjedinjene Američke Države", "United States", False), ("loc_uk", "Ujedinjeno Kraljevstvo", "United Kingdom", False),
             ("loc_de", "Njemačka", "Germany", False), ("loc_sg", "Singapur", "Singapore", False)]


def checks(name, items):
    out = ""
    for key, label, value, checked in items:
        ck = " checked" if checked else ""
        out += f'''<label class="check"><input type="checkbox" name="{name}" value="{value}"{ck}><span class="check__box">{i("check", 11)}</span>
<span class="check__label" data-i18n="{key}">{label}</span></label>'''
    return out


ENDTIMES = [("end_any", "Bilo kada", ""), ("end_24h", "Ističe za 24 sata", "24"), ("end_3d", "Ističe za 3 dana", "72"),
            ("end_7d", "Ističe za 7 dana", "168"), ("end_7d_plus", "Ističe za 7+ dana", "168+")]


def filters_markup(sfx):
    radios = "".join(
        f'<label class="radio"><input type="radio" name="end-{sfx}" value="{v}"{" checked" if n == 0 else ""}><span class="radio__dot"></span><span data-i18n="{key}">{t}</span></label>'
        for n, (key, t, v) in enumerate(ENDTIMES))
    return f'''<div class="filters__group is-open">
<button class="filters__head" type="button" aria-expanded="true"><span data-i18n="filter_seller_type">Tip prodavca</span> {i("chev-d", 17)}</button>
<div class="filters__body"><div><div class="inner">
{checks("seller_type", SELLER_TYPES)}
</div></div></div>
</div>
<div class="filters__group">
<button class="filters__head" type="button" aria-expanded="false"><span data-i18n="field_location">Lokacija</span> {i("chev-d", 17)}</button>
<div class="filters__body"><div><div class="inner">
{checks("location", LOCATIONS)}
</div></div></div>
</div>
<div class="filters__group">
<button class="filters__head" type="button" aria-expanded="false"><span data-i18n="filter_price_range">Cjenovni razred (trenutna cijena)</span> {i("chev-d", 17)}</button>
<div class="filters__body"><div><div class="inner">
<div class="range-row">
<label class="sr-only" for="pmin-{sfx}" data-i18n="sr_min_price">Minimalna cijena</label><input class="input" id="pmin-{sfx}" type="number" min="0" placeholder="Min. cijena" data-i18n-attr="placeholder:ph_min_price">
<span data-i18n="range_to">do</span>
<label class="sr-only" for="pmax-{sfx}" data-i18n="sr_max_price">Maksimalna cijena</label><input class="input" id="pmax-{sfx}" type="number" min="0" placeholder="Maks. cijena" data-i18n-attr="placeholder:ph_max_price">
</div>
</div></div></div>
</div>
<div class="filters__group">
<button class="filters__head" type="button" aria-expanded="false"><span data-i18n="filter_end_time">Vrijeme isteka</span> {i("chev-d", 17)}</button>
<div class="filters__body"><div><div class="inner">{radios}</div></div></div>
</div>
<div class="filters__group">
<button class="filters__head" type="button" aria-expanded="false"><span data-i18n="filter_access_credits">Krediti za pristup</span> {i("chev-d", 17)}</button>
<div class="filters__body"><div><div class="inner">
<div class="range-row">
<label class="sr-only" for="cmin-{sfx}" data-i18n="sr_min_credits">Minimalni krediti</label><input class="input" id="cmin-{sfx}" type="number" min="0" placeholder="Min. krediti" data-i18n-attr="placeholder:ph_min_credits">
<span data-i18n="range_to">do</span>
<label class="sr-only" for="cmax-{sfx}" data-i18n="sr_max_credits">Maksimalni krediti</label><input class="input" id="cmax-{sfx}" type="number" min="0" placeholder="Maks. krediti" data-i18n-attr="placeholder:ph_max_credits">
</div>
</div></div></div>
</div>
<div class="filters__actions">
<button class="btn btn--primary btn--block" type="button" data-apply-filters data-filters-close data-i18n="apply_filters">Primijeni filtere</button>
<button class="btn btn--outline btn--block" type="button" data-reset-filters data-i18n="reset_filters">Poništi filtere</button>
</div>'''


PARTNER_CARDS = [("rb.", "Ritchie Bros.", "40,000+", "15+"), ("cp", "Copart", "200,000+", "11+"),
                 ("IP", "IronPlanet", "85,000+", "9+"), ("YW", "YachtWorld Auctions", "12,000+", "3+")]
partner_cards = "".join(f'''<div class="partner-card">
<div class="partner-card__top"><span class="partner-card__logo">{lg}</span>
<div><b>{nm}</b><p class="tiny" style="display:flex;align-items:center;gap:4px">{i("shield", 12)}<span data-i18n="verified_partner">Provjereni partner</span></p></div></div>
<div class="partner-card__nums"><div><b>{a}</b><span data-i18n="auctions_sold">Prodatih aukcija</span></div><div><b>{c}</b><span data-i18n="countries">Zemalja</span></div></div>
</div>''' for lg, nm, a, c in PARTNER_CARDS)

TREND = [("cat-cars", "cat_cars", "Automobili", "12,540+ aukcija"), ("cat-heavy", "cat_heavy_equipment", "Teška mehanizacija", "8,320+ aukcija"),
         ("cat-real-estate", "cat_real_estate", "Nekretnine", "2,150+ aukcija"), ("cat-marine", "cat_marine", "Plovila", "1,250+ aukcija"),
         ("cat-industrial", "cat_industrial", "Industrijske mašine", "6,780+ aukcija")]
trend = "".join(f'''<figure class="trend__card"><a href="#"><img src="assets/img/{im}.webp" srcset="assets/img/{im}-md.webp 400w, assets/img/{im}.webp 800w" sizes="(min-width:760px) 230px, 46vw" alt="{t}" width="800" height="640" loading="lazy" decoding="async">
<figcaption><b data-i18n="{k}">{t}</b><span>{s}</span></figcaption></a></figure>''' for im, k, t, s in TREND)

auctions_body = f'''
<section class="section--tight wrap">
<nav class="crumbs" aria-label="Navigacija" data-i18n-attr="aria-label:breadcrumb"><a href="index.html" data-i18n="crumb_home">Početna</a>{i("chev-r", 13)}<span aria-current="page" data-i18n="crumb_partner_auctions">Partnerske aukcije</span></nav>
<div class="sec-head" style="margin-bottom:14px">
<div>
<h1 class="h1" style="font-size:clamp(28px,5vw,40px)" data-i18n-html="auctions_h1">Aukcije <span class="red">uživo</span></h1>
<p class="lead" style="margin-top:8px;font-size:13.5px" data-i18n="auctions_lead">Licitirajte direktno na provjerenim aukcijama vozila, teške mehanizacije, nekretnina, plovila, industrijskih mašina i drugog.</p>
</div>
{trust([("shield", "trust_verified", "Provjereni partneri"), ("lock", "trust_secure_payments", "Bezbjedne uplate"), ("clock", "trust_transparent", "Transparentan pristup")])}
</div>

<form class="searchbar" role="search" onsubmit="return false" style="margin-bottom:14px">
<div class="searchbar__field">
{i("search", 18, "muted")}
<label class="sr-only" for="q-auctions" data-i18n="search_auctions">Pretraži aukcije</label>
<input id="q-auctions" type="search" placeholder="Pretražite po ključnoj riječi, marki, modelu, lokaciji…" data-i18n-attr="placeholder:ph_search_auctions">
<button class="searchbar__btn" type="submit" aria-label="Pretraga" data-i18n-attr="aria-label:search">{i("search", 18)}</button>
</div>
<div class="searchbar__opts">
<label class="select"><span class="sr-only" data-i18n="field_category">Kategorija</span><select id="sb-category"><option value="" data-i18n="cat_all">Sve kategorije</option><option value="Cars" data-i18n="cat_cars">Automobili</option><option value="Heavy Equipment" data-i18n="cat_heavy_equipment">Teška mehanizacija</option><option value="Real Estate" data-i18n="cat_real_estate">Nekretnine</option><option value="Marine" data-i18n="cat_marine">Plovila</option><option value="Luxury" data-i18n="cat_luxury">Luksuz</option></select></label>
<label class="select"><span class="sr-only" data-i18n="field_location">Lokacija</span><select id="sb-location"><option value="" data-i18n="loc_all">Sve lokacije</option><option value="United Arab Emirates" data-i18n="loc_uae">Ujedinjeni Arapski Emirati</option><option value="United States" data-i18n="loc_us">Sjedinjene Američke Države</option><option value="United Kingdom" data-i18n="loc_uk">Ujedinjeno Kraljevstvo</option><option value="Germany" data-i18n="loc_de">Njemačka</option></select></label>
</div>
<button class="btn btn--outline btn-filters" type="button" data-filters-open>{i("sliders", 17)}<span data-i18n="filters">Filteri</span></button>
</form>

<div class="chips" id="categories" role="group" aria-label="Filter kategorija" data-i18n-attr="aria-label:category_filter">{chips}</div>
</section>

<section class="wrap" style="padding-bottom:36px">
<div class="layout-auctions">
<aside class="filters filters-desktop" aria-label="Filteri" data-i18n-attr="aria-label:filters">{filters_markup("d")}</aside>
<div>
<div class="results-head">
<p class="count" data-i18n="results_count_placeholder">Rezultata: 1.248</p>
<div style="display:flex;gap:8px;align-items:center">
<a class="btn btn--primary btn--sm is-hidden" href="account.html#listings" data-sell-cta data-i18n="list_an_auction">Postavi aukciju</a>
<label class="select"><span class="sr-only" data-i18n="sort_by">Sortiraj po</span>
<select id="sort-select"><option value="end_time_asc" data-i18n="sort_ending_soonest">Ističe najskorije</option><option value="created_at_desc" data-i18n="sort_newly_listed">Novo objavljeno</option><option value="price_asc" data-i18n="sort_price_asc">Cijena: rastuće</option><option value="price_desc" data-i18n="sort_price_desc">Cijena: opadajuće</option><option value="credits_asc" data-i18n="sort_fewest_credits">Najmanje kredita</option></select></label>
</div>
</div>
<div class="grid-auctions">{"".join(auction_card(a, n, lazy=(n > 2)) for n, a in enumerate(AUCTIONS))}</div>
<div style="display:flex;justify-content:center;margin-top:24px">
<button class="btn btn--outline btn--lg" type="button" data-load-more data-i18n="load_more_auctions">Učitaj još aukcija</button>
</div>
</div>
</div>
</section>

<section class="section--tight wrap" id="guest-promo">
<div class="promo">
<div>
<h2 class="h3" style="margin-bottom:6px" data-i18n="access_more_heading">Pristupite više. Licitirajte sa sigurnošću.</h2>
<p class="tiny" data-i18n="access_more_desc">Pridružite se BidMont-u da pristupite provjerenim partnerskim aukcijama i ekskluzivnim prilikama.</p>
<a class="btn btn--primary" href="auth.html#create" style="margin-top:14px" data-i18n="sign_up_now">Registruj se sada</a>
</div>
<div class="promo__items">
<div class="feature"><span class="ic">{i("users", 19)}</span><div><b data-i18n="trusted_partners">Pouzdani partneri</b><span data-i18n="trusted_partners_desc">Sarađujemo isključivo sa provjerenim aukcijskim kućama.</span></div></div>
<div class="feature"><span class="ic">{i("shield", 19)}</span><div><b data-i18n="trust_secure">Bezbjedno i transparentno</b><span data-i18n="secure_transparent_desc">Pravičan pristup, jasne cijene i sigurna plaćanja.</span></div></div>
<div class="feature"><span class="ic">{i("globe", 19)}</span><div><b data-i18n="global_opportunities">Globalne prilike</b><span data-i18n="global_opportunities_desc">Pristupite vrhunskim dobrima širom svijeta.</span></div></div>
</div>
</div>
</section>

<section class="section--tight wrap">
<div class="sec-head"><h2 class="h3" data-i18n="featured_partners">Izdvojeni partneri</h2><a class="link-arrow" href="#"><span data-i18n="view_all_partners">Pogledaj sve partnere</span> {i("arrow", 15)}</a></div>
<div class="partners">{partner_cards}</div>
</section>

<section class="section wrap">
<div class="sec-head"><h2 class="h3" data-i18n="trending_categories">Popularne kategorije</h2><a class="link-arrow" href="#"><span data-i18n="view_all_categories">Pogledaj sve kategorije</span> {i("arrow", 15)}</a></div>
<div class="trend">{trend}</div>
</section>

<div class="filter-drawer" data-filters>
<div class="filter-drawer__bg" data-filters-close></div>
<div class="filter-drawer__panel" role="dialog" aria-modal="true" aria-label="Filteri" data-i18n-attr="aria-label:filters">
<div class="filter-drawer__top">
<strong style="display:flex;align-items:center;gap:8px;font-size:15px">{i("sliders", 18)}<span data-i18n="filters">Filteri</span></strong>
<button class="burger" type="button" data-filters-close aria-label="Zatvori filtere" data-i18n-attr="aria-label:close_filters">{i("x", 20)}</button>
</div>
<div class="filter-drawer__body">{filters_markup("m")}</div>
</div>
</div>
'''

TABBAR = f'''<nav class="tabbar" aria-label="Brza navigacija" data-i18n-attr="aria-label:quick_nav">
<a href="index.html">{i("home", 20)}<span data-i18n="crumb_home">Početna</span></a>
<a href="auctions.html" aria-current="page">{i("crane", 20)}<span data-i18n="nav_auctions">Aukcije</span></a>
<a href="auctions.html#categories">{i("grid", 20)}<span data-i18n="nav_categories">Kategorije</span></a>
<a href="credits.html">{i("coins", 20)}<span data-i18n="credits_word">Krediti</span></a>
<a href="account.html">{i("user", 20)}<span data-i18n="tab_account">Nalog</span></a>
</nav>'''

# ==================================================================== AUTH ---
UPLOADS = [("idcard", "upl_id_t", "Lična karta", "upl_id_d", "Otpremite zvanični identifikacioni dokument"),
           ("bank", "upl_addr_t", "Dokaz o adresi", "upl_addr_d", "Otpremite skorašnji račun za usluge ili bankovni izvod"),
           ("selfie", "upl_selfie_t", "Selfi verifikacija", "upl_selfie_d", "Snimite selfi da potvrdite identitet")]
uploads = "".join(f'''<button class="upload" type="button" data-upload>
<span class="ic">{i(ic, 19)}</span><span><b data-i18n="{tk}">{t}</b><span data-i18n="{dk}">{d}</span></span><span class="chev">{i("chev-r", 17)}</span>
</button>''' for ic, tk, t, dk, d in UPLOADS)

COUNTRIES = [("country_select_prompt", "Izaberite državu"), ("country_tr", "Turska"), ("loc_uae", "Ujedinjeni Arapski Emirati"),
             ("loc_us", "Sjedinjene Američke Države"), ("loc_uk", "Ujedinjeno Kraljevstvo"), ("loc_de", "Njemačka"),
             ("country_nl", "Holandija"), ("loc_sg", "Singapur"), ("country_me", "Crna Gora")]
country_opts = "".join(f'<option data-i18n="{k}">{c}</option>' for k, c in COUNTRIES)

auth_body = f'''
<section class="section wrap">
<div class="auth">
<div class="auth__form">
<div class="tabs" role="tablist" aria-label="Pristup nalogu" data-i18n-attr="aria-label:account_access">
<button class="tab" id="tab-login" role="tab" aria-selected="true" aria-controls="pane-login" type="button">{i("user", 17)}<span data-i18n="hdr_login">Prijava</span></button>
<button class="tab" id="tab-create" role="tab" aria-selected="false" aria-controls="pane-create" type="button" tabindex="-1">{i("userplus", 17)}<span data-i18n="create_account">Kreiraj nalog</span></button>
</div>

<div class="pane is-active" id="pane-login" role="tabpanel" aria-labelledby="tab-login">
<h1 class="h2" style="font-size:24px" data-i18n="welcome_back">Dobrodošli nazad</h1>
<p class="lead" style="font-size:13.5px;margin:6px 0 22px" data-i18n="login_desc">Prijavite se na svoj BidMont nalog</p>
<form novalidate data-form="login">
<div class="field">
<label for="login-email" data-i18n="field_email">Email adresa</label>
<div class="field__wrap">{i("mail", 17)}<input id="login-email" name="email" type="email" autocomplete="email" placeholder="Unesite email adresu" data-i18n-attr="placeholder:ph_email" required></div>
<p class="field__error" data-i18n="err_email">Unesite ispravnu email adresu.</p>
</div>
<div class="field">
<label for="login-pass" data-i18n="field_password">Lozinka</label>
<div class="field__wrap">{i("lock", 17)}<input id="login-pass" name="password" type="password" autocomplete="current-password" placeholder="Unesite lozinku" data-i18n-attr="placeholder:ph_password" required>
<button class="eye" type="button" data-toggle-pass aria-label="Prikaži lozinku" data-i18n-attr="aria-label:show_password" aria-pressed="false">{i("eye", 17)}</button></div>
<p class="field__error" data-i18n="err_password_required">Unesite lozinku.</p>
</div>
<div class="field is-hidden" id="login-totp-wrap">
<label for="login-totp" data-i18n="field_totp">Autentifikacioni kod</label>
<div class="field__wrap">{i("lock", 17)}<input id="login-totp" name="totp_code" type="text" inputmode="numeric" autocomplete="one-time-code" placeholder="123456" maxlength="6"></div>
<p class="field__hint" data-i18n="hint_totp">Ovaj nalog ima uključenu dvofaktorsku autentifikaciju — unesite 6-cifreni kod iz svoje aplikacije za autentifikaciju.</p>
</div>
<div class="form-row">
<label class="check"><input type="checkbox" checked><span class="check__box">{i("check", 11)}</span><span class="check__label" data-i18n="remember_me">Zapamti me</span></label>
<a class="red" href="#" style="font-size:12.5px;font-weight:600" data-i18n="forgot_password">Zaboravili ste lozinku?</a>
</div>
<button class="btn btn--primary btn--block btn--lg" type="submit" data-i18n="hdr_login">Prijava</button>
</form>
<div class="divider" data-i18n="divider_or">ili</div>
<button class="btn btn--outline btn--block" type="button">{GOOGLE}<span data-i18n="continue_google">Nastavi sa Google-om</span></button>
<p class="tiny" style="text-align:center;margin-top:18px" data-i18n-html="no_account_yet">Nemate nalog? <button class="red" style="font-weight:600" type="button" data-goto-tab="create">Kreirajte nalog</button></p>
</div>

<div class="pane" id="pane-create" role="tabpanel" aria-labelledby="tab-create" tabindex="0">
<div class="stepper" data-stepper>
<div class="stepper__item is-active" data-step="1"><span class="stepper__dot">1</span><span class="stepper__lbl" data-i18n="step_account">Nalog</span></div>
<span class="stepper__bar"></span>
<div class="stepper__item" data-step="2"><span class="stepper__dot">2</span><span class="stepper__lbl" data-i18n="step_verify">Provjera</span></div>
<span class="stepper__bar"></span>
<div class="stepper__item" data-step="3"><span class="stepper__dot">3</span><span class="stepper__lbl" data-i18n="step_complete">Završeno</span></div>
</div>

<div class="pane is-active" data-substep="1">
<h1 class="h2" style="font-size:24px" data-i18n="create_account_heading">Kreirajte svoj nalog</h1>
<p class="lead" style="font-size:13.5px;margin:6px 0 22px" data-i18n="join_bidmont_desc">Pridružite se BidMont-u da pristupite partnerskim aukcijama</p>
<form novalidate data-form="signup">
<div class="field">
<label for="su-name" data-i18n="field_fullname">Ime i prezime</label>
<div class="field__wrap">{i("user", 17)}<input id="su-name" name="name" type="text" autocomplete="name" placeholder="Unesite ime i prezime" data-i18n-attr="placeholder:ph_fullname" required></div>
<p class="field__error" data-i18n="err_fullname">Unesite ime i prezime.</p>
</div>
<div class="field">
<label for="su-email" data-i18n="field_email">Email adresa</label>
<div class="field__wrap">{i("mail", 17)}<input id="su-email" name="email" type="email" autocomplete="email" placeholder="Unesite email adresu" data-i18n-attr="placeholder:ph_email" required></div>
<p class="field__error" data-i18n="err_email">Unesite ispravnu email adresu.</p>
</div>
<div class="field">
<label for="su-phone" data-i18n="field_phone_number">Broj telefona</label>
<div class="phone">
<div class="field__wrap"><label class="sr-only" for="su-code" data-i18n="field_country_code">Pozivni broj</label>
<select id="su-code"><option>+90</option><option>+971</option><option>+1</option><option>+44</option><option>+49</option></select>{i("chev-d", 14)}</div>
<div class="field__wrap">{i("phone", 17)}<input id="su-phone" name="phone" type="tel" autocomplete="tel" placeholder="Unesite broj telefona" data-i18n-attr="placeholder:ph_phone" required></div>
</div>
<p class="field__error" data-i18n="err_phone">Unesite broj telefona.</p>
</div>
<div class="field">
<label for="su-pass" data-i18n="field_password">Lozinka</label>
<div class="field__wrap">{i("lock", 17)}<input id="su-pass" name="password" type="password" autocomplete="new-password" placeholder="Kreirajte lozinku" data-i18n-attr="placeholder:ph_create_password" required minlength="8">
<button class="eye" type="button" data-toggle-pass aria-label="Prikaži lozinku" data-i18n-attr="aria-label:show_password" aria-pressed="false">{i("eye", 17)}</button></div>
<p class="field__hint" data-i18n="hint_password">Najmanje 8 karaktera, sa jednim brojem.</p>
<p class="field__error" data-i18n="err_password_format">Koristite najmanje 8 karaktera, uključujući jedan broj.</p>
</div>
<div class="field">
<label for="su-country" data-i18n="field_country">Država</label>
<div class="field__wrap">{i("globe", 17)}<select id="su-country" name="country" required>{country_opts}</select>{i("chev-d", 14)}</div>
<p class="field__error" data-i18n="err_country">Izaberite državu.</p>
</div>
<div class="field">
<label class="check" style="align-items:flex-start"><input type="checkbox" name="terms" required><span class="check__box" style="margin-top:1px">{i("check", 11)}</span>
<span class="check__label tiny" data-i18n-html="agree_terms">Slažem se sa <a class="red" href="#" data-legal="terms_of_service" style="font-weight:600;text-decoration:underline">Uslovima korišćenja</a> i <a class="red" href="#" data-legal="privacy_policy" style="font-weight:600;text-decoration:underline">Politikom privatnosti</a></span></label>
<p class="field__error" data-i18n="err_terms">Prihvatite uslove da biste nastavili.</p>
</div>
<button class="btn btn--primary btn--block btn--lg" type="submit" data-i18n="create_account">Kreiraj nalog</button>
</form>
<p class="tiny" style="text-align:center;margin-top:16px" data-i18n-html="already_have_account">Već imate nalog? <button class="red" style="font-weight:600" type="button" data-goto-tab="login">Prijavite se</button></p>
</div>

<div class="pane" data-substep="2">
<h2 class="h2" style="font-size:22px" data-i18n="verify_account_heading">Potvrdite svoj nalog</h2>
<p class="lead" style="font-size:13.5px;margin:6px 0 20px" data-i18n="verify_account_desc">Da bismo održali platformu bezbjednom, potrebno je da potvrdimo vaš identitet.</p>
<div class="stack">{uploads}</div>
<p class="tiny" style="display:flex;gap:7px;align-items:center;justify-content:center;margin-top:20px">{i("lock", 14)}<span data-i18n="info_encrypted">Vaši podaci su šifrovani i bezbjedni.</span></p>
<div style="display:grid;gap:9px;margin-top:20px">
<button class="btn btn--primary btn--block btn--lg" type="button" data-next-step data-i18n="submit_verification">Pošalji na verifikaciju</button>
<button class="btn btn--outline btn--block" type="button" data-prev-step data-i18n="back_button">Nazad</button>
</div>
</div>

<div class="pane" data-substep="3">
<div style="text-align:center">
<span class="success-mark">{i("check", 40)}</span>
<h2 class="h2" style="font-size:22px" data-i18n="verification_submitted_heading">Verifikacija poslata</h2>
<p class="lead" style="font-size:13.5px;margin:8px auto 20px" data-i18n="verification_submitted_desc">Hvala vam. Pregledamo vaše podatke i obavijestićemo vas čim vaš nalog bude verifikovan.</p>
</div>
<div class="panel panel--flat">
<h3 class="h3" style="font-size:14px;margin-bottom:12px" data-i18n="whats_next">Šta slijedi</h3>
<ul class="checklist">
<li>{i("check", 15)}<span data-i18n="check_review_docs">Pregledamo vaše dokumente</span></li>
<li>{i("check", 15)}<span data-i18n="check_verify_info">Provjeravamo vaše podatke</span></li>
<li>{i("check", 15)}<span data-i18n="check_approve">Odobravamo vaš nalog</span></li>
<li>{i("check", 15)}<span data-i18n="check_full_access">Dobijate pun pristup partnerskim aukcijama</span></li>
</ul>
</div>
<a class="btn btn--ghostred btn--block btn--lg" href="index.html" style="margin-top:18px" data-i18n="back_to_home">Nazad na početnu</a>
</div>
</div>
</div>

<aside class="auth__side">
<h2 class="h2" data-i18n-html="auth_side_h2">Pristupite <span class="red">provjerenim</span> partnerskim aukcijama</h2>
<p class="lead" style="font-size:13.5px;margin-top:8px" data-i18n="auth_side_desc">Pridružite se BidMont-u da pristupite ekskluzivnim partnerskim aukcijama vozila, teške mehanizacije, plovila, elektronike i drugog.</p>
<ul class="side-feats">
<li><span class="ic">{i("shield", 19)}</span><div><b data-i18n="trust_verified">Provjereni partneri</b><span data-i18n="side_feat1_desc">Sarađujte sa pouzdanim, unaprijed provjerenim aukcijskim kućama.</span></div></li>
<li><span class="ic">{i("lock", 19)}</span><div><b data-i18n="trust_secure_payments">Bezbjedne uplate</b><span data-i18n="side_feat2_desc">Vaša plaćanja i podaci su uvijek zaštićeni.</span></div></li>
<li><span class="ic">{i("clock", 19)}</span><div><b data-i18n="trust_transparent">Transparentan pristup</b><span data-i18n="side_feat3_desc">Jasni detalji aukcije i pravičan pristup za sve.</span></div></li>
</ul>
<img src="assets/img/hero-sm.webp" alt="Dobra dostupna kroz BidMont partnerske aukcije" width="700" height="429" style="border-radius:var(--r);margin-bottom:16px" loading="lazy" decoding="async">
<div class="notice">
<span class="ic" style="width:34px;height:34px">{i("shield", 17)}</span>
<div><b data-i18n="notice_title">Potrebna je verifikacija naloga</b><p data-i18n="notice_desc">Pristup partnerskim aukcijama zahtijeva verifikovan nalog.</p>
<a class="red" href="#" style="font-size:12px;font-weight:600;text-decoration:underline" data-i18n="learn_more">Saznaj više</a></div>
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
# wireAuctionDetail() reads `?id=` and fills every #det-* element client-side
# (still English, see the api.js dynamic-strings note in i18n.js) - only the
# static chrome around it is translated here.
auction_detail_body = f'''
<section class="section--tight wrap">
<nav class="crumbs" aria-label="Navigacija" data-i18n-attr="aria-label:breadcrumb"><a href="index.html" data-i18n="crumb_home">Početna</a>{i("chev-r", 13)}<a href="auctions.html" data-i18n="nav_auctions">Aukcije</a>{i("chev-r", 13)}<span id="det-crumb" aria-current="page" data-i18n="loading">Učitavanje…</span></nav>
</section>

<section class="wrap" style="padding-bottom:36px">
<div class="layout-detail" id="det-notfound" style="display:none">
<div class="panel" style="text-align:center;grid-column:1/-1">
<h1 class="h2" data-i18n="det_not_found">Aukcija nije pronađena</h1>
<p class="lead" style="margin-top:8px" data-i18n="det_not_found_desc">Ovaj oglas je možda uklonjen ili je link netačan.</p>
<a class="btn btn--primary" href="auctions.html" style="margin-top:16px" data-i18n="browse_auctions">Pregledaj aukcije</a>
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
<h1 class="h2" id="det-title" data-i18n="loading">Učitavanje…</h1>
<p class="tiny" id="det-meta"></p>
</div>
<button class="fav" id="det-watch" type="button" aria-pressed="false" aria-label="Sačuvaj ovu aukciju" data-i18n-attr="aria-label:save_auction">{i("heart", 18)}</button>
</div>
<p id="det-desc" style="margin-top:12px"></p>
<dl class="detail-specs" id="det-specs"></dl>
</div>
<div class="panel is-hidden" id="det-docs-wrap">
<h2 class="h3" data-i18n="documents_heading">Dokumenti</h2>
<ul class="checklist" id="det-docs"></ul>
</div>
<div class="panel">
<h2 class="h3" data-i18n="bid_history">Istorija ponuda</h2>
<div class="table-scroll"><table class="ctable">
<thead><tr><th scope="col" data-i18n="th_bidder">Ponuđač</th><th scope="col" data-i18n="th_amount">Iznos</th><th scope="col" data-i18n="th_time">Vrijeme</th></tr></thead>
<tbody id="det-bids"><tr><td colspan="3" class="tiny" data-i18n="no_bids_yet">Još nema ponuda.</td></tr></tbody>
</table></div>
</div>
</div>
<aside class="detail-side">
<div class="panel" id="det-price-panel">
<p class="lbl" data-i18n="lbl_current_price">Trenutna cijena</p>
<p class="detail-price" id="det-price">—</p>
<p class="tiny" style="margin-top:4px"><span data-i18n="lbl_ends_in">Ističe za</span> <b id="det-ends">—</b></p>
<p class="tiny" id="det-status-note" style="margin-top:4px"></p>
<div id="det-bid-area">
<div class="field">
<label for="det-bid-amount" data-i18n="field_your_bid">Vaša ponuda (€)</label>
<div class="field__wrap"><input id="det-bid-amount" type="number" min="0" step="1" placeholder="0"></div>
</div>
<button class="btn btn--primary btn--block btn--lg" id="det-bid-btn" type="button" data-i18n="place_bid">Licitiraj</button>
<p class="tiny" id="det-credit-note" style="margin-top:8px"></p>
</div>
</div>
<div class="panel is-hidden" id="det-contact-panel">
<h2 class="h3" data-i18n="contact_details">Kontakt podaci</h2>
<p class="tiny" id="det-contact-body" style="margin-top:6px"></p>
</div>
</aside>
</div>
</section>

<div class="lightbox" id="det-lightbox" data-lightbox>
<div class="lightbox__bg" data-lightbox-close></div>
<button class="burger lightbox__close" type="button" data-lightbox-close aria-label="Zatvori sliku" data-i18n-attr="aria-label:close_image">{i("x", 22)}</button>
<button class="lightbox__nav lightbox__prev" type="button" data-lightbox-prev aria-label="Prethodna slika" data-i18n-attr="aria-label:prev_image">{i("chev-r", 22)}</button>
<img class="lightbox__img" id="det-lightbox-img" src="" alt="">
<button class="lightbox__nav lightbox__next" type="button" data-lightbox-next aria-label="Sljedeća slika" data-i18n-attr="aria-label:next_image">{i("chev-r", 22)}</button>
</div>
'''

# =================================================================== ACCOUNT ---
ACCT_TABS = [("overview", "tab_overview", "Pregled"), ("bids", "tab_my_bids", "Moje ponude"), ("joined", "tab_joined", "Pridružene"),
             ("watchlist", "tab_watchlist", "Lista praćenja"), ("notifications", "tab_notifications", "Obavještenja"),
             ("settings", "tab_settings", "Podešavanja"), ("listings", "tab_my_listings", "Moji oglasi")]
acct_tabs_nav = "".join(
    f'<button class="tab" id="tab-{k}" role="tab" aria-selected="{"true" if n == 0 else "false"}" '
    f'aria-controls="pane-{k}" type="button"{"" if n == 0 else " tabindex=\"-1\""}{" is-hidden" if k == "listings" else ""}><span data-i18n="{tkey}">{t}</span></button>'
    for n, (k, tkey, t) in enumerate(ACCT_TABS))

account_body = f'''
<section class="section--tight wrap">
<nav class="crumbs" aria-label="Navigacija" data-i18n-attr="aria-label:breadcrumb"><a href="index.html" data-i18n="crumb_home">Početna</a>{i("chev-r", 13)}<span aria-current="page" data-i18n="my_account">Moj nalog</span></nav>
<h1 class="h1" style="font-size:clamp(24px,4vw,32px)" data-i18n="my_account">Moj nalog</h1>
</section>

<section class="wrap" style="padding-bottom:36px">
<div class="panel" id="acct-loggedout">
<p class="lead" style="font-size:13.5px" data-i18n="acct_loggedout_desc">Prijavite se da vidite svoje ponude, listu praćenja i stanje kredita.</p>
<a class="btn btn--primary" href="auth.html" style="margin-top:12px" data-i18n="hdr_login">Prijava</a>
</div>

<div id="acct-root" class="is-hidden">
<div class="tabs tabs--scroll" role="tablist" aria-label="Djelovi naloga" data-i18n-attr="aria-label:account_sections">{acct_tabs_nav}</div>

<div class="pane is-active" id="pane-overview" role="tabpanel" aria-labelledby="tab-overview">
<div class="panel">
<p class="wallet__lbl" data-i18n="credit_balance">Stanje kredita</p>
<p class="wallet__amt" id="acct-balance">— <small data-i18n="credits_word">Krediti</small></p>
<a class="btn btn--outline" href="credits.html" style="margin-top:12px" data-i18n="buy_more_credits">Kupi još kredita</a>
</div>
<div class="panel" style="margin-top:14px">
<h2 class="h3" style="margin-bottom:10px" data-i18n="recent_credit_activity">Nedavna aktivnost kredita</h2>
<div class="table-scroll"><table class="ctable">
<thead><tr><th scope="col" data-i18n="th_type">Tip</th><th scope="col" data-i18n="th_amount">Iznos</th><th scope="col" data-i18n="th_balance_after">Stanje nakon</th><th scope="col" data-i18n="th_date">Datum</th></tr></thead>
<tbody id="acct-ledger"><tr><td colspan="4" class="tiny" data-i18n="no_activity_yet">Još nema aktivnosti.</td></tr></tbody>
</table></div>
</div>
</div>

<div class="pane" id="pane-bids" role="tabpanel" aria-labelledby="tab-bids" tabindex="0">
<div class="panel"><div class="table-scroll"><table class="ctable">
<thead><tr><th scope="col" data-i18n="th_auction">Aukcija</th><th scope="col" data-i18n="th_my_bid">Moja ponuda</th><th scope="col" data-i18n="th_status">Status</th><th scope="col" data-i18n="th_date">Datum</th></tr></thead>
<tbody id="acct-bids-body"><tr><td colspan="4" class="tiny" data-i18n="no_bids_yet">Još nema ponuda.</td></tr></tbody>
</table></div></div>
</div>

<div class="pane" id="pane-joined" role="tabpanel" aria-labelledby="tab-joined" tabindex="0">
<div class="panel"><div class="table-scroll"><table class="ctable">
<thead><tr><th scope="col" data-i18n="th_auction">Aukcija</th><th scope="col" data-i18n="th_credits_spent">Potrošeni krediti</th><th scope="col" data-i18n="th_my_status">Moj status</th><th scope="col" data-i18n="th_joined">Pridružen</th></tr></thead>
<tbody id="acct-joined-body"><tr><td colspan="4" class="tiny" data-i18n="no_joined_yet">Još se niste pridružili nijednoj aukciji.</td></tr></tbody>
</table></div></div>
</div>

<div class="pane" id="pane-watchlist" role="tabpanel" aria-labelledby="tab-watchlist" tabindex="0">
<div class="grid-auctions" id="acct-watchlist-grid">{auction_card(AUCTIONS[0], 0, lazy=False)}</div>
</div>

<div class="pane" id="pane-notifications" role="tabpanel" aria-labelledby="tab-notifications" tabindex="0">
<div class="panel"><ul class="notif-list" id="acct-notif-list"><li class="tiny" data-i18n="no_notifications_yet">Još nema obavještenja.</li></ul></div>
</div>

<div class="pane" id="pane-settings" role="tabpanel" aria-labelledby="tab-settings" tabindex="0">
<div class="panel">
<h2 class="h3" style="margin-bottom:14px" data-i18n="profile_heading">Profil</h2>
<form id="acct-profile-form">
<div class="field"><label for="acct-name" data-i18n="field_fullname">Ime i prezime</label><div class="field__wrap">{i("user", 17)}<input id="acct-name" type="text"></div></div>
<div class="field"><label for="acct-phone" data-i18n="field_phone">Telefon</label><div class="field__wrap">{i("phone", 17)}<input id="acct-phone" type="tel"></div></div>
<div class="field"><label for="acct-city" data-i18n="field_city">Grad</label><div class="field__wrap">{i("home", 17)}<input id="acct-city" type="text"></div></div>
<div class="field"><label for="acct-address" data-i18n="field_address">Adresa</label><div class="field__wrap">{i("doc", 17)}<input id="acct-address" type="text"></div></div>
<button class="btn btn--primary" type="submit" data-i18n="save_profile">Sačuvaj profil</button>
</form>
</div>
<div class="panel" style="margin-top:14px">
<h2 class="h3" style="margin-bottom:14px" data-i18n="change_password_heading">Promjena lozinke</h2>
<form id="acct-password-form">
<div class="field"><label for="acct-pw-current" data-i18n="field_current_password">Trenutna lozinka</label><div class="field__wrap">{i("lock", 17)}<input id="acct-pw-current" type="password" autocomplete="current-password"></div></div>
<div class="field"><label for="acct-pw-new" data-i18n="field_new_password">Nova lozinka</label><div class="field__wrap">{i("lock", 17)}<input id="acct-pw-new" type="password" autocomplete="new-password" minlength="6"></div></div>
<button class="btn btn--primary" type="submit" data-i18n="update_password">Ažuriraj lozinku</button>
</form>
</div>
<div class="panel is-hidden" id="acct-seller-manage-wrap" style="margin-top:14px">
<h2 class="h3" style="margin-bottom:6px" data-i18n="selling_heading">Prodaja na BidMont-u</h2>
<p class="tiny" style="margin-bottom:12px" data-i18n="selling_desc">Upravljajte svojim oglasima ili dodajte novu aukciju.</p>
<button class="btn btn--primary" type="button" data-goto-tab="listings" data-i18n="manage_listings">Upravljaj oglasima</button>
</div>
<div class="panel" id="acct-seller-apply-wrap" style="margin-top:14px">
<h2 class="h3" style="margin-bottom:6px" data-i18n="sell_heading">Prodajte na BidMont-u</h2>
<p class="tiny" style="margin-bottom:12px" id="acct-seller-apply-note" data-i18n="seller_apply_note">Potvrdite svoj email, a zatim se prijavite da postanete prodavac.</p>
<form id="acct-seller-form">
<div class="field"><label for="acct-seller-type" data-i18n="field_account_type">Tip naloga</label><div class="field__wrap">{i("user", 17)}<select id="acct-seller-type"><option value="individual" data-i18n="opt_individual">Fizičko lice</option><option value="company" data-i18n="opt_company">Kompanija</option></select></div></div>
<div class="field"><label for="acct-seller-doc" data-i18n="field_verification_doc">Dokument za verifikaciju (rješenje o registraciji, lična karta — opciono)</label><input type="file" id="acct-seller-doc" accept=".jpg,.jpeg,.png,.webp,.pdf"></div>
<button class="btn btn--outline" type="submit" data-i18n="apply_to_sell">Prijavi se za prodaju</button>
</form>
</div>
<button class="btn btn--ghostred" type="button" id="acct-logout" style="margin-top:14px" data-i18n="log_out">Odjavi se</button>
</div>

<div class="pane" id="pane-listings" role="tabpanel" aria-labelledby="tab-listings" tabindex="0">
<div class="features" id="acct-seller-stats" style="margin-bottom:14px"></div>
<div class="panel" style="margin-bottom:14px">
<h3 class="h3" style="margin-bottom:8px" data-i18n="bulk_upload_heading">Grupno otpremanje (CSV)</h3>
<p class="tiny" style="margin-bottom:10px" data-i18n="bulk_upload_desc">Kolone: title, description, category_id, start_price, min_increment, end_time, declaration_accepted (plus i svako opciono polje oglasa). Jedan red po oglasu.</p>
<input type="file" id="acct-bulk-csv" accept=".csv">
<button class="btn btn--outline" type="button" id="acct-bulk-upload-btn" style="margin-left:8px" data-i18n="upload_csv">Otpremi CSV</button>
<div id="acct-bulk-result" class="tiny" style="margin-top:10px"></div>
</div>
<div class="panel" style="margin-bottom:14px">
<button class="btn btn--outline" type="button" id="acct-listing-new-btn" data-i18n="new_listing">+ Novi oglas</button>
<form id="acct-listing-form" class="is-hidden" style="margin-top:14px" novalidate>
<input type="hidden" id="lst-id">
<div class="field"><label for="lst-title" data-i18n="field_title">Naslov</label><div class="field__wrap">{i("doc", 17)}<input id="lst-title" type="text" required minlength="3" maxlength="200"></div></div>
<div class="field"><label for="lst-desc" data-i18n="field_description">Opis</label><div class="field__wrap" style="align-items:flex-start;padding:10px 12px"><textarea id="lst-desc" rows="4" required minlength="10" maxlength="5000" style="border:0;outline:0;width:100%;font:inherit;resize:vertical;background:transparent"></textarea></div></div>
<div class="field"><label for="lst-category" data-i18n="field_category">Kategorija</label><div class="field__wrap">{i("grid", 17)}<select id="lst-category" required></select></div></div>
<div class="field"><label for="lst-price" data-i18n="field_start_price">Početna cijena (EUR)</label><div class="field__wrap">{i("coins", 17)}<input id="lst-price" type="number" min="0.01" step="0.01" required></div></div>
<div class="field"><label for="lst-increment" data-i18n="field_min_increment">Minimalni korak licitacije (EUR)</label><div class="field__wrap">{i("coins", 17)}<input id="lst-increment" type="number" min="0.01" step="0.01" required></div></div>
<div class="field"><label for="lst-end" data-i18n="field_ends_at">Ističe</label><div class="field__wrap">{i("clock", 17)}<input id="lst-end" type="datetime-local" required></div></div>
<div class="field"><label for="lst-location" data-i18n="field_location">Lokacija</label><div class="field__wrap">{i("home", 17)}<input id="lst-location" type="text"></div></div>
<h3 class="h3" style="margin:14px 0 8px" data-i18n="item_details_heading">Detalji predmeta (opciono)</h3>
<div class="field"><label for="lst-brand" data-i18n="field_brand">Marka</label><div class="field__wrap">{i("car", 17)}<input id="lst-brand" type="text" maxlength="100"></div></div>
<div class="field"><label for="lst-model" data-i18n="field_model">Model</label><div class="field__wrap">{i("car", 17)}<input id="lst-model" type="text" maxlength="100"></div></div>
<div class="field"><label for="lst-year" data-i18n="field_year">Godište</label><div class="field__wrap">{i("clock", 17)}<input id="lst-year" type="number" min="1900" max="2100"></div></div>
<div class="field"><label for="lst-mileage" data-i18n="field_mileage">Kilometraža (km)</label><div class="field__wrap">{i("car", 17)}<input id="lst-mileage" type="number" min="0"></div></div>
<div class="field"><label for="lst-fuel" data-i18n="field_fuel_type">Vrsta goriva</label><div class="field__wrap">{i("car", 17)}<input id="lst-fuel" type="text" maxlength="50"></div></div>
<div class="field"><label for="lst-transmission" data-i18n="field_transmission">Mjenjač</label><div class="field__wrap">{i("car", 17)}<input id="lst-transmission" type="text" maxlength="50"></div></div>
<div class="field"><label for="lst-equip-brand" data-i18n="field_equipment_brand">Marka opreme</label><div class="field__wrap">{i("package", 17)}<input id="lst-equip-brand" type="text" maxlength="100"></div></div>
<div class="field"><label for="lst-serial" data-i18n="field_serial">Serijski broj</label><div class="field__wrap">{i("package", 17)}<input id="lst-serial" type="text" maxlength="100"></div></div>
<div class="field"><label for="lst-condition" data-i18n="field_condition">Stanje</label><div class="field__wrap">{i("package", 17)}<input id="lst-condition" type="text" maxlength="100"></div></div>
<div class="field"><label for="lst-hours" data-i18n="field_operating_hours">Radni sati</label><div class="field__wrap">{i("clock", 17)}<input id="lst-hours" type="number" min="0"></div></div>
<div class="field"><label for="lst-quantity" data-i18n="field_quantity">Količina (komercijalna dobra)</label><div class="field__wrap">{i("package", 17)}<input id="lst-quantity" type="number" min="0"></div></div>
<div class="field"><label for="lst-photos" data-i18n="field_photos">Fotografije</label><div class="field__wrap">{i("doc", 17)}<input id="lst-photos" type="file" accept="image/jpeg,image/png,image/webp" multiple style="border:0;padding:6px 0"></div></div>
<div class="field"><label for="lst-doc-category" data-i18n="field_doc_type">Tip dokumenta</label><div class="field__wrap">{i("doc", 17)}<select id="lst-doc-category"><option value="registration" data-i18n="opt_registration">Registracija</option><option value="inspection" data-i18n="opt_inspection">Tehnički pregled</option><option value="service" data-i18n="opt_service_history">Servisna istorija</option><option value="other" data-i18n="opt_other">Ostalo</option></select></div></div>
<div class="field"><label for="lst-documents" data-i18n="field_documents_desc">Dokumenti (registracija, tehnički pregled, servis — privatno, vidi samo osoblje)</label><div class="field__wrap">{i("doc", 17)}<input id="lst-documents" type="file" accept="image/jpeg,image/png,image/webp,application/pdf" multiple style="border:0;padding:6px 0"></div></div>
<label class="check" id="lst-declaration-wrap" style="align-items:flex-start;margin-top:8px"><input type="checkbox" id="lst-declaration"><span class="check__box" style="margin-top:1px">{i("check", 11)}</span>
<span class="check__label tiny" data-i18n="declaration_text">Potvrđujem da imam ovlašćenje da oglasim ovaj predmet i da su svi navedeni podaci tačni.</span></label>
<div style="display:flex;gap:10px;margin-top:12px">
<button class="btn btn--primary" type="submit" id="lst-submit-btn" data-i18n="publish_listing">Objavi oglas</button>
<button class="btn btn--ghostred" type="button" id="acct-listing-cancel-btn" data-i18n="cancel_button">Otkaži</button>
</div>
</form>
</div>
<div id="acct-listings-list"><p class="tiny" data-i18n="loading">Učitavanje…</p></div>
</div>
</div>
</section>
'''

# ===================================================================== ADMIN ---
# Shell only, like account.html - assets/js/api.js's wireAdminPage() fills every
# #adm-*/pane-adm-* element (still English - see the api.js dynamic-strings
# note in i18n.js; staff-only screen, lower priority than buyer-facing pages).
ADMIN_TABS = [("overview", "tab_overview", "Pregled"), ("users", "tab_users", "Korisnici"), ("sellers", "tab_sellers", "Prodavci"),
              ("auctions", "nav_auctions", "Aukcije"), ("bids", "tab_bids", "Ponude"), ("categories", "nav_categories", "Kategorije"), ("support", "tab_support", "Podrška")]
ADMIN_TAB_COUNTS = {"sellers", "auctions", "support"}
admin_tabs_nav = "".join(
    f'<button class="tab" id="tab-adm-{k}" role="tab" aria-selected="{"true" if n == 0 else "false"}" '
    f'aria-controls="pane-adm-{k}" type="button"{"" if n == 0 else " tabindex=\"-1\""}><span data-i18n="{tkey}">{t}</span>'
    + (f'<span class="tab-count is-hidden" id="tab-adm-{k}-count" aria-hidden="true"></span>' if k in ADMIN_TAB_COUNTS else "")
    + "</button>"
    for n, (k, tkey, t) in enumerate(ADMIN_TABS))

admin_body = f'''
<section class="section--tight wrap">
<nav class="crumbs" aria-label="Navigacija" data-i18n-attr="aria-label:breadcrumb"><a href="index.html" data-i18n="crumb_home">Početna</a>{i("chev-r", 13)}<span aria-current="page" data-i18n="admin_label">Admin</span></nav>
<h1 class="h1" style="font-size:clamp(24px,4vw,32px)" data-i18n="admin_panel_heading">Admin panel</h1>
</section>

<section class="wrap" style="padding-bottom:36px">
<div class="panel" id="adm-denied">
<p class="lead" style="font-size:13.5px" data-i18n="checking_access">Provjera pristupa…</p>
</div>

<div id="adm-root" class="is-hidden">
<div class="tabs tabs--scroll" role="tablist" aria-label="Djelovi admin panela" data-i18n-attr="aria-label:admin_sections">{admin_tabs_nav}</div>

<div class="pane is-active" id="pane-adm-overview" role="tabpanel" aria-labelledby="tab-adm-overview">
<div class="features" id="adm-stats"></div>
</div>

<div class="pane" id="pane-adm-users" role="tabpanel" aria-labelledby="tab-adm-users" tabindex="0">
<div class="panel" style="margin-bottom:14px">
<div class="field" style="margin-bottom:0"><div class="field__wrap">{i("search", 17)}<input id="adm-users-search" type="text" placeholder="Pretraži ime ili email" data-i18n-attr="placeholder:ph_search_users"></div></div>
</div>
<div id="adm-users-list"><p class="tiny" data-i18n="loading">Učitavanje…</p></div>
</div>

<div class="pane" id="pane-adm-sellers" role="tabpanel" aria-labelledby="tab-adm-sellers" tabindex="0">
<div class="chips" id="adm-sellers-filter" role="group" aria-label="Filter statusa prodavca" style="margin-bottom:14px">
<button class="adm-chip is-active" type="button" data-status="pending" data-i18n="status_pending">Na čekanju</button>
<button class="adm-chip" type="button" data-status="verified" data-i18n="status_verified">Verifikovan</button>
<button class="adm-chip" type="button" data-status="rejected" data-i18n="status_rejected">Odbijen</button>
<button class="adm-chip" type="button" data-status="" data-i18n="status_all">Svi</button>
</div>
<div id="adm-sellers-list"><p class="tiny" data-i18n="loading">Učitavanje…</p></div>
</div>

<div class="pane" id="pane-adm-auctions" role="tabpanel" aria-labelledby="tab-adm-auctions" tabindex="0">
<div class="chips" id="adm-auctions-filter" role="group" aria-label="Filter statusa aukcije" style="margin-bottom:14px">
<button class="adm-chip is-active" type="button" data-status="under_review" data-i18n="status_pending_review">Na pregledu</button>
<button class="adm-chip" type="button" data-status="upcoming" data-i18n="status_upcoming">Predstoji</button>
<button class="adm-chip" type="button" data-status="live" data-i18n="status_live">Uživo</button>
<button class="adm-chip" type="button" data-status="ended" data-i18n="status_ended">Završena</button>
<button class="adm-chip" type="button" data-status="cancelled" data-i18n="status_cancelled">Otkazana</button>
<button class="adm-chip" type="button" data-status="" data-i18n="status_all_f">Sve</button>
</div>
<div id="adm-auctions-list"><p class="tiny" data-i18n="loading">Učitavanje…</p></div>
</div>

<div class="pane" id="pane-adm-bids" role="tabpanel" aria-labelledby="tab-adm-bids" tabindex="0">
<div class="panel" style="margin-bottom:14px">
<div class="field" style="margin-bottom:0"><div class="field__wrap">{i("grid", 17)}<select id="adm-bids-auction-filter"><option value="" data-i18n="opt_all_auctions">Sve aukcije</option></select></div></div>
</div>
<div id="adm-bids-list"><p class="tiny" data-i18n="loading">Učitavanje…</p></div>
</div>

<div class="pane" id="pane-adm-categories" role="tabpanel" aria-labelledby="tab-adm-categories" tabindex="0">
<div class="panel" style="margin-bottom:14px">
<h2 class="h3" style="margin-bottom:10px" data-i18n="new_category_heading">Nova kategorija</h2>
<form id="adm-category-form">
<div class="field"><label for="adm-cat-name" data-i18n="field_name">Naziv</label><div class="field__wrap">{i("grid", 17)}<input id="adm-cat-name" type="text" required></div></div>
<div class="field"><label for="adm-cat-slug" data-i18n="field_slug">Slug</label><div class="field__wrap">{i("grid", 17)}<input id="adm-cat-slug" type="text" required placeholder="npr. heavy-equipment" data-i18n-attr="placeholder:ph_slug_example"></div></div>
<div class="field"><label for="adm-cat-parent" data-i18n="field_parent">Nadkategorija (opciono)</label><div class="field__wrap">{i("grid", 17)}<select id="adm-cat-parent"><option value="" data-i18n="opt_none">— Nijedna —</option></select></div></div>
<button class="btn btn--primary" type="submit" data-i18n="add_category">Dodaj kategoriju</button>
</form>
</div>
<div id="adm-categories-list"><p class="tiny" data-i18n="loading">Učitavanje…</p></div>
</div>

<div class="pane" id="pane-adm-support" role="tabpanel" aria-labelledby="tab-adm-support" tabindex="0">
<div class="chips" id="adm-support-filter" role="group" aria-label="Filter statusa tiketa" style="margin-bottom:14px">
<button class="adm-chip is-active" type="button" data-status="open" data-i18n="status_open">Otvoren</button>
<button class="adm-chip" type="button" data-status="in_progress" data-i18n="status_in_progress">U toku</button>
<button class="adm-chip" type="button" data-status="resolved" data-i18n="status_resolved">Riješen</button>
<button class="adm-chip" type="button" data-status="closed" data-i18n="status_closed">Zatvoren</button>
<button class="adm-chip" type="button" data-status="" data-i18n="status_all">Svi</button>
</div>
<div id="adm-support-list"><p class="tiny" data-i18n="loading">Učitavanje…</p></div>
</div>
</div>
</section>
'''

# =================================================================== SUPPORT ---
SUPPORT_CATEGORIES = [("account", "opt_cat_account", "Nalog"), ("credits_payment", "opt_cat_credits_payment", "Krediti i plaćanje"),
                      ("auction_bid", "opt_cat_auction_bidding", "Aukcija i licitiranje"), ("seller_application", "opt_cat_seller_application", "Prijava za prodavca"),
                      ("listing", "opt_cat_listing", "Oglas"), ("technical_issue", "opt_cat_technical", "Tehnički problem"), ("other", "opt_other", "Ostalo")]
support_cat_opts = "".join(
    f'<option value="{k}"{" selected" if k == "other" else ""} data-i18n="{tk}">{t}</option>' for k, tk, t in SUPPORT_CATEGORIES)

support_body = f'''
<section class="section--tight wrap">
<nav class="crumbs" aria-label="Navigacija" data-i18n-attr="aria-label:breadcrumb"><a href="index.html" data-i18n="crumb_home">Početna</a>{i("chev-r", 13)}<span aria-current="page" data-i18n="support_label">Podrška</span></nav>
<h1 class="h1" style="font-size:clamp(24px,4vw,32px)" data-i18n="contact_support_heading">Kontaktirajte podršku</h1>
<p class="lead" style="margin-top:6px;font-size:13.5px" data-i18n="contact_support_desc">Pitanja o vašem nalogu, kreditima, aukciji ili oglasu? Pošaljite nam poruku.</p>
</section>

<section class="wrap" style="padding-bottom:36px">
<div class="layout-detail">
<div class="detail-main">
<div class="panel">
<h2 class="h3" style="margin-bottom:14px" data-i18n="send_message_heading">Pošaljite nam poruku</h2>
<form id="support-form" novalidate>
<div class="field"><label for="sup-subject" data-i18n="field_subject">Naslov</label><div class="field__wrap">{i("mail", 17)}<input id="sup-subject" type="text" required></div></div>
<div class="field"><label for="sup-category" data-i18n="field_category">Kategorija</label><div class="field__wrap">{i("sliders", 17)}<select id="sup-category">{support_cat_opts}</select></div></div>
<div class="field"><label for="sup-lot" data-i18n="field_lot_id">ID oglasa (opciono)</label><div class="field__wrap">{i("doc", 17)}<input id="sup-lot" type="text" placeholder="npr. BM-VEH-000001" data-i18n-attr="placeholder:ph_lot_example"></div></div>
<div class="field"><label for="sup-message" data-i18n="field_message">Poruka</label>
<div class="field__wrap" style="align-items:flex-start;padding:10px 12px">
<textarea id="sup-message" rows="6" required style="border:0;outline:0;width:100%;font:inherit;resize:vertical;background:transparent"></textarea>
</div></div>
<button class="btn btn--primary btn--lg" type="submit" data-i18n="send_message_button">Pošalji poruku</button>
</form>
</div>
</div>
<aside class="detail-side">
<div class="panel">
<h2 class="h3" style="margin-bottom:8px" data-i18n="faster_answer_heading">Trebate brži odgovor?</h2>
<p class="tiny" data-i18n-html="faster_answer_desc">Pogledajte naša <a class="red" href="credits.html#faq" style="font-weight:600">Česta pitanja</a> o kreditima i aukcijama.</p>
</div>
<div class="panel is-hidden" id="sup-my-tickets-wrap">
<h2 class="h3" style="margin-bottom:10px" data-i18n="your_tickets_heading">Vaši tiketi</h2>
<ul class="notif-list" id="sup-my-tickets"><li class="tiny" data-i18n="no_tickets_yet">Još nema tiketa.</li></ul>
</div>
</aside>
</div>
</section>
'''

# ---------------------------------------------------------------- output ----
PAGES = [
    ("index.html", page("BidMont — Jedan nalog. Svaka prilika.",
                        "Pristupite provjerenim partnerskim aukcijama vozila, teške mehanizacije, nekretnina, plovila i drugog uz BidMont kredite.",
                        "home", home_body, preload=HERO_PRELOAD, title_key="pt_index")),
    ("credits.html", page("Kupi kredite — BidMont",
                          "Kupite BidMont kredite i otključajte provjerene partnerske aukcije. Krediti ne ističu, isporuka je trenutna, a plaćanja sigurna.",
                          "credits", credits_body, canonical="credits.html", preload=HERO_PRELOAD, title_key="pt_credits")),
    ("auctions.html", page("Partnerske aukcije — BidMont",
                           "Pregledajte 1.248 provjerenih partnerskih aukcija automobila, teške mehanizacije, nekretnina, plovila, luksuza i industrijskih mašina.",
                           "auctions", auctions_body, body_class="has-tabbar", tabbar=TABBAR, canonical="auctions.html", title_key="pt_auctions")),
    ("auth.html", page("Prijavite se ili kreirajte nalog — BidMont",
                       "Prijavite se na BidMont ili kreirajte nalog da pristupite provjerenim partnerskim aukcijama širom svijeta.",
                       "auth", auth_body, canonical="auth.html", title_key="pt_auth")),
    ("auction.html", page("Detalji aukcije — BidMont",
                          "Pogledajte detalje aukcije, istoriju ponuda i postavite ponudu na ovom BidMont oglasu.",
                          "auctions", auction_detail_body, canonical="auction.html", title_key="pt_auction_detail")),
    ("account.html", page("Moj nalog — BidMont",
                          "Pogledajte svoje ponude, listu praćenja, stanje kredita i podešavanja naloga na BidMont-u.",
                          "account", account_body, canonical="account.html", title_key="pt_account")),
    ("support.html", page("Kontakt podrška — BidMont",
                          "Potražite pomoć oko BidMont naloga, kredita, aukcije ili oglasa.",
                          "support", support_body, canonical="support.html", title_key="pt_support")),
    ("admin.html", page("Admin panel — BidMont",
                        "BidMont panel za osoblje: korisnici, prijave prodavaca, oglasi, kategorije i tiketi podrške.",
                        "admin", admin_body, canonical="admin.html", title_key="pt_admin")),
]

for fn, html in PAGES:
    with open(fn, "w", encoding="utf-8") as f:
        f.write(html)
    print(fn, len(html), "bytes")
