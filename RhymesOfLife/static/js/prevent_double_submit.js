(function () {
  const SUBMIT_ATTR = "data-submitting";
  const ALLOW_MULTI = "data-allow-multi-submit";
  const UNLOCK_TIMEOUT_MS = 8000;

  function applySpinner(btn) {
    if (!(btn instanceof HTMLButtonElement)) return;
    if (btn.dataset.loadingApplied === "1") return;

    btn.dataset.loadingApplied = "1";
    btn.dataset.originalHtml = btn.innerHTML;
    const label = btn.getAttribute("data-loading-label") || btn.textContent.trim() || "";
    btn.innerHTML = `<span class="spinner-border spinner-border-sm align-middle me-2" role="status" aria-hidden="true"></span><span class="align-middle">${label}</span>`;
    btn.classList.add("is-loading");
    btn.setAttribute("aria-busy", "true");
  }

  function restoreButton(btn) {
    if (!(btn instanceof HTMLButtonElement)) return;
    if (btn.dataset.loadingApplied === "1") {
      btn.innerHTML = btn.dataset.originalHtml || btn.innerHTML;
      delete btn.dataset.originalHtml;
      delete btn.dataset.loadingApplied;
      btn.classList.remove("is-loading");
      btn.removeAttribute("aria-busy");
    }
  }

  function lockButtons(btns) {
    btns.forEach((btn) => {
      btn.dataset.wasDisabled = btn.disabled ? "1" : "0";
      btn.disabled = true;
      btn.classList.add("is-submitting");
      applySpinner(btn);
    });
  }

  function unlockButtons(form, btns) {
    form.removeAttribute(SUBMIT_ATTR);
    btns.forEach((btn) => {
      if (btn.dataset.wasDisabled !== "1") btn.disabled = false;
      btn.classList.remove("is-submitting");
      restoreButton(btn);
    });
  }

  document.addEventListener(
    "submit",
    (e) => {
      const form = e.target;
      if (!(form instanceof HTMLFormElement)) return;
      if (form.hasAttribute(ALLOW_MULTI)) return;

      if (form.getAttribute(SUBMIT_ATTR) === "1") {
        e.preventDefault();
        e.stopImmediatePropagation();
        return;
      }

      form.setAttribute(SUBMIT_ATTR, "1");
      const btns = Array.from(form.querySelectorAll('button[type="submit"], input[type="submit"]'));
      lockButtons(btns);

      setTimeout(() => unlockButtons(form, btns), UNLOCK_TIMEOUT_MS);
    },
    true
  );

  document.addEventListener("click", (e) => {
    const target = e.target instanceof Element ? e.target.closest("[data-once]") : null;
    if (!target) return;

    if (target.getAttribute("data-once-locked") === "1") {
      e.preventDefault();
      e.stopImmediatePropagation();
      return;
    }

    target.setAttribute("data-once-locked", "1");
    target.setAttribute("aria-busy", "true");
    if ("disabled" in target) target.disabled = true;
    applySpinner(target);

    const timeout = parseInt(target.getAttribute("data-once-timeout") || "1500", 10);
    setTimeout(() => {
      target.removeAttribute("aria-busy");
      target.removeAttribute("data-once-locked");
      if (target.getAttribute("data-once-keep-disabled") !== "1" && "disabled" in target) {
        target.disabled = false;
      }
      restoreButton(target);
    }, timeout > 0 ? timeout : 1500);
  });
})();
