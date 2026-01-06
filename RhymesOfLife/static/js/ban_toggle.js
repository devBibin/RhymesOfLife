(function () {
  const gettext = window.gettext || ((s) => s);
  const btn = document.getElementById("ban-btn");
  if (!btn) return;

  function getCSRF() {
    const el = document.querySelector('form [name="csrfmiddlewaretoken"]');
    return el ? el.value : "";
  }

  function setBusy(v) {
    btn.disabled = v;
  }

  function updateUI(isBanned) {
    if (isBanned) {
      btn.classList.remove("btn-danger");
      btn.classList.add("btn-success");
      btn.textContent = btn.dataset.textUnban || gettext("Unban user");
      btn.dataset.initialState = "banned";
      if (btn.dataset.msgBanned) alert(btn.dataset.msgBanned);
    } else {
      btn.classList.remove("btn-success");
      btn.classList.add("btn-danger");
      btn.textContent = btn.dataset.textBan || gettext("Ban user");
      btn.dataset.initialState = "active";
      if (btn.dataset.msgUnbanned) alert(btn.dataset.msgUnbanned);
    }
  }

  async function postToggle(reason) {
    const url = btn.dataset.url;
    const headers = {
      "X-CSRFToken": getCSRF(),
      "X-Requested-With": "XMLHttpRequest"
    };
    let body;
    if (window.fetch) {
      headers["Content-Type"] = "application/json";
      body = JSON.stringify({ reason });
    }
    const resp = await fetch(url, {
      method: "POST",
      headers,
      body,
      credentials: "same-origin"
    });
    const data = await resp.json().catch(() => ({}));
    if (!resp.ok || data.status === "error") {
      const msg = data.message || btn.dataset.msgError || gettext("Failed to change status.");
      throw new Error(msg);
    }
    return data;
  }

  btn.addEventListener("click", async () => {
    const isBanned = btn.dataset.initialState === "banned";
    let reason = "";
    if (!isBanned) {
      const promptText = btn.dataset.promptReason || gettext("Enter ban reason (optional):");
      const r = window.prompt(promptText, "");
      if (r === null) return;
      reason = r.trim();
    }

    setBusy(true);
    try {
      const res = await postToggle(reason);
      updateUI(!!res.is_banned);
    } catch (e) {
      alert(e.message || btn.dataset.msgError || gettext("Failed to change status."));
    } finally {
      setBusy(false);
    }
  });
})();
