(function () {
  var button = document.querySelector(".nav-toggle");
  var nav = document.getElementById("site-nav");
  if (!button || !nav) return;

  var label = button.querySelector(".toggle-label");
  var openLabel = button.getAttribute("data-open-label") || "Menu";
  var closeLabel = button.getAttribute("data-close-label") || "Close";

  function setOpen(open) {
    document.body.classList.toggle("nav-open", open);
    button.setAttribute("aria-expanded", open ? "true" : "false");
    if (label) label.textContent = open ? closeLabel : openLabel;
  }

  button.addEventListener("click", function () {
    var open = !document.body.classList.contains("nav-open");
    setOpen(open);
    if (open) {
      var first = nav.querySelector("a");
      if (first) first.focus();
    }
  });

  document.addEventListener("keydown", function (event) {
    if (event.key === "Escape" && document.body.classList.contains("nav-open")) {
      setOpen(false);
      button.focus();
    }
  });

  window.addEventListener("resize", function () {
    if (window.matchMedia("(min-width: 1101px)").matches) setOpen(false);
  });

  nav.addEventListener("click", function (event) {
    if (event.target.closest("a")) setOpen(false);
  });
})();
