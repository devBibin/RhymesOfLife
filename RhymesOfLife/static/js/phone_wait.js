document.addEventListener("DOMContentLoaded", () => {
  const statusBox = document.getElementById("status");
  const dialBox = document.getElementById("dial-status");

  function tick() {
    fetch("/auth/phone/status/", { headers: { "X-Requested-With": "XMLHttpRequest" } })
      .then(r => r.json())
      .then(j => {
        if (j.status === "success" || j.status === "done") {
          statusBox.className = "alert alert-success";
          statusBox.textContent = "Number confirmed. Redirecting…";
          clearInterval(timer);
          setTimeout(() => { window.location.href = j.next || "/consents/"; }, 600);
          return;
        }
        if (j.status === "pending") {
          statusBox.className = "alert alert-info";
          statusBox.textContent = "Waiting for call…";
          dialBox.textContent = j.dial_status ? `Status: ${j.dial_status}` : "";
        } else {
          statusBox.className = "alert alert-danger";
          statusBox.textContent = j.message || "Error";
        }
      })
      .catch(() => {
        statusBox.className = "alert alert-warning";
        statusBox.textContent = "Network error";
      });
  }

  tick();
  const timer = setInterval(tick, 3000);
});