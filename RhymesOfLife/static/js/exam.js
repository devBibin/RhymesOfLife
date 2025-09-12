document.addEventListener("DOMContentLoaded", () => {
  const _ = (window.gettext) ? window.gettext : (s) => s;

  function normalizeUrlMaybe(u) {
    if (!u) return "";
    let s = String(u).trim();
    if (!s) return "";
    if (!/^https?:\/\//i.test(s)) s = "https://" + s;
    return s;
  }

  const examForm    = document.getElementById("exam-form");
  const dateInput   = document.getElementById("exam_date");
  const descInput   = document.getElementById("description");
  const csrfEl      = document.querySelector("[name=csrfmiddlewaretoken]");
  if (!examForm || !dateInput || !descInput || !csrfEl) return;
  const csrfToken   = csrfEl.value;

  const dropZone    = document.getElementById("drop-zone");
  const fileInput   = document.getElementById("file-input");
  const fileList    = document.getElementById("file-list");
  const submitBtn   = document.getElementById("submit-exam");
  const examIdInput = document.getElementById("exam_id");
  let filesToUpload = [];

  const linkList   = document.getElementById("link-list");
  const addLinkBtn = document.getElementById("add-link-btn");
  const singleLink = document.getElementById("external_url");

  function addLinkInput(prefill = "") {
    const wrap = document.createElement("div");
    wrap.className = "link-item";
    wrap.innerHTML = `
      <input type="url" class="form-control ext-link" placeholder="${_('Paste link')}" value="${prefill}">
      <button type="button" class="btn btn-sm btn-outline-danger remove-link-btn" aria-label="${_('Remove link')}">✖</button>
    `;
    linkList.appendChild(wrap);
    wrap.querySelector(".remove-link-btn").onclick = () => wrap.remove();
  }

  if (addLinkBtn && linkList) {
    addLinkBtn.addEventListener("click", () => addLinkInput(""));
  }

  if (dropZone && fileInput && fileList) {
    dropZone.addEventListener("click", e => { if (!e.target.closest(".dropdown")) fileInput.click(); });
    dropZone.addEventListener("dragover", e => { e.preventDefault(); dropZone.classList.add("dragover"); });
    dropZone.addEventListener("dragleave", () => dropZone.classList.remove("dragover"));
    dropZone.addEventListener("drop", e => { e.preventDefault(); dropZone.classList.remove("dragover"); handleFiles(e.dataTransfer.files); });
    fileInput.addEventListener("change", e => handleFiles(e.target.files));

    function handleFiles(list) {
      Array.from(list).forEach(file => {
        const ext = file.name.split('.').pop().toLowerCase();
        if (!['pdf','jpg','jpeg','png'].includes(ext)) {
          alert(_('Unsupported file type: %(name)s').replace('%(name)s', file.name));
          return;
        }
        if (filesToUpload.some(f => f.name===file.name && f.size===file.size)) return;
        filesToUpload.push(file);
        renderFileCard(file);
      });
      attachRemoveHandlers();
    }

    function renderFileCard(file) {
      const div = document.createElement("div");
      div.className = "file-card d-flex justify-content-between align-items-center border p-2 mb-2 rounded";
      div.dataset.name = file.name; div.dataset.size = file.size;
      div.innerHTML = `
        <span class="me-2">📎 <strong>${file.name}</strong></span>
        <button type="button" class="btn btn-sm btn-outline-danger remove-file-btn"
                data-name="${file.name}" data-size="${file.size}" aria-label="${_('Remove file')}">✖</button>
      `;
      fileList.appendChild(div);
    }

    function attachRemoveHandlers() {
      document.querySelectorAll(".remove-file-btn").forEach(btn => {
        btn.onclick = () => {
          const { name, size } = btn.dataset;
          filesToUpload = filesToUpload.filter(f => !(f.name===name && f.size==size));
          btn.closest(".file-card")?.remove();
        };
      });
    }
  }

  if (submitBtn) {
    submitBtn.addEventListener("click", () => {
      if (!dateInput.value) { alert(_("Please specify the exam date.")); return; }
      const fd = new FormData();
      fd.append("exam_date", dateInput.value);
      fd.append("description", (descInput.value || "").trim());

      if (singleLink && singleLink.value.trim()) {
        const norm = normalizeUrlMaybe(singleLink.value);
        fd.append("external_url", norm);
      }

      const multiLinks = Array.from(document.querySelectorAll(".ext-link"))
        .map(inp => normalizeUrlMaybe(inp.value))
        .filter(v => v.length > 0);
      multiLinks.forEach(u => fd.append("external_urls[]", u));

      filesToUpload.forEach(f => fd.append("files", f));

      const id = examIdInput?.value || "";
      const url = id ? `/api/exams/${id}/` : window.location.href;

      fetch(url, {
        method: "POST",
        headers: { "X-CSRFToken": csrfToken, "X-Requested-With": "XMLHttpRequest" },
        body: fd
      })
      .then(r => r.json())
      .then(j => {
        if (j.status === "ok") {
          location.reload();
        } else {
          alert(j.message || _("Failed to save."));
        }
      })
      .catch(() => alert(_("Network error.")));
    });
  }

  document.querySelectorAll(".edit-exam-btn").forEach(btn => {
    btn.addEventListener("click", () => {
      const id = btn.dataset.id; if (!id) return;
      fetch(`/api/exams/${id}/`, { headers:{"X-Requested-With":"XMLHttpRequest"} })
      .then(r=>r.json())
      .then(data => {
        examIdInput.value = data.id;
        dateInput.value   = data.exam_date;
        descInput.value   = data.description || "";
        if (fileList) fileList.innerHTML = "";
        (data.documents || []).forEach(doc => {
          const div = document.createElement("div");
          div.className = "file-card d-flex justify-content-between align-items-center border p-2 mb-2 rounded";
          div.innerHTML = `
            <a href="${doc.url}" target="_blank" class="text-decoration-none me-2" rel="noopener noreferrer">
              📎 <strong>${doc.name}</strong>
            </a>
            <button class="btn btn-sm btn-outline-danger remove-existing-file-btn" data-id="${doc.id}" aria-label="${_('Remove file')}">✖</button>
          `;
          fileList && fileList.appendChild(div);
        });
        document.getElementById("exam-form").scrollIntoView({ behavior:"smooth" });
        attachExistingRemove();
      })
      .catch(()=>alert(_("Unable to load data.")));
    });
  });

  document.querySelectorAll(".delete-exam-btn").forEach(btn => {
    btn.addEventListener("click", () => {
      const id = btn.dataset.id;
      if (!id) return;
      if (!confirm(_("Delete this exam?"))) return;
      fetch(`/api/exams/${id}/`, {
        method: "DELETE",
        headers:{"X-CSRFToken":csrfToken,"X-Requested-With":"XMLHttpRequest"}
      })
      .then(r=>r.json())
      .then(j=>{ if(j.status==="ok") location.reload(); else alert(_("Deletion failed.")); })
      .catch(()=>alert(_("Network error.")));
    });
  });

  function attachExistingRemove() {
    document.querySelectorAll(".remove-existing-file-btn").forEach(btn => {
      btn.addEventListener("click", () => {
        const id = btn.dataset.id;
        if (!id) return;
        if (!confirm(_("Delete this file?"))) return;
        fetch(`/api/documents/${id}/`, {
          method:"DELETE",
          headers:{"X-CSRFToken":csrfToken,"X-Requested-With":"XMLHttpRequest"}
        })
        .then(r=>r.json())
        .then(j=>{ if(j.status==="ok") btn.closest(".file-card")?.remove(); else alert(_("Deletion failed.")); })
        .catch(()=>alert(_("Network error.")));
      });
    });
  }
});
