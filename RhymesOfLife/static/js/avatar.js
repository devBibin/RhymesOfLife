document.addEventListener("DOMContentLoaded", () => {
  if (window.__avatarInit) return;
  window.__avatarInit = true;

  const avatarImg    = document.getElementById("avatar-img");
  const avatarMenu   = document.getElementById("avatar-menu");
  const avatarInput  = document.getElementById("avatar-input");
  const deleteInput  = document.getElementById("delete-avatar");
  const changeBtn    = document.getElementById("change-avatar-btn");
  const deleteBtn    = document.getElementById("delete-avatar-btn");
  const profileForm  = document.getElementById("profile-form");
  const fallbackSrc  = (avatarImg && avatarImg.dataset.defaultSrc) || "/static/images/default-avatar.png";

  const submitForm = () => { if (profileForm) profileForm.submit(); };

  if (avatarImg) {
    avatarImg.addEventListener("click", (e) => {
      e.stopPropagation();
      if (avatarMenu) avatarMenu.classList.toggle("show");
    });
    avatarImg.addEventListener("error", () => { avatarImg.src = fallbackSrc; });
  }

  document.addEventListener("click", (e) => {
    if (!avatarMenu || !avatarImg) return;
    if (!avatarMenu.contains(e.target) && !avatarImg.contains(e.target)) {
      avatarMenu.classList.remove("show");
    }
  });

  if (changeBtn && avatarInput) {
    changeBtn.addEventListener("click", () => {
      if (avatarMenu) avatarMenu.classList.remove("show");
      if (deleteInput) deleteInput.value = "";
      avatarInput.click();
    });
  }

  if (deleteBtn) {
    deleteBtn.addEventListener("click", () => {
      if (deleteInput) deleteInput.value = "1";
      if (avatarMenu) avatarMenu.classList.remove("show");
      if (avatarInput) avatarInput.value = "";
      if (avatarImg) avatarImg.src = fallbackSrc;
      submitForm();
    });
  }

  if (avatarInput) {
    avatarInput.addEventListener("change", () => {
      const file = avatarInput.files && avatarInput.files[0];
      if (!file) return;
      if (deleteInput) deleteInput.value = "";

      const reader = new FileReader();
      reader.onload = (e) => {
        if (avatarImg && e.target && e.target.result) {
          avatarImg.src = e.target.result;
        }
      };
      reader.readAsDataURL(file);

      submitForm();
    });
  }
});
