/* BidMont — interactions. Vanilla, no dependencies. */
(function () {
  "use strict";

  var $ = function (s, c) { return (c || document).querySelector(s); };
  var $$ = function (s, c) { return Array.prototype.slice.call((c || document).querySelectorAll(s)); };

  /* ---------------------------------------------------- overlay helper --- */
  function overlay(panelSel, openSel, closeSel) {
    var el = $(panelSel);
    if (!el) return;
    var lastFocus = null;

    function open() {
      lastFocus = document.activeElement;
      el.classList.add("is-open");
      document.body.classList.add("no-scroll");
      $$("[" + openSel.slice(1, -1) + "]").forEach(function (b) { b.setAttribute("aria-expanded", "true"); });
      var f = el.querySelector("input, button, select, a[href]");
      if (f) setTimeout(function () { f.focus(); }, 60);
    }
    function close() {
      el.classList.remove("is-open");
      document.body.classList.remove("no-scroll");
      $$("[" + openSel.slice(1, -1) + "]").forEach(function (b) { b.setAttribute("aria-expanded", "false"); });
      if (lastFocus) lastFocus.focus();
    }

    $$(openSel).forEach(function (b) { b.addEventListener("click", open); });
    $$(closeSel).forEach(function (b) { b.addEventListener("click", close); });
    document.addEventListener("keydown", function (e) {
      if (e.key === "Escape" && el.classList.contains("is-open")) close();
    });
    /* keep focus inside while open */
    el.addEventListener("keydown", function (e) {
      if (e.key !== "Tab") return;
      var items = $$('a[href], button:not([disabled]), input, select, textarea', el)
        .filter(function (n) { return n.offsetParent !== null; });
      if (!items.length) return;
      var first = items[0], last = items[items.length - 1];
      if (e.shiftKey && document.activeElement === first) { e.preventDefault(); last.focus(); }
      else if (!e.shiftKey && document.activeElement === last) { e.preventDefault(); first.focus(); }
    });
  }

  overlay("[data-drawer]", "[data-drawer-open]", "[data-drawer-close]");
  overlay("[data-filters]", "[data-filters-open]", "[data-filters-close]");

  /* close mobile menu when a link is tapped */
  $$(".drawer__nav a").forEach(function (a) {
    a.addEventListener("click", function () {
      var d = $("[data-drawer]");
      if (d) { d.classList.remove("is-open"); document.body.classList.remove("no-scroll"); }
    });
  });

  /* ------------------------------------------------------------- FAQ ----- */
  $$(".faq__q").forEach(function (btn) {
    btn.addEventListener("click", function () {
      var item = btn.closest(".faq__item");
      var open = item.classList.toggle("is-open");
      btn.setAttribute("aria-expanded", open ? "true" : "false");
    });
  });

  /* -------------------------------------------------- filter accordions -- */
  $$(".filters__head").forEach(function (btn) {
    btn.addEventListener("click", function () {
      var g = btn.closest(".filters__group");
      var open = g.classList.toggle("is-open");
      btn.setAttribute("aria-expanded", open ? "true" : "false");
    });
  });

  $$("[data-reset-filters]").forEach(function (btn) {
    btn.addEventListener("click", function () {
      var root = btn.closest(".filters, .filter-drawer__body");
      if (!root) return;
      $$('input[type="checkbox"]', root).forEach(function (c) { c.checked = false; });
      $$('input[type="number"], input[type="search"]', root).forEach(function (c) { c.value = ""; });
      var first = $('input[type="radio"]', root);
      if (first) first.checked = true;
    });
  });

  /* -------------------------------------------------------- category chips */
  $$(".chip").forEach(function (chip) {
    chip.addEventListener("click", function () {
      $$(".chip").forEach(function (c) {
        c.classList.remove("is-active");
        c.setAttribute("aria-pressed", "false");
      });
      chip.classList.add("is-active");
      chip.setAttribute("aria-pressed", "true");
    });
  });

  /* -------------------------------------------------------------- favourites */
  $$(".fav").forEach(function (btn) {
    btn.addEventListener("click", function (e) {
      e.preventDefault();
      var on = btn.getAttribute("aria-pressed") === "true";
      btn.setAttribute("aria-pressed", on ? "false" : "true");
    });
  });

  /* ---------------------------------------------------- password visibility */
  $$("[data-toggle-pass]").forEach(function (btn) {
    btn.addEventListener("click", function () {
      var input = btn.parentNode.querySelector("input");
      if (!input) return;
      var show = input.type === "password";
      input.type = show ? "text" : "password";
      btn.setAttribute("aria-pressed", show ? "true" : "false");
      btn.setAttribute("aria-label", window.t ? window.t(show ? "hide_password" : "show_password") : (show ? "Hide password" : "Show password"));
    });
  });

  /* ------------------------------------------------------------- auth tabs */
  var tabs = $$('[role="tab"]');
  function selectTab(id) {
    tabs.forEach(function (t) {
      var on = t.id === "tab-" + id;
      t.setAttribute("aria-selected", on ? "true" : "false");
      t.tabIndex = on ? 0 : -1;
      var pane = document.getElementById(t.getAttribute("aria-controls"));
      if (pane) pane.classList.toggle("is-active", on);
    });
  }
  tabs.forEach(function (t) {
    t.addEventListener("click", function () { selectTab(t.id.replace("tab-", "")); });
    t.addEventListener("keydown", function (e) {
      var n = tabs.indexOf(t);
      if (e.key === "ArrowRight" || e.key === "ArrowLeft") {
        e.preventDefault();
        var next = tabs[(n + (e.key === "ArrowRight" ? 1 : tabs.length - 1)) % tabs.length];
        next.focus();
        selectTab(next.id.replace("tab-", ""));
      }
    });
  });
  $$("[data-goto-tab]").forEach(function (b) {
    b.addEventListener("click", function () { selectTab(b.getAttribute("data-goto-tab")); });
  });
  if (tabs.length && location.hash === "#create") selectTab("create");

  /* ------------------------------------------------------------- stepper -- */
  var stepper = $("[data-stepper]");
  function goStep(n) {
    if (!stepper) return;
    $$("[data-substep]").forEach(function (p) {
      p.classList.toggle("is-active", Number(p.getAttribute("data-substep")) === n);
    });
    $$("[data-step]", stepper).forEach(function (s) {
      var v = Number(s.getAttribute("data-step"));
      s.classList.toggle("is-active", v === n);
      s.classList.toggle("is-done", v < n);
      var dot = s.querySelector(".stepper__dot");
      dot.textContent = v < n ? "✓" : String(v);
    });
    var top = $(".auth");
    if (top) window.scrollTo({ top: top.offsetTop - 90, behavior: "smooth" });
  }
  $$("[data-next-step]").forEach(function (b) { b.addEventListener("click", function () { goStep(3); }); });
  $$("[data-prev-step]").forEach(function (b) { b.addEventListener("click", function () { goStep(1); }); });

  /* mock document upload */
  $$("[data-upload]").forEach(function (b) {
    b.addEventListener("click", function () { b.classList.toggle("is-done"); });
  });

  /* ---------------------------------------------------- form validation --- */
  function invalid(input) {
    var v = input.value.trim();
    if (input.type === "checkbox") return input.required && !input.checked;
    if (input.required && !v) return true;
    if (input.type === "email") return !/^[^\s@]+@[^\s@]+\.[a-z]{2,}$/i.test(v);
    if (input.name === "password" && input.minLength > 0) return v.length < 8 || !/\d/.test(v);
    if (input.tagName === "SELECT") return input.required && input.selectedIndex === 0;
    return false;
  }

  $$("[data-form]").forEach(function (form) {
    form.addEventListener("submit", function (e) {
      e.preventDefault();
      var bad = null;
      $$("input, select", form).forEach(function (input) {
        if (input.type === "hidden") return;
        var field = input.closest(".field");
        if (!field) return;
        var isBad = invalid(input);
        field.classList.toggle("field--error", isBad);
        if (isBad && !bad) bad = input;
      });
      if (bad) { bad.focus(); return; }
      if (form.getAttribute("data-form") === "signup") goStep(2);
      else {
        var btn = form.querySelector('button[type="submit"]');
        var loginLabel = window.t ? window.t("hdr_login") : "Log in";
        btn.textContent = window.t ? window.t("logging_in") : "Logging in…";
        setTimeout(function () { btn.textContent = loginLabel; }, 1400);
      }
    });
    $$("input, select", form).forEach(function (input) {
      input.addEventListener("input", function () {
        var f = input.closest(".field");
        if (f && f.classList.contains("field--error") && !invalid(input)) f.classList.remove("field--error");
      });
    });
  });

  /* ------------------------------------------------------------ countdowns */
  var timers = $$("[data-countdown]");
  if (timers.length) {
    var pad = function (n) { return n < 10 ? "0" + n : String(n); };
    var ends = timers.map(function (el) { return Date.now() + Number(el.getAttribute("data-countdown")) * 1000; });
    var tick = function () {
      timers.forEach(function (el, n) {
        var s = Math.max(0, Math.floor((ends[n] - Date.now()) / 1000));
        if (!s) { el.textContent = window.t ? window.t("ended") : "Ended"; return; }
        var d = Math.floor(s / 86400), h = Math.floor(s % 86400 / 3600),
            m = Math.floor(s % 3600 / 60), sec = s % 60;
        el.textContent = d ? pad(d) + "d " + pad(h) + "h " + pad(m) + "m"
                           : pad(h) + "h " + pad(m) + "m " + pad(sec) + "s";
      });
    };
    tick();
    setInterval(tick, 1000);
  }

  /* -------------------------------------------------------- reveal on scroll */
  var reduce = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  var reveals = $$(".reveal");
  if (reduce || !("IntersectionObserver" in window)) {
    reveals.forEach(function (el) { el.classList.add("is-in"); });
  } else {
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (en, n) {
        if (!en.isIntersecting) return;
        en.target.style.transitionDelay = Math.min(n * 60, 240) + "ms";
        en.target.classList.add("is-in");
        io.unobserve(en.target);
      });
    }, { rootMargin: "0px 0px -8% 0px", threshold: 0.08 });
    reveals.forEach(function (el) { io.observe(el); });
  }
})();
