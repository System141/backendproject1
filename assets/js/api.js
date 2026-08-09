/* BidMont — backend wiring for the new static site. All fetch() calls live
   here; main.js (markup interactions) and the HTML are untouched so build.py
   can keep regenerating pages without clobbering this file. */
(function () {
  "use strict";

  var API_BASE = window.location.origin + "/api";
  var TOKEN_KEY = "bidmont_token"; // same key the previous SPA used
  var USER_KEY = "bidmont_user";

  function token() { return localStorage.getItem(TOKEN_KEY); }
  function setSession(accessToken, user) {
    if (accessToken) localStorage.setItem(TOKEN_KEY, accessToken); else localStorage.removeItem(TOKEN_KEY);
    if (user) localStorage.setItem(USER_KEY, JSON.stringify(user)); else localStorage.removeItem(USER_KEY);
  }

  function api(path, opts) {
    opts = opts || {};
    var headers = { "Content-Type": "application/json" };
    var t = token();
    if (t) headers.Authorization = "Bearer " + t;
    return fetch(API_BASE + path, {
      method: opts.method || "GET",
      headers: headers,
      body: opts.body ? JSON.stringify(opts.body) : undefined,
    }).then(function (res) {
      return res.json().catch(function () { return {}; }).then(function (data) {
        if (!res.ok) {
          var err = new Error(data.detail || res.statusText);
          err.status = res.status; // callers branch on 403 (not joined) vs 402 (insufficient credits)
          throw err;
        }
        return data;
      });
    });
  }

  function banner(msg, kind) {
    var el = document.getElementById("bm-banner");
    if (!el) {
      el = document.createElement("div");
      el.id = "bm-banner";
      el.style.cssText = "position:fixed;top:0;left:0;right:0;z-index:9999;padding:12px 16px;" +
        "text-align:center;font:600 13px/1.4 Inter,system-ui,sans-serif;color:#fff";
      document.body.prepend(el);
    }
    el.style.background = kind === "error" ? "#c0392b" : "#1a8a4a";
    el.textContent = msg;
    el.style.display = "block";
    clearTimeout(el._hideTimer);
    el._hideTimer = setTimeout(function () { el.style.display = "none"; }, 6000);
  }

  var esc = function (s) { return String(s == null ? "" : s); };

  function fmtEUR(n) {
    try {
      return new Intl.NumberFormat("en-GB", { style: "currency", currency: "EUR", maximumFractionDigits: 0 }).format(n);
    } catch (e) {
      return "€" + Math.round(n).toLocaleString();
    }
  }

  // ponytail: static "ends in" text computed once at render time, not a
  // live per-second tick like main.js's countdowns — upgrade if these cards
  // need to visibly count down without a page refresh.
  function fmtEndsIn(sec) {
    if (sec <= 0) return "Ended";
    var d = Math.floor(sec / 86400), h = Math.floor((sec % 86400) / 3600), m = Math.floor((sec % 3600) / 60);
    return d ? d + "d " + h + "h" : h + "h " + m + "m";
  }

  var CATEGORY_IMAGES = [
    [/vehicle/i, "car"],
    [/equipment/i, "excavator"],
    [/electronic/i, "watch"],
  ];
  function pickImage(categoryName) {
    for (var i = 0; i < CATEGORY_IMAGES.length; i++) {
      if (CATEGORY_IMAGES[i][0].test(categoryName || "")) return CATEGORY_IMAGES[i][1];
    }
    return "cnc"; // generic commercial-assets fallback
  }

  /* -------------------------------------------------------------- header -- */
  function paintHeader() {
    if (!token()) return;
    var user = null;
    try { user = JSON.parse(localStorage.getItem(USER_KEY) || "null"); } catch (e) {}
    document.querySelectorAll(".hdr__actions, .drawer__foot").forEach(function (box) {
      box.innerHTML = "";
      var pill = document.createElement("a");
      pill.href = "account.html";
      pill.className = "btn btn--outline btn--sm";
      pill.textContent = (user && user.name) || "My account";
      var out = document.createElement("button");
      out.type = "button";
      out.className = "btn btn--primary btn--sm";
      out.textContent = "Log out";
      out.addEventListener("click", function () {
        setSession(null, null);
        location.href = "index.html";
      });
      box.appendChild(pill);
      box.appendChild(out);
    });
  }

  /* ---------------------------------------------------------------- auth -- */
  var loginForm = document.querySelector('[data-form="login"]');
  if (loginForm) {
    loginForm.addEventListener("submit", function () {
      if (loginForm.querySelector(".field--error")) return; // main.js already flagged it invalid
      var email = loginForm.querySelector("#login-email").value.trim();
      var password = loginForm.querySelector("#login-pass").value;
      var totpInput = loginForm.querySelector("#login-totp");
      var body = { email: email, password: password };
      if (totpInput && totpInput.value.trim()) body.totp_code = totpInput.value.trim();
      api("/auth/login", { method: "POST", body: body })
        .then(function (data) {
          setSession(data.access_token, data.user);
          location.href = "index.html";
        })
        .catch(function (err) {
          // 2FA account, no code yet: reveal the field in place and let the
          // user resubmit — same in-place flow the legacy SPA used, no redirect.
          if (err.message === "TOTP code required" && totpInput) {
            document.getElementById("login-totp-wrap").classList.remove("is-hidden");
            totpInput.focus();
            banner("This account has 2FA enabled — enter your authenticator code.", "error");
            return;
          }
          banner(err.message, "error");
        });
    });
  }

  var signupForm = document.querySelector('[data-form="signup"]');
  if (signupForm) {
    signupForm.addEventListener("submit", function () {
      if (signupForm.querySelector(".field--error")) return;
      var code = signupForm.querySelector("#su-code");
      var termsChecked = signupForm.querySelector('input[name="terms"]').checked;
      api("/auth/register", {
        method: "POST",
        body: {
          name: signupForm.querySelector("#su-name").value.trim(),
          email: signupForm.querySelector("#su-email").value.trim(),
          phone: (code ? code.value : "") + signupForm.querySelector("#su-phone").value.trim(),
          password: signupForm.querySelector("#su-pass").value,
          role: "buyer",
          accepted_terms: termsChecked,
          accepted_privacy: termsChecked,
        },
      })
        .then(function (data) {
          setSession(data.access_token, data.user);
          banner("Account created — check your email to verify it.");
        })
        .catch(function (err) {
          banner(err.message, "error");
          var back = document.querySelector("[data-prev-step]");
          if (back) back.click(); // main.js owns the stepper; reuse its own button
        });
    });
  }

  var forgotLink = document.querySelector("#pane-login .form-row a.red");
  if (forgotLink) {
    forgotLink.addEventListener("click", function (e) {
      e.preventDefault();
      var email = prompt("Enter your account email to receive a password reset link:");
      if (!email) return;
      api("/auth/forgot-password", { method: "POST", body: { email: email } })
        .then(function (data) {
          banner(data.message || "If the email exists, a reset link has been sent.");
          if (data.reset_token) location.hash = "reset-password?token=" + data.reset_token; // dev mode only
        })
        .catch(function (err) { banner(err.message, "error"); });
    });
  }

  function handleHashActions() {
    var hash = location.hash;
    if (hash.indexOf("#verify-email") === 0) {
      var vtoken = new URLSearchParams(hash.split("?")[1] || "").get("token");
      if (vtoken) {
        api("/auth/verify-email", { method: "POST", body: { token: vtoken } })
          .then(function () { banner("Email verified — you can now log in."); })
          .catch(function (err) { banner(err.message, "error"); });
      }
    } else if (hash.indexOf("#reset-password") === 0) {
      var rtoken = new URLSearchParams(hash.split("?")[1] || "").get("token");
      if (rtoken) {
        var pass = prompt("Enter your new password (min 6 characters):");
        if (pass) {
          api("/auth/reset-password", { method: "POST", body: { token: rtoken, new_password: pass } })
            .then(function () { banner("Password reset — you can now log in."); location.hash = ""; })
            .catch(function (err) { banner(err.message, "error"); });
        }
      }
    }
  }

  /* ----------------------------------------------------------- auctions -- */
  function fetchCategories() {
    return fetch(API_BASE + "/categories").then(function (res) { return res.json(); })
      .then(function (list) {
        var map = {};
        list.forEach(function (c) { map[c.id] = c; });
        return map;
      })
      .catch(function () { return {}; });
  }

  function fetchAuctions(params) {
    var qs = new URLSearchParams(params).toString();
    return fetch(API_BASE + "/auctions?" + qs).then(function (res) {
      return res.json().then(function (data) {
        return { items: data, total: Number(res.headers.get("X-Total-Count") || data.length) };
      });
    });
  }

  function renderAuctionGrid(containerSel, auctions, categoriesById, emptyMessage) {
    var container = document.querySelector(containerSel);
    if (!container) return;
    var template = container.querySelector(".auction");
    if (!template) return;
    template = template.cloneNode(true);
    container.innerHTML = "";
    if (!auctions.length) {
      container.innerHTML = '<p class="tiny">' + esc(emptyMessage || "No live auctions right now — check back soon.") + "</p>";
      return;
    }
    auctions.forEach(function (a) {
      var node = template.cloneNode(true);
      var catName = (categoriesById[a.category_id] || {}).name || "";
      var img = pickImage(catName);
      var imgEl = node.querySelector("img");
      if (imgEl) {
        imgEl.src = "assets/img/" + img + ".webp";
        imgEl.srcset = "assets/img/" + img + "-md.webp 600w, assets/img/" + img + ".webp 1200w";
        imgEl.alt = esc(a.title);
      }
      var detailHref = "auction.html?id=" + encodeURIComponent(a.id);
      var media = node.querySelector(".auction__media");
      if (media) { media.setAttribute("aria-label", esc(a.title)); media.setAttribute("href", detailHref); }
      var fav = node.querySelector(".fav");
      if (fav) fav.setAttribute("aria-label", "Save " + esc(a.title));
      var partner = node.querySelector(".auction__partner");
      if (partner) partner.textContent = esc(a.seller_name || "BidMont seller").toUpperCase();
      var titleLink = node.querySelector(".auction__title a");
      if (titleLink) { titleLink.textContent = esc(a.title); titleLink.setAttribute("href", detailHref); }
      var catEl = node.querySelector(".auction__cat");
      if (catEl) catEl.textContent = catName;
      var priceEl = node.querySelector(".auction__meta .val");
      if (priceEl) priceEl.textContent = fmtEUR(a.current_price);
      var endsEl = node.querySelector("[data-countdown]");
      if (endsEl) {
        endsEl.removeAttribute("data-countdown");
        var secs = Math.max(0, Math.round((new Date(a.end_time + "Z").getTime() - Date.now()) / 1000));
        endsEl.textContent = fmtEndsIn(secs);
      }
      var creditsEl = node.querySelector(".credits-tag");
      if (creditsEl) {
        var c = a.participation_credit_cost;
        creditsEl.textContent = c ? c + (c === 1 ? " Credit" : " Credits") : "Free";
      }
      container.appendChild(node);
    });
  }

  function wireAuctionListings() {
    var rail = document.querySelector(".rail");
    var grid = document.querySelector(".grid-auctions");
    if (!rail && !grid) return;
    fetchCategories().then(function (categoriesById) {
      if (rail) {
        fetchAuctions({ limit: 8, sort_by: "end_time", sort_dir: "asc" })
          .then(function (r) { renderAuctionGrid(".rail", r.items, categoriesById); })
          .catch(function () {});
      }
      if (grid) {
        fetchAuctions({ limit: 24, sort_by: "end_time", sort_dir: "asc" })
          .then(function (r) {
            renderAuctionGrid(".grid-auctions", r.items, categoriesById);
            var countEl = document.querySelector(".count");
            if (countEl) countEl.textContent = r.total + " results found";
          })
          .catch(function () {});
      }
    });
  }

  /* -------------------------------------------------------- auction detail */
  var SPEC_FIELDS = [
    ["lot_code", "Lot ID"], ["brand", "Brand"], ["model", "Model"], ["year", "Year"],
    ["mileage", "Mileage (km)"], ["fuel_type", "Fuel type"], ["transmission", "Transmission"],
    ["damage_status", "Damage status"], ["defect_exterior", "Exterior defects"],
    ["defect_interior", "Interior defects"], ["defect_mechanical", "Mechanical defects"],
    ["defect_tyres", "Tyres"], ["defect_missing_parts", "Missing parts"],
    ["equipment_brand", "Equipment brand"], ["serial_number", "Serial number"],
    ["condition", "Condition"], ["location", "Location"], ["operating_hours", "Operating hours"],
    ["engine_power", "Engine power"], ["operating_weight", "Operating weight"],
    ["service_history", "Service history"], ["dimensions", "Dimensions"],
    ["included_items", "Included items"], ["quantity", "Quantity"],
  ]; // ponytail: one flat spec list for every category, not per-category layout blocks — upgrade if v1 feedback wants it

  function setText(id, text) {
    var el = document.getElementById(id);
    if (el) el.textContent = text;
  }

  function downloadDocument(imageId, filename) {
    fetch(API_BASE + "/uploads/" + imageId + "/download", {
      headers: token() ? { Authorization: "Bearer " + token() } : {},
    }).then(function (res) {
      if (!res.ok) throw new Error("Could not download this document (are you logged in as the seller?).");
      return res.blob();
    }).then(function (blob) {
      var url = URL.createObjectURL(blob);
      var a = document.createElement("a");
      a.href = url;
      a.download = filename || "document";
      document.body.appendChild(a);
      a.click();
      a.remove();
      setTimeout(function () { URL.revokeObjectURL(url); }, 4000);
    }).catch(function (err) { banner(err.message, "error"); });
  }

  function wireAuctionDetail() {
    var root = document.getElementById("det-root");
    if (!root) return; // only present on auction.html
    var id = new URLSearchParams(location.search).get("id");
    if (!id) { showNotFound(); return; }

    var ws = null, wsTimer = null, wsDelay = 1000;
    var galleryUrls = [], galleryIndex = 0;

    function showNotFound() {
      root.classList.add("is-hidden");
      var nf = document.getElementById("det-notfound");
      if (nf) nf.style.display = "grid";
    }

    function showImage(idx) {
      galleryIndex = idx;
      var mainImg = document.getElementById("det-image");
      if (mainImg) mainImg.src = galleryUrls[idx];
      document.querySelectorAll("#det-thumbs img").forEach(function (t, n) {
        t.classList.toggle("is-active", n === idx);
      });
    }

    function openLightbox(idx) {
      var lb = document.getElementById("det-lightbox");
      var img = document.getElementById("det-lightbox-img");
      if (!lb || !img) return;
      img.src = galleryUrls[idx];
      lb.dataset.i = idx;
      lb.classList.add("is-open");
    }
    var lightbox = document.getElementById("det-lightbox");
    if (lightbox) {
      lightbox.querySelectorAll("[data-lightbox-close]").forEach(function (b) {
        b.addEventListener("click", function () { lightbox.classList.remove("is-open"); });
      });
      var step = function (dir) {
        var n = (Number(lightbox.dataset.i || 0) + dir + galleryUrls.length) % galleryUrls.length;
        openLightbox(n);
      };
      var prevBtn = lightbox.querySelector("[data-lightbox-prev]");
      var nextBtn = lightbox.querySelector("[data-lightbox-next]");
      if (prevBtn) prevBtn.addEventListener("click", function () { step(-1); });
      if (nextBtn) nextBtn.addEventListener("click", function () { step(1); });
      document.addEventListener("keydown", function (e) {
        if (!lightbox.classList.contains("is-open")) return;
        if (e.key === "Escape") lightbox.classList.remove("is-open");
      }); // ponytail: no left/right-arrow nav in v1, click prev/next or Escape
    }

    function renderDetail(a, bids, categoriesById, isWatched) {
      document.title = a.title + " — BidMont";
      var catName = (categoriesById[a.category_id] || {}).name || "";
      setText("det-crumb", a.title);
      setText("det-cat", catName);
      setText("det-title", a.title);
      setText("det-meta", (a.lot_code ? "Lot " + a.lot_code + " · " : "") + (a.seller_name || "BidMont seller"));
      setText("det-desc", a.description || "");

      var specsEl = document.getElementById("det-specs");
      if (specsEl) {
        specsEl.innerHTML = "";
        SPEC_FIELDS.forEach(function (pair) {
          var val = a[pair[0]];
          if (val === null || val === undefined || val === "") return;
          var div = document.createElement("div");
          var dt = document.createElement("dt"); dt.textContent = pair[1];
          var dd = document.createElement("dd"); dd.textContent = val;
          div.appendChild(dt); div.appendChild(dd);
          specsEl.appendChild(div);
        });
      }

      var images = (a.images || []).filter(function (im) { return im.media_type !== "document"; })
        .sort(function (x, y) { return x.sort_order - y.sort_order; });
      galleryUrls = images.length ? images.map(function (im) { return im.image_url; })
        : ["assets/img/" + pickImage(catName) + ".webp"];
      var thumbsEl = document.getElementById("det-thumbs");
      if (thumbsEl) {
        thumbsEl.innerHTML = "";
        if (galleryUrls.length > 1) {
          galleryUrls.forEach(function (url, n) {
            var t = document.createElement("img");
            t.src = url; t.alt = "";
            t.addEventListener("click", function () { showImage(n); });
            thumbsEl.appendChild(t);
          });
        }
      }
      var mainImg = document.getElementById("det-image");
      if (mainImg) mainImg.onclick = function () { openLightbox(galleryIndex); };
      showImage(0);

      var docs = (a.images || []).filter(function (im) { return im.media_type === "document"; });
      var docsWrap = document.getElementById("det-docs-wrap");
      var docsEl = document.getElementById("det-docs");
      if (docs.length && docsWrap && docsEl) {
        docsWrap.classList.remove("is-hidden");
        docsEl.innerHTML = "";
        docs.forEach(function (d) {
          var li = document.createElement("li");
          var btn = document.createElement("button");
          btn.type = "button";
          btn.className = "red";
          btn.style.fontWeight = "600";
          btn.textContent = (d.doc_category || "Document") + " ↓";
          btn.addEventListener("click", function () { downloadDocument(d.id, d.doc_category || "document"); });
          li.appendChild(btn);
          docsEl.appendChild(li);
        });
      } else if (docsWrap) {
        docsWrap.classList.add("is-hidden");
      }

      setText("det-price", fmtEUR(a.current_price));
      var endsSec = Math.max(0, Math.round((new Date(a.end_time + "Z").getTime() - Date.now()) / 1000));
      setText("det-ends", fmtEndsIn(endsSec));

      var ended = ["ended", "cancelled"].indexOf(a.status) !== -1 || endsSec <= 0;
      var bidArea = document.getElementById("det-bid-area");
      if (bidArea) bidArea.classList.toggle("is-hidden", ended);
      setText("det-status-note", ended ? (a.status === "cancelled" ? "This auction was cancelled." : "This auction has ended.") : "");
      setText("det-credit-note", a.participation_credit_cost
        ? "Your first bid spends " + a.participation_credit_cost + " credit(s) to join this auction."
        : "");

      var watchBtn = document.getElementById("det-watch");
      if (watchBtn) watchBtn.setAttribute("aria-pressed", isWatched ? "true" : "false");

      var bidsBody = document.getElementById("det-bids");
      if (bidsBody) {
        if (!bids.length) {
          bidsBody.innerHTML = '<tr><td colspan="3" class="tiny">No bids yet.</td></tr>';
        } else {
          bidsBody.innerHTML = bids.slice().sort(function (x, y) { return y.amount - x.amount; })
            .map(function (b) {
              return "<tr><td>" + esc(b.user_name || "Bidder") + "</td><td>" + fmtEUR(b.amount) + "</td><td>" +
                esc(new Date(b.created_at + "Z").toLocaleString()) + "</td></tr>";
            }).join("");
        }
      }

      if (ended && token()) tryLoadContact(a); // backend enforces winner/seller-only, this just attempts
    }

    function tryLoadContact(a) {
      api("/auctions/" + a.id + "/contact")
        .then(function (c) {
          var panel = document.getElementById("det-contact-panel");
          var body = document.getElementById("det-contact-body");
          if (!panel || !body) return;
          body.innerHTML = "<b>" + esc(c.name) + "</b><br>" + esc(c.email) + (c.phone ? "<br>" + esc(c.phone) : "");
          panel.classList.remove("is-hidden");
        })
        .catch(function () { /* not ended yet, or this viewer isn't the winner/seller — stays hidden */ });
    }

    function bindWatch(auctionId, initiallyWatched) {
      var btn = document.getElementById("det-watch");
      if (!btn) return;
      var watched = initiallyWatched;
      btn.onclick = function () {
        if (!token()) { location.href = "auth.html"; return; }
        api("/watchlist/" + auctionId, { method: watched ? "DELETE" : "POST" })
          .then(function () { watched = !watched; btn.setAttribute("aria-pressed", watched ? "true" : "false"); })
          .catch(function (err) { banner(err.message, "error"); });
      };
    }

    function placeBid(auctionId, amount) {
      return api("/auctions/" + auctionId + "/bids", {
        method: "POST",
        body: { amount: amount, idempotency_key: (window.crypto && crypto.randomUUID) ? crypto.randomUUID() : String(Date.now()) + Math.random() },
      });
    }

    function bindBid(a) {
      var btn = document.getElementById("det-bid-btn");
      var input = document.getElementById("det-bid-amount");
      if (!btn || !input) return;
      var minBid = a.current_price + a.min_increment;
      input.min = minBid;
      input.placeholder = String(Math.ceil(minBid));
      btn.onclick = function () {
        if (!token()) { location.href = "auth.html"; return; }
        var amount = Number(input.value);
        if (!amount || amount < minBid) { banner("Enter at least " + fmtEUR(minBid) + ".", "error"); return; }
        if (!confirm("Place a bid of " + fmtEUR(amount) + "?")) return;
        btn.disabled = true;
        placeBid(a.id, amount)
          .then(function () { banner("Bid placed!"); load(); })
          .catch(function (err) {
            if (err.status === 403) {
              var cost = a.participation_credit_cost || 0;
              if (!confirm("Joining this auction costs " + cost + " credit(s). Continue?")) { btn.disabled = false; return; }
              api("/auctions/" + a.id + "/join", { method: "POST" })
                .then(function () { return placeBid(a.id, amount); })
                .then(function () { banner("Bid placed!"); load(); })
                .catch(function (err2) {
                  if (err2.status === 402) {
                    banner("Not enough credits — redirecting to buy more.", "error");
                    setTimeout(function () { location.href = "credits.html"; }, 1500);
                  } else banner(err2.message, "error");
                })
                .then(function () { btn.disabled = false; });
              return;
            }
            if (err.status === 402) {
              banner("Not enough credits — redirecting to buy more.", "error");
              setTimeout(function () { location.href = "credits.html"; }, 1500);
            } else {
              banner(err.message, "error");
            }
            btn.disabled = false;
          });
      };
    }

    function connectWS(auctionId) {
      if (!token()) return; // anonymous viewers get no live updates, same as before
      var proto = location.protocol === "https:" ? "wss:" : "ws:";
      ws = new WebSocket(proto + "//" + location.host + "/ws/auctions/" + auctionId + "?token=" + encodeURIComponent(token()));
      ws.onopen = function () { wsDelay = 1000; };
      ws.onmessage = function (evt) {
        var msg;
        try { msg = JSON.parse(evt.data); } catch (e) { return; }
        if (msg.type === "ping") { ws.send(JSON.stringify({ type: "pong" })); return; }
        if (msg.type === "new_bid" || msg.type === "auction_status_changed") load();
      };
      ws.onclose = function () {
        wsTimer = setTimeout(function () { connectWS(auctionId); }, wsDelay);
        wsDelay = Math.min(wsDelay * 2, 30000);
      };
      ws.onerror = function () { ws.close(); };
    }
    window.addEventListener("pagehide", function () {
      clearTimeout(wsTimer);
      if (ws) ws.close();
    });

    function load() {
      Promise.all([
        fetchCategories(),
        api("/auctions/" + id).catch(function () { return null; }),
        fetch(API_BASE + "/auctions/" + id + "/bids")
          .then(function (r) { return r.ok ? r.json() : { bids: [] }; })
          .then(function (d) { return d.bids || []; }) // GET .../bids wraps the array in {bids, total_count, ...}
          .catch(function () { return []; }),
        token() ? api("/watchlist").catch(function () { return []; }) : Promise.resolve([]),
      ]).then(function (r) {
        var categoriesById = r[0], auction = r[1], bids = r[2], watchlist = r[3];
        if (!auction) { showNotFound(); return; }
        var isWatched = watchlist.some(function (w) { return w.id === id; });
        renderDetail(auction, bids, categoriesById, isWatched);
        bindWatch(id, isWatched);
        bindBid(auction);
      });
    }

    load();
    connectWS(id);
  }

  /* -------------------------------------------------------- notifications -- */
  function timeAgo(iso) {
    var sec = Math.max(0, Math.round((Date.now() - new Date(iso + "Z").getTime()) / 1000));
    if (sec < 60) return "just now";
    var min = Math.round(sec / 60);
    if (min < 60) return min + "m ago";
    var hr = Math.round(min / 60);
    if (hr < 24) return hr + "h ago";
    return Math.round(hr / 24) + "d ago";
  }

  function renderNotifList(container, items) {
    if (!container) return;
    container.innerHTML = "";
    if (!items.length) { container.innerHTML = '<li class="tiny">No notifications yet.</li>'; return; }
    items.forEach(function (n) {
      var li = document.createElement("li");
      li.className = n.is_read ? "" : "is-unread";
      li.innerHTML = "<b>" + esc(n.title) + "</b>" + esc(n.message) + "<br><span>" + timeAgo(n.created_at) + "</span>";
      li.addEventListener("click", function () {
        if (n.is_read) return;
        api("/notifications/" + n.id + "/read", { method: "PUT" })
          .then(function () { n.is_read = true; li.className = ""; refreshUnreadBadge(); })
          .catch(function () {});
      });
      container.appendChild(li);
    });
  }

  function refreshUnreadBadge() {
    api("/notifications/unread-count").then(function (d) {
      var badge = document.getElementById("notif-badge");
      if (!badge) return;
      if (d.count > 0) { badge.textContent = d.count > 99 ? "99+" : String(d.count); badge.classList.remove("is-hidden"); }
      else badge.classList.add("is-hidden");
    }).catch(function () {});
  }

  // ponytail: 60s poll, same as the legacy SPA — no server push for
  // notifications (only the per-auction WS channel exists), upgrade if that changes.
  function wireNotificationBell() {
    if (!token()) return;
    var wrap = document.getElementById("notif-wrap");
    if (!wrap) return;
    wrap.classList.remove("is-hidden");
    refreshUnreadBadge();
    setInterval(refreshUnreadBadge, 60000);

    var bell = document.getElementById("notif-bell");
    var dropdown = document.getElementById("notif-dropdown");
    var list = document.getElementById("notif-dropdown-list");
    if (!bell || !dropdown || !list) return;
    bell.addEventListener("click", function (e) {
      e.stopPropagation();
      var isHidden = dropdown.classList.contains("is-hidden");
      if (isHidden) {
        api("/notifications").then(function (items) { renderNotifList(list, items); }).catch(function () {});
      }
      dropdown.classList.toggle("is-hidden", !isHidden);
      bell.setAttribute("aria-expanded", isHidden ? "true" : "false");
    });
    document.addEventListener("click", function (e) {
      if (!wrap.contains(e.target)) { dropdown.classList.add("is-hidden"); bell.setAttribute("aria-expanded", "false"); }
    });
  }

  /* ------------------------------------------------------------- account -- */
  function wireAccountPage() {
    var root = document.getElementById("acct-root");
    if (!root) return; // only on account.html
    if (!token()) return; // #acct-loggedout stays visible by default

    document.getElementById("acct-loggedout").classList.add("is-hidden");
    root.classList.remove("is-hidden");

    fetchCategories().then(function (categoriesById) {
      api("/users/me").then(function (user) {
        setSession(token(), user); // keep the cached copy (name shown in header) fresh
        document.getElementById("acct-name").value = user.name || "";
        document.getElementById("acct-phone").value = user.phone || "";
        document.getElementById("acct-city").value = user.city || "";
        document.getElementById("acct-address").value = user.address || "";

        var isSeller = user.role === "seller" || user.role === "corporate_seller";
        var listingsTab = document.getElementById("tab-listings");
        if (listingsTab) listingsTab.classList.toggle("is-hidden", !isSeller);
        var applyWrap = document.getElementById("acct-seller-apply-wrap");
        if (applyWrap) applyWrap.classList.toggle("is-hidden", isSeller);
        if (!user.email_verified) {
          setText("acct-seller-apply-note", "Verify your email (check your inbox) before applying to sell.");
        }
        if (isSeller) loadSellerListings(categoriesById);
      }).catch(function () {});

      api("/credits/balance").then(function (d) {
        var el = document.getElementById("acct-balance");
        if (el) el.innerHTML = Math.round(d.credits_balance) + " <small>Credits</small>";
      }).catch(function () {});

      api("/credits/ledger").then(function (entries) {
        var body = document.getElementById("acct-ledger");
        if (!body) return;
        if (!entries.length) { body.innerHTML = '<tr><td colspan="4" class="tiny">No activity yet.</td></tr>'; return; }
        body.innerHTML = entries.slice(0, 20).map(function (e) {
          return "<tr><td>" + esc(e.type) + "</td><td>" + (e.amount >= 0 ? "+" : "") + e.amount + "</td><td>" +
            e.balance_after + "</td><td>" + esc(new Date(e.created_at + "Z").toLocaleDateString()) + "</td></tr>";
        }).join("");
      }).catch(function () {});

      api("/auctions/bids/my").then(function (bids) {
        var body = document.getElementById("acct-bids-body");
        if (!body) return;
        if (!bids.length) { body.innerHTML = '<tr><td colspan="4" class="tiny">No bids yet.</td></tr>'; return; }
        body.innerHTML = bids.map(function (b) {
          return "<tr><td><a href=\"auction.html?id=" + encodeURIComponent(b.auction_id) + "\">" + esc(b.auction_title) +
            "</a></td><td>" + fmtEUR(b.amount) + "</td><td>" + esc(b.auction_status || "") + "</td><td>" +
            esc(new Date(b.created_at + "Z").toLocaleDateString()) + "</td></tr>";
        }).join("");
      }).catch(function () {});

      api("/auctions/joined").then(function (joined) {
        var body = document.getElementById("acct-joined-body");
        if (!body) return;
        if (!joined.length) { body.innerHTML = '<tr><td colspan="4" class="tiny">You haven\'t joined any auctions yet.</td></tr>'; return; }
        body.innerHTML = joined.map(function (j) {
          return "<tr><td><a href=\"auction.html?id=" + encodeURIComponent(j.auction_id) + "\">" + esc(j.auction_title) +
            "</a></td><td>" + j.credits_spent + "</td><td>" + esc(j.my_bid_status) + "</td><td>" +
            esc(new Date(j.joined_at + "Z").toLocaleDateString()) + "</td></tr>";
        }).join("");
      }).catch(function () {});

      api("/watchlist").then(function (items) {
        renderAuctionGrid("#acct-watchlist-grid", items, categoriesById, "Nothing in your watchlist yet.");
      }).catch(function () {});

      api("/notifications").then(function (items) {
        renderNotifList(document.getElementById("acct-notif-list"), items);
      }).catch(function () {});
    });

    function loadSellerListings(categoriesById) {
      api("/users/me/seller-stats").then(function (stats) {
        var el = document.getElementById("acct-seller-stats");
        if (!el) return;
        el.innerHTML = Object.keys(stats).map(function (k) {
          return '<div class="feature"><div><b>' + esc(stats[k]) + "</b><span>" + esc(k.replace(/_/g, " ")) + "</span></div></div>";
        }).join("");
      }).catch(function () {});
      api("/auctions/my").then(function (items) {
        renderAuctionGrid("#acct-listings-grid", items, categoriesById, "You haven't listed anything yet.");
      }).catch(function () {});
    }

    var profileForm = document.getElementById("acct-profile-form");
    if (profileForm) {
      profileForm.addEventListener("submit", function (e) {
        e.preventDefault();
        api("/users/me", {
          method: "PUT",
          body: {
            name: document.getElementById("acct-name").value.trim(),
            phone: document.getElementById("acct-phone").value.trim(),
            city: document.getElementById("acct-city").value.trim(),
            address: document.getElementById("acct-address").value.trim(),
          },
        })
          .then(function (u) { setSession(token(), u); banner("Profile saved."); })
          .catch(function (err) { banner(err.message, "error"); });
      });
    }

    var pwForm = document.getElementById("acct-password-form");
    if (pwForm) {
      pwForm.addEventListener("submit", function (e) {
        e.preventDefault();
        api("/users/me/password", {
          method: "PUT",
          body: {
            current_password: document.getElementById("acct-pw-current").value,
            new_password: document.getElementById("acct-pw-new").value,
          },
        })
          .then(function () { banner("Password updated."); pwForm.reset(); })
          .catch(function (err) { banner(err.message, "error"); });
      });
    }

    var sellerForm = document.getElementById("acct-seller-form");
    if (sellerForm) {
      sellerForm.addEventListener("submit", function (e) {
        e.preventDefault();
        api("/sellers/apply", {
          method: "POST",
          body: { account_type: document.getElementById("acct-seller-type").value },
        })
          .then(function () { banner("Application submitted — we'll review it soon."); })
          .catch(function (err) { banner(err.message, "error"); });
      });
    }

    var logoutBtn = document.getElementById("acct-logout");
    if (logoutBtn) {
      logoutBtn.addEventListener("click", function () { setSession(null, null); location.href = "index.html"; });
    }
  }

  /* ------------------------------------------------------------- credits -- */
  function buyCredits(packageId) {
    if (!confirm("By purchasing you accept the BidMont Credit Terms & Refund Policy. Continue to secure payment?")) return;
    api("/credits/monri/checkout", { method: "POST", body: { package_id: packageId, terms_accepted: true } })
      .then(function (data) {
        var form = document.createElement("form");
        form.method = "POST";
        form.action = data.checkout_url;
        Object.keys(data.form_fields).forEach(function (key) {
          var input = document.createElement("input");
          input.type = "hidden";
          input.name = key;
          input.value = data.form_fields[key];
          form.appendChild(input);
        });
        document.body.appendChild(form);
        form.submit();
      })
      .catch(function (err) { banner(err.message, "error"); });
  }

  function wirePlans(packages) {
    var planNodes = document.querySelectorAll(".plans .plan");
    planNodes.forEach(function (node, i) {
      var pkg = packages[i];
      if (!pkg) { node.style.display = "none"; return; }
      var nameEl = node.querySelector(".plan__name");
      if (nameEl) nameEl.textContent = pkg.name;
      var priceB = node.querySelector(".plan__price b");
      if (priceB) priceB.textContent = fmtEUR(pkg.price_eur);
      var priceSpan = node.querySelector(".plan__price span");
      if (priceSpan) priceSpan.textContent = pkg.credits + " credits";
      var buyBtn = node.querySelector("a.btn");
      if (buyBtn && token()) {
        buyBtn.setAttribute("href", "#");
        buyBtn.addEventListener("click", function (e) {
          e.preventDefault();
          buyCredits(pkg.id);
        });
      }
    });
  }

  function wireWallet() {
    var walletEl = document.querySelector(".wallet");
    if (!walletEl) return;
    var amt = walletEl.querySelector(".wallet__amt");
    var sub = walletEl.querySelector(".wallet__sub");
    if (token()) {
      api("/credits/balance").then(function (d) {
        if (amt) amt.innerHTML = Math.round(d.credits_balance) + " <small>Credits</small>";
        if (sub) sub.remove();
      }).catch(function () {});
    } else {
      if (amt) amt.innerHTML = "<small>Log in to see your balance</small>";
      if (sub) sub.remove();
      walletEl.setAttribute("href", "auth.html");
    }
  }

  /* ------------------------------------------------------------- support -- */
  function wireSupportForm() {
    var form = document.getElementById("support-form");
    if (!form) return; // only on support.html

    if (token()) {
      var wrap = document.getElementById("sup-my-tickets-wrap");
      var list = document.getElementById("sup-my-tickets");
      if (wrap && list) {
        api("/support/tickets/my").then(function (tickets) {
          wrap.classList.remove("is-hidden");
          list.innerHTML = "";
          if (!tickets.length) { list.innerHTML = '<li class="tiny">No tickets yet.</li>'; return; }
          tickets.forEach(function (t) {
            var li = document.createElement("li");
            li.innerHTML = "<b>" + esc(t.subject) + "</b>" + esc(t.status) + "<br><span>" +
              esc(new Date(t.created_at + "Z").toLocaleDateString()) + "</span>";
            list.appendChild(li);
          });
        }).catch(function () {});
      }
    }

    form.addEventListener("submit", function (e) {
      e.preventDefault();
      var body = {
        subject: document.getElementById("sup-subject").value.trim(),
        message: document.getElementById("sup-message").value.trim(),
        category: document.getElementById("sup-category").value,
        lot_code: document.getElementById("sup-lot").value.trim() || null,
      };
      if (!body.subject || !body.message) { banner("Please fill in a subject and message.", "error"); return; }
      // logged-in users get a trackable ticket; anonymous visitors use the same public contact endpoint
      api(token() ? "/support/tickets" : "/support/contact", { method: "POST", body: body })
        .then(function () { banner("Message sent — we'll get back to you soon."); form.reset(); })
        .catch(function (err) { banner(err.message, "error"); });
    });
  }

  /* --------------------------------------------------------------- init -- */
  paintHeader();
  handleHashActions();
  wireAuctionListings();
  wireAuctionDetail();
  wireAccountPage();
  wireNotificationBell();
  wireWallet();
  wireSupportForm();
  if (document.querySelector(".plans .plan")) {
    fetch(API_BASE + "/credits/packages").then(function (res) { return res.json(); })
      .then(wirePlans)
      .catch(function () {});
  }
})();
