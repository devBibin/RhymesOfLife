document.addEventListener("DOMContentLoaded", () => {
  // ----------- AVATAR ----------------
  const avatarImg = document.getElementById("avatar-img");
  const avatarMenu = document.getElementById("avatar-menu");
  const avatarInput = document.getElementById("avatar-input");
  const deleteInput = document.getElementById("delete-avatar");
  const profileForm = document.getElementById("profile-form");
  const status = document.getElementById("form-status");

  if (avatarImg) {
    avatarImg.addEventListener("click", (e) => {
      e.stopPropagation();
      avatarMenu?.classList.toggle("show");
    });

    document.getElementById("change-avatar-btn")?.addEventListener("click", () => {
      avatarMenu?.classList.remove("show");
      avatarInput?.click();
    });

    document.getElementById("delete-avatar-btn")?.addEventListener("click", () => {
      if (deleteInput) deleteInput.value = "1";
      avatarMenu?.classList.remove("show");
      if (avatarInput) avatarInput.value = "";
      avatarImg.src = "/static/images/default-avatar.png";
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

    document.addEventListener("click", function (e) {
      if (
        avatarMenu &&
        !avatarMenu.contains(e.target) &&
        !avatarImg.contains(e.target)
      ) {
        avatarMenu.classList.remove("show");
      }
    });
  }

  if (profileForm) {
    profileForm.addEventListener("submit", function (e) {
      e.preventDefault();
      const formData = new FormData(profileForm);

      fetch(profileForm.action || window.location.href, {
        method: 'POST',
        body: formData,
        headers: {
          'X-Requested-With': 'XMLHttpRequest'
        }
      })
        .then(res => res.json())
        .then(data => {
          if (data.success) {
            status?.classList.remove("d-none");
            status?.classList.add("text-success");
            if (deleteInput) deleteInput.value = "";
          } else {
            alert(data.error || "Ошибка при сохранении.");
          }
        })
        .catch(() => {
          alert("Ошибка сети или сервера.");
        });
    });
  }

  // ----------- DRAG & DROP EXAM ----------------
  const dropZone = document.getElementById("drop-zone");
  const fileInput = document.getElementById("file-input");
  const fileList = document.getElementById("file-list");
  const submitBtn = document.getElementById("submit-exam");
  const csrfToken = document.querySelector("[name=csrfmiddlewaretoken]")?.value;

  let filesToUpload = [];

  function attachRemoveEvents() {
    document.querySelectorAll(".remove-file-btn").forEach(btn => {
      btn.addEventListener("click", () => {
        const name = btn.dataset.name;
        const size = parseInt(btn.dataset.size);
        filesToUpload = filesToUpload.filter(f => !(f.name === name && f.size === size));
        const div = btn.closest(".file-card");
        div?.remove();
      });
    });
  }

  function attachRemoveExistingEvents() {
    document.querySelectorAll(".remove-existing-file-btn").forEach(btn => {
      btn.addEventListener("click", () => {
        const docId = btn.dataset.id;
        if (!confirm("Удалить файл?")) return;

        fetch(`/api/documents/${docId}/`, {
          method: "DELETE",
          headers: {
            "X-CSRFToken": csrfToken,
            "X-Requested-With": "XMLHttpRequest"
          }
        })
          .then(res => res.json())
          .then(data => {
            if (data.status === "ok") {
              btn.closest(".file-card").remove();
            } else {
              alert("Ошибка при удалении файла");
            }
          })
          .catch(() => alert("Ошибка соединения с сервером"));
      });
    });
  }

  function handleFiles(files) {
    for (const file of files) {
      if (filesToUpload.some(f => f.name === file.name && f.size === file.size)) {
        continue;
      }

      filesToUpload.push(file);

      const div = document.createElement("div");
      div.className = "file-card d-flex justify-content-between align-items-center border p-2 mb-2 rounded";
      div.dataset.name = file.name;
      div.dataset.size = file.size;

      div.innerHTML = `
        <span class="me-2">📎 <strong>${file.name}</strong></span>
        <button type="button" class="btn btn-sm btn-outline-danger remove-file-btn" data-name="${file.name}" data-size="${file.size}">✖</button>
      `;

      fileList.appendChild(div);
    }

    attachRemoveEvents();
  }

  if (dropZone && fileInput && submitBtn) {
    dropZone.addEventListener("click", () => fileInput.click());

    dropZone.addEventListener("dragover", (e) => {
      e.preventDefault();
      dropZone.classList.add("dragover");
    });

    dropZone.addEventListener("dragleave", () => {
      dropZone.classList.remove("dragover");
    });

    dropZone.addEventListener("drop", (e) => {
      e.preventDefault();
      dropZone.classList.remove("dragover");
      handleFiles(e.dataTransfer.files);
    });

    fileInput.addEventListener("change", (e) => {
      handleFiles(e.target.files);
    });

    submitBtn.addEventListener("click", () => {
      const examId = examIdInput.value;
      const examDate = examDateInput.value;
      const description = descriptionInput.value;

      if (!examDate) {
        alert("Укажите дату обследования");
        return;
      }

      const formData = new FormData();
      formData.append("exam_date", examDate);
      formData.append("description", description);
      filesToUpload.forEach(file => {
        formData.append("files", file);
      });

      const url = examId ? `/api/exams/${examId}/` : window.location.href;
      const method = examId ? "PUT" : "POST";

      fetch(url, {
        method,
        body: formData,
        headers: {
          "X-CSRFToken": csrfToken,
          "X-Requested-With": "XMLHttpRequest"
        }
      })
        .then(res => res.json())
        .then(data => {
          if (data.status === "ok") {
            filesToUpload = [];
            fileList.innerHTML = "";
            window.location.reload();
          } else {
            alert(data.message || "Ошибка при сохранении");
          }
        })
        .catch(() => alert("Ошибка сети"));
    });
  }

  // ----------- EDIF / DELETE FILES ----------------
  const examForm = document.getElementById("exam-form");
  const examIdInput = document.getElementById("exam_id");
  const examDateInput = document.getElementById("exam_date");
  const descriptionInput = document.getElementById("description");

  function clearExamForm() {
    examIdInput.value = "";
    examDateInput.value = "";
    descriptionInput.value = "";
    fileInput.value = "";
    fileList.innerHTML = "";
    filesToUpload = [];
  }

  document.querySelectorAll(".edit-exam-btn").forEach(btn => {
    btn.addEventListener("click", () => {
      const examId = btn.dataset.id;

      fetch(`/api/exams/${examId}/`, {
        headers: {
          "X-Requested-With": "XMLHttpRequest"
        }
      })
        .then(res => res.json())
        .then(data => {
          examIdInput.value = data.id;
          examDateInput.value = data.exam_date;
          descriptionInput.value = data.description;
          fileList.innerHTML = "";
          filesToUpload = [];

          data.documents.forEach(doc => {
            const div = document.createElement("div");
            div.className = "file-card d-flex justify-content-between align-items-center border p-2 mb-2 rounded";
            div.innerHTML = `
              <a href="${doc.url}" target="_blank" class="text-decoration-none me-2">📎 <strong>${doc.name}</strong></a>
              <button class="btn btn-sm btn-outline-danger remove-existing-file-btn" data-id="${doc.id}">✖</button>
            `;
            fileList.appendChild(div);
          });

          attachRemoveExistingEvents();
          window.scrollTo({ top: examForm.offsetTop, behavior: "smooth" });
        })
        .catch(() => alert("Не удалось загрузить обследование"));
    });
  });

  document.querySelectorAll(".delete-exam-btn").forEach(btn => {
    btn.addEventListener("click", () => {
      const examId = btn.dataset.id;
      if (!confirm("Удалить это обследование?")) return;

      fetch(`/api/exams/${examId}/`, {
        method: "DELETE",
        headers: {
          "X-CSRFToken": csrfToken,
          "X-Requested-With": "XMLHttpRequest"
        }
      })
        .then(res => {
          if (res.ok) {
            window.location.reload();
          } else {
            alert("Ошибка при удалении");
          }
        })
        .catch(() => alert("Ошибка соединения с сервером"));
    });
  });

  console.log("✅ new_scripts.js загружен полностью");
});
