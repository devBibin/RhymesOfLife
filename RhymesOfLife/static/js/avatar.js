document.addEventListener("DOMContentLoaded", () => {
  const _ = (window.gettext) ? window.gettext : (s) => s;

  const MSG_SAVE_ERROR    = _("Error while saving.");
  const MSG_NETWORK_ERROR = _("Network or server error.");

  const avatarImg   = document.getElementById("avatar-img");
  const avatarMenu  = document.getElementById("avatar-menu");
  const avatarInput = document.getElementById("avatar-input");
  const deleteInput = document.getElementById("delete-avatar");
  const profileForm = document.getElementById("profile-form");
  const statusEl    = document.getElementById("form-status");

  if (!avatarImg || !avatarMenu || !profileForm) return;

  // Toggle menu
  avatarImg.addEventListener("click", (e) => {
    e.stopPropagation();
    avatarMenu.classList.toggle("show");
  });
  document.addEventListener("click", (e) => {
    if (!avatarMenu.contains(e.target) && !avatarImg.contains(e.target)) {
      avatarMenu.classList.remove("show");
    }
  });

  // Upload / delete actions
  const changeBtn = document.getElementById("change-avatar-btn");
  const deleteBtn = document.getElementById("delete-avatar-btn");

  if (changeBtn && avatarInput) {
    changeBtn.addEventListener("click", () => {
      avatarMenu.classList.remove("show");
      avatarInput.click();
    });
  }

  if (deleteBtn) {
    deleteBtn.addEventListener("click", () => {
      if (deleteInput) deleteInput.value = "1";
      avatarMenu.classList.remove("show");
      if (avatarInput) avatarInput.value = "";
      // Prefer data-default-src on <img>, fallback to a static path
      const fallback = "/static/images/default-avatar.png";
      const nextSrc = avatarImg.dataset.defaultSrc || fallback;
      avatarImg.src = nextSrc;
    });
  }

  // Preview selected avatar
  if (avatarInput) {
    avatarInput.addEventListener("change", () => {
      const file = avatarInput.files?.[0];
      if (!file) return;
      const reader = new FileReader();
      reader.onload = (e) => {
        if (e.target?.result) avatarImg.src = e.target.result;
      };
      reader.readAsDataURL(file);
      if (deleteInput) deleteInput.value = "";
    });
  }

  // AJAX profile submit
  profileForm.addEventListener("submit", (e) => {
    e.preventDefault();
    const fd = new FormData(profileForm);
    fetch(profileForm.action || window.location.href, {
      method: "POST",
      body: fd,
      headers: { "X-Requested-With": "XMLHttpRequest" }
    })
      .then((r) => r.json())
      .then((data) => {
        if (data?.success) {
          if (statusEl) {
            statusEl.classList.remove("d-none");
            statusEl.classList.add("text-success");
          }
          if (deleteInput) deleteInput.value = "";
        } else {
          // If server sends a translated message, use it; otherwise, show our i18n fallback
          alert(data?.error || MSG_SAVE_ERROR);
        }
      })
      .catch(() => {
        alert(MSG_NETWORK_ERROR);
      });
  });
});
