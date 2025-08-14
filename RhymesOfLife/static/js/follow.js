document.addEventListener("DOMContentLoaded", function () {
  const _ = (window.gettext) ? window.gettext : (s) => s;

  const btn = document.getElementById("follow-button");
  if (!btn) return;

  btn.addEventListener("click", async () => {
    const isFollowing = btn.dataset.following === "true";
    const url = isFollowing ? btn.dataset.unfollowUrl : btn.dataset.followUrl;
    const csrftoken = document.querySelector('[name=csrfmiddlewaretoken]').value;

    const resp = await fetch(url, {
      method: "POST",
      headers: {
        "X-CSRFToken": csrftoken,
        "X-Requested-With": "XMLHttpRequest",
      },
    });

    if (resp.ok) {
      btn.dataset.following = (!isFollowing).toString();
      btn.textContent = isFollowing ? _("Follow") : _("Unfollow");
      btn.classList.toggle("btn-outline-primary");
      btn.classList.toggle("btn-outline-danger");
    }
  });
});
