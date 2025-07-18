document.addEventListener("DOMContentLoaded", () => {
  // Элементы аватара
  const avatarImg = document.getElementById("avatar-img");
  const avatarMenu = document.getElementById("avatar-menu");
  const avatarInput = document.getElementById("avatar-input");
  const deleteInput = document.getElementById("delete-avatar");

  // Форма
  const form = document.getElementById("profile-form");
  const status = document.getElementById("form-status");

  // Логика аватара
  if (avatarImg && avatarMenu) {
    avatarImg.addEventListener("click", () => {
      avatarMenu.classList.toggle("d-none");
    });

    document.getElementById("change-avatar-btn")?.addEventListener("click", () => {
      avatarMenu.classList.add("d-none");
      avatarInput?.click();
    });

    avatarInput?.addEventListener("change", () => {
      const file = avatarInput.files[0];
      if (file) {
        const reader = new FileReader();
        reader.onload = e => {
          avatarImg.src = e.target.result;
        };
        reader.readAsDataURL(file);
        deleteInput.value = "";
      }
    });

    document.getElementById("delete-avatar-btn")?.addEventListener("click", () => {
      deleteInput.value = "1";
      avatarMenu.classList.add("d-none");
      avatarInput.value = "";
      avatarImg.src = "/static/images/default-avatar.png";
    });

    // Скрытие меню при клике вне области
    document.addEventListener("click", function (e) {
      if (!avatarMenu.contains(e.target) && !avatarImg.contains(e.target)) {
        avatarMenu.classList.add("d-none");
      }
    });
  }

  // Обработка формы
  if (form) {
    form.addEventListener("submit", function (e) {
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
            status?.classList.remove("d-none");
            status?.classList.add("text-success");
            deleteInput.value = "";
          } else {
            alert(data.error || "Ошибка сохранения");
          }
        })
        .catch(() => {
          alert("Ошибка сети, попробуйте позже");
        });
    });
  }

  // Отладка
  console.log("✅ new_scripts.js загружен");
});