document.addEventListener("DOMContentLoaded", function () {
    console.log("JavaScript is loaded and working!");

    let heading = document.getElementById("welcome-heading");
    if (heading) {
        heading.addEventListener("click", function () {
            heading.style.color = "red";
        });
    }
});
