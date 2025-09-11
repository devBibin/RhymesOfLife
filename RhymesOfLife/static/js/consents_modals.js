(function () {
  function openModalById(id) {
    var el = document.getElementById(id);
    if (!el) return;
    if (typeof bootstrap === "undefined" || !bootstrap.Modal) {
      // fallback: toggle 'show' classes if Bootstrap JS is not loaded
      el.classList.add("show");
      el.style.display = "block";
      el.removeAttribute("aria-hidden");
      document.body.classList.add("modal-open");
      return;
    }
    var modal = bootstrap.Modal.getOrCreateInstance(el);
    modal.show();
  }

  // click handlers on links
  document.addEventListener("click", function (e) {
    var a = e.target.closest("a.open-modal[data-modal-target]");
    if (!a) return;
    e.preventDefault();
    var id = a.getAttribute("data-modal-target");
    if (id) openModalById(id);
  });

  // optional: support query ?open=patient|expert|tos|privacy
  var params = new URLSearchParams(window.location.search);
  var open = params.get("open");
  if (open) {
    var map = {
      patient: "patientConsentModal",
      expert: "expertConsentModal",
      tos: "tosModal",
      privacy: "privacyModal"
    };
    if (map[open]) openModalById(map[open]);
  }
})();
