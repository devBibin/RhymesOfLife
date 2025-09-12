document.addEventListener("DOMContentLoaded", () => {
  const _ = (window.gettext) ? window.gettext : (s) => s;

  document.querySelectorAll(".friend-request-form").forEach(form => {
    form.onsubmit = e => {
      e.preventDefault();
      fetch(form.action, {
        method: "POST",
        headers: {
          "X-CSRFToken": form.querySelector("[name=csrfmiddlewaretoken]").value,
          "X-Requested-With": "XMLHttpRequest"
        }
      })
      .then(r => r.json())
      .then(j => {
        if (j.success) {
          form.innerHTML = `<span class="text-success">✅ ${_("Success")}</span>`;
        } else {
          alert(j.error || _("Error"));
        }
      })
      .catch(() => alert(_("Network error")));
    };
  });
});
