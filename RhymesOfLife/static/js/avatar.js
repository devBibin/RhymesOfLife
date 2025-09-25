document.addEventListener("DOMContentLoaded", () => {
  const avatarImg   = document.getElementById("avatar-img");
  const avatarMenu  = document.getElementById("avatar-menu");
  const avatarInput = document.getElementById("avatar-input");
  const deleteInput = document.getElementById("delete-avatar");
  const changeBtn   = document.getElementById("change-avatar-btn");
  const deleteBtn   = document.getElementById("delete-avatar-btn");

  if (!avatarImg || !avatarMenu) return;

  avatarImg.addEventListener("click", (e) => {
    e.stopPropagation();
    avatarMenu.classList.toggle("show");
  });
  document.addEventListener("click", (e) => {
    if (!avatarMenu.contains(e.target) && !avatarImg.contains(e.target)) {
      avatarMenu.classList.remove("show");
    }
  });

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
      const fallback = avatarImg.dataset.defaultSrc || "/static/images/default-avatar.png";
      avatarImg.src = fallback;
    });
  }

  if (avatarInput) {
    avatarInput.addEventListener("change", () => {
      const file = avatarInput.files && avatarInput.files[0];
      if (!file) return;
      const reader = new FileReader();
      reader.onload = (e) => {
        if (e.target && e.target.result) avatarImg.src = e.target.result;
      };
      reader.readAsDataURL(file);
      if (deleteInput) deleteInput.value = "";
    });
  }
});
