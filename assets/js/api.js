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
  // esc() does NOT escape HTML — fine everywhere it's currently used (fed to
  // .alt/.setAttribute, or the seller's own data reflected back to them), but
  // admin tables render OTHER users' free-text input (name, title, ticket
  // message...) into innerHTML, which makes esc() an XSS hole there. Use this
  // instead for any admin-panel string built into innerHTML.
  var escHtml = function (s) {
    return String(s == null ? "" : s).replace(/[&<>"']/g, function (c) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c];
    });
  };

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

    var LISTING_STATUS_LABEL = {
      draft: "Changes requested", under_review: "Pending review", upcoming: "Upcoming",
      live: "Live", extended: "Live", ended: "Ended", cancelled: "Cancelled",
    };

    function loadSellerListings(categoriesById) {
      api("/users/me/seller-stats").then(function (stats) {
        var el = document.getElementById("acct-seller-stats");
        if (!el) return;
        el.innerHTML = Object.keys(stats).map(function (k) {
          return '<div class="feature"><div><b>' + esc(stats[k]) + "</b><span>" + esc(k.replace(/_/g, " ")) + "</span></div></div>";
        }).join("");
      }).catch(function () {});

      var categorySelect = document.getElementById("lst-category");
      if (categorySelect) {
        categorySelect.innerHTML = Object.keys(categoriesById).map(function (id) {
          return '<option value="' + id + '">' + esc(categoriesById[id].name) + "</option>";
        }).join("");
      }

      function refreshListings() {
        var el = document.getElementById("acct-listings-list");
        if (!el) return;
        api("/auctions/my").then(function (items) {
          if (!items.length) { el.innerHTML = '<p class="tiny">You haven\'t listed anything yet.</p>'; return; }
          el.innerHTML = items.map(renderListingCard).join("");
        }).catch(function () {
          el.innerHTML = '<p class="tiny">Failed to load your listings.</p>';
        });
      }

      function renderListingCard(a) {
        var badge = LISTING_STATUS_LABEL[a.status] || a.status;
        var canEdit = a.status === "under_review" || a.status === "draft";
        var actions = '<a class="btn btn--outline btn--sm" href="auction.html?id=' + encodeURIComponent(a.id) + '">View</a>';
        if (canEdit) {
          actions += ' <button class="btn btn--outline btn--sm" type="button" data-edit-listing="' + a.id + '">Edit</button>' +
            ' <button class="btn btn--ghostred btn--sm" type="button" data-delete-listing="' + a.id + '">Delete</button>';
        }
        if (a.status === "draft") {
          actions += ' <button class="btn btn--primary btn--sm" type="button" data-resubmit-listing="' + a.id + '">Resubmit</button>';
        }
        var notes = a.status === "draft" && a.review_notes
          ? '<p class="tiny" style="color:#9f1239;margin-top:6px">Admin: ' + escHtml(a.review_notes) + "</p>" : "";
        return '<div class="panel" style="margin-bottom:10px">' +
          '<div style="display:flex;justify-content:space-between;gap:10px;flex-wrap:wrap;align-items:center">' +
          '<div><b>' + escHtml(a.title) + '</b><br><span class="tiny">' + escHtml(badge) + " · " + fmtEUR(a.current_price) + "</span></div>" +
          '<div style="display:flex;gap:8px;flex-wrap:wrap">' + actions + "</div></div>" + notes + "</div>";
      }

      function uploadListingPhotos(auctionId, fileList) {
        var fd = new FormData();
        for (var idx = 0; idx < fileList.length; idx++) fd.append("files", fileList[idx]);
        return fetch(API_BASE + "/uploads/batch?auction_id=" + encodeURIComponent(auctionId), {
          method: "POST",
          headers: token() ? { Authorization: "Bearer " + token() } : {},
          body: fd,
        }).then(function (res) {
          if (!res.ok) throw new Error("Listing saved, but photo upload failed.");
          return res.json();
        });
      }

      function uploadListingDocuments(auctionId, fileList, docCategory) {
        var fd = new FormData();
        for (var idx = 0; idx < fileList.length; idx++) fd.append("files", fileList[idx]);
        var qs = "auction_id=" + encodeURIComponent(auctionId) + "&doc_category=" + encodeURIComponent(docCategory);
        return fetch(API_BASE + "/uploads/documents?" + qs, {
          method: "POST",
          headers: token() ? { Authorization: "Bearer " + token() } : {},
          body: fd,
        }).then(function (res) {
          if (!res.ok) throw new Error("Listing saved, but document upload failed.");
          return res.json();
        });
      }

      function showListingForm() {
        var form = document.getElementById("acct-listing-form");
        if (form) form.classList.remove("is-hidden");
      }
      function hideListingForm() {
        var form = document.getElementById("acct-listing-form");
        if (!form) return;
        form.classList.add("is-hidden");
        form.reset();
        document.getElementById("lst-id").value = "";
        document.getElementById("lst-submit-btn").textContent = "Publish listing";
      }

      function openListingForEdit(id) {
        api("/auctions/" + id).then(function (a) {
          document.getElementById("lst-id").value = a.id;
          document.getElementById("lst-title").value = a.title || "";
          document.getElementById("lst-desc").value = a.description || "";
          document.getElementById("lst-category").value = a.category_id;
          document.getElementById("lst-price").value = a.start_price;
          document.getElementById("lst-increment").value = a.min_increment;
          // <input type="datetime-local"> reads/writes in local time, but end_time is UTC —
          // shift by the local offset before formatting, or every edit drags the deadline
          // toward the browser's UTC offset (see submit handler for the inverse conversion).
          var endLocal = new Date(a.end_time + "Z");
          endLocal = new Date(endLocal.getTime() - endLocal.getTimezoneOffset() * 60000);
          document.getElementById("lst-end").value = endLocal.toISOString().slice(0, 16);
          document.getElementById("lst-location").value = a.location || "";
          document.getElementById("lst-brand").value = a.brand || "";
          document.getElementById("lst-model").value = a.model || "";
          document.getElementById("lst-year").value = a.year || "";
          document.getElementById("lst-mileage").value = a.mileage || "";
          document.getElementById("lst-fuel").value = a.fuel_type || "";
          document.getElementById("lst-transmission").value = a.transmission || "";
          document.getElementById("lst-equip-brand").value = a.equipment_brand || "";
          document.getElementById("lst-serial").value = a.serial_number || "";
          document.getElementById("lst-condition").value = a.condition || "";
          document.getElementById("lst-hours").value = a.operating_hours || "";
          document.getElementById("lst-quantity").value = a.quantity || "";
          document.getElementById("lst-submit-btn").textContent = "Save changes";
          showListingForm();
          document.getElementById("acct-listing-form").scrollIntoView({ behavior: "smooth", block: "center" });
        }).catch(function (err) { banner(err.message || "Failed to load listing.", "error"); });
      }

      var newBtn = document.getElementById("acct-listing-new-btn");
      if (newBtn) newBtn.addEventListener("click", function () {
        hideListingForm();
        showListingForm();
      });
      var cancelBtn = document.getElementById("acct-listing-cancel-btn");
      if (cancelBtn) cancelBtn.addEventListener("click", hideListingForm);

      var listingsList = document.getElementById("acct-listings-list");
      if (listingsList) listingsList.addEventListener("click", function (e) {
        var editBtn = e.target.closest("[data-edit-listing]");
        var delBtn = e.target.closest("[data-delete-listing]");
        var subBtn = e.target.closest("[data-resubmit-listing]");
        if (editBtn) { openListingForEdit(editBtn.getAttribute("data-edit-listing")); return; }
        if (delBtn) {
          if (!confirm("Delete this listing? This cannot be undone.")) return;
          api("/auctions/" + delBtn.getAttribute("data-delete-listing"), { method: "DELETE" })
            .then(refreshListings).catch(function (err) { banner(err.message || "Failed to delete listing.", "error"); });
          return;
        }
        if (subBtn) {
          api("/auctions/" + subBtn.getAttribute("data-resubmit-listing") + "/submit", { method: "POST" })
            .then(refreshListings).catch(function (err) { banner(err.message || "Failed to resubmit listing.", "error"); });
        }
      });

      var listingForm = document.getElementById("acct-listing-form");
      if (listingForm) listingForm.addEventListener("submit", function (e) {
        e.preventDefault();
        var id = document.getElementById("lst-id").value;
        if (!id && !document.getElementById("lst-declaration").checked) {
          banner("Confirm the seller declaration to publish.", "error");
          return;
        }
        var body = {
          title: document.getElementById("lst-title").value.trim(),
          description: document.getElementById("lst-desc").value.trim(),
          category_id: parseInt(document.getElementById("lst-category").value, 10),
          start_price: parseFloat(document.getElementById("lst-price").value),
          min_increment: parseFloat(document.getElementById("lst-increment").value),
          end_time: new Date(document.getElementById("lst-end").value).toISOString(),
          // null (not undefined) so clearing a field on an edit actually clears it server-side —
          // PUT uses exclude_unset, so an omitted key leaves the old value untouched.
          location: document.getElementById("lst-location").value.trim() || null,
          brand: document.getElementById("lst-brand").value.trim() || null,
          model: document.getElementById("lst-model").value.trim() || null,
          year: document.getElementById("lst-year").value ? parseInt(document.getElementById("lst-year").value, 10) : null,
          mileage: document.getElementById("lst-mileage").value ? parseInt(document.getElementById("lst-mileage").value, 10) : null,
          fuel_type: document.getElementById("lst-fuel").value.trim() || null,
          transmission: document.getElementById("lst-transmission").value.trim() || null,
          equipment_brand: document.getElementById("lst-equip-brand").value.trim() || null,
          serial_number: document.getElementById("lst-serial").value.trim() || null,
          condition: document.getElementById("lst-condition").value.trim() || null,
          operating_hours: document.getElementById("lst-hours").value ? parseInt(document.getElementById("lst-hours").value, 10) : null,
          quantity: document.getElementById("lst-quantity").value ? parseInt(document.getElementById("lst-quantity").value, 10) : null,
        };
        if (!id) body.declaration_accepted = true;

        var submitBtn = document.getElementById("lst-submit-btn");
        submitBtn.disabled = true; // guard against double-click double-charging the listing fee
        var req = id ? api("/auctions/" + id, { method: "PUT", body: body }) : api("/auctions", { method: "POST", body: body });
        req.then(function (auction) {
          // The auction is already created/charged at this point — an upload failure here
          // is a warning, not a reason to let the seller re-submit and get charged again.
          var photoFiles = document.getElementById("lst-photos").files;
          var photos = photoFiles.length
            ? uploadListingPhotos(auction.id, photoFiles).catch(function (err) {
                banner(err.message || "Listing saved, but photo upload failed.", "error");
              })
            : Promise.resolve();
          var docFiles = document.getElementById("lst-documents").files;
          var docCategory = document.getElementById("lst-doc-category").value;
          var docs = docFiles.length
            ? uploadListingDocuments(auction.id, docFiles, docCategory).catch(function (err) {
                banner(err.message || "Listing saved, but document upload failed.", "error");
              })
            : Promise.resolve();
          return Promise.all([photos, docs]);
        }).then(function () {
          banner(id ? "Listing updated." : "Listing submitted for review.");
          hideListingForm();
          refreshListings();
        }).catch(function (err) {
          banner(err.message || "Failed to save listing.", "error");
        }).then(function () { submitBtn.disabled = false; });
      });

      refreshListings();
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

  /* ----------------------------------------------------------------- admin */
  function wireAdminPage() {
    var root = document.getElementById("adm-root");
    if (!root) return; // only on admin.html

    var STAFF_ROLES = { admin: 1, super_admin: 1, support: 1 };
    var deniedEl = document.getElementById("adm-denied");
    // Shared cache: user id -> {name, email, ...}, filled once up front so the
    // Sellers/Support tabs can show a name instead of a raw id (neither
    // SellerProfileResponse nor SupportTicketResponse carries the applicant's
    // name — only user_id).
    var usersById = {};
    // Same idea for the Bids tab: BidResponse only carries auction_id, not
    // the auction's title/lot_code.
    var auctionsById = {};
    var viewerRole = null; // read by wireUsersTab to hide staff-role options a non-super_admin can't grant anyway

    function showLoginPrompt() {
      deniedEl.innerHTML = '<p class="lead" style="font-size:13.5px">Log in with a staff account to see this page.</p>' +
        '<a class="btn btn--primary" href="auth.html" style="margin-top:12px">Log in</a>';
    }

    if (!token()) { showLoginPrompt(); return; }

    api("/users/me").then(function (user) {
      if (!STAFF_ROLES[user.role]) {
        deniedEl.innerHTML = '<p class="lead" style="font-size:13.5px">Your account doesn\'t have staff access.</p>';
        return;
      }
      viewerRole = user.role;
      deniedEl.classList.add("is-hidden");
      root.classList.remove("is-hidden");

      // Every tab except Support/2FA is gated to get_current_admin server-side
      // (see backend/app/api/admin.py) - support-role staff would otherwise
      // land on a panel where 6 of 7 tabs silently 403. Hide those tabs and
      // land on Support instead of offering dead ends.
      if (viewerRole === "support") {
        ["overview", "users", "sellers", "auctions", "bids", "categories"].forEach(function (k) {
          var tabBtn = document.getElementById("tab-adm-" + k);
          var pane = document.getElementById("pane-adm-" + k);
          // aria-hidden + tabIndex -1, not just display:none - main.js's
          // selectTab() arrow-key handler walks all [role="tab"] elements
          // regardless of visibility, so a hidden-but-still-focusable button
          // would let keyboard nav land on an empty, unwired pane.
          if (tabBtn) { tabBtn.style.display = "none"; tabBtn.setAttribute("aria-hidden", "true"); tabBtn.tabIndex = -1; }
          if (pane) pane.classList.remove("is-active");
        });
        var supportTab = document.getElementById("tab-adm-support");
        var supportPane = document.getElementById("pane-adm-support");
        if (supportTab) { supportTab.setAttribute("aria-selected", "true"); supportTab.tabIndex = 0; }
        if (supportPane) supportPane.classList.add("is-active");
        wireSupportTab();
        return;
      }

      loadOverview();

      // Seed usersById/auctionsById before the tabs that need them render, so
      // the first paint shows names rather than ids (not just a self-heal on
      // a later refresh).
      Promise.all([
        api("/admin/users").then(function (users) {
          users.forEach(function (u) { usersById[u.id] = u; });
        }).catch(function () {}),
        api("/admin/auctions").then(function (auctions) {
          auctions.forEach(function (a) { auctionsById[a.id] = a; });
        }).catch(function () {}),
      ]).then(function () {
        wireUsersTab();
        wireSellersTab();
        wireAuctionsTab();
        wireBidsTab();
        wireCategoriesTab();
        wireSupportTab();
      });
    }).catch(showLoginPrompt);

    function loadOverview() {
      var el = document.getElementById("adm-stats");
      api("/admin/stats").then(function (s) {
        el.innerHTML = [
          ["total_users", "Users"], ["total_auctions", "Auctions"], ["total_bids", "Bids"],
          ["active_auctions", "Active"], ["completed_auctions", "Completed"], ["pending_auctions", "Pending review"],
        ].map(function (pair) {
          return '<div class="feature"><div><b>' + esc(s[pair[0]]) + "</b><span>" + pair[1] + "</span></div></div>";
        }).join("") + '<div class="feature"><div><b>' + fmtEUR(s.total_credit_revenue) +
          "</b><span>Credit revenue</span></div></div>";
      }).catch(function () {
        el.innerHTML = '<p class="tiny">Failed to load stats.</p>';
      });
    }

    // Default filter status lives in the HTML (whichever chip has is-active) —
    // each tab's own `var status = "..."` just has to match that markup.
    function wireChipFilter(filterEl, onChange) {
      filterEl.addEventListener("click", function (e) {
        var chip = e.target.closest(".adm-chip");
        if (!chip) return;
        filterEl.querySelectorAll(".adm-chip").forEach(function (c) { c.classList.toggle("is-active", c === chip); });
        onChange(chip.getAttribute("data-status"));
      });
    }

    /* ------------------------------------------------------------- users -- */
    function wireUsersTab() {
      var listEl = document.getElementById("adm-users-list");
      var searchEl = document.getElementById("adm-users-search");
      var allUsers = [];

      function userRow(u) {
        // A staff-tier row (or granting a staff role) needs super_admin server-side anyway -
        // a regular admin gets a read-only role cell instead of a select that would just 403.
        var canEditRole = viewerRole === "super_admin" || !STAFF_ROLES[u.role];
        var roleCell = canEditRole
          ? '<select data-role-select="' + u.id + '" style="font:inherit">' +
            ["buyer", "seller", "corporate_seller", "admin", "super_admin", "support"].map(function (r) {
              return '<option value="' + r + '"' + (r === u.role ? " selected" : "") + '>' + r + "</option>";
            }).join("") + "</select> " +
            '<button class="btn btn--outline btn--sm" type="button" data-save-role="' + u.id + '">Save</button>'
          : escHtml(u.role);
        return "<tr><td>" + escHtml(u.name) + "</td><td>" + escHtml(u.email) + "</td><td>" + roleCell + "</td><td>" +
          escHtml(u.status) + "</td><td>" + escHtml(u.created_at ? new Date(u.created_at + "Z").toLocaleDateString() : "—") +
          '</td><td style="white-space:nowrap">' +
          '<button class="btn btn--outline btn--sm" type="button" data-set-status="' + u.id + '" data-value="active">Active</button> ' +
          '<button class="btn btn--outline btn--sm" type="button" data-set-status="' + u.id + '" data-value="suspended">Suspend</button> ' +
          '<button class="btn btn--ghostred btn--sm" type="button" data-set-status="' + u.id + '" data-value="banned">Ban</button></td></tr>';
      }

      function render() {
        var q = searchEl.value.trim().toLowerCase();
        var filtered = !q ? allUsers : allUsers.filter(function (u) {
          return (u.name + " " + u.email).toLowerCase().indexOf(q) !== -1;
        });
        if (!filtered.length) { listEl.innerHTML = '<p class="tiny">No users found.</p>'; return; }
        listEl.innerHTML = '<div class="table-scroll"><table class="ctable"><thead><tr>' +
          "<th>Name</th><th>Email</th><th>Role</th><th>Status</th><th>Joined</th><th>Actions</th>" +
          "</tr></thead><tbody>" + filtered.map(userRow).join("") + "</tbody></table></div>";
      }

      function refresh() {
        api("/admin/users").then(function (users) {
          allUsers = users;
          usersById = {};
          users.forEach(function (u) { usersById[u.id] = u; });
          render();
        }).catch(function () {
          listEl.innerHTML = '<p class="tiny">Failed to load users.</p>';
        });
      }

      searchEl.addEventListener("input", render);
      listEl.addEventListener("click", function (e) {
        var saveBtn = e.target.closest("[data-save-role]");
        var statusBtn = e.target.closest("[data-set-status]");
        if (saveBtn) {
          var uid = saveBtn.getAttribute("data-save-role");
          var sel = listEl.querySelector('[data-role-select="' + uid + '"]');
          api("/admin/users/" + uid + "/role?new_role=" + encodeURIComponent(sel.value), { method: "PUT" })
            .then(function () { banner("Role updated."); refresh(); })
            .catch(function (err) { banner(err.message || "Failed to update role.", "error"); });
          return;
        }
        if (statusBtn) {
          api("/admin/users/" + statusBtn.getAttribute("data-set-status") + "/status?new_status=" + statusBtn.getAttribute("data-value"), { method: "PUT" })
            .then(function () { banner("Status updated."); refresh(); })
            .catch(function (err) { banner(err.message || "Failed to update status.", "error"); });
        }
      });

      refresh();
    }

    /* ----------------------------------------------------------- sellers -- */
    function wireSellersTab() {
      var listEl = document.getElementById("adm-sellers-list");
      var filterEl = document.getElementById("adm-sellers-filter");
      var status = "pending";

      function applicantLabel(userId) {
        var u = usersById[userId];
        return u ? escHtml(u.name) + " (" + escHtml(u.email) + ")" : userId;
      }

      function row(p) {
        var actions = p.verification_status === "pending"
          ? '<button class="btn btn--outline btn--sm" type="button" data-verify-seller="' + p.id + '">Verify</button> ' +
            '<button class="btn btn--ghostred btn--sm" type="button" data-reject-seller="' + p.id + '">Reject</button>'
          : (p.rejection_reason ? '<span class="tiny" style="color:#9f1239">' + escHtml(p.rejection_reason) + "</span>" : "");
        return "<tr><td>" + applicantLabel(p.user_id) + "</td><td>" + escHtml(p.account_type) +
          (p.company_name ? " — " + escHtml(p.company_name) : "") + "</td><td>" + escHtml(p.city || "—") + "</td><td>" +
          escHtml(p.verification_status) + "</td><td>" + escHtml(new Date(p.created_at + "Z").toLocaleDateString()) +
          '</td><td style="white-space:nowrap">' + actions + "</td></tr>";
      }

      function refresh() {
        var qs = status ? "?verification_status=" + status : "";
        api("/admin/sellers" + qs).then(function (apps) {
          if (!apps.length) { listEl.innerHTML = '<p class="tiny">No seller applications.</p>'; return; }
          listEl.innerHTML = '<div class="table-scroll"><table class="ctable"><thead><tr>' +
            "<th>Applicant</th><th>Type</th><th>City</th><th>Status</th><th>Applied</th><th>Actions</th>" +
            "</tr></thead><tbody>" + apps.map(row).join("") + "</tbody></table></div>";
        }).catch(function () {
          listEl.innerHTML = '<p class="tiny">Failed to load seller applications.</p>';
        });
      }

      wireChipFilter(filterEl, function (s) { status = s; refresh(); });

      listEl.addEventListener("click", function (e) {
        var verifyBtn = e.target.closest("[data-verify-seller]");
        var rejectBtn = e.target.closest("[data-reject-seller]");
        if (verifyBtn) {
          api("/admin/sellers/" + verifyBtn.getAttribute("data-verify-seller") + "/verify", { method: "POST" })
            .then(function () { banner("Seller verified."); refresh(); })
            .catch(function (err) { banner(err.message || "Failed to verify seller.", "error"); });
        } else if (rejectBtn) {
          var reason = prompt("Reason for rejecting this application:");
          if (!reason) return;
          api("/admin/sellers/" + rejectBtn.getAttribute("data-reject-seller") + "/reject", { method: "POST", body: { reason: reason } })
            .then(function () { banner("Seller application rejected."); refresh(); })
            .catch(function (err) { banner(err.message || "Failed to reject application.", "error"); });
        }
      });

      refresh();
    }

    /* ---------------------------------------------------------- auctions -- */
    function wireAuctionsTab() {
      var listEl = document.getElementById("adm-auctions-list");
      var filterEl = document.getElementById("adm-auctions-filter");
      var status = "under_review";

      function row(a) {
        var actions = '<a class="btn btn--outline btn--sm" href="auction.html?id=' + encodeURIComponent(a.id) + '">View</a> ';
        if (a.status === "under_review") {
          actions += '<button class="btn btn--primary btn--sm" type="button" data-approve="' + a.id + '">Approve</button> ' +
            '<button class="btn btn--outline btn--sm" type="button" data-request-changes="' + a.id + '">Request changes</button> ' +
            '<button class="btn btn--ghostred btn--sm" type="button" data-reject="' + a.id + '">Reject</button> ';
        }
        actions += '<button class="btn btn--outline btn--sm" type="button" data-toggle-featured="' + a.id +
          '" data-value="' + (!a.is_featured) + '">' + (a.is_featured ? "Unfeature" : "Feature") + "</button>";
        return "<tr><td>" + escHtml(a.title) + (a.is_featured ? " ★" : "") +
          (a.contact_flagged ? ' <span class="tiny" style="color:#9f1239">⚠ contact info?</span>' : "") + "</td><td>" +
          fmtEUR(a.current_price) + "</td><td>" + escHtml(a.status) + "</td><td>" +
          escHtml(new Date(a.created_at + "Z").toLocaleDateString()) + '</td><td style="white-space:nowrap">' + actions + "</td></tr>";
      }

      function refresh() {
        var qs = status ? "?status=" + status : "";
        api("/admin/auctions" + qs).then(function (auctions) {
          if (!auctions.length) { listEl.innerHTML = '<p class="tiny">No auctions.</p>'; return; }
          listEl.innerHTML = '<div class="table-scroll"><table class="ctable"><thead><tr>' +
            "<th>Title</th><th>Price</th><th>Status</th><th>Created</th><th>Actions</th>" +
            "</tr></thead><tbody>" + auctions.map(row).join("") + "</tbody></table></div>";
        }).catch(function () {
          listEl.innerHTML = '<p class="tiny">Failed to load auctions.</p>';
        });
      }

      wireChipFilter(filterEl, function (s) { status = s; refresh(); });

      listEl.addEventListener("click", function (e) {
        var approveBtn = e.target.closest("[data-approve]");
        var rejectBtn = e.target.closest("[data-reject]");
        var changesBtn = e.target.closest("[data-request-changes]");
        var featBtn = e.target.closest("[data-toggle-featured]");
        if (approveBtn) {
          api("/auctions/" + approveBtn.getAttribute("data-approve") + "/approve", { method: "POST" })
            .then(function () { banner("Auction approved."); refresh(); })
            .catch(function (err) { banner(err.message || "Failed to approve.", "error"); });
        } else if (rejectBtn) {
          if (!confirm("Reject this auction?")) return;
          api("/auctions/" + rejectBtn.getAttribute("data-reject") + "/reject", { method: "POST" })
            .then(function () { banner("Auction rejected."); refresh(); })
            .catch(function (err) { banner(err.message || "Failed to reject.", "error"); });
        } else if (changesBtn) {
          var reason = prompt("What should the seller change?");
          if (!reason) return;
          api("/auctions/" + changesBtn.getAttribute("data-request-changes") + "/request-changes", { method: "POST", body: { reason: reason } })
            .then(function () { banner("Changes requested."); refresh(); })
            .catch(function (err) { banner(err.message || "Failed to request changes.", "error"); });
        } else if (featBtn) {
          api("/admin/auctions/" + featBtn.getAttribute("data-toggle-featured") + "/featured?is_featured=" + featBtn.getAttribute("data-value"), { method: "PUT" })
            .then(refresh)
            .catch(function (err) { banner(err.message || "Failed to update featured status.", "error"); });
        }
      });

      refresh();
    }

    /* ------------------------------------------------------------- bids -- */
    function wireBidsTab() {
      var listEl = document.getElementById("adm-bids-list");
      var auctionFilterEl = document.getElementById("adm-bids-auction-filter");

      function auctionLabel(auctionId) {
        var a = auctionsById[auctionId];
        return a ? escHtml(a.lot_code ? a.lot_code + " — " + a.title : a.title) : (auctionId || "—");
      }

      function userLabel(uid) {
        var u = usersById[uid];
        return u ? escHtml(u.name) + " (" + escHtml(u.email) + ")" : (uid || "—");
      }

      function row(b) {
        var actions = b.invalidated
          ? '<span class="tiny">Invalidated</span>'
          : '<button class="btn btn--ghostred btn--sm" type="button" data-invalidate-bid="' + b.id + '">Invalidate</button>';
        return "<tr><td>" + auctionLabel(b.auction_id) + "</td><td>" + userLabel(b.user_id) + "</td><td>" +
          fmtEUR(b.amount) + "</td><td>" + escHtml(new Date(b.created_at + "Z").toLocaleString()) +
          "</td><td>" + actions + "</td></tr>";
      }

      auctionFilterEl.innerHTML = '<option value="">All auctions</option>' +
        Object.keys(auctionsById).map(function (id) {
          return '<option value="' + id + '">' + auctionLabel(id) + "</option>";
        }).join("");

      function refresh() {
        var auctionId = auctionFilterEl.value;
        var qs = auctionId ? "?auction_id=" + encodeURIComponent(auctionId) : "";
        api("/admin/bids" + qs).then(function (bids) {
          if (!bids.length) { listEl.innerHTML = '<p class="tiny">No bids.</p>'; return; }
          listEl.innerHTML = '<div class="table-scroll"><table class="ctable"><thead><tr>' +
            "<th>Auction</th><th>Bidder</th><th>Amount</th><th>Placed</th><th>Actions</th>" +
            "</tr></thead><tbody>" + bids.map(row).join("") + "</tbody></table></div>";
        }).catch(function () {
          listEl.innerHTML = '<p class="tiny">Failed to load bids.</p>';
        });
      }

      auctionFilterEl.addEventListener("change", refresh);

      listEl.addEventListener("click", function (e) {
        var btn = e.target.closest("[data-invalidate-bid]");
        if (!btn) return;
        var reason = prompt("Reason for invalidating this bid:");
        if (!reason) return;
        api("/admin/bids/" + btn.getAttribute("data-invalidate-bid") + "/invalidate", { method: "POST", body: { reason: reason } })
          .then(function () { banner("Bid invalidated."); refresh(); })
          .catch(function (err) { banner(err.message || "Failed to invalidate bid.", "error"); });
      });

      refresh();
    }

    /* -------------------------------------------------------- categories -- */
    function wireCategoriesTab() {
      var listEl = document.getElementById("adm-categories-list");
      var parentSelect = document.getElementById("adm-cat-parent");
      var form = document.getElementById("adm-category-form");
      var allCats = [];

      function row(c) {
        return "<tr><td>" + escHtml(c.name) + "</td><td>" + escHtml(c.slug) + "</td><td>" + escHtml(c.status) +
          '</td><td style="white-space:nowrap">' +
          '<button class="btn btn--outline btn--sm" type="button" data-edit-cat="' + c.id + '">Rename</button> ' +
          '<button class="btn btn--outline btn--sm" type="button" data-toggle-cat="' + c.id + '" data-value="' +
          (c.status === "active" ? "inactive" : "active") + '">' + (c.status === "active" ? "Deactivate" : "Activate") + "</button> " +
          '<button class="btn btn--ghostred btn--sm" type="button" data-delete-cat="' + c.id + '">Delete</button></td></tr>';
      }

      function refresh() {
        api("/admin/categories").then(function (cats) {
          allCats = cats;
          parentSelect.innerHTML = '<option value="">— None —</option>' +
            cats.map(function (c) { return '<option value="' + c.id + '">' + escHtml(c.name) + "</option>"; }).join("");
          if (!cats.length) { listEl.innerHTML = '<p class="tiny">No categories yet.</p>'; return; }
          listEl.innerHTML = '<div class="table-scroll"><table class="ctable"><thead><tr>' +
            "<th>Name</th><th>Slug</th><th>Status</th><th>Actions</th>" +
            "</tr></thead><tbody>" + cats.map(row).join("") + "</tbody></table></div>";
        }).catch(function () {
          listEl.innerHTML = '<p class="tiny">Failed to load categories.</p>';
        });
      }

      form.addEventListener("submit", function (e) {
        e.preventDefault();
        var body = {
          name: document.getElementById("adm-cat-name").value.trim(),
          slug: document.getElementById("adm-cat-slug").value.trim(),
          parent_id: parentSelect.value ? parseInt(parentSelect.value, 10) : null,
        };
        api("/admin/categories", { method: "POST", body: body })
          .then(function () { banner("Category added."); form.reset(); refresh(); })
          .catch(function (err) { banner(err.message || "Failed to add category.", "error"); });
      });

      listEl.addEventListener("click", function (e) {
        var editBtn = e.target.closest("[data-edit-cat]");
        var toggleBtn = e.target.closest("[data-toggle-cat]");
        var delBtn = e.target.closest("[data-delete-cat]");
        if (editBtn) {
          var id = editBtn.getAttribute("data-edit-cat");
          var cat = allCats.filter(function (c) { return String(c.id) === id; })[0];
          var newName = prompt("New name:", cat ? cat.name : "");
          if (!newName) return;
          api("/admin/categories/" + id, { method: "PUT", body: { name: newName } })
            .then(function () { banner("Category updated."); refresh(); })
            .catch(function (err) { banner(err.message || "Failed to update category.", "error"); });
        } else if (toggleBtn) {
          api("/admin/categories/" + toggleBtn.getAttribute("data-toggle-cat"), { method: "PUT", body: { status: toggleBtn.getAttribute("data-value") } })
            .then(refresh)
            .catch(function (err) { banner(err.message || "Failed to update category.", "error"); });
        } else if (delBtn) {
          if (!confirm("Delete this category? This cannot be undone.")) return;
          api("/admin/categories/" + delBtn.getAttribute("data-delete-cat"), { method: "DELETE" })
            .then(function () { banner("Category deleted."); refresh(); })
            .catch(function (err) { banner(err.message || "Failed to delete category — it may still be in use.", "error"); });
        }
      });

      refresh();
    }

    /* ----------------------------------------------------------- support -- */
    function wireSupportTab() {
      var listEl = document.getElementById("adm-support-list");
      var filterEl = document.getElementById("adm-support-filter");
      var status = "open";

      function userLabel(uid) {
        var u = usersById[uid];
        return u ? escHtml(u.name) + " (" + escHtml(u.email) + ")" : (uid || "—");
      }

      function row(t) {
        var statusOpts = ["open", "in_progress", "resolved", "closed"].map(function (s) {
          return '<option value="' + s + '"' + (s === t.status ? " selected" : "") + ">" + s + "</option>";
        }).join("");
        var preview = t.message.length > 140 ? escHtml(t.message.slice(0, 140)) + "…" : escHtml(t.message);
        return "<tr><td><b>" + escHtml(t.subject) + '</b><br><span class="tiny">' + preview + "</span>" +
          (t.lot_code ? '<br><span class="tiny">Lot: ' + escHtml(t.lot_code) + "</span>" : "") + "</td><td>" +
          escHtml(t.category) + "</td><td>" + userLabel(t.user_id) + "</td><td>" +
          escHtml(new Date(t.created_at + "Z").toLocaleDateString()) + "</td><td>" +
          '<select data-ticket-status="' + t.id + '" style="font:inherit">' + statusOpts + "</select> " +
          '<button class="btn btn--outline btn--sm" type="button" data-save-ticket="' + t.id + '">Save</button></td></tr>';
      }

      function refresh() {
        var qs = status ? "?status=" + status : "";
        api("/admin/support-tickets" + qs).then(function (tickets) {
          if (!tickets.length) { listEl.innerHTML = '<p class="tiny">No tickets.</p>'; return; }
          listEl.innerHTML = '<div class="table-scroll"><table class="ctable"><thead><tr>' +
            "<th>Message</th><th>Category</th><th>User</th><th>Created</th><th>Status</th>" +
            "</tr></thead><tbody>" + tickets.map(row).join("") + "</tbody></table></div>";
        }).catch(function () {
          listEl.innerHTML = '<p class="tiny">Failed to load support tickets.</p>';
        });
      }

      wireChipFilter(filterEl, function (s) { status = s; refresh(); });

      listEl.addEventListener("click", function (e) {
        var saveBtn = e.target.closest("[data-save-ticket]");
        if (!saveBtn) return;
        var id = saveBtn.getAttribute("data-save-ticket");
        var sel = listEl.querySelector('[data-ticket-status="' + id + '"]');
        api("/admin/support-tickets/" + id + "?new_status=" + sel.value, { method: "PUT" })
          .then(function () { banner("Ticket updated."); refresh(); })
          .catch(function (err) { banner(err.message || "Failed to update ticket.", "error"); });
      });

      refresh();
    }
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
  wireAdminPage();
  if (document.querySelector(".plans .plan")) {
    fetch(API_BASE + "/credits/packages").then(function (res) { return res.json(); })
      .then(wirePlans)
      .catch(function () {});
  }
})();
