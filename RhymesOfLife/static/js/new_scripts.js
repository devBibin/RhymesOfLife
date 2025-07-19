document.addEventListener("DOMContentLoaded", () => {
  const avatarImg = document.getElementById("avatar-img");
  const avatarMenu = document.getElementById("avatar-menu");
  const avatarInput = document.getElementById("avatar-input");
  const deleteInput = document.getElementById("delete-avatar");
  const form = document.getElementById("profile-form");
  const status = document.getElementById("form-status");

  if (avatarImg) {
    avatarImg.addEventListener("click", (e) => {
      e.stopPropagation();
      if (avatarMenu) {
        avatarMenu.classList.toggle("show");
      }
    });

    document.getElementById("change-avatar-btn")?.addEventListener("click", () => {
      avatarMenu?.classList.remove("show");
      avatarInput?.click();
    });

    document.getElementById("delete-avatar-btn")?.addEventListener("click", () => {
      if (deleteInput) deleteInput.value = "1";
      avatarMenu?.classList.remove("show");
      if (avatarInput) avatarInput.value = "";
      if (avatarImg) avatarImg.src = "/static/images/default-avatar.png";
    });

    avatarInput?.addEventListener("change", () => {
      const file = avatarInput.files[0];
      if (file && avatarImg) {
        const reader = new FileReader();
        reader.onload = e => {
          avatarImg.src = e.target.result;
        };
        reader.readAsDataURL(file);
        if (deleteInput) deleteInput.value = "";
      }
    });

    document.addEventListener("click", function(e) {
      if (
        avatarMenu &&
        !avatarMenu.contains(e.target) &&
        avatarImg &&
        !avatarImg.contains(e.target)
      ) {
        avatarMenu.classList.remove("show");
      }
    });
  }

  if (form) {
    form.addEventListener("submit", function(e) {
      e.preventDefault();
      const formData = new FormData(form);

      fetch(form.action || window.location.href, {
        method: 'POST',
        body: formData,
        headers: {
          'X-Requested-With': 'XMLHttpRequest'
        }
      })
      .then(res => {
        if (!res.ok) throw new Error("Network response was not ok");
        return res.json();
      })
      .then(data => {
        if (data.success) {
          if (status) {
            status.classList.remove("d-none");
            status.classList.add("text-success");
          }
          if (deleteInput) deleteInput.value = "";
        } else {
          alert(data.error || "Save failed");
        }
      })
      .catch(() => {
        alert("Network error or server error");
      });
    });
  }

  console.log("✅ new_scripts.js загружен");
});
